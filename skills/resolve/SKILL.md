---
name: resolve
description: Use when you need to resolve jj conflicts.
---

# Resolve

User asked to resolve: clear the present conflicts.
Self-invoked: unresolved conflicts can be safely ignored; continue with this workflow only if you choose to resolve.

- Do not create a new revision to resolve. Edit conflicted files directly.

## Loop

Walk the revision chain bottom up. Fix one conflicted revision at a time, earliest first. After a rev is clean, auto-propagation may clear or create descendant conflicts. Snapshot again, pick the earliest remaining conflicted rev, repeat. Stop when nothing is conflicted.

### Snapshot

1. `jj st` — earliest remaining conflicted revision and its files
2. Identify upstream (bookmark/rev rebased onto: `main`, `develop`, or the other parent). That is the baseline.
3. `jj edit <rev>`
4. Pin the pre-resolve state: `jj op log -n 1 -T 'id.short()' --no-graph`. Remember the returned op id.
5. `jj resolve --tool mergiraf`. One call merges every conflicted file it can by syntax tree (e.g. both sides added imports or functions). It leaves git diff3 markers (`<<<<<<<`, `|||||||` base, `=======`, `>>>>>>>`) where it cannot.
6. `jj resolve --list` — what remains.

If nothing is conflicted, stop. If mergiraf cleared everything, go to Recheck.

**Branch:** decide whether the resolution is easy or hard.

- easy: few files, conflicts have straightforward fixes, doc/test conflicts, etc
- hard: danger of regressions -> careful, spawn+review

### Easy -> Resolve in session

- Read the conflicted files (or `jj file show` for each side). Remove markers (`<<<<<<<`, `|||||||`, `=======`, `>>>>>>>`, `%%%%%%%`, `+++++++`).
- Auto-propagated conflicts: analyze this rev on its own. The later rev's old intent may no longer apply.
- Generated / regenerable files (lockfiles, `pnpm-store`): regenerate (`just install` or the repo's install command).
- Upstream is the baseline. NEVER regress it. Layer the branch on top. Lint/typecheck/tests say a symbol is missing => upstream likely deleted it. Adapt. Do not restore.

Then recheck this rev.

### Hard -> Spawn

Do the snapshot yourself. The subagent cannot see your context. Do not paste contents of the conflicted files into the prompt.

Spawn a writer subagent (Claude Code `general-purpose`, OpenCode `general`, not `explore`). Omit `model` unless the user named one. Spawn fails -> stop and report.

Pass only this (fill values):

```text
Role: resolve jj conflicts by editing files. Do not only report.

Context:
- Instructions: @/absolute/path/to/skills/resolve/resolver.md
- Worktree: <absolute path>
- Conflicted revision: <rev id>
- Upstream (do not regress): <bookmark or rev>
- Files: <paths>   (parallel split only, else omit)
```

One spawn per conflicted rev.

**Parallel split (same rev only):** 8+ remaining files that fall into independent groups => one resolver per group, all spawned in one message. Add `Files: <paths>` to each prompt. Group by cause, not directory: files tied to one upstream refactor or sharing a symbol go to the same agent. Unsure whether groups are independent => one spawn. Never parallelize across revs: fixing an earlier rev rewrites later conflicts. Run Recheck once, after all agents return.

### Recheck (this rev)

1. **Cleared** — `jj st` has no remaining conflicts on this rev. No leftover markers.
2. **Correct** — read every edit since the pin (mergiraf, then yours or the subagent's):

   ```bash
   jj op diff --git --ignore-all-space --no-graph --from <pre_resolve_op_id>
   ```

   Judge: coherent merge, no duplicated functions, half-applied refactors, stale names, or hand-merged lockfiles.
3. **Upstream not regressed:** No restoration of what upstream deleted. No breaking of what upstream added.
4. **Checks** — lint/typecheck on the whole project; tests on files that were conflicted this iteration.

Then loop: next earliest remaining conflicted rev, fresh snapshot.
Conflicts that newly appear (=>auto-propagation) are in-session.

## Rules

- Subagent merge fails -> retry once. Still wrong -> Fix yourself.
- If you notice significant wiring outside of conflicts is required to maintain behaviour of both upstream and local changes, then raise that with the user. It is to be considered blocking.
