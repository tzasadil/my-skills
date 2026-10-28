---
name: conduct
description: Use when launching chunks of work as parallel interactive agent sessions, or checking or merging those sessions' work. Not for planning the chunks (see carve), one workspace (see workspace), or subagent batches (see with-implementer).
argument-hint: "[<series or chunk list> | status | merge]"
---

Run chunks of work in parallel: one jj workspace, one herdr workspace, one interactive `claude` session per chunk. Sessions, not subagents => each chunk asks the user its own questions. This session coordinates.

Mode from args: `status` -> Status. `merge` -> Merge. Anything else -> Split, then Launch.

Chunk = id, scope, owned paths, dependencies, base revision. Id doubles as the herdr agent name => lowercase, `[a-z][a-z0-9_-]{0,31}`.

## herdr

- This session must run inside a herdr pane: `test "${HERDR_ENV:-}" = 1`. Fails -> tell the user to start `herdr`, run `claude` in a pane, rerun. Stop.
- Syntax: `herdr <group> --help`. Read IDs from the JSON responses.
- jj workspaces only. Never `herdr worktree` (git worktrees).

## Split

Done = chunk list the user approved, every field set.

- Chunks given (series, issue list, conversation) -> take them. Missing field -> ask.
- No chunks yet -> run /carve, then continue here with its series.

## Launch

Done = one herdr workspace per chunk, its `claude` session working on the chunk brief, user told where to find them.

1. Dependencies: launch a chunk only when the revisions it needs are in its base. Unmet -> name the blocker, skip the chunk.
2. Run /workspace once per chunk (name = id, from = base, including its Bootstrap), then continue here.
3. Fill the brief. Pass inputs only. The chunk's skills and the repo rules load on their own.

   ```markdown
   <!-- chunk brief: fill every <...> -->
   You run chunk <id> of a parallel split: <scope>.
   - Workspace: <absolute workspace path>. Base: <base change id>.
   - You own: <paths>. Shared files and their merge rules: <list>. Depends on: <chunks or none>.
   - Series with the full split: <absolute path, or "none">.
   - The base and other chunks' revisions are read-only. Commit only on top of your base.
   - Run `/nabu-inscribe` on this chunk, then `/nabu-build` its tablet.
   - A change outside your owned paths and shared files -> tell me, do not make it.
   ```

4. Per chunk:

   ```bash
   # herdr workspace in the chunk's jj workspace => pane id at .result.root_pane.pane_id
   herdr workspace create --cwd <workspace-dir> --label <id> --no-focus
   # interactive claude, allowed to read the series outside its workspace (no series -> drop --add-dir)
   herdr agent start <id> --kind claude --pane <pane-id> -- -n <id> --add-dir <series-dir>
   # pastes the multi-line brief as one prompt
   herdr agent prompt <id> "<brief>"
   ```

   `agent start` answers `agent_not_ready` => claude waits on a startup prompt (folder trust for a new workspace). Ask the user to answer it in that herdr workspace, then `herdr agent wait <id>` and send the brief.

5. Tell the user: one herdr workspace per chunk, labelled with its id.

## Status

Done = one row per chunk: revisions on top of its base, last description, session state.

- Revisions: `jj log -r '<base>::<id>@'`.
- Session state: `herdr agent list`. `blocked` => waiting for the user (question or approval). Agent gone => claude exited.
- Need the detail: `herdr agent read <id> --source recent-unwrapped --lines 60`.
- Waiting on one chunk: `herdr agent wait <id> --until blocked`.

## Merge

Done = the wave's chunks in one linear chain on the merge target, in dependency order, conflicts resolved, the repo's full gate green on every finished chunk. Next wave offered, not launched.

- Merge target: the chain from earlier waves. First wave: the series base.
- Chain the whole wave, finished or not. Finished = the user says so.
- Order: dependency order, finished chunks before unfinished => edits in an unfinished chunk never rebase a finished one. Finished chunk tip = the last finished chunk in the chain.
- Session working -> wait until it settles (`herdr agent wait <id>`), then rebase. Rewriting a workspace mid-edit can lose its writes.
- Rebase with `jj rebase -s <chunk root> -o <chain tip>`, then `jj -R <workspace> workspace update-stale`. Tell a live session what moved under it (`herdr agent prompt <id> "<new base, what it brings>"`).
- Conflicts: run /resolve, then continue here. Apply the series' merge rules for shared files.
- Gate red and the cause sits in one chunk -> send it to that chunk's session (`herdr agent prompt <id> "<failure and evidence>"`). Do not fix it here.
- After a chunk lands: tick its checkbox in the series (and its wave's, once every chunk is ticked). Offer `jj workspace remove <id>` and `herdr workspace close <herdr workspace id>`.
- Wave chained -> offer Launch of the next wave on the finished chunk tip. Never launch it without the user's go.
