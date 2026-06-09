#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Pre-commit hook: validate changed skills with agentskills CLI."""

import platform
import shutil
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


def _check_uvx() -> None:
    """Fail fast if uvx is not available on PATH."""
    result = subprocess.run(["uvx", "--version"], capture_output=True, check=False)
    if result.returncode != 0:
        if shutil.which("brew") and platform.system() == "Darwin":
            install_cmd = "brew install uv"
        else:
            install_cmd = "curl -LsSf https://astral.sh/uv/install.sh | sh"
        print(f"uvx not found. Install uv: {install_cmd}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    _check_uvx()
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
