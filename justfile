skills_dir := env("AGENTS_HOME", home_directory() / ".agents") / "skills"

# One symlink per skill. A real folder with the same name is left alone and reported.
link:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p "{{ skills_dir }}"
    for src in "{{ justfile_directory() }}"/skills/*/; do
        name=$(basename "$src")
        dest="{{ skills_dir }}/$name"
        if [ -e "$dest" ] && [ ! -L "$dest" ]; then
            echo "skip $name: $dest is a real folder"
            continue
        fi
        ln -sfn "${src%/}" "$dest"
        echo "$dest -> ${src%/}"
    done

# Validate every skill.
check:
    uv run -q --no-project --with pyyaml python "{{ justfile_directory() }}/skills/writing-skills/scripts/validate_skills.py"

# Count skill loads from OpenCode session history.
usage:
    python3 "{{ justfile_directory() }}/scripts/skill_usage_report.py"
