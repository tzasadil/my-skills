#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib.sh
source "$SCRIPT_DIR/lib.sh"

base_ref="$(resolve_base_ref "${1:-}")"
current_ref="$(current_ref_label)"

printf 'BASE %s\n' "$base_ref"
printf 'CURRENT %s\n\n' "$current_ref"

diff_stat="$(diff_stat_vs "$base_ref")"
changed_files="$(diff_name_only_vs "$base_ref")"
deleted_files="$(diff_deleted_vs "$base_ref")"

if [[ -z "$diff_stat" && -z "$changed_files" && -z "$deleted_files" ]]; then
  echo "No changes detected against $base_ref."
  exit 0
fi

printf '=== DIFF STAT ===\n%s\n' "$diff_stat"

printf '\n=== CHANGED FILES ===\n%s\n' "$changed_files"

printf '\n=== DELETED FILES ===\n%s\n' "$deleted_files"
