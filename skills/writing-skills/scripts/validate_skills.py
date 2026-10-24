#!/usr/bin/env python3
"""Validate SKILL.md files against the mechanical rules in the writing-skills skill.

Judgment calls (tone, scope, wording) stay with the author. This script only
catches what a machine can see reliably:

errors
  - missing or unparseable YAML frontmatter
  - missing `name` or `description`
  - `name` or `description` present but not a string
  - `name` not hyphen-case, longer than 64 chars, or not matching its folder
  - two skills sharing a name
  - `description` longer than 1024 chars or containing `<` / `>`
warnings
  - a `name` with more than 3 hyphen-separated words
  - a model-invoked description not starting with "Use when"
  - unknown frontmatter keys
  - relative Markdown links that point at missing files (skill bodies and README.md)

The checks exist because agents and parsers fail on these, not because of style.

usage:
    validate_skills.py [skills-root ...] [--strict]

Needs PyYAML. A hand-rolled line parser accepts frontmatter that real YAML
parsers reject (an unquoted colon inside a description, for example), and a
harness silently drops skills whose frontmatter does not parse. Run via
`just check` from the skills repo root, or directly with
    uv run --no-project --with pyyaml python validate_skills.py ...

Defaults to the skills directory three levels above this script
(<root>/writing-skills/scripts/validate_skills.py). `--strict` makes warnings
fail too; use it in CI after the warnings are cleaned up.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_NAME_WORDS = 3

# Frontmatter keys seen across agent harnesses. Anything else is a warning:
# harmless locally, but it usually means a typo or a key no agent reads.
ALLOWED_KEYS = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
    "disable-model-invocation",
    "argument-hint",
    "targets",
    "version",
    "compatibility",
}

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# Captures the target only: stops at the first space so `[a](b "title")` yields `b`.
LINK_RE = re.compile(r"\]\(([^)\s]+)[^)]*\)")
URL_PREFIXES = ("http://", "https://", "mailto:", "/", "#")


def parse_frontmatter(text: str) -> tuple[dict[str, object], str | None]:
    """Extract top-level frontmatter keys from a SKILL.md.

    Uses a real YAML parser so the script rejects the same frontmatter the
    harness does. Hand-rolled line parsing accepts values that YAML rejects,
    and a skill with invalid frontmatter is dropped without a warning.

    Args:
        text: Full SKILL.md contents.

    Returns:
        (values, None) on success, or ({}, error message) when the frontmatter
        is missing, not closed, or not valid YAML.
    """
    if not text.startswith("---"):
        return {}, "no YAML frontmatter"

    end = text.find("\n---", 3)
    if end == -1:
        return {}, "frontmatter is not closed with ---"

    try:
        values = yaml.safe_load(text[3:end])
    except yaml.YAMLError as error:
        return {}, f"frontmatter is not valid YAML:\n{error}"
    if values is None:
        return {}, "frontmatter is empty"
    if not isinstance(values, dict):
        return {}, "frontmatter is not a mapping"
    return values, None


def check_links(skill_dir: Path, body: str) -> list[str]:
    """Return warnings for relative Markdown links whose target file is gone.

    Stale pointers are worse than no pointer: the agent follows the link and
    wastes a read on a missing file. Fenced code blocks and inline code are
    removed first so sample output that looks like a link is not mistaken for
    one.

    Args:
        skill_dir: Directory containing the SKILL.md.
        body: SKILL.md contents after the frontmatter.

    Returns:
        Warning messages, empty when every relative link resolves.
    """
    return [
        f"link target not found: {target}"
        for target in missing_relative_links(skill_dir, body)
    ]


def missing_relative_links(base_dir: Path, markdown: str) -> list[str]:
    """Return relative link targets in `markdown` that do not exist under `base_dir`.

    Shared by skill bodies and the README so both skip URLs, anchors, and code
    spans the same way.
    """
    prose = re.sub(r"```.*?```", "", markdown, flags=re.DOTALL)
    prose = re.sub(r"`[^`\n]*`", "", prose)
    missing: list[str] = []
    for target in LINK_RE.findall(prose):
        target = urllib.parse.unquote(target.split("#", 1)[0].strip())
        if not target or target.startswith(URL_PREFIXES):
            continue
        if not (base_dir / target).resolve().exists():
            missing.append(target)
    return missing


def validate_skill(skill_dir: Path) -> tuple[str, list[str], list[str]]:
    """Run every check against one skill directory.

    Args:
        skill_dir: Directory expected to contain a SKILL.md.

    Returns:
        (name, errors, warnings). Name is empty when the frontmatter is broken.
    """
    errors: list[str] = []
    warnings: list[str] = []

    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    front, error = parse_frontmatter(text)
    name = ""
    if error:
        errors.append(error)
    else:
        unknown = sorted(set(front) - ALLOWED_KEYS)
        if unknown:
            warnings.append("unknown frontmatter key(s): " + ", ".join(unknown))

        name = front.get("name", "")
        if not name:
            errors.append("missing 'name'")
        elif not isinstance(name, str):
            errors.append(f"'name' is not a string: {name!r}")
        else:
            if not NAME_RE.match(name):
                errors.append(f"name '{name}' is not hyphen-case")
            elif len(name) > MAX_NAME_LENGTH:
                errors.append(f"name is {len(name)} chars, max {MAX_NAME_LENGTH}")
            if len(name.split("-")) > MAX_NAME_WORDS:
                warnings.append(f"name has more than {MAX_NAME_WORDS} words")
            if name != skill_dir.name:
                errors.append(f"name '{name}' does not match folder '{skill_dir.name}'")

        description = front.get("description", "")
        if not description:
            errors.append("missing 'description'")
        elif not isinstance(description, str):
            errors.append(f"'description' is not a string: {description!r}")
        else:
            if len(description) > MAX_DESCRIPTION_LENGTH:
                errors.append(
                    f"description is {len(description)} chars, max {MAX_DESCRIPTION_LENGTH}"
                )
            if "<" in description or ">" in description:
                errors.append("description contains angle brackets")
            flag = front.get("disable-model-invocation", "")
            user_invoked = flag is True or str(flag).lower() in {"true", "yes", "1"}
            if not user_invoked and not description.startswith("Use when"):
                warnings.append(
                    "model-invoked description does not start with 'Use when'"
                )

    body = text.split("\n---", 1)[-1]
    warnings.extend(check_links(skill_dir, body))

    return name, errors, warnings


def check_readme_links(wiki_root: Path) -> list[str]:
    """Warn about relative Markdown links in README.md that point at missing files.

    Why: the README is the skills index, and deleted skill folders leave dangling
    rows that no harness error surfaces.
    """
    readme = wiki_root / "README.md"
    if not readme.is_file():
        return []
    return [
        f"README link points at a missing file: {target}"
        for target in missing_relative_links(
            readme.parent, readme.read_text(encoding="utf-8")
        )
    ]


def main() -> int:
    """Validate every skill under the given roots.

    Returns:
        Process exit code: 1 when errors exist, or when warnings exist and
        --strict is set.
    """
    parser = argparse.ArgumentParser(
        description="Validate SKILL.md frontmatter, naming, and links.",
        epilog="Default root: the skills directory above this script.",
    )
    parser.add_argument("roots", nargs="*", type=Path, help="skills directories")
    parser.add_argument("--strict", action="store_true", help="fail on warnings too")
    args = parser.parse_args()

    if yaml is None:
        print(
            "ERROR: PyYAML is required. Run `just check`, or "
            "`uv run --no-project --with pyyaml python validate_skills.py`.",
            file=sys.stderr,
        )
        return 1

    roots = args.roots or [Path(__file__).resolve().parents[2]]

    skills = [
        skill_dir
        for root in roots
        if root.is_dir()
        for skill_dir in sorted(root.iterdir())
        if (skill_dir / "SKILL.md").is_file()
    ]
    if not skills:
        print(f"no SKILL.md files found under: {', '.join(str(r) for r in roots)}")
        return 1

    error_count = 0
    warning_count = 0
    seen: dict[str, Path] = {}

    for skill_dir in skills:
        name, errors, warnings = validate_skill(skill_dir)

        if name and name in seen:
            errors.append(f"name '{name}' already used by {seen[name]}")
        elif name:
            seen[name] = skill_dir

        for message in errors:
            print(f"ERROR {skill_dir.name}: {message}")
        for message in warnings:
            print(f"WARN  {skill_dir.name}: {message}")
        error_count += len(errors)
        warning_count += len(warnings)

    wiki_root = Path(__file__).resolve().parents[3]
    for message in check_readme_links(wiki_root):
        print(f"WARN  README: {message}")
        warning_count += 1

    print(
        f"\n{len(skills)} skills checked, "
        f"{error_count} error(s), {warning_count} warning(s)"
    )
    if error_count or (args.strict and warning_count):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
