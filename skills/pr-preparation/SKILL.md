---
name: pr-preparation
description: Use when preparing to open a PR upstream, as a final scan of the diff for gaps.
---

# PR Preparation

The human is the gate; you are the radar.

**`<target>` defaults to the upstream branch.** User gave none -> in jj use the revset `trunk()`. Not jj, or trunk unresolved -> ask which ref/change/branch.

Run everything from the repository root. Quote file and line from the diff.

## Phase 0 — OpenWiki (nonblocking)

No `openwiki/` -> skip. Otherwise start it right after `<target>` is known, then continue Phases 1–5 without waiting.

OpenWiki's own headless agent does the update, on OpenWiki's configured provider, not the host model. Run it from the repository root as a background shell command (Claude Code: Bash, `run_in_background: true`). Fill in `<target>` only. Do not paste the diff.

```bash
# use to update the repo wiki from the PR diff
openwiki code --update -p "PR preparation. Changes since <target>: jj diff --git --from '<target>' --to @ (git: git diff <target>...HEAD). Update pages these changes made wrong. Add a page only when a sustained concern fits no existing page. Do not rewrite INSTRUCTIONS.md. Keep the wiki a high-level overview, not implementation details. Nothing warrants a change -> make no edits."
```

It prints its final message on exit. Changed pages = `openwiki/` entries in the working-copy diff. Fold them into the report only if the run finishes before you do.

## Phase 1 — Format and lint autofix

Run first. Fixes change the diff, so the scans must see the fixed code.

1. Find the project's fix commands: `just --list`, then `package.json` scripts (`format`, `lint:fix`) or tool config (`prettier`, `eslint`, `biome`, `ruff`). Ignore `scripts/check.sh`: it checks only, and Phase 5 runs it. No command found -> ask.
2. Record the changed-file list first: run `bash <skill-dir>/scripts/diff-overview.sh <target>` and keep its `CHANGED FILES` block.
3. Run the formatter and the linter in write mode (`--fix` or equivalent). Scope to the recorded files when the tool allows it. Never touch `openwiki/`: Phase 0 may be editing it.
4. Rerun `diff-overview.sh`. A fix touched a file outside the recorded list -> revert that file.
5. A lint error that `--fix` cannot resolve -> fix by hand when obvious and safe, otherwise report as a blocker.

## Phase 2 — Automated scans

```bash
# use as the bundled PR-readiness entrypoint
bash <skill-dir>/scripts/pr-readiness.sh <target>
```

Target = jj change id, commit id, or branch name. Extra exclusions: colon-separated globs, e.g. `DIFF_SCAN_EXCLUDE='**/*.md:docs/**'`.

## Phase 3 — Manual checks

### `.orig` leftovers

`repren` and similar leave `.orig` backups. Never commit them.

```bash
# use to find leftover rename backups
find . -name '*.orig' -not -path './.jj/*' -not -path './.git/*' -not -path './node_modules/*'
```

Any hits -> delete them. **Blocker.**

### Infrastructure parity

Changes touching these must be mirrored across dev and prod, and across each other:

- `docker-compose.dev.yaml` / `docker-compose.prod.yaml` / `docker-compose.yaml`
- `Dockerfile*`
- `.env` files (including examples)
- Deploy pipeline / GitHub Actions

Red flag: a service, volume, port, or env reference in one compose file but not the other.

### DB migrations

Migration files in diff -> follow [migrations.md](migrations.md). Covers review rules and consolidating several local migrations into one (autofix).

### New service dependencies

New infra (queues, caches, object stores, external APIs, databases): grep deploy/config for production provisioning. Flag any new dependency with no corresponding prod configuration.

### OpenSpec

PR implements OpenSpec changes -> `/openspec-archive` for specs whose implementation is fully contained in this PR. Leave partial or unverified changes active. Treat 90%+ checked `tasks.md` boxes as done.

### OpenSpec stack — normalize `stack.md` (jj)

PR is or contains an OpenSpec **stack** (change names like `<stack>-N`, or `openspec/stacks/<stack>/stack.md` in range) -> every slice carries the tip's `stack.md` before upstream. Slice-by-slice edits otherwise leave divergent copies on ancestors. `<tip>` must already hold the final `stack.md`.

```bash
# use to copy the tip's stack.md onto every ancestor slice and verify the hashes
bash <skill-dir>/scripts/normalize-stack-md.sh <repo-root> openspec/stacks/<stack-name>/stack.md <first-slice> <tip>
```

Any `DIFF` line -> rerun.

## Phase 4 — Environment variables

`env-vars.sh` already extracts detected vars as a table. Extend it:

```
| Variable | Used in | Has default? | Required in prod? | In GitHub secrets/vars? |
```

For each var the diff adds to `.env.example`, check the code that reads it for a fallback.

- Sane default in code so the app runs unconfigured: timeouts, limits, log levels, ports, feature toggles, hosts. Dev mode runs with zero config, a DB password default included, and `.env.example` lists each default. Missing defaults = findings to fix in this PR.
- Required, no default: API keys, tokens, and other production secrets; deployment-specific values that vary per environment (`LLM_BASE_URL`) and do not belong in git. `.env.example` lists them empty. Production fails fast without the real value, and a default must never satisfy prod.

These must be added to GitHub repository secrets/variables before merge. The pipeline cannot automate this.

## Phase 5 — Green gate

**Invariant: whenever this skill yields to the user (report or question), format, lint, typecheck, and tests all pass on the current tree.** Phases 1 to 4 edit code (lint fixes, `.orig` removal, migration consolidation, env defaults, OpenSpec archive). Each edit can break a check that passed earlier. So the gate runs last, after the final edit.

Find the commands: prefer `scripts/check.sh` or `just --list`, then `package.json` scripts. No typecheck command -> use the build. Do not hand-roll `npm test`.

Cost rule: format, lint, and typecheck are cheap. Run them in full every time. Tests are expensive. Run the full suite once, then rerun only affected tests.

1. Run format (check mode), lint (check mode), and typecheck. Format or lint fails -> run the autofix, then recheck. Anything else fails -> fix by hand.
2. First pass: run the full test suite.
3. Fix every failure, including failures the diff did not cause. A red tree is never ready.
4. After each fix, rerun steps 1 and a **scoped** test run:
   - Use the runner's related mode (`vitest related`, `jest --findRelatedTests`, `pytest <files>`) on the files edited since the last green test run.
   - No related mode -> run the specs next to the edited files.
   - Run the full suite again only if the edit touched shared config, a lockfile, a migration, or a module many files import.
5. Done when all four checks are green with no edit after the last green run. Any edit at all (even from step 3) restarts at step 4.
6. Phase 0 edits only `openwiki/`. It does not reset the gate.

Cannot reach green after real attempts (flaky test, broken environment, needs a product decision) -> yield with the failing command and output as the **first** line of the message. Record it under Blockers. A question to the user while a check is red must state which check is red. No other red yield.

## Phase 6 — Report

Report only after the gate is green. Fill the `Checks` block from the last green runs.

```
# use as the readiness report
## PR Readiness: <branch>

### Autofixed
- Files changed by format/lint fix, or "none"

### Checks
- format / lint / typecheck: green, or the failing command
- tests: green (full run or scoped to <files>), or the failing command

### Blockers (must fix before merge)
- ...

### Warnings (should fix, reviewer discretion)
- ...

### Env vars to add to GitHub
- VAR_NAME — used in <file>:<line> — <purpose>
- ...

### OpenWiki
- started (background) / skipped (no `openwiki/`) / no-op (no update needed) / completed: <paths or "no changes">

### OK
- Items that passed their check
```
