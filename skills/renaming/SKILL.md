---
name: renaming
description: Use when renaming identifiers across multiple files. Use only when more than 3 occurances.
allowed-tools: Bash(repren:*), Bash(uvx repren@latest:*), Read, Write
---
# Renaming

Use repren when > 3 occurances, otherwise skip this workflow and manually edit the files.

Repren rewrites contents and renames matching files/directories in one pass, atomically, with `.orig` backups.

```bash
# Preview. Always. `--full` keeps contents and paths in lockstep; `--word-breaks` is identifier boundaries.
uvx repren@latest --from='old_name' --to='new_name' --word-breaks --full --dry-run PATH

# Apply once the preview is the intended set.
uvx repren@latest --from='old_name' --to='new_name' --word-breaks --full PATH

# Roll back. Same pattern flags as the run.
uvx repren@latest --undo --from='old_name' --to='new_name' --word-breaks --full PATH

# Keep the change: delete the `.orig` backups.
uvx repren@latest --clean-backups PATH
```

- Add `--preserve-case` to rename `my_var`, `myVar`, `MyVar`, and `MY_VAR` together.
- Scope `PATH` to the rename tree; repren does not honor `.gitignore`.
- One-file edit: use the Edit tool instead.
- Anything beyond this flow: `uvx repren@latest --docs`.
