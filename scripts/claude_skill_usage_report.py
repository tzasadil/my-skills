#!/usr/bin/env python3
"""Report skill invocations from local Claude Code session transcripts.

Why: skills get edited far more than they get used. A skill with zero loads
across months is either undiscoverable or dead weight.

Counts both model `Skill` tool calls and user-typed `/skill` commands, since a
slash command loads the skill without a `Skill` tool call. Slash commands count
only when the name matches a known skill, so built-ins like `/clear` stay out.

Set CLAUDE_CONFIG_DIR to point at another Claude Code config directory.
"""
import collections
import json
import os
import pathlib
import re
import sys

CONFIG = pathlib.Path(
    os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
)
PROJECTS = CONFIG / "projects"
SKILLS_DIR = pathlib.Path(__file__).resolve().parent.parent / "skills"
# Anchored: tool results quoting transcripts also contain this markup.
SLASH = re.compile(r"^(?:<command-message>[^<]*</command-message>\n)?"
                   r"<command-name>/([\w:.-]+)</command-name>")


def skill_names(root):
    return {p.parent.name for p in root.glob("*/SKILL.md")}


def invocations(path, known):
    """Yield (id, skill, day). Ids dedupe resumed or forked sessions."""
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            # Cheap prefilter: most lines are neither.
            if '"Skill"' not in line and "<command-name>" not in line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            day = (rec.get("timestamp") or "")[:10]
            content = (rec.get("message") or {}).get("content")
            # `api-request-blob` records replay history, so filter by type.
            if rec.get("type") == "assistant" and isinstance(content, list):
                for block in content:
                    if (block.get("type") == "tool_use"
                            and block.get("name") == "Skill"):
                        skill = (block.get("input") or {}).get("skill")
                        yield block.get("id"), skill, day
            elif rec.get("type") == "user" and isinstance(content, str):
                m = SLASH.match(content)
                if m and m.group(1) in known:
                    yield rec.get("uuid"), m.group(1), day


def main():
    if not PROJECTS.is_dir():
        print(f"no Claude Code transcripts at {PROJECTS}; "
              "set CLAUDE_CONFIG_DIR to point at a config directory")
        return 1
    shipped = sorted(skill_names(SKILLS_DIR))
    known = set(shipped) | skill_names(CONFIG / "skills")

    counts = collections.Counter()
    last = {}
    seen = set()
    # rglob includes subagent transcripts under <session>/subagents/.
    for path in PROJECTS.rglob("*.jsonl"):
        try:
            for key, skill, day in invocations(path, known):
                if not skill or key in seen:
                    continue
                seen.add(key)
                counts[skill] += 1
                last[skill] = max(last.get(skill, ""), day)
        except OSError as exc:
            print(f"skipping {path}: {exc}", file=sys.stderr)

    print(f"{'skill':44} {'loads':>6}  last")
    for skill, n in counts.most_common():
        print(f"{skill:44} {n:>6}  {last[skill]}")

    dead = [s for s in shipped if s not in counts]
    print(f"\n{len(dead)}/{len(shipped)} shipped skills never loaded:")
    for s in dead:
        print(f"  {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
