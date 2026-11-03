---
name: conduct
description: Use when launching strands of work as parallel interactive agent sessions, or checking, merging, and shipping their waves. Not for planning the strands (see carve), one workspace (see workspace), or subagent batches (see with-implementer).
argument-hint: "[<series or strand list> | status | merge]"
---

Run strands of work in parallel: one jj workspace, one herdr workspace, one interactive `claude` session per strand. Sessions, not subagents => each strand asks the user its own questions. This session coordinates.

Mode from args: `status` -> Status. `merge` -> Merge. Anything else -> Split, then Launch.

Strand = id, scope, dependencies, base revision, run mode. Id doubles as the herdr agent name => lowercase, `[a-z][a-z0-9_-]{0,31}`.

Run mode decides how a strand is built. Both modes get their own jj workspace and join the wave merge as a parent; only the build differs:

| | `session` | `batch` |
| --- | --- | --- |
| Who builds | an interactive `claude` session running `/strand` | one implementer subagent of this session (`/with-implementer`, mode `goal`, review `full`) |
| Tablet and review lanes | yes: the strand writes, builds and verifies its tablet | no: this session reviews the diff; finalize at merge covers the rest |
| User questions | the session asks the user itself | the implementer reports blockers; this session asks |
| Cost | a tablet (~200 lines) and five review lanes | the diff review only |

- `batch` when every part holds: about 150 changed lines or fewer, no new route, table, migration or role, no product question expected (docs, a guard with its tests, a config switch, a small fix). Several batch strands of a wave may share one implementer run when their files do not overlap.
- Else `session`. Unsure -> `session`.

## herdr

- This session must run inside a herdr pane: `test "${HERDR_ENV:-}" = 1`. Fails -> tell the user to start `herdr`, run `claude` in a pane, rerun. Stop.
- Syntax: `herdr <group> --help`. Read IDs from the JSON responses.
- jj workspaces only. Never `herdr worktree` (git worktrees).

## Split

Done = strand list the user approved, every field set.

- Strands given (series, issue list, conversation) -> take them. Missing field -> ask.
- No strands yet -> run /carve, then continue here with its series.
- Every strand has a run mode. The series names it; missing -> set it by the rule above and say so.

## Launch

Done = one jj workspace per strand. `session` strands: a herdr workspace with its `claude` session working on the brief, user told where to find them. `batch` strands: built and reviewed by an implementer run.

1. Base: the most up-to-date revision, not the base the series names. This working copy is non-empty (series edits, fixes) -> it is the base. Empty -> its parent. Then `jj new` here => the base stays fixed and later edits here never rebase the strands or leave their workspaces stale.
2. Dependencies: launch a strand only when the revisions it needs are in its base. Unmet -> name the blocker, skip the strand.
3. Run /workspace once per strand (name = id, from = base, including its Bootstrap), then continue here.
4. `session` strands: fill the brief. Pass inputs only: `/strand` holds the rules every strand follows, and the repo rules load on their own.

   ```markdown
   <!-- strand brief: fill every <...> -->
   Run `/strand` for strand <id> of a parallel split: <scope>.
   - Workspace: <absolute workspace path>. Base: <base change id>.
   - Series with the full split: <absolute path, or "none">.
   ```

5. Per `session` strand:

   ```bash
   # herdr workspace in the strand's jj workspace => pane id at .result.root_pane.pane_id
   herdr workspace create --cwd <workspace-dir> --label <id> --no-focus
   # interactive claude as the `strand` agent (sonnet), allowed to read the series outside its workspace (no series -> drop --add-dir)
   # --remote-control: auto-connect (remoteControlAtStartup) skipped strand sessions => connect explicitly, named after the strand
   herdr agent start <id> --kind claude --pane <pane-id> -- --agent strand -n <id> --remote-control <id> --add-dir <series-dir>
   # pastes the multi-line brief as one prompt
   herdr agent prompt <id> "<brief>"
   ```

   `agent start` answers `agent_not_ready` => claude waits on a startup prompt (folder trust for a new workspace). Ask the user to answer it in that herdr workspace, then `herdr agent wait <id>` and send the brief.

6. `batch` strands, after every session runs (an implementer run blocks this session, the sessions keep building): one `/with-implementer` run per strand, or per group of batch strands with disjoint files, mode `goal`, review `full`, worktree = the strand's workspace. Target = the strand's series entry plus the wave header values (migration timestamp, seed block, DV number). The implementer describes the revision. A blocker or product question -> ask the user, then continue the implementer.
7. Tell the user: one herdr workspace per `session` strand, labelled with its id, and each `batch` result.
8. The series has no draft of the next wave -> draft it while the strands build, using `/carve` => its opponent check runs now, not at merge. The draft lands in the series in this working copy. A draft exists -> skip: the merge replan reworks it.

## Status

Done = one row per strand: revisions on top of its base, last description, and session state (`session`) or implementer result (`batch`).

- Revisions: `jj log -r '<base>::<id>@'`.
- Session state: `herdr agent list`. `blocked` => waiting for the user (question or approval). Agent gone => claude exited.
- Need the detail: `herdr agent read <id> --source recent-unwrapped --lines 60`.
- Waiting on one strand: `herdr agent wait <id> --until blocked`.

## Merge

Done = one merge commit on the merge target, its parents every strand tip of the wave, conflicts resolved, finalize fixes and the current series in it, the repo's full gate green on it. Strand revisions untouched, strand workspaces and sessions closed. Each strand and the merge commit shipped. Next wave offered, not launched.

Proceed without asking up to and including the replan. Stops: a strand not finished, a strand-owned failure (sent to its session), and /nabu-ship's approval.

- Merge target: the previous merge commit. First wave: the series base.
- Finished: `session` = session `idle` or `done`, and `nabu status` in its workspace shows its tablet `ready to archive`. `batch` = its implementer reported green checks and this session's diff review is done (no tablet). A strand not finished -> report what is open, stop. The user says go on without it -> merge the finished strands now; the late strand joins later as one more parent (`jj rebase -s <merge commit> -o <tip> ... -o <late tip>`), then resolve, gate and finalize again.
- Snapshot every strand workspace before the merge and before each rebase onto new tips: `jj -R <workspace> st`. jj snapshots a workspace only when a jj command runs in it => an edit made there since stays out of the merge unseen.
- Strand tip = the strand's top non-empty revision: usually `<id>@`, or `<id>@-` when that working copy is empty.
- Create the merge commit:

  ```bash
  # merge commit with one parent per strand tip
  jj new <tip> <tip> -m "merge wave <n>: <ids>"
  ```

- Conflicts: run /resolve on the merge commit, and treat every merge conflict as hard, then continue here. Pass it the series' hotspot notes and what each strand session reported: gotchas, cross-strand notes, intent dropped => the resolver knows what each side meant.
- Cross-strand needs: `rg 'TODO: waits for (<id>|<id>)\b'` on the merge commit, one `<id>` per strand of this wave. Resolve each in the merge commit and delete its `TODO:`. Then search for the later strands' ids: leave those, and note each under its strand in the series.
- Gate red and the cause sits in one strand -> `session`: send it to that strand's session (`herdr agent prompt <id> "<failure and evidence>"`), do not fix it here. `batch`: continue its implementer with the failure. Fix lands -> move the merge commit onto the new tips (`jj rebase -s <merge commit> -o <tip> -o <tip>`), then resolve and gate again.
- Gate green -> run /nabu-finalize on the wave (base: the merge target, top: the merge commit), then continue here. A blocker that sits in one strand -> same as a red gate.
- Squash finalize's revision into the merge commit (`jj squash -u --from <finalize revision> --to <merge commit>`) => the merge PR carries resolutions and finalize fixes.
- Update the series in the merge commit: the wave and its strands leave, its `Landed` line (number, merge commit, PRs) stays, the status line points at the merge commit. What the merge taught (cross-strand fixes) becomes Hotspot or Decision rules. Each `TODO: waits for` of a later strand goes under that strand. Series edits made since the last merge come along (`jj squash -u --from <series revision> --to <merge commit> <series path>`).
- Replan after every merge, before shipping, the plan is not fixed: using `/carve`, rework the next wave's draft with what the merge changed (new needs, wrong cuts, changed dependencies). Ship approval comes after => the user sees the reworked next wave with it.
- `jj new <merge commit>` => later edits stay out of it. The next wave's series edits collect in this working copy, on disk for the strand sessions.
- Per strand, without asking: `herdr workspace close <herdr workspace id>`, then `jj workspace remove <id>`. Strand revisions stay as parents of the merge commit.
- Ship the strands first: one PR per strand from its tip using `/nabu-ship` (`-r <tip>`, target: the merge target). A shared base above the merge target (Launch step 1) ships once, as the shared bottom of their stacks. Merge commit last (`-r`, same target), only once every strand PR is open => a pushed merge commit makes its parents immutable, and `nabu ship` rewrites the revision it ships.
- Add the PR numbers to the wave's `Landed` line in the working copy. The pushed merge commit is immutable => they land with the next merge.
- Offer Launch of the next wave on the merge commit. Never launch it without the user's go.
