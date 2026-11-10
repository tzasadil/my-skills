---
name: conduct
description: Use when launching strands of work as parallel interactive agent sessions, or checking, merging, and shipping their waves. Not for planning the strands (see carve), one workspace (see workspace), or subagent batches (see with-implementer).
argument-hint: "[<series or strand list> | status | merge | megamerge]"
---

Run strands of work in parallel: one jj workspace, one herdr workspace, one interactive `claude` session per strand. Sessions, not subagents => each strand asks the user its own questions. This session coordinates.

Mode from args: `status` -> Status. `merge` -> Merge. `megamerge` -> Megamerge. Anything else -> Split, then Launch.

Strand = id, scope, dependencies, base revision. Id doubles as the herdr agent name => lowercase, `[a-z][a-z0-9_-]{0,31}`.

Series: `Read` it once per mode, then edit from that read.

## herdr

- This session must run inside a herdr pane: `test "${HERDR_ENV:-}" = 1`. Fails -> tell the user to start `herdr`, run `claude` in a pane, rerun. Stop.
- Syntax: `herdr <group> --help`. Read IDs from the JSON responses.
- jj workspaces only. Never `herdr worktree` (git worktrees).

## Split

Done = strand list the user approved, every field set.

- Strands given (series, issue list, conversation) -> take them. Missing field -> ask.
- No strands yet -> run /carve, then continue here with its series.

## Launch

Done = per strand: one jj workspace and a herdr workspace with its `claude` session working on the brief. User told where to find them.

1. Base: the most up-to-date revision, not the base the series names. This working copy is non-empty (series edits, fixes) -> it is the base. Empty -> its parent. Then `jj new` here => the base stays fixed and later edits here never rebase the strands or leave their workspaces stale. Then `jj git fetch` and `jj log -r 'heads(mutable() ~ empty())'`: the base lacks the remote head of the branch the wave ships to, or a finished head a strand builds on -> name what is missing and ask before launching.
2. Dependencies: launch a strand only when the revisions it needs are in its base. Unmet -> name the blocker, skip the strand.
3. Run /workspace once per strand (name = id, from = base, including its Bootstrap), then continue here.
4. Fill the brief. Pass inputs only: `/strand` holds the rules every strand follows, and the repo rules load on their own.

   ```markdown
   <!-- strand brief: fill every <...> -->
   Run `/strand` for strand <id> of a parallel split: <scope>.
   - Workspace: <absolute workspace path>. Base: <base change id>.
   - Series with the full split: <absolute path, or "none">.
   ```

5. Per strand:

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

6. Tell the user: one herdr workspace per strand, labelled with its id.
7. The series has no draft of the next wave -> draft it while the strands build, using `/carve` => its opponent check runs now, not at merge. The draft lands in the series in this working copy. A draft exists -> skip: the merge replan reworks it.

## Status

Done = one row per strand: revisions on top of its base, last description, session state, tablet state.

- Revisions: `jj log -r '<base>::<id>@'`.
- Session state: `herdr agent list`. `blocked` => waiting for the user (question or approval). Agent gone => claude exited.
- Tablet state: `nabu status <tablet>` in the strand's workspace. Tablet name unknown -> `nabu list` there.
- Need the detail: `herdr agent read <id> --source recent-unwrapped --lines 60`. `agent_not_idle` (the agent is blocked) -> `--source visible`.
- Waiting on one strand: `herdr agent wait <id> --until blocked`.

## Merge

Done = one merge commit on the merge target, its parents every strand tip of the wave, conflicts resolved, the gate green on it, the wave's tablets archived and the current series in it. Strand revisions untouched, strand workspaces and sessions closed. Each strand and the merge commit shipped. Next wave offered, not launched.

Proceed without asking up to and including the replan. A plan or wave the user approved is not asked again. Stops: a strand not finished, a strand-owned failure (sent to its session), a question /nabu-archive asks, and /nabu-ship's approval.

Gate = the repo's CI gate: static analysis plus the whole test suite, one command when the repo has one. It runs once on the merge commit, and this session runs no narrower check before it. Red -> rerun only the failing check while the fix lands, then the gate once. A check a subagent reported green on the current revision is done: rerun it only when the diff contradicts the report.

- Merge target: the previous merge commit. First wave: the series base.
- Finished: session `idle` or `done`, and the strand's tablet is `ready to archive` (Status). A strand not finished -> report what is open, stop. The user says go on without it -> merge the finished strands now; the late strand joins later as one more parent (`jj rebase -s <merge commit> -o <tip> ... -o <late tip>`), then resolve and gate again.
- Snapshot every strand workspace before the merge and before each rebase onto new tips: `jj -R <workspace> st`. jj snapshots a workspace only when a jj command runs in it => an edit made there since stays out of the merge unseen.
- Tips stay frozen while this session works on the merge commit: every session whose tip becomes a parent is `idle` or `done` before `jj new`. While a strand fixes a failure, run no jj command here until its session finishes: `herdr agent wait <id> --until working`, then `herdr agent wait <id>` (`blocked` => it asked the user, wait again) => a tip amended while this workspace snapshots splits the merge commit into divergent copies.
- A dev stack mounts this workspace -> stop it before `jj new`, tell the user, and leave it down until the gate is green => conflict markers crash it.
- Strand tip = the strand's top non-empty revision: usually `<id>@`, or `<id>@-` when that working copy is empty.
- Create the merge commit:

  ```bash
  # merge commit with one parent per strand tip
  jj new <tip> <tip> -m "merge wave <n>: <ids>"
  ```

- Conflicts: run /resolve on the merge commit, and treat every merge conflict as hard, then continue here. Pass it the wave header's merge notes, what each strand session reported (gotchas, cross-strand notes, intent dropped), and that the gate runs next.
- Cross-strand needs: `rg 'TODO: waits for (<id>|<id>)\b'` on the merge commit, one `<id>` per strand of this wave. Resolve each in the merge commit and delete its `TODO:`. Then search for the later strands' ids: leave those, and note each under its strand in the series.
- Update the series in the merge commit, without waiting for the gate: the wave and its strands leave, its `Landed` line (number, merge commit, PRs) stays, the status line points at the merge commit and claims only what has happened. What the merge taught (cross-strand fixes): a rule only the waves ahead need -> a wave header note or a Decision. A lasting rule -> its permanent home, not the series: a check when a script can catch it, a `GOTCHA:` comment at the site, `ARCHITECTURE.md` for a cross-module invariant, `AGENTS.md` only as a pointer. A rule for implementers or reviewers in every repo -> name it as a `/retrospective` candidate in the merge report: the user picks, and rule-forge keeps its receipts. Never write `implementer-rules.md` or `CODING_STANDARDS.md` from here. Each `TODO: waits for` of a later strand goes under that strand. Series edits made since the last merge come along (`jj squash -u --from <series revision> --to <merge commit> <series path>`).
- Gate red and the cause sits in one strand -> send it to that strand's session (`herdr agent prompt <id> "<failure and evidence>"`), do not fix it here. Fix lands -> move the merge commit onto the new tips (`jj rebase -s <merge commit> -o <tip> -o <tip>`), then resolve and gate again.
- Gate green -> in the merge commit, run /nabu-archive for each tablet of the wave and delete each root `HANDOFF-*.md` the wave fully implements, then continue here. The archive changed code comments -> rerun format and lint.
- Replan after every merge, before shipping, the plan is not fixed: using `/carve`, rework the next wave's draft with what the merge changed (new needs, wrong cuts, changed dependencies). Ship approval comes after => the user sees the reworked next wave with it.
- `jj new <merge commit>` => later edits stay out of it. The next wave's series edits collect in this working copy, on disk for the strand sessions.
- Per strand, without asking: `herdr workspace close <herdr workspace id>`, then `jj workspace remove <id>`. Strand revisions stay as parents of the merge commit.
- Ship the strands first: one PR per strand from its tip using `/nabu-ship` (`-r <tip>`, target: the merge target). A shared base above the merge target (Launch step 1) ships once, as the shared bottom of their stacks. Merge commit last (`-r`, same target), only once every strand PR is open => a pushed merge commit makes its parents immutable, and `nabu ship` rewrites the revision it ships. A ship step fails -> stop and report, nothing after it ships.
- Add the PR numbers to the wave's `Landed` line in the working copy. The pushed merge commit is immutable => they land with the next merge.
- Offer Launch of the next wave on the merge commit. Never launch it without the user's go.

## Megamerge

Done = Merge's done-state, except: the merge commit also takes the push bookmark and every approved unmerged local head as parents, nothing ships as a PR, and the push bookmarks point at the merge commit, or the revision on top of it, on the remote.

Run Merge with these changes:

- Push bookmarks: the ones the user names (`qa`, `develop`). None named -> ask.
- Merge target: the first push bookmark.
- Candidates: every non-empty head outside it. Show each with id, description, date and workspace, and wait for the user's go. Stale or replaced by later work -> recommend abandoning it.

  ```bash
  # unmerged local work: non-empty heads not yet in the push bookmark
  jj log -r 'heads(mutable() ~ empty() ~ ::<bookmark>)'
  ```

- A candidate that is another workspace's working copy: snapshot it (`jj -R <workspace> st`). Its session still edits it -> leave it out until the session stops (frozen tips, as in Merge).
- Undescribed candidate -> describe it from its diff => jj refuses to push it.
- Parents: the merge target, every finished strand tip, every approved candidate.
- A tablet whose only open boxes are manual checks counts as finished.
- A push bookmark was already pushed onto the merge commit (the user did it) => the commit is immutable: later edits (series, archive) go in one revision on top.
- Ship: no `/nabu-ship`. After the user's go, point every push bookmark at the merge commit, or at that revision on top, and push: `jj bookmark set <bookmark> -r <revision>`, then `jj git push -b <bookmark>`.
- After the push: list the non-empty heads still outside the push bookmark.
