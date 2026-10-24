---
name: retrospective
description: "Conduct a retrospective on a coding session."
disable-model-invocation: true
---

The user asked for a **retrospective**. Report improvements to the coding agent's environment and skills for future runs. Report only: do not edit anything. The user judges each candidate.

A background miner applies the same lenses at every session end, on a cheap model, read only. A manual run adds the main model's judgement and the steps that run commands.

## Steps

1. Call the Skill tool with `writing-skills` for the writing style guide.
2. Read the primary sources for the session the user specifies. Search session logs on this machine if needed. Unspecified -> current session.
   - `debugging-duck` reports first (see `lenses.md`). Each run, nested and background included, is a `<session>/subagents/agent-<id>.jsonl` whose `.meta.json` has `agentType: debugging-duck`. Report = last text of each turn.
3. Read `<skill-dir>/../rule-forge/lenses.md`. Find candidates with every lens in it. On top, in a manual run:
   - **Automated checks:** read the repo's own check command first (`package.json` / lint / check scripts / CI). Before proposing a new check, run it over the repo and report hits, real defects among them, and what silencing the rest takes. Mostly false hits -> say so.
   - **Failed standard:** an existing standard the reviewer had and still missed => rewording rarely helps. Clarify it only when the line is unclear. Otherwise propose a check that catches the mistake, or keep the line.
   - **Skill merge:** skills that load together in nearly every run -> one skill, when one is never useful without the other. `just usage` (skills repo root) counts loads. Session logs show co-occurrence.
4. Present candidates in order of severity. Apply only what the user picks.
   - A picked coding standard -> file it so it gets receipts: pipe `{lens: "coding-standard", rule, class, receipts: [{date, session, speaker, quote}]}` (one receipt per moment: the line that shows the mistake, not the agent's reply to the correction) to `<skill-dir>/../rule-forge/scripts/rule_forge.py add --by retrospective`, then `accept <C id>`, then add `- <rule> (<S id>)` to the repo's `CODING_STANDARDS.md`. Run `list` first. Same rule as a rejected one -> do not file it, mention it was rejected. Same rule as an open candidate, or a standard that failed -> pipe `{supports: <C, G, or S id>, receipts}` instead, so the evidence joins it.

## Files

- `AGENTS.md`: always in the agent's context. Use sparingly, usually **navigation pointers**.
- `<skill-dir>/../with-implementer/implementer-rules.md`: every implementer subagent gets it, the main agent never does. Implementation behavior true in every repo. Never write `~/.claude/CLAUDE.md`.
- `CODING_STANDARDS.md` (repo root): read by reviewers only, never by the implementer. The implementer carries the most context pressure (explore, write, debug). The reviewer gets a diff -> standards belong on the reviewer. No file yet -> create it on the first picked rule.
- Docs: references, pointed to by other files. Look for existing docs before writing new ones.
- Skills: for docs (description goes into context) or user-invoked commands. Follow `writing-skills`.
