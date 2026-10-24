#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib.sh
source "$SCRIPT_DIR/lib.sh"

base_ref="$(resolve_base_ref "${1:-}")"

printf 'BASE %s\n\n' "$base_ref"

if [[ ! -f ".env.example" ]]; then
  echo "No .env.example found, skipping stale env check."
  exit 0
fi

vars=()
while IFS='=' read -r key rest || [[ -n "$key" ]]; do
  key="${key#"${key%%[![:space:]]*}"}"
  [[ -z "$key" || "$key" == \#* ]] && continue
  if [[ "$key" =~ ^[A-Z][A-Z0-9_]*$ ]]; then
    vars+=("$key")
  fi
done < .env.example

if [[ ${#vars[@]} -eq 0 ]]; then
  echo "No env vars found in .env.example."
  exit 0
fi

stale=()
for v in "${vars[@]}"; do
  if ! grep -rqP "(process\.env\.$v|import\.meta\.env\.$v|os\.Getenv\(\"$v\"\)|getenv\(\"$v\"\)|\$\{$v(\}|:-))" \
    --exclude='.env.example' \
    --exclude-dir=.git --exclude-dir=.jj --exclude-dir=node_modules \
    --exclude-dir=target --exclude-dir=dist --exclude-dir=build \
    --exclude-dir=.next --exclude-dir=__pycache__ . 2>/dev/null; then
    stale+=("$v")
  fi
done

if [[ ${#stale[@]} -eq 0 ]]; then
  echo "All vars in .env.example are referenced in the codebase."
  exit 0
fi

printf 'Stale entries in .env.example (no references found in code):\n'
for v in "${stale[@]}"; do
  printf '  - %s\n' "$v"
done
