---
name: golang-gocognit
description: Use when Go code is hard to follow, deeply nested, branch-heavy, or when analyzing, reviewing, or refactoring functions with high cognitive complexity — running gocognit, interpreting diagnostic output, or setting complexity thresholds in CI/CD.
metadata:
  author: d.horkhover
  version: 1.1.0
---

# gocognit — Go Cognitive Complexity Analyzer

## Overview

`gocognit` measures **cognitive complexity**: how hard a function is for a human (or AI) to understand
intuitively. Unlike cyclomatic complexity which counts decision paths, cognitive complexity penalizes
deeply nested control flow and rewards idiomatic Go patterns like `switch` over `if/else` chains.

**Key insight for AI agents:** The `-d` (diagnostic) flag exposes the exact increments that raised
a function's score — giving a structured, line-by-line map of *why* code is complex, not just *how much*.

## When to Use

- Go code that is **hard to follow**, deeply nested, or branch-heavy — even without a score yet
- Deciding where to focus refactoring on legacy or unfamiliar code (**readability hotspot** discovery)
- Auditing a codebase for **complex functions** before a code review or architectural review
- Setting a CI gate (`-over N`) to prevent complexity regressions
- Comparing two implementations to confirm a refactor actually reduced complexity
- Reviewing a **complex PR** — validate that new code is not introducing cognitive debt

## When NOT to Use

- Cyclomatic complexity analysis — use `gocyclo` instead (different metric, different scores)
- Non-Go codebases — tool is Go-only
- Counting test coverage or detecting bugs — `gocognit` is a **readability** tool, not a correctness tool
- Tiny changesets (a 3-line diff rarely benefits from a full complexity audit)
- Generated code files — mark with `//gocognit:ignore` or use `-ignore` flag instead

## Default Agent Workflow

Run this as a starting point for any complexity audit:

```bash
# 1. Find all high-complexity functions with full diagnostic detail
gocognit -json -d -over 15 ./...

# 2. Fix the highest-score function, then re-run to confirm improvement
gocognit -json -over 15 ./...

# 3. When done: verify average is reasonable
gocognit -avg ./...
```

**Loop:** inspect top offenders → open file at `Pos.Line` → apply one refactor → rerun → compare score.
Stop when `-over 15` produces no output.

## Complexity Score Guide

| Score | Interpretation | Typical action                                                 |
| ----- | -------------- | -------------------------------------------------------------- |
| 0–9   | Simple         | No action needed                                               |
| 10–15 | Moderate       | Consider splitting if function has multiple responsibilities   |
| 16–25 | High           | Refactor — extract helpers, flatten nesting, use early returns |
| 25+   | Very high      | High-priority refactor target; high review risk                |

> Common CI threshold: `15`. SonarSource's original paper recommends investigating functions above `15`.

## Quick Reference

```bash
# Scan entire package tree (recursive)
gocognit ./...

# Single file
gocognit main.go

# Show only functions above threshold (CI gate: exits 1 if any found)
gocognit -over 15 ./...

# Top 10 most complex functions
gocognit -top 10 ./...

# Show average complexity across all functions
gocognit -avg ./...

# Include test files
gocognit -test ./...

# JSON output (machine-readable)
gocognit -json ./...

# Diagnostic: show exactly what incremented the score
gocognit -json -d ./...

# Ignore files matching regex (e.g., generated code, vendor)
gocognit -ignore "_generated|vendor" ./...

# Custom output format
gocognit -f "{{.Complexity}}\t{{.FuncName}}\t{{.Pos}}" ./...
```

> **Scope note:** `gocognit .` scans only the current directory's `.go` files (non-recursive).
> Use `./...` to scan all packages in the module tree. Prefer `./...` for project-wide audits.

## CLI Flags

| Flag           | Description                                                     |
| -------------- | --------------------------------------------------------------- |
| `-over N`      | Show functions with complexity > N; exits 1 if output non-empty |
| `-top N`       | Show the N most complex functions                               |
| `-avg`         | Print average complexity across all functions                   |
| `-test`        | Include `_test.go` files (excluded by default)                  |
| `-json`        | Output as JSON array                                            |
| `-d`           | Enable diagnostic output (per-increment details)                |
| `-f format`    | Custom Go template format string                                |
| `-ignore expr` | Skip **files** whose paths match this regexp                    |

**Default output format:** `{{.Complexity}} {{.PkgName}} {{.FuncName}} {{.Pos}}`

## Understanding JSON Output

### Top-level result fields

| Field          | Type   | Meaning                                         |
| -------------- | ------ | ----------------------------------------------- |
| `PkgName`      | string | Go package name                                 |
| `FuncName`     | string | Function or method name                         |
| `Complexity`   | int    | Total cognitive complexity score                |
| `Pos`          | object | Location of the function declaration            |
| `Pos.Filename` | string | File path                                       |
| `Pos.Line`     | int    | Line number — open file here to start reviewing |
| `Diagnostics`  | array  | Present only when `-d` is used; see below       |

### Diagnostic fields (with `-d`)

| Field      | Meaning                                                       |
| ---------- | ------------------------------------------------------------- |
| `Inc`      | Points added by this construct (1 base + nesting level)       |
| `Nesting`  | Nesting depth at this increment                               |
| `Text`     | Construct name: `if`, `for`, `switch`, `continue LABEL`, etc. |
| `Pos.Line` | Source line — jump directly to the problem                    |

### Example diagnostic output

```bash
$ gocognit -json -d -over 15 ./pkg/...
```

```json
[
  {
    "PkgName": "parser",
    "FuncName": "ParseExpr",
    "Complexity": 22,
    "Pos": {
      "Filename": "parser.go",
      "Line": 45
    },
    "Diagnostics": [
      {
        "Inc": 1,
        "Nesting": 0,
        "Text": "for",
        "Pos": {
          "Line": 50
        }
      },
      {
        "Inc": 2,
        "Nesting": 1,
        "Text": "if",
        "Pos": {
          "Line": 53
        }
      },
      {
        "Inc": 3,
        "Nesting": 2,
        "Text": "switch",
        "Pos": {
          "Line": 58
        }
      },
      {
        "Inc": 4,
        "Nesting": 3,
        "Text": "if",
        "Pos": {
          "Line": 62
        }
      },
      {
        "Inc": 1,
        "Nesting": 0,
        "Text": "continue",
        "Pos": {
          "Line": 71
        }
      }
    ]
  }
]
```

**Reading diagnostic output as an AI agent:**

1. **Sort by `Inc` descending** — entries with the highest `Inc` are deepest nesting; extracting them yields the largest score reduction per change
1. **Many `Inc=1` at `Nesting=0`** → sequential branching; check for multiple responsibilities — consider splitting into smaller functions
1. **`Inc=3+` entries** → deep nesting; flatten with early returns or extract a helper function
1. **`continue LABEL` / `break LABEL` entries** → complex loop control; often extractable to a named helper with a clear return value

## Increment Rules (Go-specific)

These constructs **add** to cognitive complexity:

| Construct                                           | Increment                                  |
| --------------------------------------------------- | ------------------------------------------ |
| `if`, `else if`, `else`                             | +1 each                                    |
| `switch`, `select`                                  | +1 (not per case — the whole block is +1)  |
| `for`                                               | +1                                         |
| `goto LABEL`, `break LABEL`, `continue LABEL`       | +1 each                                    |
| Sequence of binary logical operators (`&&`, `\|\|`) | +1 per sequence                            |
| Each method in a recursion cycle                    | +1                                         |
| **Nesting**                                         | +depth for `if`, `switch`, `select`, `for` |

Key examples:

- `switch number { case 1: ... case 2: ... }` → **1** total (one increment for the `switch`)
- `if ... else if ... else if ...` → **3** (one per branch)

## Responding to Diagnostic Patterns

**Pattern: high `Inc` at deep nesting → flatten with early returns**

```go
// Before: complexity 6 (deep nesting)
func Process(s *State) error {
	if s != nil { // +1
		if s.Ready { // +2 (nesting=1)
			if err := s.Run(); err != nil { // +3 (nesting=2)
				return err
			}
		}
	}
	return nil
}

// After: complexity 3 (early returns eliminate nesting)
func Process(s *State) error {
	if s == nil { // +1
		return nil
	}
	if !s.Ready { // +1
		return nil
	}
	if err := s.Run(); err != nil { // +1
		return err
	}
	return nil
}
```

**Pattern: `if/else if` chain → `switch` (fewer branches, lower score)**

```go
// Before: complexity 4
func Label(n int) string {
	if n == 1 { // +1
		return "one"
	} else if n == 2 { // +1
		return "two"
	} else if n == 3 { // +1
		return "three"
	} else { // +1
		return "many"
	}
}

// After: complexity 1
func Label(n int) string {
	switch n { // +1 (whole block — not per case)
	case 1:
		return "one"
	case 2:
		return "two"
	case 3:
		return "three"
	default:
		return "many"
	}
}
```

**Compare before/after:** Always rerun `gocognit -json -over 15 ./...` after refactoring to confirm
the score dropped — and that you haven't accidentally shifted complexity into a helper function.

## Ignoring Functions

Skip functions that are intentionally complex (generated parsers, large state machines, etc.):

```go
//gocognit:ignore
func GeneratedParser() {
	// tool-generated — complexity not meaningful here
}
```

Or ignore whole files by path pattern:

```bash
gocognit -ignore "_generated|pb.go" ./...
```

## CI Integration

```yaml
# GitHub Actions — gate on complexity > 15
  - name: Check cognitive complexity
    run: |
      go install github.com/uudashr/gocognit/cmd/gocognit@latest
      gocognit -over 15 ./...
```

```makefile
# Makefile target
.PHONY: complexity
complexity:
	gocognit -over 15 -avg ./...
```

## Common Mistakes

| Mistake                                      | Reality                                                                                                |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Treating score as a bug signal               | `gocognit` measures readability, not correctness. A score of 30 means "hard to follow" — not "broken". |
| Optimizing the number, not the code          | If a refactor reduces the score but makes the logic harder to follow, it's the wrong refactor.         |
| Scanning with `.` and assuming full coverage | `.` is non-recursive — it only checks the current directory. Use `./...` for module-wide analysis.     |
| Forgetting generated/vendored files          | Generated code is legitimately complex; use `-ignore "_generated\|vendor"` to exclude it.              |
| Refactoring before checking diagnostics      | Always run `-d` first — it tells you *which* lines to change, not just that the score is high.         |
| Comparing gocognit scores to gocyclo scores  | Cognitive and cyclomatic complexity are different metrics with different scales; don't mix thresholds. |

## What gocognit Does NOT Tell You

- **Correctness:** A function with score 2 can still be buggy.
- **Performance:** Low complexity does not mean fast code.
- **Test coverage:** A simple function can be completely untested.
- **Architecture:** gocognit operates at function granularity; it cannot identify problematic module boundaries.

Use it alongside `go vet`, `golangci-lint`, and test coverage tools — not as a replacement.

## References

- [Installation guide](references/installation.md)
- [gocognit source and README](https://github.com/uudashr/gocognit)
- [Cognitive Complexity whitepaper](https://www.sonarsource.com/docs/CognitiveComplexity.pdf) — G. Ann Campbell, SonarSource
