---
name: splitting-epics
description: Use when breaking an epic, plan or meeting notes into GitHub issues for a human team, or listing a work queue for project management. Not for agent sessions or jj stacks (see carve, nabu-outline).
---

# Splitting Epics

Done = the user approved the task list, every approved task exists as an issue, and the source links each one (epic issue, or issue numbers in the plan doc).

## Tasks

- One task = one person can pick it up and finish it. Outcome a tester can check.
- Only work not yet built. Code on the main branch = done, no task.
- Core build only by default. Production, compliance hardening and repo moves stay in the plan doc until the user pulls them in.
- Tests, docs and cleanup ride in the task that needs them. No internal testing-only, docs-only or cleanup-only task. A deliverable for someone outside the team (customer doc, prototype, review of their document) is a task.
- Each task names what it depends on.
- Every source item (epic requirement, meeting decision) maps to a task or to a decision the user approved.

## Flow

1. Read the sources and the code they touch. Present the task list (title, outcome, depends on) plus what you left out.
2. User approves -> per task, run `/writing-tickets` for the body, then `/humanizer` on its prose.
3. Create the issues in queue order => numbers show the order. Depends-on cites issue numbers.
4. Link each from the epic, or write the numbers into the plan doc.

## Changing the queue

- Task dropped -> close it: done work `--reason completed`, the rest `--reason "not planned"`. No comment unless the user asks.
