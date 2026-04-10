# ShellCheck Pre-commit Hook

## Quick Setup

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.11.0
    hooks:
      - id: shellcheck
```

Then install the hooks:

```bash
pre-commit install
```

> The pre-commit hook lives in a separate repository:
> <https://github.com/koalaman/shellcheck-precommit>
> (the main `shellcheck` repo does not contain `.pre-commit-hooks.yaml`)

## Common Configurations

### Only fail on errors and warnings (skip style/info)

```yaml
repos:
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.11.0
    hooks:
      - id: shellcheck
        args: [--severity=warning]
```

### Exclude specific SC codes project-wide

```yaml
repos:
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.11.0
    hooks:
      - id: shellcheck
        args: ['--exclude=SC1091,SC2016']
```

### Force a specific shell dialect

```yaml
repos:
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.11.0
    hooks:
      - id: shellcheck
        args: [--shell=bash]
```

### Follow sourced files

```yaml
repos:
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.11.0
    hooks:
      - id: shellcheck
        args: [--external-sources]
```

### Only check specific file types

By default the hook checks all `.sh` files staged for commit. To also check
files with other extensions or no extension:

```yaml
repos:
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.11.0
    hooks:
      - id: shellcheck
        types: [shell]                   # uses file magic, not extension
        # or restrict to specific extensions:
        # files: \.(sh|bash|bats)$
```

## Combining with `.shellcheckrc`

Pre-commit passes arguments directly to `shellcheck`. Project-level configuration
belongs in `.shellcheckrc` (auto-discovered). You can mix both — keep project-wide
settings in `.shellcheckrc` and pass only hook-specific flags via `args`:

> For the canonical `.shellcheckrc` example, see
> [.shellcheckrc Configuration](../SKILL.md#shellcheckrc-configuration) in the main skill.

```yaml
# .pre-commit-config.yaml — only pass args not in .shellcheckrc
repos:
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.11.0
    hooks:
      - id: shellcheck
        args: [--severity=warning]
```

## Version Pinning

Always pin `rev` to a specific tag — avoid `main` or `HEAD`. This prevents
unexpected failures when new warnings are added.

Check for new releases:

```bash
# Update rev to latest tag automatically
pre-commit autoupdate --repo https://github.com/koalaman/shellcheck-precommit
```

## Run Manually

```bash
# Run on all files (not just staged)
pre-commit run shellcheck --all-files

# Run on a specific file
pre-commit run shellcheck --files scripts/deploy.sh

# Run against a specific revision
pre-commit run shellcheck --from-ref HEAD~1 --to-ref HEAD
```

## CI/CD Integration

### GitHub Actions

```yaml
jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - uses: pre-commit/action@v3.0.1
```

### GitLab CI

```yaml
shellcheck:
  image: python:3.12-slim
  script:
    - pip install pre-commit
    - pre-commit run shellcheck --all-files
```

## Troubleshooting

### Hook not running on shell scripts without `.sh` extension

ShellCheck detects shell scripts by shebang (`#!/bin/bash`, `#!/bin/sh`, etc.).
If your files lack shebangs or extensions, force detection:

```yaml
  - id: shellcheck
    types_or: [shell, bash]
```

Or add shebangs to your scripts.

### `SC1091`: Not following source

The hook runs in an isolated environment; sourced files may not be on the path.
Suppress globally or point to the source:

```ini
# .shellcheckrc
source-path=SCRIPTDIR
disable=SC1091
```

### Hook is slow on large repos

Stage fewer files or narrow the `files` pattern:

```yaml
  - id: shellcheck
    files: ^scripts/ # only check scripts/ directory
```
