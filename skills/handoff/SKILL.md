---
name: handoff
description: Use when the user asks for a handoff, or to write down findings or remaining work for a later session.
argument-hint: "What will the next session be used for?"
---

Write a handoff doc so a fresh agent can continue. Save to the root of the project the session worked in as `HANDOFF-<topic>.md`. Same-topic handoff exists -> update it.

- Focus = user arguments, else the session's open work. Tailor the doc to it.
- Content: what the next agent cannot get from the repo. Findings with evidence (`path:line`), decisions + why, open questions, unverified assumptions.
- No reading-order or onboarding section => repo docs and `AGENTS.md` cover orientation.
- Do not duplicate PRDs, plans, ADRs, issues, commits, diffs. Reference by path / URL / bash command.
- Redact secrets, passwords, PII.
