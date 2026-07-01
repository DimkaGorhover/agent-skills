---
name: gitlab-ci-rules-test
description: Use when a GitLab CI rules:if fails with "invalid expression syntax", or before adding/editing rules:if expressions with many ==/=~/&&/|| conditions or long OR-chains of $CI_PROJECT_PATH / branch checks.
metadata:
  author: d.horkhover
  version: 1.0.0
---

# GitLab CI Rules Test

## When to Use

- A GitLab CI job fails with `jobs:<job>:rules:rule if invalid expression syntax`
  and the YAML itself looks fine
- Before adding or editing a `rules:if` with many `==` / `=~` / `&&` / `||`
  conditions
- Long OR-chains of `$CI_PROJECT_PATH` or branch checks (each
  `|| $VAR =~ /.../` costs 4 tokens toward the 100-token cap)
- Validating a `rules:if` expression before pushing — catch the token limit and
  genuine syntax errors before CI does

## When NOT to Use

- **Authoring** `rules` logic — which pipeline sources trigger a job,
  `rules:changes`, avoiding duplicate pipelines, `only`/`except` migration. Use
  the `gitlab-ci-rules` skill. This skill is only about *why an expression fails
  to parse*.
- Plain YAML errors (indentation, wrong keys) — those are structural, not
  expression syntax; `yamllint` and CI Lint catch them.
- GitHub Actions `if:` expressions — different platform, different syntax.

## Overview

GitLab reports almost every `rules:if` problem as one opaque message:

```
jobs:<job>:rules:rule if invalid expression syntax
```

The message rarely points at the real cause. The most common real cause is the
**100-token limit**, not YAML or bad syntax. Diagnose by tokenizing the
expression and validating it against GitLab's actual parser — never by eyeballing.

## The #1 cause: MAX_TOKENS = 100

GitLab's expression lexer caps an expression at **100 tokens**
(`lib/gitlab/ci/pipeline/expression/lexer.rb`, `MAX_TOKENS = 100`). Over the cap
it raises `Lexer::SyntaxError: Too many tokens!`, surfaced as *"invalid
expression syntax"*.

A token is any lexeme, whitespace ignored:

| Token kind  | Examples                                    |
| ----------- | ------------------------------------------- |
| variable    | `$CI_COMMIT_BRANCH`, `$FOO`                 |
| operator    | `==` `!=` `=~` `!~` `&&` `\|\|`             |
| pattern     | `/^main$/` (one token, whatever its length) |
| string      | `"main"`, `'web'`                           |
| parenthesis | `(` `)` (each one token)                    |
| keyword     | `null` `true` `false`                       |

Each extra `|| $CI_PROJECT_PATH =~ /.../` costs **4 tokens**. ~23 OR'd path
checks blow past 100. Count with the bundled tool:

```bash
uv run count_expression_tokens.py all.yml            # scan whole file
uv run count_expression_tokens.py all.yml --job mirror-push
uv run count_expression_tokens.py --expr '$A == "x" && ($B || $C)'
```

## Fix for the token limit: collapse OR-chains into one regex

A long chain of `$VAR =~ /a/ || $VAR =~ /b/ || ...` is one variable repeated.
Fold the branches into a single pattern (one token instead of 4 per branch):

```yaml
# BEFORE — 4 tokens per branch, blows the 100-token cap
- if: >-
    $CI_PROJECT_PATH =~ /^mygroup\/myproject\/alpha\//
    || $CI_PROJECT_PATH =~ /^mygroup\/myproject\/beta\//
    || $CI_PROJECT_PATH =~ /^mygroup\/myproject\/gamma\//

# AFTER — 3 tokens total, unlimited branches
- if: >-
    $CI_PROJECT_PATH =~ /^mygroup\/myproject\/(alpha|beta|gamma)\//
```

When a rule spans several second-level groups, splitting into one rule per group
(each with its own alternation regex) keeps every rule tiny and readable while
staying identical in coverage. Verify equivalence: every original prefix must
still match, and near-misses (`myprojectxx`, unknown subgroups) must not.

## Do NOT misdiagnose these (they are NOT the cause)

| Suspected cause                                 | Reality                                                                                                        |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Folded-scalar (`>-`) newlines in the expression | The lexer skips `\s` incl. newlines. Embedded newlines are harmless; re-indenting to one line changes nothing. |
| Parentheses for grouping                        | Supported since GitLab 12.11: `($A \|\| $B) && $C`. Not the problem.                                           |
| Comparing two variables                         | `$CI_COMMIT_REF_NAME == $CI_DEFAULT_BRANCH` is valid.                                                          |
| Bare variable truthiness                        | `... && $MY_TOKEN && ...` is valid (non-empty check).                                                          |

If you "fixed" the YAML and it's still broken, you fixed the wrong thing —
count the tokens.

## How to test rules before pushing

1. **Token count** (catches the 100-token trap): `count_expression_tokens.py`.
1. **Real parser via CI Lint API** (catches genuine syntax errors) — validates
   against the branch's actual config:
   ```bash
   curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
     "$GITLAB_HOST/api/v4/projects/$PROJECT_ID/ci/lint?include_merged_yaml=true" \
     --data-urlencode "content@.gitlab-ci.yml" | jq '{valid, errors, warnings}'
   ```
   Or `glab ci lint` if the CLI is available.
1. **`yamllint`** — structural YAML only; it does **not** understand expression
   semantics, so a rule can be yamllint-clean and still fail CI lint.
1. **Confirm what CI actually runs.** The error cites a commit — CI lints the
   pushed/committed config, not your unpushed working tree. Reproduce against the
   committed version (`git show <sha>:path`) before concluding a fix works.

## Common mistakes

- Trusting yamllint or a YAML parse as proof the rule is valid — it only proves
  the YAML is well-formed, not that the expression parses.
- Testing your local edit while CI keeps failing on the committed version.
- Reducing the number of OR branches to duck under 100 tokens (lossy) instead of
  folding them into one regex (lossless).
- Assuming a passing count means valid — also run CI Lint for true syntax errors
  (`=~` needs a `/regex/` literal on the right, unbalanced parens, etc.).

## Real-world impact

A `mirror-push` rule with 23 OR'd `$CI_PROJECT_PATH` checks tokenized to 103 →
"invalid expression syntax". Two YAML-focused "fixes" (de-indenting the folded
scalar, questioning parentheses) changed nothing. Folding the branches into
per-group alternation regexes dropped it to 13 tokens per rule and fixed it.
