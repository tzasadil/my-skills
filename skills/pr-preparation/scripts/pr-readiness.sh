#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
base_arg="${1:-}"

"$SCRIPT_DIR/diff-overview.sh" "$base_arg"
printf '\n'
"$SCRIPT_DIR/risk-scan.sh" "$base_arg"
printf '\n'
"$SCRIPT_DIR/env-vars.sh" "$base_arg"
printf '\n'
"$SCRIPT_DIR/env-example-stale.sh" "$base_arg"
