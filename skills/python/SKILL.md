---
name: python
description: Use when writing, debugging, or reviewing Python scripts and small utilities. Triggers on Python syntax, scripting workflows, or interpreter/tooling questions.
---

# Python Skill

This document outlines the standard workflow for managing dependencies, environments, and execution using **uv**.

## When to Use

- In Python projects.
- When you want to manage dependencies, virtual environments, and Python versions in a streamlined way.
- When you need to modify Dockerfile to use `uv` for dependency management and execution.

## When NOT to Use

- Projects using Poetry, pipenv, or plain pip that explicitly want to keep their existing tooling
- Environments where `uv` is unavailable and cannot be installed
- Non-Python tasks — use the relevant language skill instead

## Guidelines

- Always use latest Python version (3.12+).

- Use `uv run ...` instead of `python ...` to run scripts. For example, run scripts: `uv run {{ script_file_path }}`.

- Use `uv tool install ...` to install global dependencies instead of `pip install ...`.

- Instead of manually managing virtual environments, `uv` handles the creation and syncing of the `.venv` directory based on the `pyproject.toml` file.

- Use `uv venv {{ path_to_venv }}` to create a virtual environment.

- Add dependencies: `uv add <package_name>` (e.g., `uv add requests`)

- For declaring script dependencies, use comment the following format in your script file:

  ```python
  #!/usr/bin/env -S uv run --script
  # /// script
  # requires-python = ">=3.12"
  # dependencies = [
  #   "requests",
  # ]
  # ///

  import requests # example dependency

  # Your code here
  ```
