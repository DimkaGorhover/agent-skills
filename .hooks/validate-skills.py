#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Pre-commit hook: validate changed skills with agentskills CLI."""

import subprocess
import sys
from pathlib import Path


def _unique_skill_dirs(files: list[str]) -> list[str]:
    seen: set[str] = set()
    dirs: list[str] = []
    for f in files:
        parts = Path(f).parts
        if len(parts) > 2 and parts[0] == "skills":  # noqa: PLR2004
            skill = parts[1]
            if skill not in seen:
                seen.add(skill)
                dirs.append(skill)
    return dirs


def main() -> None:
    dirs = _unique_skill_dirs(sys.argv[1:])
    if not dirs:
        sys.exit(0)

    exit_code = 0
    for skill_dir in dirs:
        result = subprocess.run(
            [
                "uvx",
                "--from",
                "skills-ref",
                "agentskills",
                "validate",
                f"skills/{skill_dir}",
            ],
            check=False,
        )
        if result.returncode != 0:
            exit_code = result.returncode

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
