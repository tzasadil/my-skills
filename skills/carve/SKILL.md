---
name: carve
description: Use when figuring out the next work and splitting it into waves of chunks that separate sessions can build in parallel, or updating that series after a wave lands.
argument-hint: "[goal or area] [max parallel sessions]"
---

Write a series: the next work, split into waves of chunks that separate agent sessions build in parallel, each in its own workspace. Save to the project root as `SERIES-<topic>.md`. Same-topic series exists -> update it: tick landed chunks, re-derive the next waves.

One checkbox per wave and per chunk. Chunk ticked = landed on the merge target. Wave ticked = all its chunks ticked.

Done = the user approved a series where every chunk could start today in its own workspace, every goal requirement maps to a chunk or a decision, and no two chunks in one wave edit the same lines unless a merge rule covers it.

## Find the work

- Goal from args, else the open work: requirements or design docs vs what the code does, in-progress stacks and plans, `TODO:`s, recent history. Cite each finding as `path:line`.
- Record the foundations the work can reuse and the real gaps, with `path:line`.
- Reference existing plans, tablets, issues, docs by path. Never copy them.

## Cut chunks

Chunk = id, scope, observable outcome, owned paths, shared files it touches, dependencies, base revision. Id: lowercase slug, `[a-z][a-z0-9_-]{0,31}` (doubles as the agent session name).

- One chunk = one vertical feature slice a session can finish and ship on its own.
- Two or more parts a reviewer could verify alone (a table with its rules, a route group, a screen) -> split, unless they only make sense together.
- A chunk builds only what its own flows consume. Cleanup stays in the chunk that creates the need.
- Each chunk leaves the merge target working, whatever order its wave merges in.
- Each goal requirement maps to a chunk. Dropped or deferred -> a Decisions line the user approved.
- Owned paths disjoint within a wave. Overlap -> give the path to one chunk, or order the two chunks.
- Wave n+1 holds the chunks that need wave n's output. A chunk that only needs part of a dependency (a model, a facade signature) -> name that part, so it starts as soon as the part lands.
- Wave width = how many sessions the user can review at once. Unknown -> ask.

## Find the hotspots

Hotspot = a file several chunks must edit. Name each with its merge rule.

- Look for lists every feature extends: composition root, route mounting, closed unions, nav, schema, seed data, env config, dependency manifest and lockfile, generated files.
- Look for the same list spelled out in many places (every test building the full deps object) => each new feature edits every other chunk's files, and the break shows only after the merge. Fix it in a prep chunk.
- Prep chunk (wave 0): any change that turns a cross-chunk edit into a one-line append in one file. Lands before the others branch.
- Shared runtime (dev stack, database, ports, auth callback URLs): name which chunks contend and the rule.

## Check

Spawn `debugging-duck` for the opponent critique. Give it the absolute series path, the goal source (issue, design docs) when one exists outside chat, and `@<base directory>/opponent.md`.

- `empty` = clean.
- Resolve every finding with a fix, evidence-backed pushback, or a user decision.
- Re-present changed waves to the user.

## Doc

```markdown
<!-- series skeleton: drop empty sections -->
# Series: <topic>

**Status <date>:** <planned | wave N landed>. Base: `<change id>` ("<description>").
**Goal:** <one line>

## Findings
- <what exists or is missing, with path:line>

## Requirements
- <requirement from the goal source> -> `<id>` | Decisions

## Waves
- [ ] **Wave 0: prep**
  - [ ] `<id>`: <scope>. Outcome: <observable result>. Owns: <paths>. Touches: <hotspots>. Depends on: none. Base: `<change id>`.
- [ ] **Wave 1**
  - [ ] `<id>`: <scope>. Outcome: <observable result>. Owns: <paths>. Touches: <hotspots>. Depends on: <ids or parts>. Base: `<change id>`.
- [ ] **Later**
  - [ ] `<id>`: <scope>. Needs: <part of which chunk>.

## Hotspots
| File | Merge rule |
| --- | --- |

## Shared runtime
- <resource>: <who contends, rule>

## Decisions
- <decision> => <why>

## Open questions
1. <subject, why it matters, recommended answer>
```

Series approved -> offer `/conduct` with the series path.
