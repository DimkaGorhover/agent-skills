---
name: shellcheck
description: Use when linting shell scripts with ShellCheck — running checks, configuring .shellcheckrc, suppressing false positives, integrating with CI/CD, or setting up pre-commit hooks for sh/bash/dash/ksh/busybox scripts.
metadata:
  author: d.horkhover
  version: 1.0.1
---

# ShellCheck

## Overview

ShellCheck is a static analysis tool for sh/bash/dash/ksh scripts. It detects syntax errors,
quoting bugs, portability issues, and common pitfalls — giving precise, actionable warnings with
SC-numbered codes and wiki links.

## When to Use

- Running ShellCheck on shell scripts from CLI or CI/CD
- Configuring `.shellcheckrc` for a project (disable/enable rules, shell dialect, source paths)
- Suppressing false positives inline or globally
- Setting up pre-commit hooks with shellcheck
- Interpreting SC warning codes and deciding whether to fix or suppress (see [shellcheck.net/wiki/SCNNNN](https://www.shellcheck.net/wiki/))
- Choosing output format for editor/CI integration
- Checking portability across sh/bash/dash/ksh

## When NOT to Use

- Formatting or indenting shell scripts — use `shfmt` instead
- Non-shell file linting (Python, YAML, etc.)
- Writing new shell scripts from scratch where no linting has been requested — this is a linter skill, not a shell-scripting guide

## Quick Reference

```bash
# Basic usage
shellcheck script.sh

# Check multiple files
shellcheck scripts/*.sh

# Set shell dialect explicitly (when shebang is missing/wrong)
shellcheck --shell=bash script.sh

# Only show errors and warnings (skip info/style)
shellcheck --severity=warning script.sh

# Exclude specific codes
shellcheck --exclude=SC2086,SC2016 script.sh

# Include only specific codes
shellcheck --include=SC2086 script.sh

# Output formats: tty (default), gcc, checkstyle, diff, json, json1, quiet
shellcheck --format=gcc script.sh

# Auto-fix: output unified diff, apply with git apply
shellcheck --format=diff script.sh | git apply

# Follow sourced files
shellcheck --external-sources script.sh

# List available optional checks
shellcheck --list-optional
```

## CLI Flags

| Flag                        | Description                                                  |
| --------------------------- | ------------------------------------------------------------ |
| `-s`, `--shell=SHELL`       | Override dialect: `sh`, `bash`, `dash`, `ksh`, `busybox`     |
| `-S`, `--severity=LEVEL`    | Minimum level: `error`, `warning`, `info`, `style` (default) |
| `-e`, `--exclude=CODES`     | Exclude comma-separated SC codes                             |
| `-i`, `--include=CODES`     | Include only these codes (overrides excludes)                |
| `-f`, `--format=FORMAT`     | Output format (see Formats section)                          |
| `-x`, `--external-sources`  | Follow `source` statements to external files                 |
| `-a`, `--check-sourced`     | Also emit warnings inside sourced files                      |
| `-o`, `--enable=NAMES`      | Enable optional checks (`all` enables everything)            |
| `-P`, `--source-path=PATH`  | Colon-separated paths to search for sourced files            |
| `--rcfile=FILE`             | Use specific rc file instead of auto-discovery               |
| `--norc`                    | Disable rc file loading entirely                             |
| `--extended-analysis=false` | Disable dataflow analysis (for 2000+ line generated scripts) |
| `-W`, `--wiki-link-count=N` | Show N wiki links in TTY output (0 = disable)                |
| `-V`, `--version`           | Print version and exit                                       |

## Exit Codes

| Code | Meaning                         |
| ---- | ------------------------------- |
| `0`  | No issues found                 |
| `1`  | Issues found                    |
| `2`  | File(s) could not be processed  |
| `3`  | Bad syntax (unknown flag)       |
| `4`  | Bad options (unknown formatter) |

## Output Formats

| Format           | Use Case                                                          |
| ---------------- | ----------------------------------------------------------------- |
| `tty`            | Default — human readable, with colors                             |
| `gcc`            | Editor integration (`:set makeprg=shellcheck\ -f\ gcc\ %` in Vim) |
| `checkstyle`     | IDEs and build monitoring systems (XML)                           |
| `diff`           | Auto-fix: pipe to `git apply` or `patch -p1`                      |
| `json` / `json1` | Downstream tooling; `json1` is the current format                 |
| `quiet`          | CI exit-code-only (suppress all output)                           |

## Inline Suppression (Directives)

```bash
# Suppress a single code on next command
# shellcheck disable=SC2086
echo $var

# Suppress multiple codes on next command
# shellcheck disable=SC2086,SC2016
for f in $(ls "$dir"); do echo "$f"; done

# Suppress on a block (brace group / loop)
# shellcheck disable=SC2016
{
  echo 'PATH=$HOME/bin:$PATH'
  echo 'export PATH' >> ~/.bashrc
}

# Tell shellcheck where a dynamically-sourced file lives
# shellcheck source=./lib/helpers.sh
source "$(find_lib_dir)/helpers.sh"

# Skip a source entirely
# shellcheck source=/dev/null
source "$DYNAMIC_PATH"

# Override the detected shell for this file
# shellcheck shell=bash
```

```bash
# Re-enable a previously disabled check in a scoped block
# shellcheck enable=SC2086
echo "$re_enabled_var"
```

All directives before the first command apply file-wide.

## `.shellcheckrc` Configuration

ShellCheck searches for `.shellcheckrc` upward from each script's directory, then `~/.shellcheckrc`
and `$XDG_CONFIG_HOME/shellcheckrc`.

```ini
# .shellcheckrc

# Default shell dialect
shell=bash

# Always follow sourced files
external-sources=true

# Search for sourced files relative to the script being checked.
# SCRIPTDIR is a special token that resolves to the directory of the script
# currently being checked (not the CWD or the project root).
source-path=SCRIPTDIR
source-path=SCRIPTDIR/../lib

# Enable optional checks
enable=quote-safe-variables
enable=check-unassigned-uppercase

# Project-wide suppressions (explain why inline if non-obvious)
disable=SC1091   # Don't follow 3rd-party sourced files
```

> `SHELLCHECK_OPTS` env var works too: `export SHELLCHECK_OPTS='--shell=bash --exclude=SC2016'`

## Common Mistakes and Fixes

| Code   | Pattern                                  | Fix                                            |
| ------ | ---------------------------------------- | ---------------------------------------------- |
| SC2086 | `echo $var`                              | `echo "$var"` — always quote variables         |
| SC2181 | `if [ $? -eq 0 ]`                        | `if command; then` — check exit code directly  |
| SC2015 | `[ -f f ] && echo yes \|\| echo no`      | Use `if/then/else`                             |
| SC2016 | `echo '$HOME'` in single quotes          | Use double quotes if expansion needed          |
| SC2046 | `$(ls *.txt)` in command args            | Use globs directly: `*.txt`                    |
| SC2006 | `` `backtick` `` substitution            | Use `$(...)`                                   |
| SC2164 | `cd /dir; command` without error check   | `cd /dir \|\| exit` or `set -e`                |
| SC1091 | Not following sourced file               | Add `# shellcheck source=./file.sh` or disable |
| SC2155 | `export VAR=$(cmd)` masks exit code      | Declare and assign separately                  |
| SC2206 | `arr=($(...))` word-splits on whitespace | Use `mapfile -t arr < <(...)` (bash 4+)        |
| SC2207 | `arr=($(cmd))` — word-split array fill   | Use `mapfile -t arr < <(cmd)` instead          |

## CI/CD Integration

```bash
# Find and check all shell scripts in a project
find . -type f -name "*.sh" -exec shellcheck {} +

# Fail only on errors (allow warnings/style)
find . -name "*.sh" | xargs shellcheck --severity=error

# GCC format for editor-parseable CI output
shellcheck --format=gcc myscript.sh
```

**Docker** (no local installation needed):

```bash
docker run --rm -v "$PWD:/mnt" koalaman/shellcheck:stable myscript.sh
```

**GitHub Actions** (native, no pre-commit required):

```yaml
  - name: ShellCheck
    run: find . -name "*.sh" | xargs shellcheck --severity=warning
```

## References

- [Installation guide](references/installation.md) — all package managers, binary install, Docker
- [Pre-commit hook setup](references/pre-commit.md) — `.pre-commit-config.yaml` configuration
- [ShellCheck wiki](https://www.shellcheck.net/wiki/) — per-code explanations
- [ShellCheck.net](https://www.shellcheck.net) — online checker
