---
name: rule-forge
description: "Triages the repo's mined rule candidates. Applies or drops each, keeping receipts for coding standards."
disable-model-invocation: true
---

The user wants to empty the **rule inbox**: candidates a background miner extracted from past sessions of this repo. Done-state: every candidate is applied or dropped.

## Files

`<repo>` = directory name of the current repo's main checkout. Store files live outside the repo.

- `~/.agents/rule-forge/<repo>.json`: open candidates `C<n>`. Each has `kind`, `rule`, `class` (root cause), `source` (`by`: the pass or skill that filed it, `lens`: the retrospective lens), and `receipts` (dated verbatim quotes with a `cc:<project>/<session>` ref). `merged` lists the `{id, rule}` of candidates folded into it. `promoted_to: G<n>`: the problem recurs in 3 or more repos, so the shared `G<n>` holds the rule for every repo, and this candidate holds the local fix. Also `dropped` (rejected rules with reasons, shown to the miner) and triage `stats`, overall and per source.
- `~/.agents/rule-forge/_shared.json`: same shape, candidates `G<n>` of kinds `skill`, `global-rule`, and `harness`. Their fix lives outside any one repo, so every repo's triage shows them.
- `CODING_STANDARDS.md` (repo root): rules for reviewers only. Each line ends with its id: `(S3)`. Missing -> create it on the first accepted standard.
- `~/.agents/rule-forge/<repo>.receipts.json`: receipts per standard, plus `retired` entries.
- `scripts/rule_forge.py`: `status`, `list`, `accept`, `drop`, `retire`. Other skills file candidates and receipts with `add`. Run `--help`. Mining config and prompts: `config.json`, `miner-prompt.md` (one session), `compose-prompt.md` (every `compose_every` sessions: merges duplicates, combines scattered candidates of one root cause), and `promote-prompt.md` (right after: moves a problem that recurs across repos to the shared inbox) in this skill's directory. All three apply the lenses in `lenses.md`, which `/retrospective` reads too.

## Steps

1. Run `status`. It prints open counts, the miner's invalid-proposal rate, and triage outcomes per inbox. A warning -> tell the user before anything else: an empty inbox from a broken miner is not a clean inbox. No candidates and no warning -> say so and stop.
2. Read both inboxes. More than 15 candidates -> offer a slice: the 10 oldest, or one kind. Say how many stay open.
3. Present one table: id, kind, source, rule, receipt count, your recommendation (apply, done, merge into another id, or drop) with a one-line reason. Read the cited quotes before recommending.
   - Check each candidate against its target as it is now: `CODING_STANDARDS.md`, `AGENTS.md`, implementer rules, global user rules, the named skill, the linter or hook config. Already says it -> recommend done. Fixes often land through normal work after mining.
   - Same rule as another candidate -> recommend merging into the one with better wording.
   - A `merged` list holds a rule the candidate's text no longer covers -> the composer merged wrongly. Say so: re-file that rule with `add`.
   - A promoted shared candidate lists its parts in `promoted_from` and `applied_in`. Applying it -> recommend deleting each `applied_in` line from its repo, now redundant. Its `promoted_to` repo candidates stay: recommend done when the global rule covers them, else apply the local fix.
   - A `duck` receipt is a reviewer catch, never `weak`. Rank duck-backed candidates first.
   - Recommend drop, with its `--reason`, for: one weak receipt with no correction behind it (`weak`), generic advice (`generic`), a pattern or technique that went well with no mistake behind it (`not-a-mistake`), a rule that is wrong for this user or repo (`wrong`).
4. The user picks. Apply what they pick:
   - done: `accept <id>`. A standard already covers it -> `accept <id> --into S<n>`, so the standard keeps the receipts.
   - merge: `drop <id> --into <target id>` moves the receipts, then handle the target. Both ids in the same inbox.
   - `coding-standard`: `accept <id>` -> prints the new `S<n>`. Add `- <rule> (S<n>)` under the matching heading of `CODING_STANDARDS.md`. Same class as an existing standard -> sharpen that line instead, then `accept <id> --into S<n> --edited`.
   - `recurrence`: standard `S<n>` did not prevent a repeat. The reviewer had the line and missed the mistake anyway, so rewording rarely helps. Pick the first that fits:
     - The line is unclear -> rewrite it, then `accept <id> --edited`.
     - A tool can catch most cases (lint rule, CI grep, test) -> build that check (see `automated-check`), then `accept <id>`.
     - Neither -> keep the line unchanged, then `accept <id>`. It keeps failing -> `retire S<n> --reason "..."`, delete the line, then `drop <id> --reason other --note "S<n> retired"`.
   - `automated-check`: first run the check over the repo. Count hits, real defects among them, and what silencing the rest takes. Mostly false hits -> show the user the numbers and let them pick: build, narrow, or drop. To build: add it to the repo's linter, hooks, or CI, then `accept <id>`.
   - `harness`: change the agent's setup (settings, hooks, MCP servers, a CLI swap), or delete the no-op instruction, then `accept <id>`.
   - `agents-md`: add the line to the repo `AGENTS.md`, then `accept <id>`.
   - `global-rule`: add `- <rule>` to `<skill-dir>/../with-implementer/implementer-rules.md`, then `accept <id>`. Every implementer subagent gets that file. Never write `~/.claude/CLAUDE.md`. File past ~20 rules -> merge into broader lines before adding.
   - `skill`: pick the smallest target that fits:
     - An existing skill fits the task but never loaded -> fix its description, not its body.
     - The skill loaded and still let the mistake through -> fix its body.
     - A `new:` candidate -> first look for an existing skill whose trigger covers the task, and extend it. Only a new trigger earns a new skill.
     - One-line fix the implementer acts on -> it belongs in `AGENTS.md` or the implementer rules instead.

     Skills live next to this one, in the repo that holds this skill. Write with `writing-skills`. Check siblings: skills with the same prefix (`openspec-*`) or that run the same step. The fix still holds with the skill's name removed -> edit each sibling too. Run `just check` from that repo's root. A new skill -> tell the user to link it into `~/.agents/skills/`. Never run `just link-*`: the user picks which skills load. Then `accept <id>`.
5. `drop` everything the user rejected, each with a `--reason`. Add `--note` when the reason alone would not stop the miner from proposing a variant.

## Report

Standards added, rewritten, or retired, with ids. Other edits by file. Done, merged, and dropped ids. Any `status` warning. A dominant drop reason, a source with mostly drops in `status`, or a high invalid-proposal rate -> suggest the change that would cut it: that lens in `lenses.md`, `miner-prompt.md`, `compose-prompt.md`, `promote-prompt.md`, or the model.
