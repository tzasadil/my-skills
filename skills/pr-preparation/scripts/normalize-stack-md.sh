#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: normalize-stack-md.sh <repo> <stack-md> <first-slice> <tip>

Force TIP's OpenSpec stack.md onto every slice from FIRST-SLICE to TIP (jj), then verify.
Run from the repository root.

  repo         worktree or repo root for `jj -R` (`.` for the main checkout)
  stack-md     e.g. openspec/stacks/<stack-name>/stack.md
  first-slice  change id of the revision that introduced stack.md (slice 1 / stack root)
  tip          change id holding the final stack.md (often the last slice, not always @)

Prints `ok <rev>` or `DIFF <rev>` per slice. Exit 1 when any slice still differs.
EOF
}

case "${1:-}" in -h | --help) usage; exit 0 ;; esac
if [[ $# -ne 4 ]]; then
  usage >&2
  exit 2
fi
repo=$1 stack_md=$2 first=$3 tip=$4

# Hash of stack.md at a revision. Fails when the file is missing there.
hash_at() {
  jj -R "$repo" file show -r "$1" -- "$stack_md" 2>/dev/null | sha256sum
}

if ! want=$(hash_at "$tip"); then
  echo "error: '$stack_md' not found at tip '$tip'. Pass the path from the repo root and the change that holds the final stack.md." >&2
  exit 1
fi

# One `restore --into <first> --restore-descendants` keeps each descendant's own content,
# so restore from TIP into every ancestor, newest first (jj log order).
jj -R "$repo" log -r "${first}::${tip}-" --no-graph -T 'change_id ++ "\n"' |
  xargs -r -I{} jj -R "$repo" restore --from "$tip" --into {} --restore-descendants -- "$stack_md"

status=0
while IFS= read -r rev; do
  if got=$(hash_at "$rev") && [[ $got == "$want" ]]; then
    printf 'ok   %s\n' "$rev"
  else
    printf 'DIFF %s\n' "$rev"
    status=1
  fi
done < <(jj -R "$repo" log -r "${first}::${tip}" --no-graph -T 'change_id ++ "\n"')
exit "$status"
