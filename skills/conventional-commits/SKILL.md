---
name: conventional-commits
description: Guidelines for writing conventional commit messages that follow project standards and trigger automated releases
metadata:
  author: d.horkhover
  version: 1.0.0
---

# Conventional Commits Skill

This skill provides comprehensive guidance on writing conventional commit messages for the vm0 project. All commits must follow the Conventional Commits format to ensure consistent history and enable automated versioning via release-please.

## When to Use

- Writing a commit message for any change
- Validating an existing commit message before pushing
- Planning which changes belong in a single commit
- Deciding whether a change should trigger a release bump (`feat`/`fix` vs `chore`/`docs`)

## When NOT to Use

- Projects that don't use semantic versioning or automated releases — use plain prose commits instead
- Commits in branches that are squash-merged (the final squash message matters, not individual commits)

## Quick Reference

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Core Rules (STRICT REQUIREMENTS)

1. **Type must be lowercase** - `feat:` not `Feat:` or `FEAT:`
1. **Description must start with lowercase** - `add feature` not `Add feature`
1. **No period at the end** - `fix user login` not `fix user login.`
1. **Keep title under 100 characters** - Be concise
1. **Use imperative mood** - `add` not `added` or `adds`

## Common Types (Quick List)

| Type        | Purpose          | Release?      |
| ----------- | ---------------- | ------------- |
| `feat:`     | New feature      | ✅ Minor bump |
| `fix:`      | Bug fix          | ✅ Patch bump |
| `docs:`     | Documentation    | ❌ No release |
| `refactor:` | Code refactoring | ❌ No release |
| `test:`     | Tests            | ❌ No release |
| `chore:`    | Build/tools      | ❌ No release |

**Pro tip:** If you want a `refactor` to trigger a release, use `fix: refactor ...` instead.

## When to Load Additional Context

- **Need detailed type definitions?** → Read `types.md`
- **Confused about what triggers releases?** → Read `release-triggers.md`
- **Want to see good and bad examples?** → Read `examples.md`

## Quick Validation Checklist

Before committing, verify:

- ✅ Type is lowercase and valid
- ✅ Description starts with lowercase
- ✅ No period at the end
- ✅ Under 100 characters
- ✅ Imperative mood (add, fix, update)
- ✅ Accurately describes the "why" not just the "what"

## Common Mistakes to Avoid

❌ `Fix: Resolve database connection timeout.` (capitalized type, has period)
❌ `added user auth` (missing type, wrong tense)
❌ `feat: Add user authentication system with OAuth2...` (capitalized description, too long)

✅ `fix: resolve database connection timeout`
✅ `feat: add user authentication`
✅ `docs(api): update endpoint documentation`

## Integration with Workflow

This skill should be triggered whenever:

1. Creating a commit message
1. Validating an existing commit message
1. Planning what changes should go into a single commit
1. Deciding if changes should trigger a release

The commit message should focus on **why** the change was made, not **what** was changed (git diff shows the what).
