---
name: golang-urfave-v2-to-v3
description: A practical, pattern-complete guide for migrating Go projects from urfave/cli v2 to v3, derived from the official migration guide plus real-world gotchas discovered during production migration.
---

# urfave/cli v2 → v3 Migration Guide (AI Agent Reference)

## When to Use

- Migrating a Go project from `github.com/urfave/cli/v2` to `github.com/urfave/cli/v3`
- Fixing compiler errors after a v2→v3 import path update
- The project uses `cli.App`, `*cli.Context`, `EnvVars`, or `HasBeenSet` — all removed or changed in v3
- Integrating viper or custom `FlagValue` adapters after migrating to v3

## When NOT to Use

- urfave/cli v1 → v2 migrations (different breaking changes)
- Other Go CLI libraries (cobra, kingpin, flag) — not applicable
- Projects already on v3 that just need usage guidance (the migration guide contains both v2 and v3 patterns)

A practical, pattern-complete guide for migrating Go projects from `github.com/urfave/cli/v2` to `github.com/urfave/cli/v3`. Derived from the official migration guide **plus** real-world gotchas discovered during production migration.

______________________________________________________________________

## Table of Contents

1. [Quick Checklist](#quick-checklist)
1. [Step 1 — Update go.mod](#step-1--update-gomod)
1. [Step 2 — Update All Imports](#step-2--update-all-imports)
1. [Step 3 — cli.App → cli.Command](#step-3--cliapp--clicommand)
1. [Step 4 — Handler Function Signatures](#step-4--handler-function-signatures)
1. [Step 5 — Flag Definitions](#step-5--flag-definitions)
1. [Step 6 — cli.Context → cli.Command](#step-6--clicontext--clicommand)
1. [Step 7 — Run the App](#step-7--run-the-app)
1. [Step 8 — Authors Field](#step-8--authors-field)
1. [Step 9 — Shell Completion](#step-9--shell-completion)
1. [Step 10 — cli.Command.Subcommands → Commands](#step-10--clicommandsubcommands--commands)
1. [Non-Obvious Gotchas](#non-obvious-gotchas)
   - [Viper Adapter / Custom FlagValue Integration](#viper-adapter--custom-flagvalue-integration)
   - [DocGenerationFlag Interface Change](#docgenerationflag-interface-change)
   - [HasBeenSet Field Removed](#hasbeenset-field-removed)
   - [StringSliceFlag Default Value](#stringsliceflag-default-value)
   - [Accessing App Name/Version from Action](#accessing-app-nameversion-from-action)
   - [EnvVars on Flag Structs Are Gone](#envvars-on-flag-structs-are-gone)
1. [Full Before/After Examples](#full-beforeafter-examples)
1. [Migration Verification Checklist](#migration-verification-checklist)

______________________________________________________________________

## Quick Checklist

Before starting, grep for all files that need changes:

```bash
grep -rl "github.com/urfave/cli/v2" .
```

Items to migrate per file:

- [ ] Import path: `cli/v2` → `cli/v3`
- [ ] `cli.App{}` → `cli.Command{}`
- [ ] `*cli.App` return/param types → `*cli.Command`
- [ ] `EnableBashCompletion` → `EnableShellCompletion`
- [ ] `Authors: []*cli.Author{...}` → `Authors: []any{mail.Address{...}}`
- [ ] `app.RunContext(ctx, args)` → `app.Run(ctx, args)`
- [ ] All `ActionFunc`: `func(*cli.Context) error` → `func(context.Context, *cli.Command) error`
- [ ] All flag `Action`: `func(*cli.Context, T) error` → `func(context.Context, *cli.Command, T) error`
- [ ] All flag `EnvVars: []string{...}` → `Sources: cli.EnvVars(...)`
- [ ] All flag `FilePath: "..."` → `Sources: cli.Files("...")`
- [ ] `*cli.Context` everywhere → `*cli.Command`
- [ ] `c.Context` field → first `context.Context` param
- [ ] `c.App.Name / c.App.Version` → `c.Root().Name / c.Root().Version`
- [ ] `cli.Command.Subcommands: []*cli.Command` → `Commands: []*cli.Command`
- [ ] `cli.DocGenerationFlag` usage — `Names()` no longer on this interface
- [ ] `HasBeenSet: true` — remove (field no longer exists)
- [ ] `cli.NewStringSlice(...)` → `[]string{...}` for `StringSliceFlag.Value`
- [ ] Any custom `viper.FlagValue` adapter — fix `ValueString()` to use type-specific methods
- [ ] `.EnvVars[0]` direct field access — replace with constants

______________________________________________________________________

## Step 1 — Update go.mod

```diff
-require github.com/urfave/cli/v2 v2.x.x
+require github.com/urfave/cli/v3 v3.3.2
```

Then fetch:

```bash
go get github.com/urfave/cli/v3@v3.3.2
go mod tidy
```

______________________________________________________________________

## Step 2 — Update All Imports

Every file that imports `cli/v2` must change:

```diff
-import "github.com/urfave/cli/v2"
+import "github.com/urfave/cli/v3"
```

Batch-replace across the project:

```bash
find . -name "*.go" -exec sed -i '' \
  's|github.com/urfave/cli/v2|github.com/urfave/cli/v3|g' {} +
```

______________________________________________________________________

## Step 3 — cli.App → cli.Command

In v3, `cli.App` was renamed to `cli.Command`. The root command of the application is now just a `*cli.Command`.

```diff
-func newApp() *cli.App {
-    return &cli.App{
+func newApp() *cli.Command {
+    return &cli.Command{
         Name:    "myapp",
         Version: AppVersion,
         // ...
     }
 }
```

______________________________________________________________________

## Step 4 — Handler Function Signatures

**All handler functions now receive `(context.Context, *cli.Command)` as the first two arguments.**

### ActionFunc

```diff
-func myAction(c *cli.Context) error {
+func myAction(ctx context.Context, c *cli.Command) error {
```

### Flag Action callbacks

```diff
-Action: func(c *cli.Context, s string) error {
+Action: func(_ context.Context, c *cli.Command, s string) error {
```

This applies to every `*Flag` type: `StringFlag`, `BoolFlag`, `UintFlag`, `DurationFlag`, etc.

### BeforeFunc / AfterFunc

```diff
-Before: func(c *cli.Context) error {
+Before: func(ctx context.Context, c *cli.Command) (context.Context, error) {

-After: func(c *cli.Context) error {
+After: func(ctx context.Context, c *cli.Command) error {
```

### Other handler types

| v2                                  | v3                                                       |
| ----------------------------------- | -------------------------------------------------------- |
| `func(*Context) error`              | `func(context.Context, *cli.Command) error`              |
| `func(*Context, string) error`      | `func(context.Context, *cli.Command, string) error`      |
| `func(*Context, error, bool) error` | `func(context.Context, *cli.Command, error, bool) error` |

______________________________________________________________________

## Step 5 — Flag Definitions

### EnvVars → Sources

**This is the most pervasive change.** Every `EnvVars: []string{...}` on a flag must be replaced:

```diff
-&cli.StringFlag{
-    Name:    "postgres-host",
-    EnvVars: []string{"POSTGRES_HOST"},
-}
+&cli.StringFlag{
+    Name:    "postgres-host",
+    Sources: cli.EnvVars("POSTGRES_HOST"),
+}
```

Multiple env vars:

```diff
-EnvVars: []string{"S3_BUCKET", "MINIO_BUCKET"},
+Sources: cli.EnvVars("S3_BUCKET", "MINIO_BUCKET"),
```

### FilePath → Sources

```diff
-&cli.StringFlag{
-    Name:     "config",
-    FilePath: "/etc/app/config",
-}
+&cli.StringFlag{
+    Name:    "config",
+    Sources: cli.Files("/etc/app/config"),
+}
```

### Combining Sources (EnvVars + Files + altsrc)

In v3, `Sources` replaces all of `EnvVars`, `FilePath`, and `altsrc`. The first source that provides a non-empty value wins (order matters):

```go
Sources: cli.NewValueSourceChain(
    cli.EnvVar("APP_LANG"),    // checked first
    cli.File("/path/to/foo"),  // checked second
),
```

### Remove HasBeenSet

The `HasBeenSet` exported field no longer exists in v3. **Remove it from all flag definitions.**

```diff
 &cli.BoolFlag{
     Name:       "diagnostic",
-    HasBeenSet: true,
     Destination: &Diagnostic,
 }
```

> **Why this mattered:** In v2, setting `HasBeenSet: true` made `flag.IsSet()` always return `true`, which caused viper (and similar adapters) to treat every flag as explicitly set. After removing it, `IsSet()` only returns `true` when the flag was explicitly provided via CLI/env. See the [Viper Gotcha](#viper-adapter--custom-flagvalue-integration) for the fix this requires.

### StringSliceFlag Default Value

```diff
-Value: cli.NewStringSlice("default@example.com"),
+Value: []string{"default@example.com"},
```

### PathFlag → StringFlag with TakesFile

```diff
-&cli.PathFlag{Name: "output"}
+&cli.StringFlag{Name: "output", TakesFile: true}
```

### TimestampFlag Layout → Config

```diff
-&cli.TimestampFlag{
-    Name:   "expires",
-    Layout: time.RFC3339,
-}
+&cli.TimestampFlag{
+    Name: "expires",
+    Config: cli.TimestampConfig{
+        Layouts: []string{time.RFC3339},
+    },
+}
```

______________________________________________________________________

## Step 6 — cli.Context → cli.Command

`cli.Context` has been **removed**. All methods it had are now on `*cli.Command`.

| v2                                        | v3                                               |
| ----------------------------------------- | ------------------------------------------------ |
| `c.String("name")`                        | `c.String("name")` ✓ same                        |
| `c.Bool("name")`                          | `c.Bool("name")` ✓ same                          |
| `c.Int("name")`                           | `c.Int("name")` ✓ same                           |
| `c.StringSlice("name")`                   | `c.StringSlice("name")` ✓ same                   |
| `c.IsSet("name")`                         | `c.IsSet("name")` ✓ same                         |
| `c.Context` (the `context.Context` field) | First `ctx context.Context` param in the handler |
| `c.App.Name`                              | `c.Root().Name`                                  |
| `c.App.Version`                           | `c.Root().Version`                               |
| `c.Lineage()`                             | `c.Lineage()` ✓ same                             |
| `c.Args()`                                | `c.Args()` ✓ same                                |
| `c.NArg()`                                | `c.NArg()` ✓ same                                |

### c.Context → ctx parameter

In v2, context was accessed via `c.Context`. In v3, context is passed directly as the first argument to all handler functions.

```diff
-func myAction(c *cli.Context) error {
-    ctx := c.Context
+func myAction(ctx context.Context, c *cli.Command) error {
     // use ctx directly
```

______________________________________________________________________

## Step 7 — Run the App

```diff
-if err := app.RunContext(ctx, os.Args); err != nil {
+if err := app.Run(ctx, os.Args); err != nil {
```

The old `Run(args)` (without context) is gone. `Run(ctx, args)` is the only signature in v3.

______________________________________________________________________

## Step 8 — Authors Field

```diff
+import "net/mail"

-Authors: []*cli.Author{
-    {Name: "Alice", Email: "alice@example.com"},
-},
+Authors: []any{
+    mail.Address{Name: "Alice", Address: "alice@example.com"},
+},
```

Note the field rename: `Email` → `Address` (matching `net/mail.Address`).

______________________________________________________________________

## Step 9 — Shell Completion

```diff
-EnableBashCompletion: true,
+EnableShellCompletion: true,
```

______________________________________________________________________

## Step 10 — cli.Command.Subcommands → Commands

```diff
 &cli.Command{
     Name: "server",
-    Subcommands: []*cli.Command{
+    Commands: []*cli.Command{
         {Name: "start"},
         {Name: "stop"},
     },
 }
```

______________________________________________________________________

## Non-Obvious Gotchas

### Viper Adapter / Custom FlagValue Integration

> **This is the most critical non-obvious issue.** If your project integrates `github.com/spf13/viper` via a custom `viper.FlagValue` adapter, you **must** fix `ValueString()`.

**The problem:** In v2, calling `c.String(name)` on any flag (even non-string types like `UintFlag`, `DurationFlag`, `BoolFlag`) would resolve the flag's underlying `flag.Value.String()` method via the `fmt.Stringer` interface, returning the correct string representation (e.g., `"5432"`, `"1m0s"`, `"true"`).

In v3, `c.String(name)` **only works for StringFlag**. For any other flag type it returns `""`.

This means a naive adapter returns empty strings for numeric and duration fields, causing viper to fail with errors like:

```
'minio.shareLinkTTL' time: invalid duration
'metrics.pushgateway.interval' time: invalid duration
```

**The fix:** Use type-specific methods on `*cli.Command`:

```go
// v2 adapter (broken in v3)
func (s *viperFlagAdapter) ValueString() string {
    return s.c.String(s.Name()) // returns "" for non-string flags in v3
}

// v3 adapter (correct)
func (s *viperFlagAdapter) ValueString() string {
    name := s.Name()
    switch s.flag.(type) {
    case *cli.BoolFlag:
        return strconv.FormatBool(s.c.Bool(name))
    case *cli.IntFlag:
        return strconv.Itoa(s.c.Int(name))
    case *cli.Int64Flag:
        return strconv.FormatInt(s.c.Int64(name), 10)
    case *cli.UintFlag:
        return strconv.FormatUint(uint64(s.c.Uint(name)), 10)
    case *cli.Uint64Flag:
        return strconv.FormatUint(s.c.Uint64(name), 10)
    case *cli.Float64Flag:
        return strconv.FormatFloat(s.c.Float64(name), 'f', -1, 64)
    case *cli.DurationFlag:
        return s.c.Duration(name).String()
    default:
        return s.c.String(name)
    }
}
```

Also update the adapter struct and constructor to use `*cli.Command` instead of `*cli.Context`:

```diff
 type viperFlagAdapter struct {
-    c    *cli.Context
+    c    *cli.Command
     flag cli.Flag
 }

-func UrfaveFlagAdapter(c *cli.Context) AdapterFunc {
+func UrfaveFlagAdapter(c *cli.Command) AdapterFunc {
```

______________________________________________________________________

### DocGenerationFlag Interface Change

In v2, `cli.DocGenerationFlag` included a `Names() []string` method. In v3, `Names()` was moved to the base `cli.Flag` interface, and `DocGenerationFlag` no longer has it.

**If you cast to `cli.DocGenerationFlag` and call `Names()`:**

```diff
-flag0 := Flags[i].(cli.DocGenerationFlag)
-name := flag0.Names()[0]          // compile error in v3
-envVars := flag0.GetEnvVars()

+flag0 := Flags[i]                          // cli.Flag has Names()
+flag0Doc := flag0.(cli.DocGenerationFlag)  // only for GetEnvVars()
+name := flag0.Names()[0]                   // works
+envVars := flag0Doc.GetEnvVars()           // works
```

> `GetEnvVars()` on `DocGenerationFlag` still works correctly in v3 even though env vars are now declared via `Sources: cli.EnvVars(...)`.

______________________________________________________________________

### HasBeenSet Field Removed

In v2, many codebases set `HasBeenSet: true` on flags to force `flag.IsSet()` to return `true`. This is an exported field in v2 but **does not exist in v3** (it became unexported `hasBeenSet`).

Consequences:

1. **Remove it** from all flag struct literals — it will cause a compile error otherwise.
1. **Audit any `viper.FlagValue` adapter** — previously `HasChanged()` always returned `true` (via `HasBeenSet: true` → `IsSet() = true`), making viper treat every flag as explicitly set. After removal, `HasChanged()` returns `true` only when the flag was actually set by the user. Ensure viper still receives correct default values (see [Viper Adapter](#viper-adapter--custom-flagvalue-integration)).

______________________________________________________________________

### StringSliceFlag Default Value

```diff
-Value: cli.NewStringSlice("a@example.com", "b@example.com"),
+Value: []string{"a@example.com", "b@example.com"},
```

`cli.NewStringSlice` is gone. `StringSliceFlag.Value` is now a plain `[]string`.

______________________________________________________________________

### Accessing App Name/Version from Action

In v2, the app name was accessible via `c.App.Name`. In v3, since there is no `App`, use `c.Root()` which returns the root `*cli.Command`:

```diff
-PrometheusJob = c.App.Name
+PrometheusJob = c.Root().Name
```

For a flat (single-command) app where the action is on the root command, `c.Root()` is identical to `c`. But using `c.Root()` is explicit and correct for both cases.

______________________________________________________________________

### EnvVars on Flag Structs Are Gone

In v2, flag structs had an `EnvVars []string` field that you could read programmatically:

```go
// v2 — direct field access
envVar := flags.MyFlag.EnvVars[0]
conf.BindEnv("key", envVar)
```

In v3, there is no `EnvVars` field — env vars are inside `Sources`. Attempting to access `.EnvVars` is a **compile error**.

**The fix:** Define package-level constants for env var names and use them in both the flag definition and any programmatic access:

```go
// constants.go (or in the same flags file)
const (
    DiagnosticEnvVar      = "DIAGNOSTIC_ENABLED"
    DiagnosticEmailsEnvVar = "DIAGNOSTIC_EMAILS"
)

// flag definition
DiagnosticFlag = &cli.BoolFlag{
    Sources: cli.EnvVars(DiagnosticEnvVar),
}

// programmatic access (viper, etc.)
conf.BindEnv("diagnostic.enabled", DiagnosticEnvVar)
```

You can still retrieve env vars at runtime via `cli.DocGenerationFlag`:

```go
envVars := flag.(cli.DocGenerationFlag).GetEnvVars()
```

______________________________________________________________________

## Full Before/After Examples

### main.go (app setup + action)

```go
// ── v2 ──────────────────────────────────────────────────
import "github.com/urfave/cli/v2"

func newApp() *cli.App {
    return &cli.App{
        Name:                 "myapp",
        Version:              AppVersion,
        EnableBashCompletion: true,
        Authors: []*cli.Author{
            {Name: "Alice", Email: "alice@example.com"},
        },
        Action: myAction,
    }
}

func myAction(c *cli.Context) error {
    ctx := c.Context
    _ = ctx
    return doWork(c.String("config"))
}

// in main():
app.RunContext(ctx, os.Args)
```

```go
// ── v3 ──────────────────────────────────────────────────
import (
    "net/mail"
    "github.com/urfave/cli/v3"
)

func newApp() *cli.Command {
    return &cli.Command{
        Name:                  "myapp",
        Version:               AppVersion,
        EnableShellCompletion: true,
        Authors: []any{
            mail.Address{Name: "Alice", Address: "alice@example.com"},
        },
        Action: myAction,
    }
}

func myAction(ctx context.Context, c *cli.Command) error {
    return doWork(c.String("config"))
}

// in main():
app.Run(ctx, os.Args)
```

______________________________________________________________________

### Flag definition (all patterns)

```go
// ── v2 ──────────────────────────────────────────────────
&cli.StringFlag{
    Name:       "postgres-host",
    HasBeenSet: true,
    EnvVars:    []string{"POSTGRES_HOST", "PG_HOST"},
    Action: func(c *cli.Context, s string) error {
        return validate(s)
    },
}

&cli.BoolFlag{
    Name:       "verbose",
    HasBeenSet: true,
    EnvVars:    []string{"VERBOSE"},
}

&cli.DurationFlag{
    Name:       "timeout",
    HasBeenSet: true,
    EnvVars:    []string{"TIMEOUT"},
}

&cli.StringSliceFlag{
    Name:  "recipients",
    Value: cli.NewStringSlice("a@b.com"),
}
```

```go
// ── v3 ──────────────────────────────────────────────────
&cli.StringFlag{
    Name:    "postgres-host",
    Sources: cli.EnvVars("POSTGRES_HOST", "PG_HOST"),
    Action: func(_ context.Context, _ *cli.Command, s string) error {
        return validate(s)
    },
}

&cli.BoolFlag{
    Name:    "verbose",
    Sources: cli.EnvVars("VERBOSE"),
}

&cli.DurationFlag{
    Name:    "timeout",
    Sources: cli.EnvVars("TIMEOUT"),
}

&cli.StringSliceFlag{
    Name:  "recipients",
    Value: []string{"a@b.com"},
}
```

______________________________________________________________________

## Migration Verification Checklist

Run these after applying all changes:

```bash
# Must produce zero output (no v2 imports remaining)
grep -r "cli/v2" . --include="*.go"

# Must compile cleanly
go build ./...

# Must pass all tests
go test ./...

# Must tidy cleanly
go mod tidy && git diff go.mod go.sum
```

**Common compiler errors and their fixes:**

| Error                                                                            | Fix                                                                       |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `undefined: cli.App`                                                             | Change to `cli.Command`                                                   |
| `undefined: cli.Author`                                                          | Use `mail.Address` from `net/mail`                                        |
| `undefined: cli.Context`                                                         | Change to `*cli.Command` in params; use `ctx context.Context` for context |
| `undefined: cli.NewStringSlice`                                                  | Use `[]string{...}` directly                                              |
| `unknown field HasBeenSet`                                                       | Remove the field                                                          |
| `unknown field EnvVars`                                                          | Replace with `Sources: cli.EnvVars(...)`                                  |
| `cannot use func literal (type func(*cli.Context) error) as type cli.ActionFunc` | Update signature to `func(context.Context, *cli.Command) error`           |
| `app.RunContext undefined`                                                       | Replace with `app.Run(ctx, args)`                                         |
| `c.App undefined`                                                                | Replace with `c.Root()`                                                   |
| `flag.EnvVars undefined`                                                         | Replace direct field access with constants                                |
| `DocGenerationFlag has no field or method Names`                                 | Use `flag.(cli.Flag).Names()` or just `flag.Names()`                      |

**Common runtime errors and their fixes:**

| Error                                                     | Fix                                                                             |
| --------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `time: invalid duration` on viper Unmarshal               | Fix `ValueString()` in viper adapter to use `c.Duration(name).String()`         |
| `decoding failed: ... invalid duration / uint`            | Same — `ValueString()` returning `""` for non-string flags                      |
| Nil pointer on `appConfig.XxxField` after viper Unmarshal | Check if condition after `Unmarshal` is inverted (`err == nil` vs `err != nil`) |
