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

## Available Skills

| Skill                                                            | Description                                                                                                                                                |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [ansible-naming-conventions](skills/ansible-naming-conventions/) | Use when writing, reviewing, or structuring Ansible code — roles, variables, tasks, handlers, playbooks, inventory groups, or tags.                        |
| [backstage-app-upgrade](skills/backstage-app-upgrade/)           | Use when upgrading a Backstage developer portal to a newer version. Covers the full upgrade lifecycle from planning through manual QA.                     |
| [changelog-generator](skills/changelog-generator/)               | Automatically creates user-facing changelogs from git commits by analyzing commit history and transforming technical commits into release notes.           |
| [cli-crane](skills/cli-crane/)                                   | Use when performing registry-direct operations with the crane CLI — copying images, inspecting manifests, mutating metadata, rebasing, multi-arch indexes. |
| [cli-taskfile](skills/cli-taskfile/)                             | Use when writing, debugging, or reviewing Taskfile.yml configurations for task automation and build workflows.                                             |
| [clickhouse-chproxy-users](skills/clickhouse-chproxy-users/)     | Use when configuring chproxy user authentication, wildcard passthrough, heartbeat users, or LDAP integration with ClickHouse.                              |
| [conventional-commits](skills/conventional-commits/)             | Guidelines for writing conventional commit messages that follow project standards and trigger automated releases.                                          |
| [doc-to-markdown](skills/doc-to-markdown/)                       | Convert a doc/docx file to markdown format.                                                                                                                |
| [excel-parsing](skills/excel-parsing/)                           | Use when reading, analyzing, or extracting data from .xls or .xlsx binary spreadsheet files.                                                               |
| [gitlab-ci-gitleaks](skills/gitlab-ci-gitleaks/)                 | Use when writing, reviewing, or configuring gitleaks secret scanning jobs in GitLab CI pipelines.                                                          |
| [golang-urfave-v2-to-v3](skills/golang-urfave-v2-to-v3/)         | A practical guide for migrating Go projects from urfave/cli v2 to v3.                                                                                      |
| [helm-chart-structuring](skills/helm-chart-structuring/)         | Use when creating, extending, or reviewing Helm charts.                                                                                                    |
| [helm-chart-unittest](skills/helm-chart-unittest/)               | Use when writing, reviewing, or extending helm-unittest test files for Helm charts.                                                                        |
| [markdown-to-pdf](skills/markdown-to-pdf/)                       | Use when generating a PDF file from markdown content or converting a markdown file to PDF using Python.                                                    |
| [orchestrating-swarms](skills/orchestrating-swarms/)             | Master multi-agent orchestration using Claude Code's Task system — parallel code reviews, pipeline workflows, self-organizing task queues.                 |
| [python](skills/python/)                                         | Basic skill for using Python.                                                                                                                              |
| [python-lib-rich](skills/python-lib-rich/)                       | Use when writing Python CLI tools that need formatted terminal output — tables, progress bars, colored text, syntax highlighting, spinners.                |
| [vector-remap-language](skills/vector-remap-language/)           | Use when writing, debugging, or reviewing VRL scripts for data transformation in Vector pipelines.                                                         |

## Adding a New Skill

Each skill lives in its own directory under `skills/`:

```
skills/
  my-skill/
    SKILL.md           # required
    references/        # optional companion docs
    templates/         # optional templates
```

Create a new skill:

```bash
bunx skills init skills/my-skill
```

`SKILL.md` format:

```markdown
---
name: my-skill
description: What this skill does and when Claude should use it
---

# My Skill

Instructions for the agent...
```

### Required frontmatter fields

| Field         | Description                                                                          |
| ------------- | ------------------------------------------------------------------------------------ |
| `name`        | Unique identifier, lowercase, hyphens allowed                                        |
| `description` | Brief explanation — this is what the agent reads to decide whether to load the skill |

## Supported Agents

Skills install to any agent supported by the `skills` CLI — including Claude Code, OpenCode, Cursor, Codex, GitHub Copilot, and [40+ others](https://github.com/vercel-labs/skills#supported-agents).

## License

See [LICENSE](LICENSE).
