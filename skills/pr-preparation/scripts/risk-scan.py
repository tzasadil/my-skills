#!/usr/bin/env python3
"""Scan added diff lines for common PR risk patterns.

Reads compact added-line stream from stdin (see list_added_lines):
  path
  line\\tcontent
Same shape as openspec-verify scan-utility-handrolls.py. First matching category wins.
"""

from __future__ import annotations

import re
import sys

found = False


def emit(category: str, location: str, content: str) -> None:
    global found
    print(f"[{category}] {location} {content}")
    found = True


def main() -> int:
    global found
    current_file = ""
    for raw in sys.stdin:
        line = raw.rstrip("\n")
        # Path headers have no tab; content rows are "lineno\\tcontent".
        if "\t" not in line:
            current_file = line
            continue
        if not current_file:
            continue
        lineno, content = line.split("\t", 1)
        location = f"{current_file}:{lineno}"

        if re.search(
            r"(process\.env\.[A-Z][A-Z0-9_]*|import\.meta\.env\.[A-Z][A-Z0-9_]*)",
            content,
        ):
            emit("env-usage", location, content)
            continue

        if re.search(
            r"(password|secret|token|api[_-]?key)\s*[:=]\s*[\"'`][^\"'`]+[\"'`]",
            content,
            re.I,
        ) or re.search(r"https?://[^/\s]+:[^@\s]+@", content):
            emit("secret-like", location, content)
            continue

        if re.search(r"(localhost|127\.0\.0\.1|0\.0\.0\.0)", content):
            emit("local-address", location, content)
            continue

        if re.search(
            r"(console\.log|print\(|fmt\.Println|var_dump\(|dump\(|"
            r"logger\.(debug|trace)\(|log\.(debug|trace)\()",
            content,
        ):
            emit("debug-leftover", location, content)
            continue

        if re.search(
            r"(^\s*(#|//|/\*|\*|<!--)\s*(TODO|FIXME|HACK)\b)|"
            r"((//|/\*|\*|<!--).*(TODO|FIXME|HACK)\b)",
            content,
        ):
            emit("todo-comment", location, content)
            continue

        if re.search(r"import\s*\(", content):
            emit("dynamic-import", location, content)
            continue

        if re.search(
            r"^\s*(//|/\*|\*|#)\s*"
            r"(if |for |while |return |const |let |var |function |class |"
            r"import |export |def |async )",
            content,
        ):
            emit("commented-code", location, content)
            continue

        if re.search(r"(catch|except|rescue)\s*[({]?$", content):
            emit("empty-catch", location, content)
            continue

        if re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", content) and not re.search(
            r"(localhost|127\.0\.0\.1|0\.0\.0\.0)", content
        ):
            emit("hardcoded-ip", location, content)
            continue

        if re.search(
            r"(xdescribe|xit|\.skip\(|\.only\(|@Disabled|@Ignore|"
            r"pytest\.mark\.skip|unittest\.skip)",
            content,
        ):
            emit("skipped-test", location, content)
            continue

        if re.search(
            r"(eval\(|exec\(|new Function\(|subprocess\.call|os\.system\(|__import__)",
            content,
        ):
            emit("dangerous-exec", location, content)
            continue

        if re.search(r"(import \*|from .+ import \*|using namespace std)", content):
            emit("wildcard-import", location, content)
            continue

    if not found:
        print("No matching risky added lines found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
