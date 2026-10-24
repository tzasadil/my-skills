#!/usr/bin/env python3
"""Mine Claude Code sessions into a per-repo rule inbox, and keep receipts for applied standards.

Pipeline:
  SessionEnd hook -> `hook` detaches `mine` -> the configured miner CLI runs a retrospective
  (the lenses in `lenses.md`) over a condensed transcript, plus the failed tool calls of its
  subagents (`<session>/subagents/`) and every `debugging-duck` report -> verified proposals
  land in the repo's inbox -> desktop notification.
  Every `compose_every` mined sessions, the same run continues with `compose`: one miner call
  per inbox merges duplicates and combines scattered candidates of one root cause. Then one
  call over all repo inboxes promotes a problem that recurs across repos to the shared inbox.
  Other skills file candidates with `add` (JSON on stdin).
  Each candidate carries `source: {by, lens}`, and triage outcomes are counted per source,
  so `status` shows which pass or lens proposes noise.
  The user empties the inbox with the `rule-forge` skill: `accept` or `drop` each candidate.
  Each drop is kept with its reason and shown to later miner runs, so a rejected rule stays rejected.

Files in ~/.agents/rule-forge/ (override: RULE_FORGE_DIR). Nothing lands in the repo itself.
Repo files are named after the main checkout dir, also for jj workspaces and git worktrees.
  <repo>.json           candidates `C<n>` whose fix lives in the repo, each with receipts,
                        plus `dropped` (rejected rules with reasons) and triage `stats`
  _shared.json          same shape, candidates `G<n>` of SHARED_KINDS: one inbox for every repo
  <repo>.receipts.json  receipts per `CODING_STANDARDS.md` rule `(S<n>)`

Config: `config.json` in the skill dir, or the path in RULE_FORGE_CONFIG.
  command: key into `commands`, each an argv list.
    `{prompt}` in an element -> replaced by the prompt. No placeholder -> prompt on stdin.
    The prompt holds the instructions. The transcript goes to a file the prompt points at,
    so the miner needs a file read tool. A headless CLI that asks before a tool call (`agy`)
    ends the turn with empty output: give it a skip-permissions flag. The prompt keeps it read
    only.
  roots: only repos under these dirs are mined. Empty -> every repo.
  fallback: optional key into `commands`. Runs when the primary command fails (usage limit,
    timeout, crash) or answers with no JSON array. Its failure fails the run.
  timeout_s, min_user_messages, max_transcript_bytes, enabled.
  compose_every: mined sessions between `compose` runs. 0 -> never.
  notify: desktop notification after a successful run. A failed run always notifies.

Install: add to `hooks` in ~/.claude/settings.json
  "SessionEnd": [{"hooks": [{"type": "command",
    "command": "python3 /data/src/my-skills/skills/rule-forge/scripts/rule_forge.py hook"}]}]

Failed runs: failed.json in the state dir lists every run that failed and has not succeeded
  since, each with a `rerun` shell command. `status` prints the list. A later success of the
  same transcript (or of `compose`) removes its entry. `retry` reruns them all (run it from a timer for
  automatic retries). An agent can also read the file.

State and log: $RULE_FORGE_STATE_DIR, else $XDG_STATE_HOME/rule-forge/ (default ~/.local/state/rule-forge/).
  runs.json stamps the last run per repo and the last error. The detached miner has no other
  proof that it ran, so `status` warns when the stamps say mining stopped. It also counts
  miner proposals and how many were invalid (bad shape, or a quote not in the transcript): a measure of the miner's quality.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import fcntl
import hashlib
import json
import os
import pathlib
import re
import shlex
import signal
import string
import subprocess
import sys
import tempfile

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
PROMPT_TEMPLATE = SKILL_DIR / "miner-prompt.md"
COMPOSE_TEMPLATE = SKILL_DIR / "compose-prompt.md"
PROMOTE_TEMPLATE = SKILL_DIR / "promote-prompt.md"
# One lens list for the miner, the composer, and manual `/retrospective` runs.
LENSES_FILE = SKILL_DIR / "lenses.md"
# RULE_FORGE_STATE_DIR moves only this tool's state. Overriding XDG_STATE_HOME instead also
# moves the miner CLI's own state: `opencode` then misses its running service and fails.
STATE_DIR = pathlib.Path(
    os.environ.get("RULE_FORGE_STATE_DIR")
    or pathlib.Path(
        os.environ.get("XDG_STATE_HOME") or pathlib.Path.home() / ".local" / "state"
    )
    / "rule-forge"
)
GLOBAL_RULES = pathlib.Path.home() / ".claude" / "CLAUDE.md"
# Where `global-rule` candidates land. Shown to the miner as coverage => no re-proposals.
IMPLEMENTER_RULES = SKILL_DIR.parent / "with-implementer" / "implementer-rules.md"

RUNS = STATE_DIR / "runs.json"
# Runs that failed and have not succeeded since, keyed by transcript path (or "compose").
FAILED = STATE_DIR / "failed.json"
COMPOSE_KEY = "compose"
# A repo worked in weekly ends a session within this many days. No run for longer -> suspect the hook.
STALE_DAYS = 7

INBOX_DIR = pathlib.Path(
    os.environ.get("RULE_FORGE_DIR") or pathlib.Path.home() / ".agents" / "rule-forge"
)
STANDARDS = "CODING_STANDARDS.md"
SHARED = "_shared"  # file stem and lock name of the shared inbox

# Kinds whose fix lives outside any one repo: user-level skills and implementer rules. Filed per
# repo, one finding splits across inboxes and a triage in one repo never sees the rest.
# TODO: a repo-local skill (`.claude/skills/` inside a repo) also routes here. Upgrade path:
# route `skill` by where the named skill lives. Revisit when a repo gets its own skills.
SHARED_KINDS = ("skill", "global-rule", "harness")
# TODO: a `harness` fix can be repo-local (a no-op line in one repo's AGENTS.md, a repo's dev
# server log). It still lands in the shared inbox. Upgrade path: let the miner mark `local`
# and route by it. Revisit when triage meets a repo-specific harness candidate.
# Why the user rejected a candidate. Fixed values so `status` can count them: one reason
# dominating points at the miner prompt rule that lets those through.
DROP_REASONS = ("weak", "generic", "not-a-mistake", "wrong", "other")
# Rejected candidates shown to the miner per inbox, newest first. Older ones leave the prompt.
REJECTED_IN_PROMPT = 40

# Set on the detached miner run. A miner that is itself Claude Code would fire SessionEnd
# again on exit -> endless mining without this guard.
CHILD_ENV = "RULE_FORGE_CHILD"

KINDS = (
    "coding-standard",
    "automated-check",
    "agents-md",
    "global-rule",
    "skill",
    "harness",
)
# `duck`: a `debugging-duck` report. Its findings are the top-priority source.
SPEAKERS = ("user", "agent", "tool", "duck")
STANDARD_ID_RE = re.compile(r"\((S\d+)\)")
# A rule seen in fewer repos may still be local to those codebases: promote only past this.
MIN_PROMOTE_REPOS = 3
LENS_RE = re.compile(r"^## ([a-z-]+)\n- Kind: `([a-z-]+)`", re.MULTILINE)
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)

# Harness wrappers inside user messages. None of them is the user speaking.
NOISE_RE = re.compile(
    r"<(ide_opened_file|ide_selection|system-reminder|local-command-stdout|local-command-caveat)>.*?</\1>",
    re.DOTALL,
)
NOT_HUMAN_PREFIXES = (
    "<task-notification>",
    "[Request interrupted",
    "<command-",
    "<local-command",
    "Base directory for this skill",
    "Another Claude session sent a message",
    "<bash-input>",
    "<bash-stdout>",
    "<bash-stderr>",
)
# Per-entry caps. The user's words carry most signal -> largest cap.
USER_CHARS = 3000
AGENT_CHARS = 1500
TOOL_INPUT_CHARS = 200
# A subagent brief is where the agent re-teaches codebase gotchas -> keep far more of it.
SUBAGENT_TOOLS = ("Agent", "Task")
SUBAGENT_INPUT_CHARS = 2500
TOOL_ERROR_CHARS = 600
DUCK_AGENT = "debugging-duck"
# Observed duck reports run 0.7k to 6.8k chars. A cut tail fails quote checks.
DUCK_CHARS = 10000
# Each context section (global rules, AGENTS.md, standards, open and rejected candidates).
CONTEXT_CHARS = 8000
# Shorter quotes match by chance, so they prove nothing.
MIN_QUOTE_CHARS = 12


# ---------- pure core ----------


def one_line(text: str) -> str:
    return " ".join(text.split())


def parse_lenses(text: str) -> dict[str, str]:
    """`lenses.md` -> {lens: kind}. The miner names a lens, the kind follows from it."""
    lenses = dict(LENS_RE.findall(text))
    bad = {l: k for l, k in lenses.items() if k not in KINDS}
    if not lenses or bad:
        raise SystemExit(
            f"{LENSES_FILE}: need `## <lens>` + `- Kind: `<kind>`` entries with kinds in "
            f"{KINDS}. Found {lenses or 'none'}"
        )
    return lenses


def human_text(text: str) -> str:
    """The user's own words in one message, or "" for harness-generated messages."""
    text = NOISE_RE.sub("", text).strip()
    if not text or text.startswith(NOT_HUMAN_PREFIXES):
        return ""
    return text


def condense(records: list[dict]) -> tuple[str, int]:
    """Transcript records -> (miner-readable text, count of real user messages).

    Keeps the user's words, agent prose, tool names with short inputs, and failed tool
    results. Drops thinking, successful tool output, and harness metadata: they cost prompt
    budget and rarely show a correction. Of a sidechain (a subagent run) only failed tool
    results stay: its `user` records are the parent agent's brief and tool results, never
    the human, so they must not count as user messages or pass as `[user]` quotes.
    """
    out: list[str] = []
    user_messages = 0
    for r in records:
        sidechain = bool(r.get("isSidechain"))
        # Compact summaries paraphrase the session in a user-role record: not the user speaking.
        if (
            r.get("isMeta")
            or r.get("isCompactSummary")
            or r.get("type") not in ("user", "assistant")
        ):
            continue
        content = (r.get("message") or {}).get("content")
        blocks = (
            [{"type": "text", "text": content}]
            if isinstance(content, str)
            else content or []
        )
        for b in blocks:
            if not isinstance(b, dict):
                continue
            kind = b.get("type")
            if sidechain and not (kind == "tool_result" and b.get("is_error")):
                continue
            if r["type"] == "user" and kind == "text":
                text = human_text(b.get("text", ""))
                if text:
                    user_messages += 1
                    out.append(f"[user] {text[:USER_CHARS]}")
            elif r["type"] == "user" and kind == "tool_result" and b.get("is_error"):
                body = b.get("content")
                body = (
                    body
                    if isinstance(body, str)
                    else " ".join(
                        c.get("text", "") for c in body or [] if isinstance(c, dict)
                    )
                )
                out.append(f"[tool error] {one_line(body)[:TOOL_ERROR_CHARS]}")
            elif (
                r["type"] == "assistant"
                and kind == "text"
                and b.get("text", "").strip()
            ):
                out.append(f"[agent] {b['text'].strip()[:AGENT_CHARS]}")
            elif r["type"] == "assistant" and kind == "tool_use":
                args = one_line(json.dumps(b.get("input"), ensure_ascii=False))
                cap = (
                    SUBAGENT_INPUT_CHARS
                    if b.get("name") in SUBAGENT_TOOLS
                    else TOOL_INPUT_CHARS
                )
                out.append(f"[tool {b.get('name')}] {args[:cap]}")
    return "\n".join(out), user_messages


def subagent_header(meta: dict) -> str:
    """Label line for one subagent's block, from its `.meta.json`. Not a speaker line, so
    `speaker_text` never accepts a quote from it."""
    what = ": ".join(str(meta[k]) for k in ("agentType", "description") if meta.get(k))
    return f"[subagent {what}]" if what else "[subagent]"


def turn_reports(records: list[dict]) -> list[str]:
    """Each `end_turn` text of one subagent run: its report, plus one per `SendMessage`
    follow-up. The stop reason marks a finished report => a preamble before tool calls, or
    a turn still running at mining time, never passes as one."""
    reports = []
    for r in records:
        message = r.get("message") or {}
        if r.get("type") != "assistant" or message.get("stop_reason") != "end_turn":
            continue
        content = message.get("content")
        texts = [
            b["text"]
            for b in (content if isinstance(content, list) else [])
            if isinstance(b, dict)
            and b.get("type") == "text"
            and b.get("text", "").strip()
        ]
        reports += texts[-1:]
    return reports


def fit_tail(text: str, max_bytes: int) -> str:
    """Keep the end of `text` within `max_bytes` of UTF-8. A cost cap for very long sessions."""
    raw = text.encode()
    if len(raw) <= max_bytes:
        return text
    return "[earlier part truncated]\n" + raw[-max_bytes:].decode(errors="ignore")


def section(text: str) -> str:
    """One prompt context section, capped. A cut is marked so the miner knows it saw a part."""
    if not text.strip():
        return "(none)"
    return (
        text if len(text) <= CONTEXT_CHARS else text[:CONTEXT_CHARS] + "\n[truncated]"
    )


def build_prompt(
    template: str,
    *,
    global_rules: str,
    implementer_rules: str,
    agents_md: str,
    standards: str,
    lenses: str,
    open_items: str,
    rejected: str,
    transcript_file: str,
) -> str:
    """Fill the miner prompt. The transcript itself stays in `transcript_file`."""
    return string.Template(template).safe_substitute(
        global_rules=section(global_rules),
        implementer_rules=section(implementer_rules),
        agents_md=section(agents_md),
        standards=section(standards),
        lenses=lenses,
        open_items=section(open_items),
        rejected=section(rejected),
        transcript_file=transcript_file,
    )


def parse_output(stdout: str) -> list:
    """Miner stdout -> the JSON array it answered with.

    CLIs wrap the answer in banners (opencode prints `> build · <model>`) or code fences,
    so try the whole text, then each fence, then the outermost brackets.
    """
    text = ANSI_RE.sub("", stdout).strip()
    tries = [text, *FENCE_RE.findall(text)]
    if "[" in text and "]" in text:
        tries.append(text[text.index("[") : text.rindex("]") + 1])
    for t in tries:
        with contextlib.suppress(json.JSONDecodeError):
            value = json.loads(t)
            if isinstance(value, list):
                return value
    raise ValueError(f"miner output holds no JSON array. Start: {text[:200]!r}")


def parse_records(lines: list[str]) -> tuple[list[dict], int, int]:
    """Transcript lines -> (records, lines consumed, skipped corrupt lines).

    A broken last line is a record still being written: leave it unconsumed, so the next run
    reads it whole. A broken line earlier in the file never heals -> skip it.
    """
    records, skipped, consumed = [], 0, len(lines)
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            if i == len(lines) - 1:
                consumed = i
            else:
                skipped += 1
    return records, consumed, skipped


def quote_found(quote: str, haystack: str) -> bool:
    """True when every `…`-separated fragment of `quote` appears in order in `haystack`."""
    pos = 0
    for part in (one_line(p) for p in re.split(r"…|\.\.\.", quote)):
        if not part:
            continue
        pos = haystack.find(part, pos)
        if pos < 0:
            return False
        pos += len(part)
    return True


def speaker_text(transcript: str, speaker: str) -> str:
    """Flattened text of one speaker's lines. A quote must come from the speaker it claims."""
    prefix = "[tool" if speaker == "tool" else f"[{speaker}]"
    lines, keep = [], False
    for line in transcript.splitlines():
        if line.startswith(
            "["
        ):  # a new entry starts. Continuation lines belong to the last one
            keep = line.startswith(prefix)
        if keep:
            lines.append(line)
    return one_line("\n".join(lines))


def check_proposal(
    item, transcript: str, known_ids: set[str], lenses: dict[str, str]
) -> str | None:
    """Reason the miner's item is unusable, or None. Validates the untrusted boundary."""
    if not isinstance(item, dict):
        return "not an object"
    receipts = item.get("receipts")
    if not isinstance(receipts, list) or not receipts:
        return "no receipts"
    for r in receipts:
        if isinstance(r, dict) and isinstance(r.get("speaker"), str):
            r["speaker"] = (r["speaker"].split() or [""])[
                0
            ]  # models echo the line prefix: "tool error"
        if (
            not isinstance(r, dict)
            or r.get("speaker") not in SPEAKERS
            or not isinstance(r.get("quote"), str)
        ):
            return f"bad receipt shape: {r!r}"[:200]
        if len(one_line(r["quote"])) < MIN_QUOTE_CHARS:
            return f"quote under {MIN_QUOTE_CHARS} chars: {r['quote']!r}"
        if not quote_found(r["quote"], speaker_text(transcript, r["speaker"])):
            return f"quote not in {r['speaker']} lines: {r['quote'][:120]!r}"
    if "supports" in item:
        if not isinstance(item["supports"], str) or item["supports"] not in known_ids:
            return f"supports unknown id {item['supports']!r}"
        if not all(isinstance(item.get(k, ""), str) for k in ("rule", "class")):
            return "rule and class must be strings"
        return None
    lens = item.get("lens")
    if not isinstance(lens, str) or lens not in lenses:
        return f"unknown lens {lens!r}"
    if not all(
        isinstance(item.get(k), str) and item[k].strip() for k in ("rule", "class")
    ):
        return "rule and class must be non-empty strings"
    item["kind"] = lenses[item["lens"]]
    return None


def stamp(receipts: list[dict], *, date: str, session: str) -> list[dict]:
    return [
        {"date": date, "session": session, "speaker": r["speaker"], "quote": r["quote"]}
        for r in receipts
    ]


def same_moment(a: dict, b: dict) -> bool:
    """True when two receipts quote the same message of one session: one quote holds the other.

    Re-mining a resumed session quotes a correction again with a wider or narrower span,
    and models file one message whole and in part. Either way it is one moment, not a repeat.
    Trade-off: a later repeat in the same session that contains the earlier words is lost too.
    Repeats across sessions, the signal that matters, are never affected.
    """
    if a["session"] != b["session"]:
        return False
    qa, qb = one_line(a["quote"]), one_line(b["quote"])
    return qa in qb or qb in qa


def add_receipts(target: dict, receipts: list[dict]) -> int:
    """Append receipts that quote a new moment (see `same_moment`). Returns how many landed."""
    held = target.setdefault("receipts", [])
    added = 0
    for r in receipts:
        if not any(same_moment(r, h) for h in held):
            held.append(r)
            added += 1
    return added


def routes_to_shared(item: dict) -> bool:
    """True when a checked proposal belongs in the shared inbox. Evidence follows its candidate."""
    ref = item.get("supports")
    return ref.startswith("G") if ref else item["kind"] in SHARED_KINDS


def merge_proposals(
    inbox: dict, items: list[dict], *, prefix: str, date: str, by: str
) -> dict[str, int]:
    """Fold checked proposals into one inbox, new ids `<prefix><n>`. Mutates `inbox`, returns counts.

    Receipts arrive stamped with date and session. `date` marks new candidates as created.
    `by` names the pass that filed them, kept in each new candidate's `source`.

    `supports: C<n>` or `G<n>` -> receipts join that candidate.
    `supports: S<n>` -> the applied standard did not prevent this: one `recurrence`
    candidate per standard collects the receipts until the user handles it.
    """
    counts = {"new": 0, "supported": 0}
    by_id = {c["id"]: c for c in inbox["candidates"]}
    for item in items:
        receipts = item["receipts"]
        ref = item.get("supports")
        if ref and not ref.startswith("S"):
            counts["supported"] += bool(add_receipts(by_id[ref], receipts))
            continue
        if ref:
            existing = next(
                (c for c in inbox["candidates"] if c.get("standard") == ref), None
            )
            if existing:
                counts["supported"] += bool(add_receipts(existing, receipts))
                continue
            entry = {
                "kind": "recurrence",
                "standard": ref,
                "rule": item.get("rule")
                or f"{ref} did not prevent this. Add a check, clarify the line, or retire it.",
                "class": item.get("class") or "",
            }
        else:
            entry = {
                "kind": item["kind"],
                "rule": item["rule"].strip(),
                "class": item["class"].strip(),
            }
        cid = f"{prefix}{inbox['next_id']}"
        inbox["next_id"] += 1
        source = {"by": by, "lens": None if ref else item.get("lens")}
        inbox["candidates"].append(
            {"id": cid, **entry, "source": source, "created": date}
        )
        by_id[cid] = inbox["candidates"][-1]
        add_receipts(by_id[cid], receipts)
        counts["new"] += 1
    return counts


def run_warnings(
    last_run: str | None, last_error: dict | None, now: datetime.datetime
) -> list[str]:
    """Signs that mining stopped working for a repo. An empty inbox proves nothing without a recent run.

    Stamps are UTC ISO strings, so string order is time order.
    """
    warnings = []
    if not last_run:
        warnings.append(
            "no mining run recorded for this repo. Check the SessionEnd hook and miner.log."
        )
    else:
        age = (
            now
            - datetime.datetime.strptime(last_run, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=datetime.timezone.utc
            )
        ).days
        if age >= STALE_DAYS:
            warnings.append(
                f"last mining run was {age} days ago. Check the SessionEnd hook and miner.log."
            )
    if last_error and (not last_run or last_error["at"] > last_run):
        warnings.append(
            f"a miner run failed after this repo's last run: {last_error['at']} {last_error['message']}"
        )
    return warnings


def open_items_text(*inboxes: dict) -> str:
    """Compact list of open candidate ids the miner may attach evidence to."""
    return "\n".join(
        f"{c['id']} [{c['kind']}] {one_line(c['rule'])}"
        for inbox in inboxes
        for c in inbox["candidates"]
    )


def rejected_text(*inboxes: dict) -> str:
    """Recently dropped rules with the user's reason, so the miner stops proposing them."""
    lines = []
    for inbox in inboxes:
        for d in reversed(inbox.get("dropped", [])[-REJECTED_IN_PROMPT:]):
            why = d["reason"] + (f". {d['note']}" if d.get("note") else "")
            lines.append(f"- [{d['kind']}] {one_line(d['rule'])} (rejected: {why})")
    return "\n".join(lines)


def source_key(cand: dict) -> str:
    """`<by>/<lens>` of a candidate. Candidates filed before sources existed -> `unknown`."""
    src = cand.get("source")
    return f"{src['by']}/{src.get('lens') or '-'}" if src else "unknown"


def count_outcome(inbox: dict, cand: dict, outcome: str) -> None:
    """Count one outcome overall and per source.

    `accepted`, `merged`, `dropped`: the user's triage. `composed`: folded by the composer or
    promoter, kept apart so automatic merges do not pass for triage in `status`.
    """
    stats = inbox.setdefault("stats", {})
    if outcome != "dropped":  # the overall drop count comes from the `dropped` list
        stats[outcome] = stats.get(outcome, 0) + 1
    per = stats.setdefault("sources", {}).setdefault(source_key(cand), {})
    per[outcome] = per.get(outcome, 0) + 1


def sources_line(name: str, inbox: dict) -> str:
    """Outcomes per source. A source with mostly drops -> fix that lens or pass."""
    per = inbox.get("stats", {}).get("sources", {})
    parts = [
        f"{key} " + " ".join(f"{n} {o}" for o, n in sorted(counts.items()))
        for key, counts in sorted(per.items())
    ]
    return f"Sources {name}: " + ("; ".join(parts) or "(no outcomes yet)") + "."


def compose_input(inbox: dict) -> list[dict]:
    """What the composer reads per candidate: rule, origin, and every receipt."""
    return [
        {
            "id": c["id"],
            "kind": c["kind"],
            "lens": (c.get("source") or {}).get("lens"),
            "rule": c["rule"],
            "class": c["class"],
            "receipts": [
                {"date": r["date"], "session": r["session"], "quote": r["quote"]}
                for r in c["receipts"]
            ],
        }
        for c in inbox["candidates"]
    ]


def check_compose_action(
    action, by_id: dict, used: set[str], allowed_lenses: dict[str, str]
) -> str | None:
    """Reason a composer action is unusable against the current inbox, or None."""
    if not isinstance(action, dict):
        return "not an object"
    op = "merge" if "merge" in action else "combine" if "combine" in action else None
    if not op:
        return "neither merge nor combine"
    ids = action[op]
    targets = [action.get("into")] if op == "merge" else []
    if not (isinstance(ids, list) and ids and all(isinstance(i, str) for i in ids)):
        return f"{op} must be a non-empty list of ids"
    if op == "combine" and len(set(ids)) < 2:
        return "combine needs 2 or more ids"
    for i in [*ids, *targets]:
        if not isinstance(i, str) or i not in by_id or i in used:
            return f"unknown or already used id {i!r}"
        if by_id[i]["kind"] == "recurrence":
            return f"{i} is a recurrence of a standard: never merged"
    if op == "merge" and action["into"] in ids:
        return "into is also in merge"
    for key in ("rule", "class"):
        value = action.get(key)
        required = op == "combine"
        if (required or value is not None) and not (
            isinstance(value, str) and value.strip()
        ):
            return f"{key} must be a non-empty string"
    lens = action.get("lens")
    if op == "combine" and not (isinstance(lens, str) and lens in allowed_lenses):
        return f"lens {action.get('lens')!r} not allowed in this inbox"
    return None


def apply_compose(
    inbox: dict,
    actions: list,
    *,
    prefix: str,
    date: str,
    allowed_lenses: dict[str, str],
) -> dict:
    """Apply the composer's merges and combines to one inbox. Mutates `inbox`, returns counts.

    Every folded candidate leaves `{id, rule}` in its target's `merged` list, so triage can
    see what a merge absorbed and re-file a rule a wrong merge lost.
    """
    by_id = {c["id"]: c for c in inbox["candidates"]}
    used: set[str] = set()  # each id in at most one action
    gone: set[str] = set()  # folded into another candidate
    counts: dict = {"merged": 0, "combined": 0, "invalid": []}
    for action in actions:
        reason = check_compose_action(action, by_id, used, allowed_lenses)
        if reason:
            counts["invalid"].append(reason)
            continue
        if "merge" in action:
            target = by_id[action["into"]]
            sources = list(dict.fromkeys(action["merge"]))
            used.add(target["id"])
            if action.get("rule"):
                target.setdefault("merged", []).append(
                    {"id": target["id"], "rule": target["rule"]}
                )
                target["rule"] = action["rule"].strip()
            if action.get("class"):
                target["class"] = action["class"].strip()
        else:
            cid = f"{prefix}{inbox['next_id']}"
            inbox["next_id"] += 1
            target = {
                "id": cid,
                "kind": allowed_lenses[action["lens"]],
                "rule": action["rule"].strip(),
                "class": action["class"].strip(),
                "source": {"by": "composite", "lens": action["lens"]},
                "created": date,
                "receipts": [],
            }
            inbox["candidates"].append(target)
            by_id[cid] = target
            sources = list(dict.fromkeys(action["combine"]))
            counts["combined"] += 1
        for i in sources:
            src = by_id[i]
            add_receipts(target, src["receipts"])
            target.setdefault("merged", []).extend(
                [*src.get("merged", []), {"id": i, "rule": src["rule"]}]
            )
            if src.get(
                "promoted_to"
            ):  # keep the link to the shared rule it is a local fix for
                target.setdefault("promoted_to", src["promoted_to"])
            count_outcome(inbox, src, "composed")
            gone.add(i)
            used.add(i)
            counts["merged"] += 1
    inbox["candidates"] = [c for c in inbox["candidates"] if c["id"] not in gone]
    return counts


def promote_input(
    repo_inboxes: dict[str, dict], applied: dict[str, dict[str, str]]
) -> dict[str, dict]:
    """What the promoter reads per repo: open candidates not yet promoted, and applied rules."""
    return {
        stem: {
            "candidates": [
                c
                for c, raw in zip(compose_input(inbox), inbox["candidates"])
                if c["kind"] != "recurrence" and not raw.get("promoted_to")
            ],
            "applied": {f: section(t) for f, t in applied.get(stem, {}).items()},
        }
        for stem, inbox in repo_inboxes.items()
    }


def check_promotion(
    action,
    repo_inboxes: dict[str, dict],
    applied: dict[str, dict[str, str]],
    shared_ids: set[str],
    used: set[str],
    allowed_lenses: dict[str, str],
) -> str | None:
    """Reason a promoter action is unusable against the current inboxes, or None.

    Repos count from open candidates and from verbatim lines of applied rules. At least one
    open candidate is required: the promotion is grounded in a session.
    """
    if not isinstance(action, dict):
        return "not an object"
    qids = action.get("promote")
    if not (isinstance(qids, list) and qids and all(isinstance(q, str) for q in qids)):
        return "promote must be a non-empty list of `<repo>:<id>`"
    repos = set()
    for q in qids:
        stem, _, cid = q.rpartition(":")
        inbox = repo_inboxes.get(stem)
        cand = (
            next((c for c in inbox["candidates"] if c["id"] == cid), None)
            if inbox
            else None
        )
        if not cand or q in used:
            return f"unknown or already used id {q!r}"
        if cand["kind"] == "recurrence":
            return f"{q} is a recurrence of a standard: never promoted"
        if cand.get("promoted_to"):
            return f"{q} is already promoted to {cand['promoted_to']}"
        repos.add(stem)
    refs = action.get("applied", [])
    if not isinstance(refs, list):
        return "applied must be a list"
    for ref in refs:
        if not (
            isinstance(ref, dict)
            and all(isinstance(ref.get(k), str) for k in ("repo", "file", "line"))
        ):
            return f"bad applied shape: {ref!r}"[:200]
        text = applied.get(ref["repo"], {}).get(ref["file"])
        line = one_line(ref["line"])
        if text is None or len(line) < MIN_QUOTE_CHARS or line not in one_line(text):
            return f"applied line not in {ref['repo']}:{ref['file']}: {line[:120]!r}"
        repos.add(ref["repo"])
    if len(repos) < MIN_PROMOTE_REPOS:
        return f"promote needs {MIN_PROMOTE_REPOS} or more repos, got {sorted(repos)}"
    if "into" in action:
        into = action["into"]
        return (
            None
            if isinstance(into, str) and into in shared_ids
            else f"unknown shared id {into!r}"
        )
    lens = action.get("lens")
    if not (isinstance(lens, str) and lens in allowed_lenses):
        return f"lens {action.get('lens')!r} cannot be promoted"
    if not all(
        isinstance(action.get(k), str) and action[k].strip() for k in ("rule", "class")
    ):
        return "rule and class must be non-empty strings"
    return None


def apply_promotions(
    repo_inboxes: dict[str, dict],
    shared: dict,
    actions: list,
    *,
    applied: dict[str, dict[str, str]],
    date: str,
    allowed_lenses: dict[str, str],
) -> dict:
    """Lift a problem that recurs across repos into a shared candidate. Mutates all inboxes.

    Repo candidates stay in their inbox, marked `promoted_to: G<n>`: each still holds a local
    fix that needs doing, while the shared candidate holds the rule for every repo. The shared
    target lists its parts in `promoted_from` (`{id: <repo>:<id>, rule}`) and `applied_in`
    (`{repo, file, line}`: local copies the global rule makes redundant).
    """
    shared_by_id = {c["id"]: c for c in shared["candidates"]}
    used: set[str] = set()
    counts: dict = {"promoted": 0, "linked": 0, "invalid": []}
    for action in actions:
        reason = check_promotion(
            action, repo_inboxes, applied, set(shared_by_id), used, allowed_lenses
        )
        if reason:
            counts["invalid"].append(reason)
            continue
        if "into" in action:
            target = shared_by_id[action["into"]]
        else:
            cid = f"G{shared['next_id']}"
            shared["next_id"] += 1
            target = {
                "id": cid,
                "kind": allowed_lenses[action["lens"]],
                "rule": action["rule"].strip(),
                "class": action["class"].strip(),
                "source": {"by": "promote", "lens": action["lens"]},
                "created": date,
                "receipts": [],
            }
            shared["candidates"].append(target)
            shared_by_id[cid] = target
        counts["promoted"] += 1
        for q in dict.fromkeys(action["promote"]):
            stem, _, cid = q.rpartition(":")
            src = next(c for c in repo_inboxes[stem]["candidates"] if c["id"] == cid)
            add_receipts(target, src["receipts"])
            target.setdefault("promoted_from", []).append(
                {"id": q, "rule": src["rule"]}
            )
            src["promoted_to"] = target["id"]
            used.add(q)
            counts["linked"] += 1
        target.setdefault("applied_in", []).extend(
            {"repo": r["repo"], "file": r["file"], "line": r["line"]}
            for r in action.get("applied", [])
        )
    return counts


def triage_line(name: str, inbox: dict) -> str:
    """Triage outcomes of one inbox. A low accept share means the miner proposes noise."""
    stats = inbox.get("stats", {})
    dropped = inbox.get("dropped", [])
    counts = [(r, sum(d["reason"] == r for d in dropped)) for r in DROP_REASONS]
    by_reason = ", ".join(f"{r} {n}" for r, n in counts if n)
    return (
        f"Triage {name}: {stats.get('accepted', 0)} accepted, "
        f"{stats.get('merged', 0)} merged, {len(dropped)} dropped"
        + (f" ({by_reason})" if by_reason else "")
        + "."
    )


def miner_line(miner: dict) -> str:
    """Miner output quality. Many invalid proposals -> the model ignores the output shape or invents quotes."""
    proposed, invalid = miner.get("proposed", 0), miner.get("invalid", 0)
    share = f" ({invalid * 100 // proposed}%)" if proposed else ""
    return f"Miner: {proposed} proposals, {invalid} were invalid{share}."


# ---------- effectful shell ----------


def utc_stamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with (STATE_DIR / "miner.log").open("a") as f:
        f.write(f"{utc_stamp()} {msg}\n")


def stamp_run(
    *,
    repo: str | None = None,
    error: str | None = None,
    proposed: int = 0,
    invalid: int = 0,
) -> None:
    """Record a finished run in RUNS: success for `repo` with its proposal counts, or the latest `error`."""
    with locked("state"):
        runs = read_json(RUNS, {})
        if repo:
            runs.setdefault("repos", {})[repo] = utc_stamp()
            miner = runs.setdefault("miner", {})
            miner["proposed"] = miner.get("proposed", 0) + proposed
            miner["invalid"] = miner.get("invalid", 0) + invalid
        if error:
            runs["last_error"] = {"at": utc_stamp(), "message": error[:300]}
        write_json(RUNS, runs)


def today() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


@contextlib.contextmanager
def locked(name: str):
    """Exclusive lock for read-modify-write of one inbox (named by its file stem) or the state."""
    lock_dir = STATE_DIR / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    with (lock_dir / f"{hashlib.sha256(name.encode()).hexdigest()[:16]}.lock").open(
        "w"
    ) as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield


def read_json(path: pathlib.Path, default: dict) -> dict:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as e:
        raise SystemExit(f"{path} is not valid JSON ({e}). Fix it by hand, then rerun.")


def write_json(path: pathlib.Path, data: dict) -> None:
    """Atomic write: a crash never leaves half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)


def empty_inbox() -> dict:
    return {"next_id": 1, "candidates": []}


def empty_receipts() -> dict:
    return {"next_id": 1, "rules": [], "retired": []}


def inbox_path(repo: pathlib.Path) -> pathlib.Path:
    return INBOX_DIR / f"{repo.name}.json"


def receipts_path(repo: pathlib.Path) -> pathlib.Path:
    return INBOX_DIR / f"{repo.name}.receipts.json"


def shared_path() -> pathlib.Path:
    return INBOX_DIR / f"{SHARED}.json"


def store_of(cid: str, repo: pathlib.Path) -> tuple[pathlib.Path, str]:
    """Inbox file and lock name for a candidate id: `G<n>` is shared, `C<n>` belongs to the repo."""
    return (
        (shared_path(), SHARED)
        if cid.startswith("G")
        else (inbox_path(repo), repo.name)
    )


def main_checkout(start: pathlib.Path) -> pathlib.Path | None:
    """Repo root for `start`, mapped from a jj workspace or git worktree to the main checkout.

    The inbox must outlive throwaway workspaces, so it is keyed by the main checkout.
    """
    for d in (start, *start.parents):
        jj = d / ".jj"
        if jj.is_dir():
            pointer = jj / "repo"
            if (
                pointer.is_file()
            ):  # secondary workspace: file holds the main `.jj/repo` path
                target = pathlib.Path(pointer.read_text().strip())
                return (
                    (target if target.is_absolute() else (pointer.parent / target))
                    .resolve()
                    .parent.parent
                )
            return d
        git = d / ".git"
        if git.is_dir():
            return d
        if git.is_file():  # git worktree: `gitdir: <main>/.git/worktrees/<name>`
            gitdir = pathlib.Path(git.read_text().split("gitdir:", 1)[-1].strip())
            return (
                (gitdir if gitdir.is_absolute() else d / gitdir)
                .resolve()
                .parent.parent.parent
            )
    return None


def load_config() -> dict:
    """Read and validate the config. Named errors -> one-step fix."""
    path = pathlib.Path(
        os.environ.get("RULE_FORGE_CONFIG") or SKILL_DIR / "config.json"
    )
    cfg = read_json(path, {})
    if not cfg:
        raise SystemExit(f"config missing or empty: {path}")
    commands = cfg.get("commands") or {}
    key = cfg.get("command")
    if key not in commands:
        raise SystemExit(
            f"{path}: command {key!r} is not a key of commands. Available: {sorted(commands)}"
        )
    argv = commands[key]
    if not (isinstance(argv, list) and argv and all(isinstance(a, str) for a in argv)):
        raise SystemExit(f"{path}: commands.{key} must be a non-empty list of strings")
    cfg["argv"] = argv
    fallback = cfg.get("fallback")
    if fallback:
        fb = commands.get(fallback)
        if not (isinstance(fb, list) and fb and all(isinstance(a, str) for a in fb)):
            raise SystemExit(
                f"{path}: fallback {fallback!r} must be a key of commands holding a non-empty list of strings"
            )
        cfg["fallback_argv"] = fb
    cfg.setdefault("timeout_s", 900)
    cfg.setdefault("min_user_messages", 2)
    cfg.setdefault("max_transcript_bytes", 1_000_000)
    cfg.setdefault("notify", True)
    cfg.setdefault("enabled", True)
    cfg.setdefault("compose_every", 10)
    cfg["roots"] = [
        pathlib.Path(r).expanduser().resolve() for r in cfg.get("roots") or []
    ]
    return cfg


def run_command(argv_template: list[str], cfg: dict, prompt: str, cwd: str) -> list:
    """Run one miner command in `cwd`, a temp dir that holds only the transcript file.

    Returns the JSON array it answered with. Any failure raises.
    """
    use_arg = any("{prompt}" in a for a in argv_template)
    argv = [a.replace("{prompt}", prompt) for a in argv_template]
    done = subprocess.run(
        argv,
        input=None if use_arg else prompt,
        stdin=subprocess.DEVNULL if use_arg else None,
        check=False,  # the exit code is checked below, with stderr in the error
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=cfg["timeout_s"],
        env={**os.environ, CHILD_ENV: "1"},
    )
    if done.returncode != 0:
        raise RuntimeError(f"miner exit {done.returncode}: {done.stderr.strip()[:500]}")
    return parse_output(done.stdout)


def run_miner(cfg: dict, prompt: str, cwd: str) -> list:
    """Run the primary miner, then the `fallback` one when the primary fails for any reason.

    A usage limit may exit 0 with a plain-text message, so a missing JSON array also counts as a
    failure. The fallback's own failure propagates.
    """
    try:
        return run_command(cfg["argv"], cfg, prompt, cwd)
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as e:
        if not cfg.get("fallback_argv"):
            raise
        log(
            f"primary miner failed ({type(e).__name__}: {e}); using fallback {cfg['fallback']}"
        )
        return run_command(cfg["fallback_argv"], cfg, prompt, cwd)


def cmd_hook(_args) -> int:
    """SessionEnd entry. Detach the miner and return at once: the hook must not delay exit."""
    if os.environ.get(CHILD_ENV):
        return 0
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    transcript, cwd = event.get("transcript_path"), event.get("cwd")
    if not transcript or not cwd:
        return 0
    try:
        subprocess.Popen(
            [
                sys.executable,
                __file__,
                "mine",
                "--transcript",
                transcript,
                "--cwd",
                cwd,
            ],
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as e:
        summary = f"could not start the miner: {e}"
        with contextlib.suppress(Exception, SystemExit):
            record_failure(transcript, summary, mine_rerun(transcript, cwd))
        notify(summary, failed=True)
    return 0


def notify(summary: str, *, failed: bool = False) -> None:
    """Desktop notification for a finished run. Best effort: never fails the run.

    A failure stays on screen until dismissed (critical urgency): the detached run has no other
    visible output. A notification that cannot be shown is logged.
    """
    argv = (
        [
            "notify-send",
            "-a",
            "rule-forge",
            "-u",
            "critical",
            "rule-forge failed",
            summary,
        ]
        if failed
        else ["notify-send", "-a", "rule-forge", "-t", "5000", "rule-forge", summary]
    )
    try:
        done = subprocess.run(
            argv, timeout=5, capture_output=True, text=True, check=False
        )
        problem = (
            f"exit {done.returncode}: {done.stderr.strip()[:200]}"
            if done.returncode
            else ""
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        problem = str(e)
    if problem:
        with contextlib.suppress(OSError):
            log(f"notify-send failed ({problem}) for: {summary}")


def exit_on_signal() -> None:
    """Logout or `kill` ends a detached run by signal. Raise SystemExit instead, so the
    failure path still logs and notifies."""
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(
            sig,
            lambda signum, _frame: sys.exit(f"killed by {signal.Signals(signum).name}"),
        )


def rerun_command(*args: str) -> str:
    """Shell command that repeats a failed run."""
    return shlex.join([sys.executable, str(pathlib.Path(__file__).resolve()), *args])


def mine_rerun(transcript: str, cwd: str) -> str:
    return rerun_command("mine", "--transcript", str(transcript), "--cwd", str(cwd))


def record_failure(key: str, message: str, rerun: str) -> None:
    """Note a failed run in FAILED until the same run succeeds. A repeat failure overwrites."""
    with locked("state"):
        failed = read_json(FAILED, {})
        failed[str(key)] = {"at": utc_stamp(), "error": message[:300], "rerun": rerun}
        write_json(FAILED, failed)


def clear_failure(key: str) -> None:
    """The run succeeded: drop its FAILED entry, if any."""
    with locked("state"):
        failed = read_json(FAILED, {})
        if failed.pop(str(key), None) is not None:
            write_json(FAILED, failed)


def report_failure(what: str, e: BaseException, *, key: str, rerun: str) -> int:
    """Detached run: log and notification are its only outputs, so signals and interrupts
    must reach them too. `key` and `rerun` file it in FAILED for a later rerun."""
    summary = f"error {what}: {type(e).__name__}: {e}"
    with contextlib.suppress(OSError):
        log(summary)
    # A corrupt state file must not block the notification.
    with contextlib.suppress(Exception, SystemExit):
        stamp_run(error=summary)
    with contextlib.suppress(Exception, SystemExit):
        record_failure(key, summary, rerun)
    notify(summary, failed=True)
    return 1


def cmd_mine(args) -> int:
    transcript = pathlib.Path(args.transcript)
    exit_on_signal()
    try:
        cfg = load_config()
        summary = mine(cfg, transcript, pathlib.Path(args.cwd))
    except BaseException as e:  # noqa: BLE001
        return report_failure(
            transcript.name,
            e,
            key=str(transcript),
            rerun=mine_rerun(args.transcript, args.cwd),
        )
    with contextlib.suppress(Exception, SystemExit):
        clear_failure(str(transcript))
    if summary and cfg["notify"]:
        notify(summary)
    if summary and compose_due(cfg["compose_every"]):
        return run_compose(cfg)
    return 0


def cmd_retry(_args) -> int:
    """Rerun every run in FAILED, one after another. Each rerun clears its own entry on
    success and refreshes it on failure, so a timer can call this repeatedly.

    A second retry while one is running exits at once: the same run twice would mine twice.
    """
    lock_dir = STATE_DIR / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    with (lock_dir / "retry.lock").open("w") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("another retry is running")
            return 0
        failed = read_json(FAILED, {})
        still = 0
        for key, entry in failed.items():
            code = subprocess.run(shlex.split(entry["rerun"]), check=False).returncode
            print(f"{'ok' if code == 0 else 'FAILED'}: {key}")
            still += code != 0
        print(f"{len(failed) - still} redone, {still} still failing")
        return 1 if still else 0


def compose_due(every: int) -> bool:
    """Count one mined session. True once every `every` sessions, and the count restarts."""
    if every <= 0:
        return False
    with locked("state"):
        runs = read_json(RUNS, {})
        pending = runs.get("compose_pending", 0) + 1
        runs["compose_pending"] = 0 if pending >= every else pending
        write_json(RUNS, runs)
    return pending >= every


def cmd_compose(_args) -> int:
    exit_on_signal()
    try:
        cfg = load_config()
    except BaseException as e:  # noqa: BLE001
        return report_failure(
            "compose", e, key=COMPOSE_KEY, rerun=rerun_command("compose")
        )
    return run_compose(cfg)


def run_compose(cfg: dict) -> int:
    """Compose every inbox. Log, notify, and stamp like a mining run."""
    try:
        summary = compose_all(cfg)
    except BaseException as e:  # noqa: BLE001
        return report_failure(
            "compose", e, key=COMPOSE_KEY, rerun=rerun_command("compose")
        )
    with contextlib.suppress(Exception, SystemExit):
        clear_failure(COMPOSE_KEY)
    log(f"composed -> {summary}")
    if cfg["notify"]:
        notify(f"compose: {summary}")
    return 0


def compose_all(cfg: dict) -> str:
    """One composer call per inbox with 2 or more candidates. Summary of all changes."""
    lenses = parse_lenses(LENSES_FILE.read_text())
    parts, failed = [], []

    def attempt(name: str, call):
        """One model call fails alone: models return empty output now and then."""
        try:
            return call()
        except Exception as e:  # noqa: BLE001
            log(f"error compose {name}: {type(e).__name__}: {e}")
            failed.append(name)
            return None

    for path in inbox_files():
        counts = attempt(path.stem, lambda p=path: compose_inbox(cfg, p, lenses))
        if counts and (counts["merged"] or counts["invalid"]):
            parts.append(
                f"{path.stem}: {counts['merged']} folded, {counts['combined']} new, "
                f"{len(counts['invalid'])} invalid"
            )
    counts = attempt("promote", lambda: promote_across(cfg, lenses))
    if counts and (counts["promoted"] or counts["invalid"]):
        parts.append(
            f"across repos: {counts['promoted']} promoted from {counts['linked']}, "
            f"{len(counts['invalid'])} invalid"
        )
    if failed:
        raise RuntimeError(
            f"failed for {', '.join(failed)} (see miner.log). Done: "
            + ("; ".join(parts) or "nothing")
        )
    return "; ".join(parts) or "nothing to consolidate"


def inbox_files() -> list[pathlib.Path]:
    """Every inbox file: one per repo, plus the shared one. Receipt stores excluded."""
    return [
        p
        for p in sorted(INBOX_DIR.glob("*.json"))
        if not p.name.endswith(".receipts.json")
    ]


def promote_across(cfg: dict, lenses: dict[str, str]) -> dict | None:
    """Ask the promoter about all repo inboxes at once, then apply to a fresh read.

    Lock order: repo inboxes sorted, then shared. `mine` holds one repo, then shared, so no
    lock cycle forms.
    """
    allowed = {l: k for l, k in lenses.items() if k in SHARED_KINDS}
    stems = [p.stem for p in inbox_files() if p.stem != SHARED]

    def read_all() -> tuple[dict[str, dict], dict]:
        repos = {st: read_json(INBOX_DIR / f"{st}.json", empty_inbox()) for st in stems}
        return repos, read_json(shared_path(), empty_inbox())

    with contextlib.ExitStack() as stack:
        for st in [*stems, SHARED]:
            stack.enter_context(locked(st))
        repos, shared = read_all()
    applied = {st: applied_rules(inbox) for st, inbox in repos.items()}
    if (
        not any(i["candidates"] for i in repos.values())
        or sum(bool(i["candidates"] or applied[st]) for st, i in repos.items())
        < MIN_PROMOTE_REPOS
    ):
        return None
    with tempfile.TemporaryDirectory(prefix="rule-forge-") as workdir:
        candidates_file = pathlib.Path(workdir) / "candidates.json"
        candidates_file.write_text(
            json.dumps(promote_input(repos, applied), indent=1, ensure_ascii=False)
        )
        prompt = string.Template(PROMOTE_TEMPLATE.read_text()).safe_substitute(
            candidates_file=str(candidates_file),
            min_repos=MIN_PROMOTE_REPOS,
            allowed_lenses=", ".join(f"`{l}`" for l in allowed),
            lenses=LENSES_FILE.read_text(),
            shared_items=section(open_items_text(shared)),
            rejected=section(rejected_text(shared, *repos.values())),
        )
        actions = run_miner(cfg, prompt, workdir)
    with contextlib.ExitStack() as stack:
        for st in [*stems, SHARED]:
            stack.enter_context(locked(st))
        repos, shared = read_all()
        counts = apply_promotions(
            repos,
            shared,
            actions,
            applied=applied,
            date=today(),
            allowed_lenses=allowed,
        )
        if counts["promoted"]:
            for st, inbox in repos.items():
                write_json(INBOX_DIR / f"{st}.json", inbox)
            write_json(shared_path(), shared)
    log(f"promoted across repos: {counts}")
    return counts


def compose_inbox(cfg: dict, path: pathlib.Path, lenses: dict[str, str]) -> dict | None:
    """Ask the composer about one inbox, then apply its actions to a fresh read.

    The model call runs outside the lock: it takes minutes, and miners must keep writing.
    Actions on candidates that changed meanwhile fail validation and are skipped.
    """
    stem = path.stem
    shared = stem == SHARED
    allowed = {l: k for l, k in lenses.items() if (k in SHARED_KINDS) == shared}
    with locked(stem):
        inbox = read_json(path, empty_inbox())
    if len(inbox["candidates"]) < 2:
        return None
    with tempfile.TemporaryDirectory(prefix="rule-forge-") as workdir:
        candidates_file = pathlib.Path(workdir) / "candidates.json"
        candidates_file.write_text(
            json.dumps(compose_input(inbox), indent=1, ensure_ascii=False)
        )
        prompt = string.Template(COMPOSE_TEMPLATE.read_text()).safe_substitute(
            candidates_file=str(candidates_file),
            allowed_lenses=", ".join(f"`{l}`" for l in allowed),
            lenses=LENSES_FILE.read_text(),
            rejected=section(rejected_text(inbox)),
        )
        actions = run_miner(cfg, prompt, workdir)
    with locked(stem):
        inbox = read_json(path, empty_inbox())
        counts = apply_compose(
            inbox,
            actions,
            prefix="G" if shared else "C",
            date=today(),
            allowed_lenses=allowed,
        )
        if counts["merged"]:
            write_json(path, inbox)
    log(f"composed {stem}: {counts}")
    return counts


def read_subagents(
    transcript: pathlib.Path, marks: dict
) -> tuple[str, str, dict[str, int]]:
    """Subagent runs of the session since their marks -> (tool errors, duck reports, new marks).

    Claude Code writes each subagent run to `<session>/subagents/agent-<id>.jsonl`, apart
    from the parent transcript. The user never talks to a subagent, so only its tool errors
    carry signal (harness friction, a gotcha the brief missed). Each file keeps its own mark:
    a resumed session or a `SendMessage` follow-up appends to a file already mined.
    Duck reports come from these files, not the parent's tool result: one source covers
    foreground, background, and nested runs (a subagent calling the duck).
    """
    blocks: list[str] = []
    ducks: list[str] = []
    new_marks: dict[str, int] = {}
    for path in sorted(
        (transcript.with_suffix("") / "subagents").glob("agent-*.jsonl")
    ):
        start = marks.get(str(path), 0)
        lines = path.read_text().rstrip("\n").split("\n")
        records, consumed, _ = parse_records(lines[start:])
        new_marks[str(path)] = start + consumed
        # A corrupt meta must not fail the whole run: the block loses its label, and a duck
        # run reads as a plain subagent.
        meta: dict = {}
        with contextlib.suppress(SystemExit):
            meta = read_json(path.with_name(f"{path.stem}.meta.json"), {})
        if meta.get("agentType") == DUCK_AGENT:
            # One line per report: a report line starting with `[user]` would pass as a user quote.
            ducks += [
                f"{subagent_header(meta)}\n[duck] {one_line(t)[:DUCK_CHARS]}"
                for t in turn_reports(records)
            ]
        errors, _ = condense(records)
        if errors:
            blocks.append(f"{subagent_header(meta)}\n{errors}")
    return "\n".join(blocks), "\n".join(ducks), new_marks


def mine(cfg: dict, transcript: pathlib.Path, cwd: pathlib.Path) -> str | None:
    """Mine new transcript lines into the repo's inbox. Summary of the run, or None when skipped."""
    if not cfg["enabled"]:
        return None
    repo = main_checkout(cwd.resolve())
    if not repo:
        log(f"skip {transcript.name}: {cwd} is not in a repo")
        return None
    if cfg["roots"] and not any(repo.is_relative_to(r) for r in cfg["roots"]):
        log(f"skip {transcript.name}: {repo} is outside roots")
        return None
    if not transcript.is_file():
        # SessionEnd fires for sessions that never wrote a transcript (nothing sent, or
        # a tool's headless run): nothing to mine.
        log(f"skip {transcript.name}: no transcript file")
        return None
    marks_path = STATE_DIR / "mined.json"
    with locked("state"):
        all_marks = read_json(marks_path, {})
    start = all_marks.get(str(transcript), 0)
    # Split on "\n" only: `splitlines()` also cuts at U+2028, U+0085 and others, which JSON
    # allows unescaped inside a string -> it tore records apart. rstrip keeps line indexes
    # stable when a trailing newline appears or grows.
    lines = transcript.read_text().rstrip("\n").split("\n")
    records, consumed, skipped = parse_records(lines[start:])
    if skipped:
        log(f"skip {skipped} corrupt line(s) in {transcript.name}")
    text, user_messages = condense(records)
    subagent_text, duck_text, subagent_marks = read_subagents(transcript, all_marks)
    # A duck report is worth mining even in a session the user barely spoke in.
    if user_messages < cfg["min_user_messages"] and not duck_text:
        # Subagent marks stay too: their errors join the next segment that gets mined.
        log(f"skip {transcript.name}: {user_messages} user messages since line {start}")
        stamp_run(repo=repo.name)  # the pipeline works, the session was just too short
        return None
    # `fit_tail` cuts from the front. Subagent errors go first: the user's words matter more.
    # Duck reports go last: the top-priority source must survive the cut.
    text = "\n".join(t for t in (subagent_text, text, duck_text) if t)

    session = f"cc:{transcript.parent.name}/{transcript.stem}"
    inbox = read_json(inbox_path(repo), empty_inbox())
    shared = read_json(shared_path(), empty_inbox())
    standards = standards_text(repo)
    agents_md = (
        (repo / "AGENTS.md").read_text() if (repo / "AGENTS.md").exists() else ""
    )
    global_rules = GLOBAL_RULES.read_text() if GLOBAL_RULES.exists() else ""
    implementer_rules = (
        IMPLEMENTER_RULES.read_text() if IMPLEMENTER_RULES.exists() else ""
    )
    lenses_text = LENSES_FILE.read_text()
    lenses = parse_lenses(lenses_text)
    with tempfile.TemporaryDirectory(prefix="rule-forge-") as workdir:
        transcript_file = pathlib.Path(workdir) / "transcript.txt"
        transcript_file.write_text(fit_tail(text, cfg["max_transcript_bytes"]))
        prompt = build_prompt(
            PROMPT_TEMPLATE.read_text(),
            global_rules=global_rules,
            implementer_rules=implementer_rules,
            agents_md=agents_md,
            standards=standards,
            lenses=lenses_text,
            open_items=open_items_text(inbox, shared),
            rejected=rejected_text(inbox, shared),
            transcript_file=str(transcript_file),
        )
        items = run_miner(cfg, prompt, workdir)

    stamps = [r.get("timestamp", "") for r in records if r.get("timestamp")]
    date = stamps[-1][:10] if stamps else today()
    # Lock order is always repo, then shared. No other path holds both -> no deadlock.
    with locked(repo.name), locked(SHARED):
        # Re-read: another miner may have written meanwhile.
        inbox = read_json(inbox_path(repo), empty_inbox())
        shared = read_json(shared_path(), empty_inbox())
        known = {c["id"] for c in inbox["candidates"] + shared["candidates"]} | set(
            STANDARD_ID_RE.findall(standards)
        )
        good, invalid = [], []
        for item in items:
            reason = check_proposal(item, text, known, lenses)
            (invalid.append(reason) if reason else good.append(item))
        counts = {"new": 0, "supported": 0}
        for target, path, prefix, to_shared in (
            (inbox, inbox_path(repo), "C", False),
            (shared, shared_path(), "G", True),
        ):
            picked = [
                {**i, "receipts": stamp(i["receipts"], date=date, session=session)}
                for i in good
                if routes_to_shared(i) == to_shared
            ]
            c = merge_proposals(target, picked, prefix=prefix, date=date, by="session")
            repo_changed = not to_shared and note_repo(target, repo)
            if c["new"] or c["supported"] or repo_changed:
                write_json(path, target)
            counts = {k: counts[k] + c[k] for k in counts}
    with locked("state"):
        marks = read_json(marks_path, {})
        marks[str(transcript)] = start + consumed
        marks.update(subagent_marks)
        write_json(marks_path, marks)
    summary = (
        f"{repo.name}: {counts['new']} new, {counts['supported']} supported, "
        f"{len(invalid)} invalid, {len(inbox['candidates'])} open "
        f"+ {len(shared['candidates'])} shared"
    )
    log(f"mined {session} -> {summary} {invalid}")
    stamp_run(repo=repo.name, proposed=len(items), invalid=len(invalid))
    return summary


def applied_rules(inbox: dict) -> dict[str, str]:
    """The repo's applied rules, by file name. Needs the repo path the miner stores in the inbox."""
    repo = inbox.get("repo")
    if not repo:
        return {}
    files = ((pathlib.Path(repo) / f) for f in ("AGENTS.md", STANDARDS))
    return {f.name: f.read_text() for f in files if f.is_file()}


def note_repo(inbox: dict, repo: pathlib.Path) -> bool:
    """Store the repo path in its inbox, so passes that only see inbox files can read the
    repo's applied rules. True when it changed."""
    changed = inbox.get("repo") != str(repo)
    inbox["repo"] = str(repo)
    return changed


def standards_text(repo: pathlib.Path) -> str:
    path = repo / STANDARDS
    return path.read_text() if path.exists() else ""


def repo_of(args) -> pathlib.Path:
    repo = main_checkout(pathlib.Path(args.repo or os.getcwd()).resolve())
    if not repo:
        raise SystemExit("not inside a jj or git repo. Pass --repo <path>.")
    return repo


def parse_candidate(raw) -> dict:
    """Validate what another skill files: a new candidate, or `supports` evidence for an
    open candidate or applied standard (the miner's output shape). Named errors -> one-step fix.
    """
    if not isinstance(raw, dict):
        raise SystemExit("stdin must be one JSON object")
    receipts = parse_receipts(raw.get("receipts"))
    if "supports" in raw:
        ref = raw["supports"]
        if not (isinstance(ref, str) and re.fullmatch(r"[CGS]\d+", ref)):
            raise SystemExit(f"supports must be C<n>, G<n>, or S<n>, got {ref!r}")
        # Against a standard, rule and class optionally describe the fix (see miner prompt).
        extra = {
            k: raw[k].strip()
            for k in ("rule", "class")
            if isinstance(raw.get(k), str) and raw[k].strip()
        }
        return {"supports": ref, **extra, "receipts": receipts}
    lens = raw.get("lens")
    if lens is not None:
        lenses = parse_lenses(LENSES_FILE.read_text())
        if lens not in lenses:
            raise SystemExit(f"lens must be one of {sorted(lenses)}, got {lens!r}")
        raw = {**raw, "kind": raw.get("kind") or lenses[lens]}
        if raw["kind"] != lenses[lens]:
            raise SystemExit(
                f"lens {lens} files kind {lenses[lens]}, got {raw['kind']!r}"
            )
    if raw.get("kind") not in KINDS:
        raise SystemExit(f"kind must be one of {KINDS}, got {raw.get('kind')!r}")
    for key in ("rule", "class"):
        if not (isinstance(raw.get(key), str) and raw[key].strip()):
            raise SystemExit(f"{key} must be a non-empty string")
    return {
        "kind": raw["kind"],
        "lens": lens,
        "rule": raw["rule"].strip(),
        "class": raw["class"].strip(),
        "receipts": receipts,
    }


def parse_receipts(receipts) -> list[dict]:
    """Validate receipts filed by another skill: each already carries its date and session."""
    fields = ("date", "session", "speaker", "quote")
    if not (isinstance(receipts, list) and receipts):
        raise SystemExit("receipts must be a non-empty list")
    for r in receipts:
        if not (
            isinstance(r, dict)
            and all(isinstance(r.get(f), str) and r[f] for f in fields)
        ):
            raise SystemExit(f"each receipt needs string fields {fields}, got {r!r}")
        if r["speaker"] not in SPEAKERS:
            raise SystemExit(f"speaker must be one of {SPEAKERS}, got {r['speaker']!r}")
    return [{f: r[f] for f in fields} for r in receipts]


def cmd_add(args) -> int:
    """File a new candidate, or receipts for an existing one. Prints the id that holds them."""
    repo = repo_of(args)
    try:
        item = parse_candidate(json.load(sys.stdin))
    except json.JSONDecodeError as e:
        raise SystemExit(f"stdin is not valid JSON: {e}")
    to_shared = routes_to_shared(item)
    path, lock = (shared_path(), SHARED) if to_shared else (inbox_path(repo), repo.name)
    ref = item.get("supports")
    with locked(lock):
        inbox = read_json(path, empty_inbox())
        known = {c["id"] for c in inbox["candidates"]}
        known |= set(STANDARD_ID_RE.findall(standards_text(repo)))
        if ref and ref not in known:
            raise SystemExit(f"unknown id {ref}. Run `list` for open candidates.")
        before = known.copy()
        if not to_shared:
            note_repo(inbox, repo)
        counts = merge_proposals(
            inbox, [item], prefix="G" if to_shared else "C", date=today(), by=args.by
        )
        write_json(path, inbox)
    new = [c["id"] for c in inbox["candidates"] if c["id"] not in before]
    if new:
        print(new[0])  # a new candidate, or the first recurrence of a standard
    else:
        held = next(
            c["id"] for c in inbox["candidates"] if ref in (c["id"], c.get("standard"))
        )
        print(
            f"{held}: {'receipts added' if counts['supported'] else 'receipts already there'}"
        )
    return 0


def cmd_list(args) -> int:
    """Open candidates (the ids `supports` can target), then rejected rules not to file again."""
    repo = repo_of(args)
    inbox = read_json(inbox_path(repo), empty_inbox())
    shared = read_json(shared_path(), empty_inbox())
    print(f"Open:\n{open_items_text(inbox, shared) or '(none)'}")
    print(f"Rejected:\n{rejected_text(inbox, shared) or '(none)'}")
    return 0


def cmd_status(args) -> int:
    repo = repo_of(args)
    inbox = read_json(inbox_path(repo), empty_inbox())
    shared = read_json(shared_path(), empty_inbox())
    runs = read_json(RUNS, {})
    last_run = runs.get("repos", {}).get(repo.name)
    print(
        f"{repo.name}: {len(inbox['candidates'])} open. "
        f"Shared: {len(shared['candidates'])} open. "
        f"Last mining run: {last_run or 'none recorded'}."
    )
    print(miner_line(runs.get("miner", {})))
    print(triage_line(repo.name, inbox))
    print(sources_line(repo.name, inbox))
    print(triage_line("shared", shared))
    print(sources_line("shared", shared))
    for w in run_warnings(
        last_run, runs.get("last_error"), datetime.datetime.now(datetime.timezone.utc)
    ):
        print(f"WARNING: {w}")
    failed = read_json(FAILED, {})
    if failed:
        print(
            f"WARNING: {len(failed)} failed run(s) not yet redone. "
            f"Each has a `rerun` command in {FAILED}."
        )
    return 0


def cmd_drop(args) -> int:
    """Reject candidates with a reason, kept for the miner. `--into <id>` merges instead."""
    repo = repo_of(args)
    if bool(args.into) == bool(args.reason):
        raise SystemExit("pass exactly one: --reason (reject) or --into (merge)")
    if args.into in args.ids:
        raise SystemExit(f"--into {args.into} is also in the ids to drop")
    ids = [*args.ids, *([args.into] if args.into else [])]
    if len({i[:1] for i in ids}) > 1:
        raise SystemExit(
            f"ids mix the repo (C) and shared (G) inbox: {ids}. Drop each inbox's ids separately."
        )
    path, lock = store_of(ids[0], repo)
    with locked(lock):
        inbox = read_json(path, empty_inbox())
        by_id = {c["id"]: c for c in inbox["candidates"]}
        missing = set(ids) - by_id.keys()
        if missing:
            raise SystemExit(f"unknown candidate ids: {sorted(missing)}")
        if args.into:
            target = by_id[args.into]
            moved = sum(add_receipts(target, by_id[i]["receipts"]) for i in args.ids)
            for i in args.ids:
                count_outcome(inbox, by_id[i], "merged")
            result = (
                f"merged {' '.join(args.ids)} into {args.into}, moved {moved} receipts"
            )
        else:
            note = {"note": args.note} if args.note else {}
            inbox.setdefault("dropped", []).extend(
                {
                    "id": i,
                    "kind": by_id[i]["kind"],
                    "rule": by_id[i]["rule"],
                    "reason": args.reason,
                    **note,
                    "date": today(),
                }
                for i in args.ids
            )
            for i in args.ids:
                count_outcome(inbox, by_id[i], "dropped")
            result = f"dropped {' '.join(args.ids)} ({args.reason})"
        inbox["candidates"] = [
            c for c in inbox["candidates"] if c["id"] not in args.ids
        ]
        write_json(path, inbox)
    print(result)
    return 0


def cmd_accept(args) -> int:
    """Remove a candidate from the inbox. Standards keep its receipts; other kinds discard them."""
    repo = repo_of(args)
    path, lock = store_of(args.id, repo)
    with locked(lock):
        inbox = read_json(path, empty_inbox())
        receipts = read_json(receipts_path(repo), empty_receipts())
        cand = next((c for c in inbox["candidates"] if c["id"] == args.id), None)
        if not cand:
            raise SystemExit(
                f"unknown candidate {args.id}. Open: {[c['id'] for c in inbox['candidates']]}"
            )
        in_md = STANDARD_ID_RE.findall(standards_text(repo))
        # Ids added to CODING_STANDARDS.md by hand must never be handed out again.
        receipts["next_id"] = max(
            [receipts["next_id"], *(int(i[1:]) + 1 for i in in_md)]
        )
        into = args.into or cand.get("standard")
        if cand["kind"] in ("coding-standard", "recurrence") and into:
            rule = next((r for r in receipts["rules"] if r["id"] == into), None)
            if (
                not rule and into in in_md
            ):  # hand-written standard: start its receipts now
                rule = {
                    "id": into,
                    "class": cand["class"],
                    "introduced": today(),
                    "last_edited": today(),
                    "receipts": [],
                }
                receipts["rules"].append(rule)
            if not rule:
                raise SystemExit(f"unknown standard {into}. In {STANDARDS}: {in_md}")
            rule["receipts"].extend(cand["receipts"])
            if args.edited:
                rule["last_edited"] = today()
            result = into
        elif cand["kind"] == "coding-standard":
            result = f"S{receipts['next_id']}"
            receipts["next_id"] += 1
            receipts["rules"].append(
                {
                    "id": result,
                    "class": cand["class"],
                    "introduced": today(),
                    "last_edited": today(),
                    "receipts": cand["receipts"],
                }
            )
        else:
            result = "applied, receipts discarded"
        inbox["candidates"].remove(cand)
        count_outcome(inbox, cand, "accepted")
        if result != "applied, receipts discarded":
            write_json(receipts_path(repo), receipts)
        write_json(path, inbox)
    print(result)
    return 0


def cmd_retire(args) -> int:
    repo = repo_of(args)
    with locked(repo.name):
        receipts = read_json(receipts_path(repo), empty_receipts())
        rule = next((r for r in receipts["rules"] if r["id"] == args.id), None)
        if not rule:
            raise SystemExit(f"unknown standard {args.id}")
        line = next(
            (
                l.strip()
                for l in standards_text(repo).splitlines()
                if f"({args.id})" in l
            ),
            "",
        )
        receipts["rules"].remove(rule)
        receipts["retired"].append(
            {**rule, "rule": line, "retired": today(), "reason": args.reason}
        )
        write_json(receipts_path(repo), receipts)
    print(f"retired {args.id}. Delete its line from {STANDARDS}.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser(
        "hook", help="SessionEnd hook entry: reads the event on stdin, detaches `mine`"
    )
    m = sub.add_parser("mine", help="mine one transcript now (foreground)")
    m.add_argument("--transcript", required=True)
    m.add_argument("--cwd", required=True, help="session cwd, used to find the repo")
    sub.add_parser(
        "compose",
        help="consolidate every inbox now (foreground). `mine` runs it every compose_every sessions",
    )
    sub.add_parser(
        "retry",
        help="rerun every failed run listed in failed.json (foreground). Safe to call from a timer",
    )
    for name, help_ in (
        (
            "add",
            (
                "file one candidate: JSON {lens or kind, rule, class, receipts:[{date, "
                "session, speaker, quote}]} on stdin, or receipts for an existing one: "
                "{supports: C<n>|G<n>|S<n>, receipts}. Prints the id that holds them"
            ),
        ),
        ("list", "open candidate ids, then recently rejected rules"),
        ("status", "open counts, miner and triage stats, warnings when mining broke"),
        ("drop", "reject candidates with a reason, or merge them --into another"),
        ("accept", "remove a handled candidate, keep standard receipts"),
        ("retire", "retire a standard, keep its id taken"),
    ):
        s = sub.add_parser(name, help=help_)
        s.add_argument("--repo", help="repo path (default: cwd)")
        if name == "add":
            s.add_argument(
                "--by",
                default="add",
                help="the filing skill, kept in the candidate's source (e.g. retrospective)",
            )
        if name == "drop":
            s.add_argument("ids", nargs="+")
            s.add_argument(
                "--reason",
                choices=DROP_REASONS,
                help="why the user rejected them. Later miner runs see it",
            )
            s.add_argument("--note", help="optional one-line detail for the miner")
            s.add_argument(
                "--into",
                help="merge: move the receipts to this candidate of the same inbox",
            )
        if name == "accept":
            s.add_argument("id")
            s.add_argument(
                "--into", help="merge receipts into this existing standard S<n>"
            )
            s.add_argument(
                "--edited",
                action="store_true",
                help="the standard's text was rewritten",
            )
        if name == "retire":
            s.add_argument("id")
            s.add_argument("--reason", required=True)
    args = p.parse_args()
    return {
        "hook": cmd_hook,
        "mine": cmd_mine,
        "compose": cmd_compose,
        "retry": cmd_retry,
        "add": cmd_add,
        "list": cmd_list,
        "status": cmd_status,
        "drop": cmd_drop,
        "accept": cmd_accept,
        "retire": cmd_retire,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
