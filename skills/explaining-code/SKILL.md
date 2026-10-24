---
name: explaining-code
description: Use when the user is confused about some code or functionality and asks for an explanation.
---

# Explain

Explain in chat. Add comments so the understanding sticks. Do not refactor or change behavior — comments only. Obviously buggy -> mention in chat; do not fix unless asked.

## Understand

Read the function, callers, callees, surrounding context. Trace data flow.

- **What:** contract / purpose
- **How:** algorithm, data structures, control flow
- **Why:** edge cases, performance, platform quirks, history

Whole file: structural overview first (public API, internal organization, key types, how pieces connect), then each major function or section.

Block or line: focus there. Still check callers/callees when they explain the behavior.

## Chat

One-sentence purpose, then step through the logic. Highlight non-obvious side effects, key invariants/assumptions, and why simpler alternatives were not used (if clear from context). Brief. No line-by-line narration unless asked.

## Comments

Existing comment style. Both **why** and **what**.
