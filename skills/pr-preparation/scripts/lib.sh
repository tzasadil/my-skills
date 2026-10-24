#!/usr/bin/env bash

set -euo pipefail

# Prefer jj when both exist (colocated checkouts).
detect_vcs() {
  if jj root >/dev/null 2>&1; then
    printf 'jj\n'
  elif git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    printf 'git\n'
  else
    echo "error: not inside a jj or git repository" >&2
    exit 1
  fi
}

resolve_base_ref() {
  local vcs
  vcs="$(detect_vcs)"

  if [[ $# -eq 0 || -z ${1:-} ]]; then
    if [[ "$vcs" == jj ]]; then
      # Default upstream branch. The revset needs no bookmark lookup.
      printf 'trunk()\n'
      return 0
    fi
    echo "error: no base ref provided; pass a branch or commit explicitly" >&2
    echo "usage: $0 <base-ref>" >&2
    exit 1
  fi

  local arg="$1"

  if [[ "$vcs" == jj ]]; then
    if jj log --no-graph -r "$arg" --no-pager --limit 1 >/dev/null 2>&1; then
      printf '%s\n' "$arg"
      return 0
    fi
    if jj log --no-graph -r "remote_branches(exact:\"origin/$arg\")" --no-pager --limit 1 >/dev/null 2>&1; then
      printf '%s\n' "$(jj log --no-graph -r "remote_branches(exact:\"origin/$arg\")" --no-pager -T 'change_id.shortest()' 2>/dev/null)"
      return 0
    fi
    if jj log --no-graph -r "bookmarks(exact:\"$arg\")" --no-pager --limit 1 >/dev/null 2>&1; then
      printf '%s\n' "$(jj log --no-graph -r "bookmarks(exact:\"$arg\")" --no-pager -T 'change_id.shortest()' 2>/dev/null)"
      return 0
    fi
    echo "error: could not resolve base ref '$arg' (jj)" >&2
    exit 1
  fi

  if git rev-parse --verify --quiet "$arg^{commit}" >/dev/null 2>&1; then
    printf '%s\n' "$arg"
    return 0
  fi
  if git rev-parse --verify --quiet "origin/$arg^{commit}" >/dev/null 2>&1; then
    printf 'origin/%s\n' "$arg"
    return 0
  fi
  echo "error: could not resolve base ref '$arg' (git)" >&2
  exit 1
}

# Default path noise excluded from PR scans (tracked but high-churn).
# Override / extend with DIFF_SCAN_EXCLUDE (colon-separated). PR_PREP_EXCLUDE still accepted.
diff_scan_default_exclude_patterns() {
  printf '%s\n' \
    'openspec/**' \
    '**/pnpm-lock.yaml'
}

diff_scan_exclude_patterns() {
  diff_scan_default_exclude_patterns
  if [[ -n ${DIFF_SCAN_EXCLUDE:-}${PR_PREP_EXCLUDE:-} ]]; then
    local IFS=':'
    local -a extra
    read -r -a extra <<<"${DIFF_SCAN_EXCLUDE:-${PR_PREP_EXCLUDE:-}}"
    local pat
    for pat in "${extra[@]}"; do
      [[ -z "$pat" ]] && continue
      printf '%s\n' "$pat"
    done
  fi
}

diff_scan_jj_fileset() {
  local -a pats=()
  local pat
  while IFS= read -r pat; do
    [[ -z "$pat" ]] && continue
    pats+=("$pat")
  done < <(diff_scan_exclude_patterns)

  if [[ ${#pats[@]} -eq 0 ]]; then
    printf 'all()\n'
    return 0
  fi

  local union="${pats[0]}"
  local i
  for ((i = 1; i < ${#pats[@]}; i++)); do
    union+=" | ${pats[i]}"
  done

  printf '~(%s)\n' "$union"
}

diff_scan_git_pathspecs() {
  printf '%s\n' '.'
  local pat
  while IFS= read -r pat; do
    [[ -z "$pat" ]] && continue
    printf ':(exclude,glob)%s\n' "$pat"
  done < <(diff_scan_exclude_patterns)
}

current_ref_label() {
  local vcs
  vcs="$(detect_vcs)"
  if [[ "$vcs" == jj ]]; then
    jj log --no-graph -r 'present(@)' --no-pager -T 'change_id.shortest()' 2>/dev/null
  else
    printf 'HEAD\n'
  fi
}

# Unified overview helpers used by diff-overview.sh
diff_stat_vs() {
  local base_ref="$1"
  local vcs
  vcs="$(detect_vcs)"
  if [[ "$vcs" == jj ]]; then
    local fileset current
    fileset="$(diff_scan_jj_fileset)"
    current="$(current_ref_label)"
    jj diff --git --from "$base_ref" --to "$current" --stat -- "$fileset" 2>/dev/null || true
  else
    local -a pathspecs=()
    local ps
    while IFS= read -r ps; do
      [[ -z "$ps" ]] && continue
      pathspecs+=("$ps")
    done < <(diff_scan_git_pathspecs)
    git diff --stat "${base_ref}...HEAD" -- "${pathspecs[@]}" 2>/dev/null || true
  fi
}

diff_name_only_vs() {
  local base_ref="$1"
  local vcs
  vcs="$(detect_vcs)"
  if [[ "$vcs" == jj ]]; then
    local fileset current
    fileset="$(diff_scan_jj_fileset)"
    current="$(current_ref_label)"
    jj diff --from "$base_ref" --to "$current" --name-only -- "$fileset" 2>/dev/null || true
  else
    local -a pathspecs=()
    local ps
    while IFS= read -r ps; do
      [[ -z "$ps" ]] && continue
      pathspecs+=("$ps")
    done < <(diff_scan_git_pathspecs)
    git diff --name-only "${base_ref}...HEAD" -- "${pathspecs[@]}" 2>/dev/null || true
  fi
}

diff_deleted_vs() {
  local base_ref="$1"
  local vcs
  vcs="$(detect_vcs)"
  if [[ "$vcs" == jj ]]; then
    local fileset current
    fileset="$(diff_scan_jj_fileset)"
    current="$(current_ref_label)"
    jj diff --from "$base_ref" --to "$current" --summary -- "$fileset" 2>/dev/null | grep '^D' | awk '{print $2}' || true
  else
    local -a pathspecs=()
    local ps
    while IFS= read -r ps; do
      [[ -z "$ps" ]] && continue
      pathspecs+=("$ps")
    done < <(diff_scan_git_pathspecs)
    git diff --diff-filter=D --name-only "${base_ref}...HEAD" -- "${pathspecs[@]}" 2>/dev/null || true
  fi
}

# Emits compact added-line stream (path once per file, not per line):
#   path
#   line<TAB>content
# Why: repeating path:line on every row balloons tokens/agent context.
#
# Usage: list_added_lines <base-ref> [--include-tests|--exclude-tests]
# Tests default OFF. INCLUDE_TESTS=1 also opts in; explicit flags win over env.
list_added_lines() {
  local base_ref=""
  local include_tests=0
  if [[ "${INCLUDE_TESTS:-0}" == "1" ]]; then
    include_tests=1
  fi

  local arg
  for arg in "$@"; do
    case "$arg" in
      --include-tests) include_tests=1 ;;
      --exclude-tests) include_tests=0 ;;
      -*)
        echo "error: unknown argument to list_added_lines: $arg (want --include-tests|--exclude-tests)" >&2
        return 1
        ;;
      *)
        if [[ -n "$base_ref" ]]; then
          echo "error: unexpected argument to list_added_lines: $arg" >&2
          return 1
        fi
        base_ref="$arg"
        ;;
    esac
  done

  if [[ -z "$base_ref" ]]; then
    echo "error: list_added_lines requires a base ref" >&2
    return 1
  fi

  local vcs
  vcs="$(detect_vcs)"

  if [[ "$vcs" == jj ]]; then
    local current fileset
    current="$(current_ref_label)"
    fileset="$(diff_scan_jj_fileset)"
    jj diff --git --from "$base_ref" --to "$current" -- "$fileset" \
      | parse_added_lines_from_diff "$include_tests"
  else
    local -a pathspecs=()
    local ps
    while IFS= read -r ps; do
      [[ -z "$ps" ]] && continue
      pathspecs+=("$ps")
    done < <(diff_scan_git_pathspecs)
    git diff --ignore-all-space "${base_ref}...HEAD" -- "${pathspecs[@]}" \
      | parse_added_lines_from_diff "$include_tests"
  fi
}

# $1: 1 = emit test paths, 0 = skip *.test.*/ *.spec.*/ __tests__/
parse_added_lines_from_diff() {
  local include_tests="${1:-0}"
  awk -v include_tests="$include_tests" '
    function is_test_path(f) {
      return f ~ /\.(test|spec)\.(ts|tsx|js|jsx|mjs|cjs|mts|cts)$/ || index(f, "/__tests__/") > 0
    }

    BEGIN {
      file = ""
      line = 0
      need_header = 0
      skip = 0
    }

    /^\+\+\+ b\// {
      file = substr($0, 7)
      skip = (include_tests == 0 && is_test_path(file))
      need_header = (skip == 0)
      next
    }

    /^@@ / {
      if (match($0, /\+([0-9]+)/)) {
        line = substr($0, RSTART + 1, RLENGTH - 1) + 0
      }
      next
    }

    /^\+/ && $0 !~ /^\+\+\+/ {
      if (!skip) {
        if (need_header) {
          printf "%s\n", file
          need_header = 0
        }
        printf "%d\t%s\n", line, substr($0, 2)
      }
      line += 1
      next
    }

    /^-/ {
      next
    }

    {
      line += 1
    }
  '
}
