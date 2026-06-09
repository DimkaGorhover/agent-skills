# agent-skills

Personal collection of [agent skills](https://agentskills.io) for Claude Code and other AI coding agents.

## Install

> **Private repository.** You must have access to `DimkaGorhover/agent-skills` on GitHub before installing.

### Prerequisites

The `skills` CLI authenticates against GitHub using the [GitHub CLI](https://cli.github.com).
Log in once before running any install command:

```bash
gh auth login
```

If you prefer SSH, use `git@github.com:DimkaGorhover/agent-skills.git` as a drop-in replacement
for the `DimkaGorhover/agent-skills` shorthand in all commands below.

### Via `bunx skills` (recommended)

```bash
# Install all skills globally for Claude Code
bunx skills add DimkaGorhover/agent-skills -g -a claude-code

# Install globally for OpenCode
bunx skills add DimkaGorhover/agent-skills -g -a opencode

# Install all skills to all supported agents
bunx skills add DimkaGorhover/agent-skills --all

# Install specific skills only
bunx skills add DimkaGorhover/agent-skills --skill my-skill -g -a claude-code

# List available skills without installing
bunx skills add DimkaGorhover/agent-skills --list

# SSH alternative (no GitHub CLI required)
bunx skills add git@github.com:DimkaGorhover/agent-skills.git -g -a claude-code
```

> `bunx` is Bun's package runner — equivalent to `npx` if you prefer:
>
> ```bash
> npx skills add DimkaGorhover/agent-skills -g -a claude-code
> ```

### Via Claude Code Marketplace

This repository is registered in the Claude Code plugin marketplace.
Install via the Claude Code UI or CLI:

```bash
claude plugin install github:DimkaGorhover/agent-skills
```

## Upgrade

When a new version of this skills collection is released, re-run the install commands — the `skills` CLI
handles updates automatically:

```bash
# Check which skills have updates available
bunx skills check

# Pull the latest version of all installed skills
bunx skills update
```

Or with `npx`:

```bash
npx skills check
npx skills update
```

> If you installed via the Claude Code Marketplace, use:
>
> ```bash
> claude plugin update github:DimkaGorhover/agent-skills
> ```

## Available Skills

| Skill                                                            | Description                                                                                                                                                                                                        |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [ansible-naming-conventions](skills/ansible-naming-conventions/) | Use when writing, reviewing, or structuring Ansible code — roles, variables, tasks, handlers, playbooks, inventory groups, or tags.                                                                                |
| [ansible-plugins-cache](skills/ansible-plugins-cache/)           | Use when selecting, configuring, or troubleshooting Ansible cache plugins for fact or inventory caching (memory, jsonfile, yaml, redis, memcached, mongodb).                                                       |
| [backstage-app-upgrade](skills/backstage-app-upgrade/)           | Use when upgrading a Backstage developer portal to a newer version. Covers the full upgrade lifecycle from planning through manual QA.                                                                             |
| [changelog-generator](skills/changelog-generator/)               | Automatically creates user-facing changelogs from git commits by analyzing commit history and transforming technical commits into release notes.                                                                   |
| [cli-aws-ce](skills/cli-aws-ce/)                                 | Use when querying AWS Cost Explorer with `aws ce` — cost/usage reports, forecasts, anomaly detection, savings plans, reservation utilization, and rightsizing recommendations.                                     |
| [cli-crane](skills/cli-crane/)                                   | Use when performing registry-direct operations with the crane CLI — copying images, inspecting manifests, mutating metadata, rebasing, multi-arch indexes.                                                         |
| [cli-stern](skills/cli-stern/)                                   | Use when tailing logs from multiple Kubernetes pods or containers simultaneously — filtering by pod name regex, label selector, namespace, container state, or resource type.                                      |
| [cli-opendataloader-pdf](skills/cli-opendataloader-pdf/)         | Use when converting PDF files to text, markdown, HTML, or JSON using opendataloader-pdf — extracting content for RAG pipelines, chunking for vector stores, or processing multi-column/table-heavy documents.      |
| [cli-taskfile](skills/cli-taskfile/)                             | Use when writing, debugging, or reviewing Taskfile.yml configurations for task automation and build workflows.                                                                                                     |
| [clickhouse-chproxy-users](skills/clickhouse-chproxy-users/)     | Use when configuring chproxy user authentication, wildcard passthrough, heartbeat users, or LDAP integration with ClickHouse.                                                                                      |
| [conventional-commits](skills/conventional-commits/)             | Guidelines for writing conventional commit messages that follow project standards and trigger automated releases.                                                                                                  |
| [doc-to-markdown](skills/doc-to-markdown/)                       | Convert a doc/docx file to markdown format.                                                                                                                                                                        |
| [dockerfile-fnox](skills/dockerfile-fnox/)                       | Use when installing fnox (secrets manager) in a Dockerfile on Alpine, Debian, or Rocky Linux.                                                                                                                      |
| [excel-parsing](skills/excel-parsing/)                           | Use when reading, analyzing, or extracting data from .xls or .xlsx binary spreadsheet files.                                                                                                                       |
| [gitlab-ci-gitleaks](skills/gitlab-ci-gitleaks/)                 | Use when writing, reviewing, or configuring gitleaks secret scanning jobs in GitLab CI pipelines.                                                                                                                  |
| [gitlab-ci-predefined-vars](skills/gitlab-ci-predefined-vars/)   | Use when looking up GitLab CI predefined variables — availability phases, commit/pipeline/job/MR/registry vars, and common patterns.                                                                               |
| [gitlab-ci-rules](skills/gitlab-ci-rules/)                       | Use when writing, debugging, or reviewing GitLab CI job rules — rules:if, CI_PIPELINE_SOURCE, rules:changes, rules:exists, duplicate pipelines, only/except migration.                                             |
| [golang-urfave-v2-to-v3](skills/golang-urfave-v2-to-v3/)         | A practical guide for migrating Go projects from urfave/cli v2 to v3.                                                                                                                                              |
| [grafana-foundation-sdk](skills/grafana-foundation-sdk/)         | Use when building Grafana dashboards programmatically with grafana-foundation-sdk in Go, Python, or TypeScript — panels, variables, datasource refs, manifest output.                                              |
| [helm-chart-structuring](skills/helm-chart-structuring/)         | Use when creating, extending, or reviewing Helm charts.                                                                                                                                                            |
| [helm-chart-unittest](skills/helm-chart-unittest/)               | Use when writing, reviewing, or extending helm-unittest test files for Helm charts.                                                                                                                                |
| [markdown-to-pdf](skills/markdown-to-pdf/)                       | Use when generating a PDF file from markdown content or converting a markdown file to PDF using Python.                                                                                                            |
| [opencode-custom-tools](skills/opencode-custom-tools/)           | Use when creating, registering, or debugging custom tools for OpenCode — TypeScript/JavaScript tool definitions, Zod argument schemas, multi-tool files, overriding built-in tools, or invoking external scripts.  |
| [orchestrating-swarms](skills/orchestrating-swarms/)             | Master multi-agent orchestration using Claude Code's Task system — parallel code reviews, pipeline workflows, self-organizing task queues.                                                                         |
| [python](skills/python/)                                         | Modern Python tooling with uv, ruff, ty — use when creating projects, writing standalone scripts, or migrating from pip/Poetry/mypy/black.                                                                         |
| [python-lib-rich](skills/python-lib-rich/)                       | Use when writing Python CLI tools that need formatted terminal output — tables, progress bars, colored text, syntax highlighting, spinners.                                                                        |
| [security-audit](skills/security-audit/)                         | Use when auditing a codebase, web app, or API for security vulnerabilities — reviewing auth, access control, input handling, secrets, or data flow across trust boundaries; threat modeling or pre-release review. |
| [shellcheck](skills/shellcheck/)                                 | Use when linting shell scripts with ShellCheck — running checks, configuring .shellcheckrc, suppressing false positives, integrating with CI/CD, or setting up pre-commit hooks for sh/bash/dash/ksh scripts.      |
| [terraform-actions](skills/terraform-actions/)                   | Use when writing Terraform 1.14+ action block and action_trigger workflows for day-2 operations, including after_create/after_update and -invoke execution.                                                        |
| [vector-remap-language](skills/vector-remap-language/)           | Use when writing, debugging, or reviewing VRL scripts for data transformation in Vector pipelines.                                                                                                                 |

## Recommended Skills from Other Repositories

High-quality third-party skill collections worth installing alongside this one.

### Token Efficiency

| Repository                                                        | Stars | Install                                 | Description                                                                                                                                                                                                                                                     |
| ----------------------------------------------------------------- | ----- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | 41k+  | `claude plugin install caveman@caveman` | Cuts ~65–75% of output tokens by making the agent respond in caveman-speak — same technical accuracy, dramatically less verbosity. Includes `caveman-commit`, `caveman-review`, and a `caveman-compress` tool that reduces input tokens in `CLAUDE.md` by ~46%. |

### Go

| Repository                                                                        | Stars | Install                                                            | Description                                                                                                                                                                                                                                           |
| --------------------------------------------------------------------------------- | ----- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [samber/cc-skills-golang](https://github.com/samber/cc-skills-golang)             | 1.3k+ | `bunx skills add https://github.com/samber/cc-skills-golang --all` | 30+ atomic Go skills covering code style, testing, error handling, concurrency, security, observability, and popular libraries (samber/lo, samber/mo, stretchr/testify). +44pp error rate improvement over baseline.                                  |
| [madflojo/go-style-agent-skill](https://github.com/madflojo/go-style-agent-skill) | 29+   | `gh skill install madflojo/go-style-agent-skill`                   | Opinionated Go engineering guide for package design, Config-driven constructors, boundary-driven interfaces, sentinel error contracts, and idiomatic godoc. Includes deep reference docs on benchmarks, concurrency, testing, and a review checklist. |

### Security & Reverse Engineering

| Repository                                                                                                              | Stars | Install                                                                               | Description                                                                                                                                                                                                                                                     |
| ----------------------------------------------------------------------------------------------------------------------- | ----- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [SimoneAvogadro/android-reverse-engineering-skill](https://github.com/SimoneAvogadro/android-reverse-engineering-skill) | 4.3k+ | `claude plugin install android-reverse-engineering@android-reverse-engineering-skill` | Decompiles APK/XAPK/JAR/AAR files and extracts HTTP APIs — Retrofit endpoints, OkHttp calls, hardcoded URLs, auth patterns. Uses jadx, Fernflower/Vineflower. Includes `/decompile` slash command and shell scripts for dependency checking and API extraction. |

### Dev Workflow & Content

| Repository                                              | Stars | Install                                                     | Description                                                                                                                                                                                                                                                                       |
| ------------------------------------------------------- | ----- | ----------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [samber/cc-skills](https://github.com/samber/cc-skills) | 70+   | `bunx skills add https://github.com/samber/cc-skills --all` | Marketing and engineering skills: `conventional-git`, `promql-cli`, `linkedin-ghostwriting`, `substack-ghostwriting`, `technical-article-writer`, `press-release-writer`, `snyk-agent-scan-compliance`, `deep-research`, `training-report`. +41pp overall error rate improvement. |

### GitLab Ecosystem

| Repository                                                      | Skills   | Install                                                                                                        | Description                                                                                                                                                                                                                                                                    |
| --------------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [gitlab-org/ai/skills](https://gitlab.com/gitlab-org/ai/skills) | 8 skills | `bunx @dgruzd/skills add https://gitlab.com/gitlab-org/ai/skills/-/tree/main/skills --global --agent opencode` | Official GitLab AI skills: `glab` CLI automation, `commit-messages`, `gitlab-psql` / `gitlab-clickhouse` GDK inspection, `opencode-refine` for iterative prompt tuning, `playwright-cli`, `run-in-tmux-pane`, and `self-service-performance-testing` with k6 and sitespeed.io. |

### Reference Lists

| Repository                                                    | Stars | Description                                                                                                                                                                                          |
| ------------------------------------------------------------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [samber/awesome-olap](https://github.com/samber/awesome-olap) | 116+  | Curated reference list of 100+ OLAP databases, data lake tools, columnar engines, brokers, ETL frameworks, and BI tools across 20+ categories. Not a skills package — a bookmark for data engineers. |

## Supported Agents

Skills install to any agent supported by the `skills` CLI — including Claude Code, OpenCode, Cursor, Codex, GitHub Copilot, and [40+ others](https://github.com/vercel-labs/skills#supported-agents).

## License

See [LICENSE](LICENSE).
