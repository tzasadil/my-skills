#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib.sh
source "$SCRIPT_DIR/lib.sh"

base_ref="$(resolve_base_ref "${1:-}")"

printf 'BASE %s\n\n' "$base_ref"

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

# Default excludes tests (mock env noise). Compact stream: path header, then line<TAB>content.
current_file=""
while IFS= read -r raw; do
  if [[ "$raw" != *$'\t'* ]]; then
    current_file="$raw"
    continue
  fi
  [[ -z "$current_file" ]] && continue
  lineno="${raw%%$'\t'*}"
  content="${raw#*$'\t'}"
  location="${current_file}:${lineno}"
  rest="$content"

  while [[ $rest =~ process\.env\.([A-Z][A-Z0-9_]*) ]]; do
    printf '%s\t%s\n' "${BASH_REMATCH[1]}" "$location" >>"$tmp_file"
    rest=${rest#*"${BASH_REMATCH[0]}"}
  done

  rest="$content"
  while [[ $rest =~ import\.meta\.env\.([A-Z][A-Z0-9_]*) ]]; do
    printf '%s\t%s\n' "${BASH_REMATCH[1]}" "$location" >>"$tmp_file"
    rest=${rest#*"${BASH_REMATCH[0]}"}
  done

  rest="$content"
  while [[ $rest =~ os\.Getenv\(\"([A-Z][A-Z0-9_]*)\"\) ]]; do
    printf '%s\t%s\n' "${BASH_REMATCH[1]}" "$location" >>"$tmp_file"
    rest=${rest#*"${BASH_REMATCH[0]}"}
  done

  rest="$content"
  while [[ $rest =~ getenv\(\"([A-Z][A-Z0-9_]*)\"\) ]]; do
    printf '%s\t%s\n' "${BASH_REMATCH[1]}" "$location" >>"$tmp_file"
    rest=${rest#*"${BASH_REMATCH[0]}"}
  done

  rest="$content"
  while [[ $rest =~ \$\{([A-Z][A-Z0-9_]*)(:-[^}]*)?\} ]]; do
    printf '%s\t%s\n' "${BASH_REMATCH[1]}" "$location" >>"$tmp_file"
    rest=${rest#*"${BASH_REMATCH[0]}"}
  done
done < <(list_added_lines "$base_ref")

if [[ ! -s "$tmp_file" ]]; then
  echo 'No env vars detected in added diff lines.'
  exit 0
fi

printf '| Variable | Used in |\n'
printf '| --- | --- |\n'
sort -u "$tmp_file" | while IFS=$'\t' read -r variable location; do
  printf '| %s | %s |\n' "$variable" "$location"
done
