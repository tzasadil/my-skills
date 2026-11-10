---
name: carve
description: Use when figuring out the next work and splitting it into waves of strands that separate sessions can build in parallel, or updating that series after a wave lands.
argument-hint: "[goal or area] [max parallel sessions]"
---

Write a series: the next work, split into waves of strands that separate agent sessions build in parallel, each in its own workspace. Save to the project root as `SERIES-<topic>.md`. Same-topic series exists -> update it: landed work leaves, Findings and the waves ahead are re-derived.

The series holds only work ahead. A landed wave leaves with its strands. Its Decisions, Findings, wave header notes and answered Open questions leave too unless a strand ahead still needs them => the series stays readable in one pass; version control keeps the rest. `Landed` keeps one line (number, merge commit, PRs) only for the latest wave (the next merge target, the highest wave number) and for waves whose PRs are still open. Wave numbers continue across updates: a new wave takes the next unused number.

Done = the user approved a series where every strand could start today in its own workspace, every goal requirement maps to a strand or a decision, and strands in one wave mostly touch different files.

## Find the work

- Goal from args, else the open work: requirements or design docs vs what the code does, in-progress stacks and plans, `TODO:` and `REVISIT:` comments, recent history. Cite each finding as `path:line`.
- Record the foundations the work can reuse and the real gaps, with `path:line`.
- With or without a goal, list the work in flight: `jj log -r 'heads(mutable() ~ empty())'` and `jj workspace list`. Each head lands in the base, becomes a strand, or gets a Decisions line => no strand starts on a base that lacks finished work it builds on.
- Base: holds its remote bookmark and every finished head the strands build on. Behind -> sync it before cutting (a prep strand when the sync conflicts).
- Reference existing plans, tablets, issues, docs by path. Never copy them.

## Cut strands

Strand = id, scope, observable outcome, likely paths, dependencies, base revision. Id: lowercase slug, `[a-z][a-z0-9_-]{0,31}` (doubles as the agent session name).

- One strand = one vertical feature a session can finish and ship on its own.
- Two or more parts a reviewer could verify alone (a table with its rules, a route group, a screen) -> split, unless they only make sense together or form a bundle (next rule).
- A strand costs a tablet and five review lanes whatever its size. Small items of one wave (each about 150 changed lines or fewer, no new route, table, migration or role, no product question) -> one bundle strand with one tablet, even when unrelated. A lone small item joins the strand whose files it touches.
- A strand builds only what its own flows consume. Cleanup stays in the strand that creates the need.
- Each strand works alone on its base and merged with its whole wave.
- Each goal requirement maps to a strand. Dropped or deferred -> a Decisions line the user approved.
- Likely paths = a guess at the footprint, used only to cut the wave. Not a boundary for the session.
- Likely paths roughly disjoint within a wave. Heavy overlap -> merge the two strands or order them. Small overlap is fine => `/resolve` handles it at merge.
- Wave n+1 holds the strands that need wave n's output. A strand that only needs part of a dependency (a model, a facade signature) -> name that part, so it starts as soon as the part lands.
- Wave width = how many sessions the user can review at once. Unknown -> ask.

## Find the overlaps

Overlap = a file or sequence several strands of one wave will likely edit. Purpose: cut the waves and find prep strands. The series gets no list of them: an overlap ends as a prep strand, an order between two strands, a value in the wave header, or a merge note there when the resolution is project-specific (one strand owns a shared signature). A lasting project rule (date formatting, logging, how migrations are named) belongs where every session reads it (`AGENTS.md`, a comment at the site), not in the series.

- Look for lists every feature extends: composition root, route mounting, closed unions, nav, schema, seed data, env config, dependency manifest and lockfile, generated files, a doc with a line per module.
- Three or more strands of a wave append to one such list => a conflict with that many sides, resolved by hand at every merge. Spread the strands over waves, or a prep strand gives each feature its own file.
- Look for the same list spelled out in many places (every test building the full deps object) => each new feature edits every other strand's files, and the break shows only after the merge. Fix it in a prep strand.
- Prep strand (wave 0): any change that turns a cross-strand edit into a one-line append in one file. Lands before the others branch.
- Shared runtime (dev stack, database, ports, auth callback URLs): name which strands contend and the rule.
- Global sequences (deviation IDs, migration timestamps, seed id blocks): the wave header gives each strand its own value. "Next free" on a shared base => two strands take the same one.

## Check

Spawn `opponent` for the critique (`debugging-duck` when that profile is missing). Give it the absolute series path, the goal source (issue, design docs) when one exists outside chat, and `@<base directory>/opponent.md`.

- `empty` = clean.
- Resolve every finding with a fix, evidence-backed pushback, or a user decision.
- Re-present changed waves to the user, with the Open questions in the same call.

## Doc

Series names roles only: implementer, reviewer. No agent, session, or person => any team can build from it.

```markdown
<!-- series skeleton: drop empty sections -->
# Series: <topic>

**Status <date>:** <planned | wave N landed>. Base: `<change id>` ("<description>").
**Goal:** <one line>

## Findings
- <what exists or is missing, with path:line>

## Requirements
- <requirement from the goal source> -> `<id>` | Decisions

## Landed
- Wave <n>: `<merge commit>`, PRs <numbers>.

## Waves
- **Wave <n>: prep**
  - `<id>`: <scope>. Outcome: <observable result>. Likely paths: <paths>. Depends on: none. Base: `<change id>`.
- **Wave <n+1>.** <per-strand values: `<id>` migration timestamp, id block> <merge note>
  - `<id>`: <scope>. Outcome: <observable result>. Likely paths: <paths>. Depends on: <ids or parts>. Base: `<change id>`.
- **Later**
  - `<id>`: <scope>. Needs: <part of which strand>.

## Shared runtime
- <resource>: <who contends, rule>

## Decisions
- <decision> => <why>

## Open questions
1. <subject, why it matters, recommended answer>
```

Series approved -> recommend the next step, do not start it: `/conduct` with the series path, or `/splitting-epics` for one issue per strand.
