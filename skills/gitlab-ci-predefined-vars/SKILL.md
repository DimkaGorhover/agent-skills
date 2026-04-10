---
name: gitlab-ci-predefined-vars
description: >-
  Use when writing GitLab CI/CD pipelines and need to reference predefined
  variables — CI_COMMIT_SHA, CI_PIPELINE_SOURCE, CI_MERGE_REQUEST_IID,
  CI_REGISTRY, CI_JOB_TOKEN, and others. Triggers when unsure which variable
  to use, what its availability phase is (pre-pipeline vs pipeline vs job-only),
  or whether a variable is set in a given pipeline type.
metadata:
  author: d.horkhover
  version: 1.0.0
---

# GitLab CI Predefined Variables

## When to Use

- Looking up a specific predefined variable name or value format
- Checking whether a variable is available in `rules:`, `workflow:`, or `include:rules:`
- Debugging why `$CI_COMMIT_BRANCH` is empty in a tag pipeline
- Finding the right variable for commit info, registry credentials, MR metadata, runner info
- Building Docker image tags, URLs, or environment names from predefined vars

## When NOT to Use

- Custom/user-defined variables set in project Settings → CI/CD — those are project-specific
- Variables set with `variables:` in `.gitlab-ci.yml` — those are user-defined
- GitHub Actions contexts (`github.sha`, `github.ref`) — different platform

## Variable Availability Phases

**Critical:** Wrong phase = variable is empty or unavailable.

| Phase            | Available in                                               | Cannot use in                                     |
| ---------------- | ---------------------------------------------------------- | ------------------------------------------------- |
| **Pre-pipeline** | `include:rules`, `workflow:rules`, `rules:if`, job scripts | —                                                 |
| **Pipeline**     | `workflow:rules`, `rules:if`, job scripts                  | `include:rules`                                   |
| **Job-only**     | Job `script`, `before_script`, `after_script`              | `rules:`, `workflow:`, `include:`, `trigger` jobs |

> **Rule of thumb:** If you need it in `rules:if`, use a Pre-pipeline variable. If only needed in `script:`, Job-only is fine.

## Most-Used Variables Quick Reference

### Commit & Branch

| Variable                | Phase        | Example value                                  |
| ----------------------- | ------------ | ---------------------------------------------- |
| `CI_COMMIT_SHA`         | Pre-pipeline | `a1b2c3d4e5f6...`                              |
| `CI_COMMIT_SHORT_SHA`   | Pre-pipeline | `a1b2c3d4`                                     |
| `CI_COMMIT_BRANCH`      | Pre-pipeline | `main` (branch pipelines only, not tags/MRs)   |
| `CI_COMMIT_TAG`         | Pre-pipeline | `v1.2.3` (tag pipelines only)                  |
| `CI_COMMIT_REF_NAME`    | Pre-pipeline | branch or tag name                             |
| `CI_COMMIT_REF_SLUG`    | Pre-pipeline | `my-feature-branch` (URL-safe, 63 bytes max)   |
| `CI_COMMIT_TITLE`       | Pre-pipeline | First line of commit message                   |
| `CI_COMMIT_DESCRIPTION` | Pre-pipeline | Message body (everything after the first line) |
| `CI_COMMIT_MESSAGE`     | Pre-pipeline | Full commit message                            |
| `CI_COMMIT_AUTHOR`      | Pre-pipeline | `Name <email>`                                 |
| `CI_COMMIT_TIMESTAMP`   | Pre-pipeline | `2022-01-31T16:47:55Z` (ISO 8601, UTC)         |
| `CI_DEFAULT_BRANCH`     | Pre-pipeline | `main`                                         |

### Pipeline

| Variable                 | Phase        | Example value              |
| ------------------------ | ------------ | -------------------------- |
| `CI_PIPELINE_ID`         | Job-only     | `123456` (instance-unique) |
| `CI_PIPELINE_IID`        | Pipeline     | `42` (project-unique)      |
| `CI_PIPELINE_SOURCE`     | Pre-pipeline | See sources table below    |
| `CI_PIPELINE_URL`        | Job-only     | Full pipeline URL          |
| `CI_PIPELINE_NAME`       | Pre-pipeline | From `workflow:name`       |
| `CI_PIPELINE_CREATED_AT` | Job-only     | ISO 8601 timestamp         |

### `CI_PIPELINE_SOURCE` Values

```text
# Most common — use these in rules:if
push                          # branch or tag push
merge_request_event           # merge request pipeline
schedule                      # scheduled pipeline
web                           # triggered via UI
trigger                       # trigger token
pipeline                      # multi-project / parent-child pipeline
api                           # pipelines API
```

Other sources: `chat`, `external`, `external_pull_request_event`, `ondemand_dast_scan`, `ondemand_dast_validation`, `parent_pipeline`, `security_orchestration_policy`, `webide`.

### Job

| Variable            | Phase    | Example value                   |
| ------------------- | -------- | ------------------------------- |
| `CI_JOB_ID`         | Job-only | `98765` (instance-unique)       |
| `CI_JOB_NAME`       | Pipeline | `build`                         |
| `CI_JOB_STAGE`      | Pipeline | `test`                          |
| `CI_JOB_TOKEN`      | Job-only | Short-lived auth token          |
| `CI_JOB_URL`        | Job-only | Full job URL                    |
| `CI_JOB_STATUS`     | Job-only | `success`, `failed`, `canceled` |
| `CI_JOB_STARTED_AT` | Job-only | ISO 8601 timestamp              |
| `CI_JOB_IMAGE`      | Job-only | Docker image name (if set)      |
| `CI_JOB_MANUAL`     | Pipeline | `true` if started manually      |

### Project

| Variable                | Phase        | Example value                                 |
| ----------------------- | ------------ | --------------------------------------------- |
| `CI_PROJECT_ID`         | Pre-pipeline | `12345`                                       |
| `CI_PROJECT_NAME`       | Pre-pipeline | `my-project`                                  |
| `CI_PROJECT_PATH`       | Pre-pipeline | `group/my-project`                            |
| `CI_PROJECT_PATH_SLUG`  | Pre-pipeline | `group-my-project` (URL-safe)                 |
| `CI_PROJECT_NAMESPACE`  | Pre-pipeline | `my-group`                                    |
| `CI_PROJECT_URL`        | Pre-pipeline | `https://gitlab.example.com/group/my-project` |
| `CI_PROJECT_VISIBILITY` | Pre-pipeline | `private`, `internal`, `public`               |
| `CI_PROJECT_TITLE`      | Pre-pipeline | Human-readable name                           |

### Registry & Deployment

| Variable               | Phase        | Notes                                        |
| ---------------------- | ------------ | -------------------------------------------- |
| `CI_REGISTRY`          | Pre-pipeline | Registry host `registry.gitlab.example.com`  |
| `CI_REGISTRY_IMAGE`    | Pre-pipeline | Full image base path                         |
| `CI_REGISTRY_USER`     | Job-only     | Push username                                |
| `CI_REGISTRY_PASSWORD` | Job-only     | Same as `CI_JOB_TOKEN`, valid while job runs |
| `CI_DEPLOY_USER`       | Job-only     | Deploy token username (if configured)        |
| `CI_DEPLOY_PASSWORD`   | Job-only     | Deploy token password (long-lived)           |
| `CI_REPOSITORY_URL`    | Job-only     | Full HTTPS clone URL with job token          |

### Server

| Variable         | Phase        | Example value                       |
| ---------------- | ------------ | ----------------------------------- |
| `CI_SERVER_URL`  | Pre-pipeline | `https://gitlab.example.com:8080`   |
| `CI_SERVER_HOST` | Pre-pipeline | `gitlab.example.com`                |
| `CI_SERVER_PORT` | Pre-pipeline | `8080`                              |
| `CI_SERVER_FQDN` | Pre-pipeline | `gitlab.example.com:8080`           |
| `CI_API_V4_URL`  | Pre-pipeline | `https://gitlab.example.com/api/v4` |

### Runner

| Variable            | Phase    | Notes                                 |
| ------------------- | -------- | ------------------------------------- |
| `CI_RUNNER_ID`      | Job-only | Unique runner ID                      |
| `CI_RUNNER_TAGS`    | Job-only | JSON array, e.g. `["docker","linux"]` |
| `CI_RUNNER_VERSION` | Job-only | Runner version string                 |
| `CI_BUILDS_DIR`     | Job-only | Top-level builds directory            |
| `CI_PROJECT_DIR`    | Job-only | Full path to cloned repo              |
| `CI_CONCURRENT_ID`  | Job-only | Unique build ID per executor          |

## Merge Request Variables

Only set when the pipeline is a **merge request pipeline** (`CI_PIPELINE_SOURCE == "merge_request_event"`). All are Pre-pipeline phase.

| Variable                              | Description                                                                                 |
| ------------------------------------- | ------------------------------------------------------------------------------------------- |
| `CI_MERGE_REQUEST_IID`                | Project-level MR number (shown in MR URL)                                                   |
| `CI_MERGE_REQUEST_ID`                 | Instance-level MR ID                                                                        |
| `CI_MERGE_REQUEST_TITLE`              | MR title                                                                                    |
| `CI_MERGE_REQUEST_SOURCE_BRANCH_NAME` | Source branch                                                                               |
| `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` | Target branch                                                                               |
| `CI_MERGE_REQUEST_SOURCE_BRANCH_SHA`  | HEAD SHA of source (empty in merge request pipelines; only set in merged results pipelines) |
| `CI_MERGE_REQUEST_TARGET_BRANCH_SHA`  | HEAD SHA of target (empty in merge request pipelines; only set in merged results pipelines) |
| `CI_MERGE_REQUEST_DIFF_BASE_SHA`      | Base SHA of the diff                                                                        |
| `CI_MERGE_REQUEST_LABELS`             | Comma-separated labels                                                                      |
| `CI_MERGE_REQUEST_MILESTONE`          | Milestone title                                                                             |
| `CI_MERGE_REQUEST_APPROVED`           | `true` if approved                                                                          |
| `CI_MERGE_REQUEST_DRAFT`              | `true` if draft MR (GitLab 17.10+)                                                          |
| `CI_MERGE_REQUEST_EVENT_TYPE`         | `detached`, `merged_result`, or `merge_train`                                               |
| `CI_MERGE_REQUEST_PROJECT_PATH`       | MR project path                                                                             |
| `CI_MERGE_REQUEST_REF_PATH`           | `refs/merge-requests/<iid>/head`                                                            |

## Common Patterns

### Docker image tagged with commit SHA

```yaml
build:
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
```

### Run only on default branch

```yaml
deploy:
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Run only on tags matching semver

```yaml
release:
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
```

### Access GitLab API from job

```yaml
script:
  - curl --header "JOB-TOKEN: $CI_JOB_TOKEN" "$CI_API_V4_URL/projects/$CI_PROJECT_ID/packages"
```

### Login to container registry

```yaml
before_script:
  - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
```

### MR-specific logic

```yaml
check-mr-labels:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  script:
    - echo "MR !$CI_MERGE_REQUEST_IID targeting $CI_MERGE_REQUEST_TARGET_BRANCH_NAME"
```

## Common Mistakes

| Mistake                                     | Problem                                    | Fix                                                                                                           |
| ------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| `$CI_COMMIT_BRANCH` in tag pipeline         | Empty — only set for branch pipelines      | Use `$CI_COMMIT_REF_NAME` for both                                                                            |
| `$CI_COMMIT_TAG` in branch pipeline         | Empty — only set for tag pipelines         | Check first: `if: $CI_COMMIT_TAG`                                                                             |
| `$CI_PIPELINE_ID` in `rules:if`             | Job-only — unavailable at rules evaluation | Use `$CI_PIPELINE_IID` (Pipeline phase) — note it's project-scoped, not instance-unique like `CI_PIPELINE_ID` |
| `$CI_JOB_TOKEN` in `trigger:` jobs          | Job-only — not available in trigger jobs   | Use project/group access tokens for cross-project auth                                                        |
| `$CI_REGISTRY_PASSWORD` for long-lived auth | Expires when job ends                      | Use `$CI_DEPLOY_PASSWORD` (deploy token) for long-lived access                                                |
| MR vars in push pipeline                    | Empty — only set in MR pipelines           | Guard with `if: $CI_PIPELINE_SOURCE == "merge_request_event"`                                                 |
| `$CI_MERGE_REQUEST_SOURCE_BRANCH_SHA` empty | Empty in detached MR pipelines             | Only populated in merged results pipelines                                                                    |
