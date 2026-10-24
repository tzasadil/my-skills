---
name: workspace
description: Use when the user asks to create a jj workspace.
argument-hint: "<workspace-name> [from <base-rev-or-bookmark>] <feature-description>"
---

# Jujutsu Workspaces

Required background: jj. See the version-control section of your global agent rules.

User args: `<feature-description> <from <base-rev>]`. Name: if based on github issue, then use number+title as name (can be shortened), else invent name from feature description. Missing `from` -> start from the upstream branch: `-r 'trunk()'`.

`jj workspace` = multiple working directories, one repo. Each workspace has its own `.jj/` linked to the shared commit store and can check out a different commit. Separate filesystem trees. Shared commit graph: a change in one is immediately visible to others.

## Create

First, before anything else: `jj git fetch`. Stale remote bookmarks => `trunk()` and `<base-rev>` resolve to old commits => the workspace starts behind upstream.

`jj workspace add -r <parent> -m "<msg>"` creates a fresh empty commit on top of `<parent>` for the workspace. Never omit `-r`: without it the workspace shares the default workspace's parent and the trees tangle.

If a GitHub issue number is already known (URL or message), include it in the name: `1234-fix-login`. Do not hunt for one.

```bash
# use to add a sibling workspace on a fresh empty commit
jj workspace add --name my-task -r <parent_rev_or_bookmark> -m "<my-task>" ../my-task
```

Directory basename MUST equal `--name`. Sibling of the main repo, not nested. Target directory must not exist; jj creates it.

- Good: `../my-task`, `../1234-fix-login`
- Bad: `../my-app-my-task`, `../my-task-work`, `../workspace/my-task`

## Git colocation

`jj workspace add` also creates a Git worktree when the current workspace is colocated and `git.colocate` is `true` (the default). Then IDE Git tooling works in the workspace. Still use jj, never git.

- Force: `--colocate`. Skip: `--no-colocate`.
- Inspect or toggle later, inside the workspace: `jj git colocation status|enable|disable`.
- `jj workspace remove` and `forget` also remove the Git worktree.
- Containers: the workspace `.git` file holds a relative path into the main repo's `.git`. Mounting only the workspace => `fatal: not a git repository`. Mount the shared parent directory, or use `--no-colocate`.

## Commands

- List: `jj --no-pager workspace list`
- Root: `jj workspace root` or `jj workspace root --name foo`
- Advance: `jj edit <revision>` or `jj new -r <revision>`. `jj edit` is simpler than `jj rebase -d` + `jj workspace update-stale` when catching up to HEAD.
- Stale (another workspace rewrote the checked-out commit, interrupted jj, or `jj op abandon`): `jj workspace update-stale`. Lost operation -> recovery commit from working-copy contents.
- Remove: `jj workspace remove foo`. Deletes the directory. Snapshots the working copy into a commit first, so work stays recoverable. Cannot remove the default workspace.
- Forget (keep files on disk): `jj workspace forget foo`

If the workspace is a project root: `cd` into it. If not: `jj -R <absolute-path>` from the main workspace.

## Root-owned files

Docker bind mounts create root-owned files (e.g. `/workspace`) => `Permission denied` from jj snapshot, `jj workspace remove`, rsync, or builds. Workspace under `/data/src`:

```bash
# use to chown root-owned files in a workspace back to the user
sudo -n /usr/local/bin/reclaim-src /absolute/path/to/workspace
```

`a password is required` or `command not found` -> not installed. Ask the user to run `sudo <path-to-skill>/scripts/reclaim-src --install` once. Details: `--help`.

## Agent tooling

The terminal `cd` parameter is gated to registered project roots. A sibling workspace is not a project root. Do not `cd` into it unless it is registered.

From the **main project root**, any jj command via `jj -R <absolute-workspace-path>`:

```bash
# use to run jj against a sibling workspace
jj -R /absolute/path/to/workspace st
jj -R /absolute/path/to/workspace rebase -d <target>
jj -R /absolute/path/to/workspace workspace update-stale
```

Read/write with file tools and absolute paths. Unlike `cd`, file tools work as long as the directory exists on disk.

Non-jj commands (builds, tests, lint): `cd` stays at the main project root; pass the workspace path explicitly:

```bash
# use to run a workspace command without cd'ing into a non-root
cd /path/to/main/repo && pnpm --dir /absolute/path/to/workspace/web test
(cd /absolute/path/to/workspace && pnpm test)
```

Preferred for active development: add the workspace as an additional project root so `cd` and relative paths work.

## Bootstrap

New workspace has no runtime dependencies. Bootstrap from the main repo.

**Docker volumes.** Workspace has no `deployment/_data/`. Copy the main repo's through a throwaway container:

- Container-owned data (e.g. Postgres uid 999, mode `700`) is unreadable to the user. Never chown it => the main stack's DB crashes or refuses to start.
- `cp -a` as container root keeps uids => the workspace stack starts as-is. Isolated copy => parallel stacks never share one DB dir.
- Main stack stopped => consistent DB copy.
- `label=disable` => SELinux allows the mounts without relabeling the main repo's data. Absolute paths => `-v` never reads them as named volumes.

```bash
# use to copy main-repo docker data into the workspace, keeping container uids
mkdir -p /abs/workspace/deployment/_data
docker run --rm --security-opt label=disable \
  -v /abs/main-repo/deployment/_data:/src:ro \
  -v /abs/workspace/deployment/_data:/dst \
  alpine cp -a /src/. /dst/
```

The copy stays container-owned => `jj workspace remove` cannot delete it. Empty it first:

```bash
# use to empty the workspace docker data before jj workspace remove
docker run --rm --security-opt label=disable \
  -v /abs/workspace/deployment/_data:/d \
  alpine find /d -mindepth 1 -delete
```

**`.env`.** Gitignored; not copied. List them, then `cp` each to the same relative path:

```bash
# use to list every non-example .env file in the main repo
cd ../<main-repo> && fd -HI -t f --max-depth 5 '^\.env' -E node_modules -E '*.example'
```

**Dependencies.** pnpm store needs `rsync`; plain `cp` chokes on symlinks:

```bash
# use to copy node_modules trees into the workspace
# -E 'node_modules/*/' skips the nested pnpm store; -R keeps the relative path under the workspace
cd ../<main-repo> && fd -HI -t d --max-depth 5 '^node_modules$' -E 'node_modules/*/' -E _data -x rsync -aR {} ../<workspace-name>/
```

Local `node_modules` => lint, typecheck, IDE work immediately. Docker still installs inside containers.

**MCP:**

```bash
# use to index the new workspace for codegraph
cd /absolute/path/to/workspace && \
codegraph init
```

## GitHub

User provides a GitHub issue URL:

1. `gh` fetch the issue **and its sub-issues**. Always include comments.
2. Create a workspace.
3. Run `openspec-propose` there.

```bash
# use to pull an issue with comments and sub-issues (--comments and --json cannot combine)
gh issue view <n> --json title,body,number,url,comments,subIssues
```

Then `gh issue view` each sub-issue the same way.

**Tracker with bug sub-issues:** after artifacts are ready and before the refine pass, one entry per sub-issue:

- **Problem** — what that GitHub issue reported (symptoms, expected vs actual)
- **Cause** — root cause found while proposing (grounded in code)
- **Fix** — how the proposed OpenSpec change will fix it (point at blueprint/tasks)

Do not skip this wrap-up when sub-issues exist. Do not collapse several bugs into one vague row. Out of scope of this propose -> say so under **Fix**.
