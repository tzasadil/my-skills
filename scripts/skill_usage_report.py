#!/usr/bin/env python3
"""Report skill invocations from the local OpenCode session database.

Why: skills get edited far more than they get used. A skill with zero loads
across months is either undiscoverable or dead weight.

Set OPENCODE_DB to point at another database.
"""
import collections
import datetime
import json
import os
import pathlib
import sqlite3
import sys

DB = os.environ.get("OPENCODE_DB") or os.path.expanduser(
    "~/.local/share/opencode/opencode.db"
)
SKILLS_DIR = pathlib.Path(__file__).resolve().parent.parent / "skills"


def main():
    if not os.path.exists(DB):
        print(f"no OpenCode database at {DB}; set OPENCODE_DB to point at one")
        return 1
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        rows = con.execute(
            """
            SELECT COALESCE(json_extract(c.value,'$.state.input.name'),
                            json_extract(c.value,'$.state.input.id')) skill,
                   m.time_created
            FROM session_message m, json_each(json_extract(m.data,'$.content')) c
            WHERE json_extract(c.value,'$.type')='tool'
              AND json_extract(c.value,'$.name')='skill'
            """
        ).fetchall()
    except sqlite3.Error as exc:
        print(f"cannot read skill invocations: {exc}")
        return 1

    counts = collections.Counter()
    last = {}
    for skill, ts in rows:
        if not skill:
            continue
        counts[skill] += 1
        day = datetime.datetime.fromtimestamp(
            ts / 1000, datetime.timezone.utc
        ).strftime("%Y-%m-%d")
        last[skill] = max(last.get(skill, ""), day)

    shipped = sorted(p.parent.name for p in SKILLS_DIR.glob("*/SKILL.md"))
    print(f"{'skill':44} {'loads':>6}  last")
    for skill, n in counts.most_common():
        print(f"{skill:44} {n:>6}  {last[skill]}")

    dead = [s for s in shipped if s not in counts]
    print(f"\n{len(dead)}/{len(shipped)} shipped skills never loaded:")
    for s in dead:
        print(f"  {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
