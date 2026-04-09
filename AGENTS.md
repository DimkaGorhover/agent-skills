# AGENTS.md

Guidelines for AI coding agents working in this repository.

## Repository Overview

This is a personal collection of [agent skills](https://agentskills.io) — reusable instruction sets for
Claude Code, OpenCode, and 40+ other AI coding agents. There is no compiled code. All content is
Markdown, YAML, and JSON.

## Commands

### Lint & Format (run before every commit)

```bash
# Run all hooks against all files
uvx pre-commit run --all-files

# Run hooks on specific files only
uvx pre-commit run --files skills/my-skill/SKILL.md

# Format a single Markdown file
uvx --with "mdformat-gfm" --with "mdformat-frontmatter" mdformat <file.md>

# Lint YAML files
uvx yamllint -c .yamllint.yaml <file.yaml>

# Validate a skill directory
uvx --from skills-ref agentskills validate skills/my-skill
```

> Pre-commit is invoked via `uvx pre-commit` — never call `pre-commit` directly.

### Install hooks (once per clone)

```bash
uvx pre-commit install
```

### Install skills from this repo

This is a **private repository**. Authenticate with the GitHub CLI before running install commands:

```bash
gh auth login
```

```bash
# Install all skills globally for Claude Code
bunx skills add DimkaGorhover/agent-skills -g -a claude-code

# List available skills without installing
bunx skills add DimkaGorhover/agent-skills --list

# SSH alternative (no GitHub CLI required)
bunx skills add git@github.com:DimkaGorhover/agent-skills.git -g -a claude-code
```

## Skill File Structure

Each skill is a directory under `skills/` containing a `SKILL.md` and optional companion files:

```
skills/
  my-skill/
    SKILL.md                # required — agent instructions
    README.md               # optional — human-readable overview
    references/             # optional — deep-dive reference docs
      topic.md
    templates/              # optional — copy-paste templates
      example.yaml
```

### SKILL.md Frontmatter

```yaml
---
name: my-skill              # required: unique, lowercase, kebab-case
description: >              # required: one sentence — this is what agents read
  Use when doing X. Triggers on Y.
version: 1.0.0              # required: semver — bump on every meaningful change
---
```

**Rules:**

- `name` must match the directory name exactly
- `description` is the primary trigger signal agents use to decide whether to load the skill — make it
  precise, actionable, and mention trigger phrases
- `version` must follow semver — bump it whenever the skill content changes (see [Per-Skill Versioning](#per-skill-versioning))
- No other frontmatter fields are needed; avoid adding unnecessary metadata

### SKILL.md Body Conventions

- Start with a `# <Skill Name>` heading
- Include a **When to Use** section (bullets or short prose) — **required**
- Include a **When NOT to Use** section — **required** (prevents the skill from being loaded in wrong contexts)
- Use GFM tables for comparisons, avoid/use patterns, command references
- Use fenced code blocks with language hints for all code samples
- End sections with a "Read Next" or companion-file reference when deep docs exist

## Naming Conventions

| Artifact           | Convention                   | Example                        |
| ------------------ | ---------------------------- | ------------------------------ |
| Skill directory    | lowercase kebab-case         | `golang-urfave-v2-to-v3`       |
| `name` frontmatter | matches directory name       | `name: golang-urfave-v2-to-v3` |
| Companion Markdown | lowercase kebab-case         | `vrl-functions.md`             |
| JSON keys          | camelCase (marketplace.json) | `"pluginRoot"`                 |

## Updating `marketplace.json`

When adding a new skill, register it in `.claude-plugin/marketplace.json`:

```json
{
  "plugins": [
    {
      "name": "agent-skills",
      "skills": [
        "./skills/my-new-skill"
      ]
    }
  ]
}
```

Keep the `skills` array sorted alphabetically.

### Versioning

**Bump `metadata.version` in `.claude-plugin/marketplace.json` whenever:**

- Any skill file under `skills/` is added, removed, or meaningfully changed
- `.claude-plugin/marketplace.json` itself is modified (skills list, descriptions, plugin metadata)

Use [semver](https://semver.org) patch/minor/major increments:

| Change type                          | Bump    | Example           |
| ------------------------------------ | ------- | ----------------- |
| New skill added                      | `minor` | `1.0.0` → `1.1.0` |
| Skill removed                        | `major` | `1.1.0` → `2.0.0` |
| Skill content updated (non-breaking) | `patch` | `1.1.0` → `1.1.1` |
| Skill renamed or path changed        | `major` | `1.1.1` → `2.0.0` |
| Marketplace metadata only updated    | `patch` | `2.0.0` → `2.0.1` |

## Code Style

### Markdown

- Enforced by `mdformat` with `mdformat-gfm` + `mdformat-frontmatter` plugins
- GFM tables, fenced code blocks, and frontmatter are all supported
- Line length is not enforced — mdformat handles wrapping
- Always end files with a newline (enforced by pre-commit `end-of-file-fixer`)
- No trailing whitespace (enforced by pre-commit `trailing-whitespace`)

### YAML

- Config: `.yamllint.yaml` (extends `default`, max line length 120 as warning, `document-start` disabled)
- Quote all string values in `.pre-commit-config.yaml` hook IDs and rev tags
- Use 2-space indentation

### JSON

- 2-space indentation
- All string values double-quoted
- No trailing commas
- Validated by pre-commit `check-json` hook

## Pre-commit Hooks Summary

| Hook                      | What it checks                                            |
| ------------------------- | --------------------------------------------------------- |
| `check-added-large-files` | Prevents committing large binary files                    |
| `check-symlinks`          | Detects broken symlinks                                   |
| `trailing-whitespace`     | Removes trailing spaces                                   |
| `end-of-file-fixer`       | Ensures files end with a newline                          |
| `check-json`              | Validates JSON syntax                                     |
| `check-yaml`              | Validates YAML syntax                                     |
| `gitleaks`                | Secret scanning (blocks credential leaks)                 |
| `yamllint`                | YAML style lint (rules from `.yamllint.yaml`)             |
| `mdformat`                | Auto-formats all Markdown files                           |
| `agentskills-validate`    | Validates skill structure and content (`skills/` changes) |

## Adding a New Skill

Each skill lives in its own directory under `skills/`:

```
skills/
  my-skill/
    SKILL.md           # required
    references/        # optional companion docs
    templates/         # optional templates
```

Scaffold a new skill:

```bash
bunx skills init skills/my-skill
```

`SKILL.md` format:

```markdown
---
name: my-skill
description: What this skill does and when Claude should use it
metadata:
  author: d.horkhover
  version: 1.0.0
---

# My Skill

Instructions for the agent...
```

### Required frontmatter fields

| Field              | Description                                                                          |
| ------------------ | ------------------------------------------------------------------------------------ |
| `name`             | Unique identifier, lowercase, hyphens allowed                                        |
| `description`      | Brief explanation — this is what the agent reads to decide whether to load the skill |
| `metadata.author`  | The name of the author of the skill                                                  |
| `metadata.version` | Semver string — start at `1.0.0`, bump on every meaningful change                    |

### Per-Skill Versioning

Every `SKILL.md` carries its own `version` field. **Bump it whenever you make a meaningful change to the skill.**

| Change type                                                      | Bump    | Example           |
| ---------------------------------------------------------------- | ------- | ----------------- |
| Bug fix, typo, clarification (non-breaking)                      | `patch` | `1.0.0` → `1.0.1` |
| New section, improved examples, added rules                      | `minor` | `1.0.0` → `1.1.0` |
| Renamed fields, removed sections, restructured in a breaking way | `major` | `1.1.0` → `2.0.0` |

### Checklist

1. Create `skills/<skill-name>/SKILL.md` with `name`, `description`, and `version: 1.0.0` frontmatter
1. Write the body — include **When to Use** and **When NOT to Use** sections (both required), plus guidelines and examples
1. Add companion files in `references/` or `templates/` if the skill is complex
1. Register the path in `.claude-plugin/marketplace.json` `skills` array (keep sorted)
1. Bump `metadata.version` in `.claude-plugin/marketplace.json` (see [Versioning](#versioning))
1. Add a row to the README.md skills table
1. Run `uvx pre-commit run --all-files` — fix any failures before committing
