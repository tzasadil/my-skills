#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib.sh
source "$SCRIPT_DIR/lib.sh"

base_ref="$(resolve_base_ref "${1:-}")"

printf 'BASE %s\n\n' "$base_ref"

# Include tests: skipped-test / .only / fixture secrets live there.
# Pattern rules live in risk-scan.py (shared shape with openspec-verify scanners).
list_added_lines "$base_ref" --include-tests | python3 "$SCRIPT_DIR/risk-scan.py"
