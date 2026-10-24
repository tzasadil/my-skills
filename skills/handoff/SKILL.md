---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---

Write a handoff so a fresh agent can continue. Save to the root of the project the session worked in.

- Include a "suggested skills" section.
- Do not duplicate PRDs, plans, ADRs, issues, commits, diffs. Reference by path / URL / bash command.
- Redact secrets, passwords, PII.
- User arguments = what the next session focuses on. Tailor the doc to that as intent.
