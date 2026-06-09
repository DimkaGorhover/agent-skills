---
name: gitlab-ci-gitleaks
description: Use when writing, reviewing, or configuring gitleaks secret scanning jobs in GitLab CI pipelines. Triggers on gitleaks CI job creation, .gitleaks.toml configuration, incremental scan setup, report artifact configuration, or pre-commit hook integration with gitleaks.
metadata:
  author: d.horkhover
  version: 1.0.0
---

# GitLab CI Gitleaks — Secret Scanning Skill

## When to Use

- Writing a new gitleaks secret scanning job in a GitLab CI pipeline
- Reviewing or debugging an existing gitleaks CI job
- Configuring `.gitleaks.toml` allowlists, custom rules, or baseline suppression
- Setting up incremental scanning (MR-only vs full-history)
- Integrating gitleaks as a pre-commit hook

## When NOT to Use

- GitHub Actions pipelines — gitleaks usage differs; check the gitleaks GitHub Actions docs directly
- Non-gitleaks secret scanning tools (Trivy, truffleHog, detect-secrets)
- General GitLab CI questions unrelated to secret scanning

## Overview

Gitleaks scans git history for hardcoded secrets (API keys, tokens, passwords). This skill covers writing GitLab CI jobs, configuring `.gitleaks.toml`, and setting up pre-commit hooks — based on gitleaks v8.x conventions.

**Reference image**: `ghcr.io/gitleaks/gitleaks:v8.30.1`

> Find latest image tag: `crane ls ghcr.io/gitleaks/gitleaks | grep -E -i '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1`

## Canonical CI Job Template

This is the reference pattern. Copy and adapt per-recipe below.

```yaml
gitleaks:
  stage: validate
  image:
    name: ghcr.io/gitleaks/gitleaks:v8.30.1
    entrypoint:
      - ""
  allow_failure: true  # set to false once existing secrets are triaged
  variables:
    GIT_DEPTH: 0
    GITLEAKS_LOG_LEVEL: "warn"
  script:
    - |-
      # gitleaks: set safe directory for git
      set -eu
      git config --global --add safe.directory "${CI_PROJECT_DIR}"
    - |-
      # gitleaks: determine log options based on pipeline source
      LOG_OPTS_FLAG=""
      if [ -n "${CI_MERGE_REQUEST_DIFF_BASE_SHA:-}" ]; then
        LOG_OPTS_FLAG="--log-opts=${CI_MERGE_REQUEST_DIFF_BASE_SHA}..HEAD"
      elif [ "${CI_COMMIT_BEFORE_SHA}" != "0000000000000000000000000000000000000000" ]; then
        LOG_OPTS_FLAG="--log-opts=${CI_COMMIT_BEFORE_SHA}..HEAD"
      fi
    - |-
      # gitleaks: run gitleaks
      # shellcheck disable=SC2086
      gitleaks git \
        --log-level=${GITLEAKS_LOG_LEVEL} \
        --exit-code=2 \
        --verbose \
        --redact \
        --platform=gitlab \
        --no-banner \
        --max-target-megabytes=10 \
        $LOG_OPTS_FLAG \
        --report-format=junit \
        --report-path=gitleaks-report.xml \
        "${CI_PROJECT_DIR}"
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      when: on_success
    - if: >-
        $CI_PIPELINE_SOURCE =~ /^(web|push)$/
        && $CI_COMMIT_REF_NAME == $CI_DEFAULT_BRANCH
      when: on_success
  artifacts:
    when: always
    reports:
      junit: gitleaks-report.xml
    paths:
      - gitleaks-report.xml
    expire_in: 1 week
```

## Critical Implementation Details

### 1. `entrypoint: [""]` is REQUIRED

The gitleaks Docker image has `gitleaks` as its entrypoint. GitLab CI needs an empty entrypoint to run shell scripts.

### 2. `GIT_DEPTH: 0` is REQUIRED

Gitleaks uses `git log` internally. Shallow clones (`GIT_DEPTH: 20` default) will miss commits referenced in `--log-opts` ranges, causing silent scan gaps or fatal errors.

### 3. `safe.directory` is REQUIRED

GitLab CI runners clone repos with different UID than the container user. Git 2.35.2+ refuses to operate in such directories. Always add:

```yaml
git config --global --add safe.directory "${CI_PROJECT_DIR}"
```

### 4. Incremental Scan Logic (the `LOG_OPTS_FLAG` pattern)

The three-tier fallback handles all pipeline types correctly:

| Pipeline Source                   | Variable Available                | Scan Range                                |
| --------------------------------- | --------------------------------- | ----------------------------------------- |
| `merge_request_event`             | `CI_MERGE_REQUEST_DIFF_BASE_SHA`  | MR base..HEAD (only MR commits)           |
| `push` (subsequent)               | `CI_COMMIT_BEFORE_SHA` (non-zero) | Previous push..HEAD (new commits only)    |
| `push` (first), `web`, `schedule` | Neither available                 | Full history scan (empty `LOG_OPTS_FLAG`) |

**Never use `CI_COMMIT_BEFORE_SHA` for MR pipelines** — it is all-zeros in that context. Always check `CI_MERGE_REQUEST_DIFF_BASE_SHA` first.

### 5. `--exit-code=2` vs `--exit-code=1`

- Default exit code for leaks found is `1`
- Errors (git failures, config problems) also exit `1`
- Using `--exit-code=2` distinguishes "leaks found" from "tool error"
- Combine with `allow_failure: exit_codes: [2]` for granular control

### 6. `--redact` Behavior

- `--redact` alone = 100% redaction (shows `REDACTED`)
- `--redact=20` = redacts 20% of secret characters (80% visible)
- Affects `Secret`, `Match`, and `Line` fields in both log output and report files
- Always use in CI to prevent secrets from appearing in job logs

### 7. Report Format Selection

| Format  | Flag                    | Use Case                    | GitLab Integration |
| ------- | ----------------------- | --------------------------- | ------------------ |
| `junit` | `--report-format=junit` | GitLab test reports tab     | `reports: junit:`  |
| `json`  | `--report-format=json`  | Downstream processing       | `paths:` only      |
| `sarif` | `--report-format=sarif` | Code quality / SAST viewers | `reports: sast:`   |
| `csv`   | `--report-format=csv`   | Spreadsheet export          | `paths:` only      |

**JUnit requires explicit `--report-format=junit`** — gitleaks cannot infer it from `.xml` extension.

### 8. `artifacts: when: always`

Always collect reports even on job failure. Without `when: always`, a failed gitleaks scan (leaks found) would not upload the report artifact.

## Command Reference (gitleaks v8.x)

### Subcommands

| Command               | Purpose                                   | Notes                                        |
| --------------------- | ----------------------------------------- | -------------------------------------------- |
| `gitleaks git [repo]` | Scan git history                          | Primary command for CI                       |
| `gitleaks dir [path]` | Scan directory (no git)                   | For non-git repos or release artifacts       |
| `gitleaks stdin`      | Scan stdin input                          | Pipe content for scanning                    |
| `gitleaks detect`     | (deprecated) alias for `git`              | Hidden but functional; use `git` in new jobs |
| `gitleaks protect`    | (deprecated) alias for `git --pre-commit` | Hidden but functional                        |

### Key Flags for `gitleaks git`

| Flag           | Type     | Default | Description                                                                      |
| -------------- | -------- | ------- | -------------------------------------------------------------------------------- |
| `--log-opts`   | `string` | `""`    | Passed verbatim to `git log -p` — controls scan scope                            |
| `--platform`   | `string` | `""`    | SCM for link generation: `github`, `gitlab`, `azuredevops`, `gitea`, `bitbucket` |
| `--pre-commit` | `bool`   | `false` | Use `git diff` instead of `git log` (pre-commit mode)                            |
| `--staged`     | `bool`   | `false` | Scan staged changes only (with `--pre-commit`)                                   |

### Global Flags (all subcommands)

| Flag                      | Short | Type       | Default   | Description                                           |
| ------------------------- | ----- | ---------- | --------- | ----------------------------------------------------- |
| `--config`                | `-c`  | `string`   | `""`      | Config file path                                      |
| `--exit-code`             |       | `int`      | `1`       | Exit code when leaks found                            |
| `--report-path`           | `-r`  | `string`   | `""`      | Report output file (`"-"` for stdout)                 |
| `--report-format`         | `-f`  | `string`   | `""`      | `json`, `csv`, `junit`, `sarif`, `template`           |
| `--baseline-path`         | `-b`  | `string`   | `""`      | JSON report to diff against (suppress known findings) |
| `--log-level`             | `-l`  | `string`   | `"info"`  | `trace`, `debug`, `info`, `warn`, `error`, `fatal`    |
| `--verbose`               | `-v`  | `bool`     | `false`   | Print each finding to stdout                          |
| `--no-color`              |       | `bool`     | `false`   | Disable ANSI color output                             |
| `--no-banner`             |       | `bool`     | `false`   | Suppress ASCII art banner                             |
| `--redact`                |       | `uint`     | `0`/`100` | Bare flag = 100%; `--redact=N` = N% of chars redacted |
| `--max-target-megabytes`  |       | `int`      | `0`       | Skip files larger than this (0 = no limit)            |
| `--max-decode-depth`      |       | `int`      | `5`       | Recursive decode depth for encoded secrets (0 = off)  |
| `--enable-rule`           |       | `[]string` | `[]`      | Allowlist of rule IDs to run (disables all others)    |
| `--gitleaks-ignore-path`  | `-i`  | `string`   | `"."`     | Path to `.gitleaksignore` file or its directory       |
| `--ignore-gitleaks-allow` |       | `bool`     | `false`   | Ignore `gitleaks:allow` inline comments               |
| `--timeout`               |       | `int`      | `0`       | Command timeout in seconds (0 = no timeout)           |

### Config Resolution Order

1. `--config` / `-c` flag
1. `GITLEAKS_CONFIG` env var (file path)
1. `GITLEAKS_CONFIG_TOML` env var (inline TOML content)
1. `{source}/.gitleaks.toml`
1. Built-in default config

### Exit Codes

| Code          | Meaning               |
| ------------- | --------------------- |
| `0`           | No leaks found        |
| `1` (default) | Leaks found, or error |
| `126`         | Unknown flag          |

`--exit-code` only controls the leaks-found code. Errors always exit `1`.

## `.gitleaks.toml` Configuration

### Minimal Config (extend defaults)

```toml
title = "Gitleaks Configuration"
[[allowlists]]
description = "Project-specific safe patterns"
paths = [ "(^|/)\\.terraform\\.lock\\.hcl$", "(^|/)\\.terraform/",]
stopwords = [ "REPLACE_ME", "EXAMPLE", "placeholder",]

[extend]
useDefault = true # inherit all built-in detection rules
```

### Full Schema Reference

```toml
title = "Config Title" # informational
description = "..." # informational
minVersion = "v8.25.0" # warn if gitleaks version < this
# ── EXTEND ──────────────────────────────────────────────────
[[rules]]
id = "my-custom-rule" # REQUIRED, must be unique
description = "Human text"
regex = "regex-pattern" # Go RE2 syntax (no lookaheads)
path = "path-regex" # match on file path
secretGroup = 1 # capture group index to treat as the secret
entropy = 3.5 # minimum Shannon entropy (0 = disabled)
keywords = [ "token", "key",] # case-insensitive pre-filter (performance optimization)
tags = [ "custom",] # metadata for reporting
# Per-rule allowlist (can have multiple)
[[rules.allowlists]]
description = "ignore test fixtures"
condition = "OR" # "OR" (default) | "AND"
commits = [ "abc123",] # exact commit SHAs to skip
paths = [ "tests/",] # regex matched against file path
regexes = [ "(?i)fake",] # regex matched against regexTarget
regexTarget = "secret" # "secret" (default) | "match" | "line"
stopwords = [ "example",] # case-insensitive substring match
# ── GLOBAL ALLOWLISTS ──────────────────────────────────────


[[allowlists]]
description = "global safe patterns"
condition = "OR"
paths = [ "\\.md$", "vendor/",]
regexes = [ "219-09-9999",]
regexTarget = "match" # "match" | "line" (no "secret" in global context)
stopwords = [ "placeholder",]
commits = [ "deadbeef",]
# Target specific rules only (v8.25.0+)

[[allowlists]]
targetRules = [ "rule-a",] # apply only to these rule IDs
paths = [ "tests/expected/",]

[extend]
useDefault = true # merge into built-in rules (mutually exclusive with path)
# path = "base-config.toml"   # merge into another config file
disabledRules = [ "rule-id",] # rules from extended config to disable
# ── CUSTOM RULES ────────────────────────────────────────────
```

### Rule Validation Constraints

- `id` is required and non-empty
- At least one of `regex` or `path` must be set
- `secretGroup` must be \<= number of capture groups in `regex`
- Allowlist must have at least one of: `commits`, `paths`, `regexes`, `stopwords`
- `condition = "AND"` requires all non-empty criteria to match simultaneously

### `regexTarget` Values

| Value                | Tested Against                 |
| -------------------- | ------------------------------ |
| `"secret"` (default) | The captured secret group only |
| `"match"`            | The entire regex match string  |
| `"line"`             | The complete source line       |

### Inline Suppression

```python
secret = "known-safe-value"  # gitleaks:allow
```

### `.gitleaksignore` File

One fingerprint per line. Format: `{commit}:{file}:{rule-id}:{line}`

```text
abc123def:config/settings.py:gitlab-pat:10
```

## CI Job Recipes

### Recipe 1: Standard MR + Push Scan (recommended starting point)

Uses the canonical template above — incremental scanning with JUnit reports.

### Recipe 2: Blocking MR Gate (no `allow_failure`)

```yaml
gitleaks:
  stage: validate
  image:
    name: ghcr.io/gitleaks/gitleaks:v8.30.1
    entrypoint: [""]
  allow_failure: false
  variables:
    GIT_DEPTH: 0
  script:
    - |-
      set -eu
      git config --global --add safe.directory "${CI_PROJECT_DIR}"
    - |-
      gitleaks git \
        --log-opts="${CI_MERGE_REQUEST_DIFF_BASE_SHA}..HEAD" \
        --exit-code=1 \
        --verbose \
        --redact \
        --platform=gitlab \
        --no-banner \
        --max-target-megabytes=10 \
        --report-format=junit \
        --report-path=gitleaks-report.xml \
        "${CI_PROJECT_DIR}"
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
  artifacts:
    when: always
    reports:
      junit: gitleaks-report.xml
    paths:
      - gitleaks-report.xml
    expire_in: 1 week
```

### Recipe 3: Scheduled Full-History Audit

```yaml
gitleaks-audit:
  stage: validate
  image:
    name: ghcr.io/gitleaks/gitleaks:v8.30.1
    entrypoint: [""]
  allow_failure: true
  variables:
    GIT_DEPTH: 0
  script:
    - |-
      set -eu
      git config --global --add safe.directory "${CI_PROJECT_DIR}"
    - |-
      gitleaks git \
        --log-opts="--all" \
        --exit-code=0 \
        --verbose \
        --redact \
        --no-banner \
        --max-target-megabytes=10 \
        --report-format=junit \
        --report-path=gitleaks-report.xml \
        "${CI_PROJECT_DIR}"
  rules:
    - if: '$CI_PIPELINE_SOURCE == "schedule"'
  artifacts:
    when: always
    reports:
      junit: gitleaks-report.xml
    expire_in: 4 weeks
```

### Recipe 4: Baseline Suppression (for repos with historical secrets)

```yaml
gitleaks:
  stage: validate
  image:
    name: ghcr.io/gitleaks/gitleaks:v8.30.1
    entrypoint: [""]
  variables:
    GIT_DEPTH: 0
  script:
    - |-
      set -eu
      git config --global --add safe.directory "${CI_PROJECT_DIR}"
    - |-
      LOG_OPTS_FLAG=""
      if [ -n "${CI_MERGE_REQUEST_DIFF_BASE_SHA:-}" ]; then
        LOG_OPTS_FLAG="--log-opts=${CI_MERGE_REQUEST_DIFF_BASE_SHA}..HEAD"
      elif [ "${CI_COMMIT_BEFORE_SHA}" != "0000000000000000000000000000000000000000" ]; then
        LOG_OPTS_FLAG="--log-opts=${CI_COMMIT_BEFORE_SHA}..HEAD"
      fi
    - |-
      # shellcheck disable=SC2086
      gitleaks git \
        --baseline-path="${CI_PROJECT_DIR}/.gitleaks-baseline.json" \
        --exit-code=1 \
        --verbose \
        --redact \
        --no-banner \
        $LOG_OPTS_FLAG \
        --report-format=json \
        --report-path=gitleaks-report.json \
        "${CI_PROJECT_DIR}"
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
  artifacts:
    when: always
    paths:
      - gitleaks-report.json
    expire_in: 1 week
```

Generate baseline: `gitleaks git --report-format json --report-path .gitleaks-baseline.json`

## Pre-commit Hook Integration

```yaml
# .pre-commit-config.yaml
- repo: "https://github.com/gitleaks/gitleaks"
  rev: "v8.30.1"
  hooks:
    - id: gitleaks
      name: "Gitleaks"
      args:
        - "--verbose"
        - "--redact"
        - "--no-banner"
        - "--max-target-megabytes=10"
      stages:
        - "pre-commit"
```

The pre-commit hook runs `gitleaks git --pre-commit --staged` internally — scanning only staged changes.

## `allow_failure` Decision Matrix

| Scenario                        | `allow_failure`   | Rationale                                               |
| ------------------------------- | ----------------- | ------------------------------------------------------- |
| Initial rollout                 | `true`            | Let teams triage existing findings                      |
| Established pipeline (blocking) | `false`           | Prevent new secrets from merging                        |
| Full-history scheduled audit    | `true`            | Historical findings expected                            |
| Informational / advisory        | `true`            | Audit without blocking merges                           |
| Granular (leaks vs errors)      | `exit_codes: [2]` | Only allow leaks (with `--exit-code=2`), fail on errors |

## Common Mistakes

| Mistake                             | Problem                                                            | Fix                                               |
| ----------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------- |
| Missing `entrypoint: [""]`          | Container runs `gitleaks` as entrypoint, breaking script execution | Always set empty entrypoint                       |
| Using default `GIT_DEPTH`           | Shallow clone misses commits in scan range                         | Set `GIT_DEPTH: 0`                                |
| Missing `safe.directory`            | Git refuses to operate, job fails with `dubious ownership`         | Add `git config --global --add safe.directory`    |
| Using `CI_COMMIT_BEFORE_SHA` for MR | All-zeros in MR pipelines, scans entire history                    | Check `CI_MERGE_REQUEST_DIFF_BASE_SHA` first      |
| Missing `when: always` on artifacts | Report not uploaded when leaks found (non-zero exit)               | Set `artifacts: when: always`                     |
| Expecting `.xml` to infer junit     | Gitleaks does not infer junit from extension                       | Always set `--report-format=junit` explicitly     |
| `--redact` without value            | Redacts 100% — may be desired, but know the behavior               | Use `--redact=50` for partial visibility          |
| Quoting `$LOG_OPTS_FLAG`            | Prevents word splitting; empty string becomes empty arg            | Leave unquoted with `# shellcheck disable=SC2086` |
