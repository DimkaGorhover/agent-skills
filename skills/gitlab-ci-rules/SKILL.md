---
name: gitlab-ci-rules
description: >-
  Use when writing, debugging, or reviewing GitLab CI job rules. Triggers on
  rules:if conditions, CI_PIPELINE_SOURCE filtering, unexpected job inclusion or
  exclusion, duplicate pipelines, rules:changes, rules:exists, when:never/manual/always,
  variable expressions with =~, !~, &&, ||, or migrating from only/except to rules.
---

# GitLab CI Rules

## When to Use

- Writing `rules:` for a job to control when it runs
- Debugging why a job runs (or doesn't) unexpectedly
- Filtering jobs per pipeline type: push, MR, schedule, tag, web, trigger
- Using `rules:changes` to trigger only on specific file changes
- Using `rules:exists` to trigger based on file presence
- Avoiding duplicate pipelines (both push + MR triggered for the same commit)
- Migrating deprecated `only` / `except` to `rules`
- Reusing rule sets across jobs with `!reference`

## When NOT to Use

- `workflow:rules` — controls the whole pipeline, not individual jobs (different keyword)
- GitHub Actions `on:` triggers — different platform, different syntax
- Existing `only/except` jobs that don't need to change — leave them alone; mixing causes issues

## Overview

`rules` is evaluated **top-to-bottom; the first matching rule wins**. When a rule
matches, the job is included (default `when: on_success`) or excluded (`when: never`).
If no rule matches, the job is excluded from the pipeline.

**Put specific conditions before catch-all rules.** A `when: on_success` / `when: always`
at the top will match everything, making the rules below it unreachable.

## `rules` Keyword Reference

| Keyword         | Purpose                               | Value type                                           |
| --------------- | ------------------------------------- | ---------------------------------------------------- |
| `if`            | Variable expression                   | String equality, regex, null, truthy checks          |
| `changes`       | File path patterns changed            | Path globs + optional `compare_to`                   |
| `exists`        | File presence in the repo             | Path globs                                           |
| `when`          | Job disposition when the rule matches | `on_success`, `never`, `manual`, `always`, `delayed` |
| `start_in`      | Delay before `when: delayed` job runs | Duration string, e.g. `"30 minutes"`, `"1 day"`      |
| `allow_failure` | Let pipeline continue on job failure  | `true` / `false`                                     |
| `variables`     | Set variables when rule matches       | Key-value map                                        |
| `interruptible` | Cancel job when pipeline superseded   | `true` / `false`                                     |
| `needs`         | Override needs when rule matches      | List                                                 |

## `CI_PIPELINE_SOURCE` Values

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"  # MR pipeline
  - if: $CI_PIPELINE_SOURCE == "push"                 # branch or tag push
  - if: $CI_PIPELINE_SOURCE == "schedule"             # scheduled pipeline
  - if: $CI_PIPELINE_SOURCE == "web"                  # triggered via UI
  - if: $CI_PIPELINE_SOURCE == "trigger"              # trigger token
  - if: $CI_PIPELINE_SOURCE == "pipeline"             # multi-project pipeline
  - if: $CI_PIPELINE_SOURCE == "api"                  # pipelines API
```

Other sources: `chat`, `external`, `external_pull_request_event`, `ondemand_dast_scan`,
`ondemand_dast_validation`, `parent_pipeline`, `security_orchestration_policy`, `webide`.

## Common Patterns

### Run only on default branch push

```yaml
job:
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Run on MR and scheduled pipelines only

```yaml
job:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

### Manual in MRs, automatic on default branch

```yaml
job:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: manual
      allow_failure: true
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Skip on a specific branch, run everywhere else

```yaml
job:
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: never
    - when: on_success
```

### Trigger only when specific files change (MR context)

```yaml
job:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        - src/**/*
        - Dockerfile
```

### Run only when branch has changes vs default branch

```yaml
job:
  rules:
    - if: $CI_COMMIT_BRANCH
      changes:
        compare_to: "refs/heads/main"
        paths:
          - "**/*"
```

### Run only when a file exists

```yaml
job:
  rules:
    - exists:
        - Dockerfile
```

> **Note:** `rules:exists` evaluates against the HEAD of the **source branch** — not the diff
> context. It does not support `compare_to`. To check diff-based file presence, use
> `rules:changes` instead.

### Run only when a file does NOT exist

```yaml
job:
  rules:
    - exists:
        - "config/skip-deploy.txt"
      when: never
    - when: on_success
```

### Run only for tagged commits

```yaml
job:
  rules:
    - if: $CI_COMMIT_TAG
```

### Delay a job start (when: delayed)

```yaml
notify:
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: delayed
      start_in: "30 minutes"
```

> `start_in` is **required** when `when: delayed` — omitting it is a syntax error.

## Variable Expressions

| Operator  | Example                         | Meaning                                                          |
| --------- | ------------------------------- | ---------------------------------------------------------------- |
| `==`      | `$VAR == "value"`               | Exact string match                                               |
| `!=`      | `$VAR != "value"`               | Not equal                                                        |
| `=~`      | `$VAR =~ /^main/`               | Regex match (RE2 syntax)                                         |
| `!~`      | `$VAR !~ /^feat/`               | Regex non-match                                                  |
| `&&`      | `$A && $B`                      | Both truthy                                                      |
| `\|\|`    | `$A \|\| $B`                    | Either truthy                                                    |
| (bare)    | `$VAR`                          | Defined and non-empty                                            |
| `== null` | `$VAR == null`                  | Undefined                                                        |
| `== ""`   | `$VAR == ""`                    | Defined but empty                                                |
| `!`       | `!$VAR` (GitLab 18.11+)         | Empty or undefined                                               |
| `!()`     | `!($A \|\| $B)` (GitLab 18.11+) | Group negation — e.g. `!($VAR1 \|\| $VAR2)`, `!($VAR1 && $VAR2)` |
| `( )`     | `($A \|\| $B) && $C`            | Parentheses for grouping                                         |

Regex rules:

- When matching predefined branch/tag variables (e.g. `$CI_COMMIT_BRANCH`, `$CI_COMMIT_TAG`) with
  `=~`, patterns **must** be wrapped in `/…/` (e.g. `/^main/`); file paths and other strings match literally
- Case-insensitive modifier: `/pattern/i`
- Use `^` and `$` anchors to avoid partial matches: `/^issue-.*$/`
- Variables inside regex patterns are **not** expanded

## Avoid Duplicate Pipelines

The most common mistake: both a push pipeline and an MR pipeline run for the same commit.

**Bad — triggers both pipeline types:**

```yaml
job:
  rules:
    - when: always  # matches push AND merge_request_event
```

**Fix 1 — be explicit about every pipeline source the job should run in:**

```yaml
job:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_PIPELINE_SOURCE == "schedule"
    # No catch-all — job is excluded from push/tag/web pipelines
```

**Fix 2 — `workflow:rules` (prevents duplicates pipeline-wide):**

```yaml
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH
```

## Reuse Rules with `!reference`

```yaml
.default_rules:
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
      when: never
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

job1:
  rules:
    - !reference [.default_rules, rules]
  script: echo "default branch only, no schedules"

job2:
  rules:
    - !reference [.default_rules, rules]
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  script: echo "also runs in MRs"
```

Additional rules after a `!reference` extend — they are evaluated after the referenced rules.

> **Warning:** If the referenced rule set ends with a `when: on_success` (or bare) catch-all,
> any rules you append after `!reference` are **unreachable** — the catch-all matches first.
> Ensure referenced rule sets end with `when: never` or have no catch-all before appending.

## Complex Rules (Multiple Conditions in One Rule)

All conditions inside a single rule entry must match for the rule to trigger:

```yaml
docker build:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        - Dockerfile
        - docker/**/*
      when: manual
      allow_failure: true
```

Logical expressions with parentheses:

```yaml
rules:
  - if: ($CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH || $CI_COMMIT_BRANCH == "develop") && $DEPLOY_ENABLED
```

## Migrate from `only`/`except`

| `only`/`except`            | `rules` equivalent                                                              |
| -------------------------- | ------------------------------------------------------------------------------- |
| `only: [main]`             | `if: $CI_COMMIT_BRANCH == "main"`                                               |
| `only: [schedules]`        | `if: $CI_PIPELINE_SOURCE == "schedule"` ¹                                       |
| `only: [merge_requests]`   | `if: $CI_PIPELINE_SOURCE == "merge_request_event"`                              |
| `only: [tags]`             | `if: $CI_COMMIT_TAG`                                                            |
| `only: [/^stable-.*/]`     | `if: $CI_COMMIT_BRANCH =~ /^stable-/`                                           |
| `except: [main]`           | `if: $CI_COMMIT_BRANCH == "main"; when: never` + fallthrough `when: on_success` |
| `except: [merge_requests]` | `if: $CI_PIPELINE_SOURCE == "merge_request_event"; when: never` + fallthrough   |

¹ `only: [schedules]` implicitly adds `except: merge_requests` — the job was also excluded from
MR pipelines. The `rules` equivalent (`if: $CI_PIPELINE_SOURCE == "schedule"`) preserves the
same behavior since non-matching pipelines are excluded when no other rule matches.

**Do not mix `only/except` and `rules` in the same pipeline.** They have different default
behaviors (jobs without rules default to `except: merge_requests`) which causes hard-to-debug
duplicate or missing pipeline runs.

## Common Mistakes

| Mistake                                           | Problem                                                                   | Fix                                                                    |
| ------------------------------------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Final `when: on_success` without `workflow:rules` | Triggers both push + MR pipelines (duplicate runs)                        | Add `workflow:rules` or be explicit about `CI_PIPELINE_SOURCE`         |
| `$CI_COMMIT_TAG` for scheduled pipelines          | Only true if the schedule runs on a tag; branch schedules don't set it    | Use `$CI_PIPELINE_SOURCE == "schedule"` instead                        |
| Mixing `only/except` and `rules` in one pipeline  | Different defaults produce unpredictable inclusion/exclusion              | Convert all jobs to `rules`                                            |
| RHS of `=~` not wrapped in `/`                    | GitLab treats RHS as substring check, not regex; `"23" =~ "1234"` is true | Always use `/pattern/` syntax                                          |
| `changes:` without `if:` in MR pipelines          | `changes` is always true for a new branch (no base to diff)               | Pair `changes` with `if: $CI_PIPELINE_SOURCE == "merge_request_event"` |
| Catch-all rule before specific rules              | Catch-all matches first; specific rules never reached                     | Always order specific rules before `when: always` / `when: on_success` |
| Variables inside regex patterns                   | Variables in `/…$VARNAME…/` patterns are not expanded                     | Store regex in a variable and use `$VAR =~ $PATTERN` syntax            |
