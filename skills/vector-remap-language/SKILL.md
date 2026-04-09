---
name: vector-remap-language
description: Use when writing, debugging, validating, or reviewing Vector Remap Language (VRL) scripts for data transformation in Vector pipelines. Triggers on VRL syntax questions, compile-time errors (100-900), fallible function handling, type coercion, path expressions, event manipulation, or VRL CLI usage. Covers the standalone `vrl` CLI for validation, REPL, and script execution.
metadata:
  author: d.horkhover
  version: 2.1.0
---

# Vector Remap Language (VRL)

## Overview

VRL is an **expression-oriented**, **fail-safe**, **stateless** language for transforming observability data in [Vector](https://vector.dev) pipelines. Every expression returns a value. All errors must be handled at compile time. No custom functions, no recursion, no I/O, no state across events.

## When to Use

- Writing `remap` transforms in Vector config
- Debugging VRL compile-time errors (codes 100–900)
- Validating VRL scripts with the standalone `vrl` CLI
- Parsing logs (syslog, JSON, key-value, custom formats)
- Coercing types, enriching events, routing data
- Understanding VRL's type safety and error handling model
- Interactive VRL development via the REPL

## When NOT to Use

- **Vector pipeline configuration** (sources, sinks, routing topology) — VRL only covers the `remap` transform layer, not Vector's YAML/TOML pipeline config
- **Stateful aggregation** — VRL is stateless per-event; use Vector's `reduce` transform for multi-event aggregation, windowing, or session tracking
- **Custom function authoring** — VRL has no user-defined functions or recursion; if you need reusable logic across transforms, compose Vector transforms instead
- **General scripting or automation** — VRL is not a general-purpose language; use Python, Bash, or another scripting language for tasks outside event transformation
- **Vector installation, source/sink config, or pipeline topology questions** — these are Vector concerns, not VRL

## VRL CLI — Standalone Validation and Execution

The `vrl` binary (built from the VRL project at https://github.com/vectordotdev/vrl) provides a standalone CLI for validating, running, and interactively developing VRL scripts — independent of Vector itself.

### CLI Usage

```bash
# Interactive REPL (no arguments)
vrl

# Execute inline program
vrl '.foo = downcase(.bar)'

# Execute inline program with JSON input
vrl '.parsed = parse_json!(.message)' --input event.json

# Execute program from file
vrl --program my_script.vrl

# Execute program from file with input
vrl --program my_script.vrl --input events.jsonl

# Validate only (compilation errors printed with diagnostics)
vrl --program my_script.vrl

# Print modified event object instead of final expression result
vrl --program my_script.vrl --input event.json --print-object

# Show compilation warnings
vrl --program my_script.vrl --print-warnings

# Set timezone for date parsing
vrl --program my_script.vrl --timezone "America/New_York"

# Quiet mode (suppress REPL banners)
vrl -q
```

### CLI Options

| Flag                  | Short | Description                                             |
| --------------------- | ----- | ------------------------------------------------------- |
| `PROGRAM`             |       | Inline VRL program to execute                           |
| `--program <FILE>`    | `-p`  | File containing VRL program                             |
| `--input <FILE>`      | `-i`  | JSON input file (one event per line)                    |
| `--print-object`      | `-o`  | Print modified event instead of final expression result |
| `--timezone <TZ>`     | `-z`  | Timezone for date parsing                               |
| `--runtime <RUNTIME>` | `-v`  | Runtime to use (default: ast)                           |
| `--print-warnings`    |       | Emit compilation warnings                               |
| `--quiet`             | `-q`  | Suppress REPL banners                                   |

### Input Format

The `--input` file expects one JSON object per line (JSONL):

```json lines
{"message": "2024-01-15 ERROR failed to connect", "host": "web-01"}
{"message": "2024-01-15 INFO request completed", "host": "web-02"}
```

When no input is provided, the CLI uses an empty object `{}` as the event.

### Validation Workflow

The `vrl` CLI compiles the program before execution. If compilation fails, it prints rich diagnostic output with error codes, source spans, and suggestions — then exits with a non-zero code. This makes it suitable for CI/CD validation:

```bash
# Validate all VRL scripts in a directory
for f in scripts/*.vrl; do
  vrl --program "$f" < /dev/null || echo "FAIL: $f"
done
```

### REPL

Running `vrl` with no program argument opens an interactive REPL where you can:

- Test VRL expressions against a live event object
- Iterate on transformations interactively
- Provide initial event data with `--input`

#### REPL Commands

| Command             | Description                                                                                                       |
| ------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `help`              | Show available REPL commands                                                                                      |
| `help functions`    | Display a table of all available VRL functions (aliases: `help funcs`, `help fs`)                                 |
| `help docs`         | Open the VRL docs website in your browser                                                                         |
| `help docs <func>`  | Open browser docs for a specific function (e.g. `help docs parse_json`)                                           |
| `help error <code>` | Open browser docs for a specific error code (e.g. `help error 103`) — resolves to `https://errors.vrl.dev/<code>` |
| `next`              | Load the next input event (or create a new empty one)                                                             |
| `prev`              | Load the previous input event                                                                                     |
| `exit` / `quit`     | Terminate the REPL                                                                                                |

#### REPL Multi-Event Workflow

When you pass a JSONL file with multiple events via `--input`, the REPL loads the first one. Use `next` and `prev` to cycle through events:

```bash
# Start REPL with a file containing multiple events
vrl --input events.jsonl

# In the REPL:
$ .              # inspect current event
$ next           # advance to next event
$ prev           # go back to previous event
```

The REPL supports:

- **Tab completion** for function names
- **History hints** (inline completion of previous commands)
- **Bracket matching** highlighting
- **Multi-line expressions** — incomplete expressions (e.g. open `if`) are detected and continuation is prompted automatically

## Core Concepts

### Events

VRL operates on a single **event** (log or metric) at a time. Access fields via path expressions:

```coffee
# Event root
.message           # top-level field
.host.name         # nested field
.tags[0]           # array index
.tags[0].name      # nested in array

# Metadata
%custom_metadata_field
```

> **Metadata writability**: In `remap` transforms, `%field` metadata paths are **read-only** by default.
> They are writable in `log_to_metric` and certain other Vector transform contexts. Attempting to write
> `%field` in a `remap` transform produces error 315 (ReadOnly).

### Data Types

| Type      | Literal        | Example                                  |
| --------- | -------------- | ---------------------------------------- |
| String    | `"..."`        | `"hello"`, `"template: {{ .name }}"`     |
| Integer   | digits         | `42`, `-7`                               |
| Float     | digits.digits  | `3.14`                                   |
| Boolean   | `true`/`false` | `true`                                   |
| Null      | `null`         | `null`                                   |
| Array     | `[...]`        | `[1, "two", true]`                       |
| Object    | `{...}`        | `{"key": "value"}`                       |
| Regex     | `r'...'`       | `r'\d{4}-\d{2}-\d{2}'`                   |
| Timestamp | `t'...'`       | `t'2021-02-11T10:32:50.553Z'` (RFC 3339) |

### String Templates

```coffee
name = "world"
greeting = "Hello, {{ name }}!"  # "Hello, world!"
```

### Expressions

VRL is expression-oriented — everything returns a value:

```coffee
# If/else returns a value
severity = if .level == "error" { "high" } else { "low" }

# Block returns last expression
result = {
    x = 1
    y = 2
    x + y  # returns 3
}

# Coalesce returns first non-null/non-error
val = .primary ?? .fallback ?? "default"
```

### Operators

| Op                          | Description         | Example             |
| --------------------------- | ------------------- | ------------------- |
| `+` `-` `*` `/` `%`         | Arithmetic          | `.count + 1`        |
| `==` `!=` `<` `>` `<=` `>=` | Comparison          | `.status >= 400`    |
| `&&` `\|\|` `!`             | Logical             | `.a && !.b`         |
| `??`                        | Null/error coalesce | `.x ?? "default"`   |
| `!` (suffix)                | Abort on error      | `parse_json!(.msg)` |

### Keywords

`if`, `else`, `for`, `while`, `abort`, `true`, `false`, `null`

> `for` and `while` exist as keywords but loops are done via iteration functions like `for_each`.

## Type System — Progressive Type Safety

VRL narrows types as expressions execute:

```coffee
# .value starts as "any"
.value = parse_json!(.raw)    # now: any JSON type
if is_string(.value) {
    .value = upcase(.value)   # compiler knows it's string here; upcase is infallible
}
```

**Type coercion functions** (all prefixed with `to_`):

- `to_string`, `to_int`, `to_float`, `to_bool`, `to_timestamp`
- All are fallible — must handle errors

```coffee
.count = to_int!(.count_str)          # abort on failure
.count = to_int(.count_str) ?? 0      # default on failure
.count, err = to_int(.count_str)      # capture error
```

## Error Handling — The Critical Pattern

VRL's defining feature: **all fallible expressions must have errors handled at compile time**.

### Fallible vs Infallible

Functions marked as **fallible** can fail at runtime. The compiler enforces handling:

```coffee
# ERROR 103: unhandled fallible assignment
.parsed = parse_json(.raw)         # WON'T COMPILE

# Three ways to handle:

# 1. Abort on error (suffix !)
.parsed = parse_json!(.raw)        # drops event on failure

# 2. Coalesce (??)
.parsed = parse_json(.raw) ?? {}   # fallback value

# 3. Assign error
.parsed, err = parse_json(.raw)    # err is null on success
if err != null {
    log("Parse failed: " + err, level: "error")
}
```

### Compile-Time Error Codes (Complete Reference)

Sourced from the VRL compiler source code. Each error code links to `https://errors.vrl.dev/<code>` — accessible from the REPL with `help error <code>`.

#### Parser Errors (200–210)

| Code | Error                | Description                           |
| ---- | -------------------- | ------------------------------------- |
| 200  | InvalidToken         | Invalid token in source               |
| 201  | ExtraToken           | Unexpected extra token                |
| 202  | UserParseError       | User-triggered parse error            |
| 203  | UnrecognizedToken    | Unrecognized token in source          |
| 204  | UnrecognizedEof      | Unexpected end of input               |
| 205  | ReservedKeyword      | Use of reserved keyword as identifier |
| 206  | NumericLiteral       | Invalid numeric literal               |
| 207  | StringLiteral        | Invalid string literal                |
| 208  | Literal              | Invalid literal                       |
| 209  | EscapeChar           | Invalid escape character              |
| 210  | UnexpectedParseError | Unexpected parser error               |

#### Literal Errors

| Code | Error            | Description                           |
| ---- | ---------------- | ------------------------------------- |
| 101  | InvalidRegex     | Malformed regex literal in `r'...'`   |
| 601  | InvalidTimestamp | Invalid timestamp literal in `t'...'` |
| 602  | NanFloat         | NaN float literal                     |

#### Predicate / Boolean Errors

| Code | Error                | Description                              |
| ---- | -------------------- | ---------------------------------------- |
| 102  | NonBoolean predicate | If-condition does not resolve to boolean |
| 660  | NonBoolean negation  | `!` applied to non-boolean expression    |

#### Assignment Errors

| Code | Error                    | Description                                                 |
| ---- | ------------------------ | ----------------------------------------------------------- |
| 103  | FallibleAssignment       | Unhandled fallible assignment — use `!`, `??`, or `, err =` |
| 104  | InfallibleAssignment     | Unnecessary error handling on infallible call               |
| 315  | ReadOnly                 | Attempt to write to a read-only path                        |
| 640  | UnnecessaryNoop          | No-op assignment has no effect                              |
| 641  | InvalidTarget            | Invalid assignment target                                   |
| 642  | InvalidParentPathSegment | Invalid parent path segment in assignment                   |

#### Function Call Errors

| Code | Error                        | Description                                |
| ---- | ---------------------------- | ------------------------------------------ |
| 105  | Undefined                    | Call to undefined function                 |
| 106  | WrongNumberOfArgs            | Wrong number of arguments                  |
| 107  | MissingArgument              | Required argument missing                  |
| 108  | UnknownKeyword               | Unknown keyword argument                   |
| 109  | UnexpectedClosure            | Unexpected closure / grok pattern error    |
| 110  | InvalidArgumentKind          | Invalid argument type                      |
| 111  | MissingClosure               | Required closure not provided              |
| 120  | ClosureArityMismatch         | Closure has wrong number of parameters     |
| 121  | ClosureParameterTypeMismatch | Closure parameter type mismatch            |
| 122  | ReturnTypeMismatch           | Function return type mismatch              |
| 610  | Compilation                  | Function compilation error                 |
| 620  | AbortInfallible              | Abort `!` on infallible function (warning) |
| 630  | FallibleArgument             | Fallible expression used as argument       |

#### Function Argument Errors (400–420)

| Code | Error                    | Description                             |
| ---- | ------------------------ | --------------------------------------- |
| 400  | UnexpectedExpression     | Unexpected expression type for argument |
| 401  | InvalidEnumVariant       | Invalid enum variant for argument       |
| 402  | ExpectedStaticExpression | Argument requires a static expression   |
| 403  | InvalidArgument          | Invalid argument value                  |
| 420  | ExpectedFunctionClosure  | Expected a function closure             |

#### Value / Type Errors (300–316)

| Code | Error            | Description                            |
| ---- | ---------------- | -------------------------------------- |
| 300  | Expected type    | Value type mismatch                    |
| 301  | Coerce           | Type coercion failed                   |
| 302  | Rem              | Remainder type error                   |
| 303  | Mul              | Multiplication type error              |
| 304  | Div              | Division type error                    |
| 305  | DivideByZero     | Division by zero                       |
| 306  | NanFloat         | NaN float in operation                 |
| 307  | Add              | Addition type error                    |
| 308  | Sub              | Subtraction type error                 |
| 309  | Or               | Logical OR type error                  |
| 310  | And              | Logical AND type error                 |
| 311  | Gt               | Greater-than comparison type error     |
| 312  | Ge               | Greater-or-equal comparison type error |
| 313  | Lt               | Less-than comparison type error        |
| 314  | Le               | Less-or-equal comparison type error    |
| 315  | Merge / ReadOnly | Merge type error or read-only path     |
| 316  | OutOfRange       | Value out of range                     |

#### Operator Errors (650–652)

| Code | Error               | Description                              |
| ---- | ------------------- | ---------------------------------------- |
| 650  | ChainedComparison   | Chained comparison operators not allowed |
| 651  | UnnecessaryCoalesce | Unnecessary `??` coalesce                |
| 652  | MergeNonObjects     | `\|=` merge on non-object types          |

#### Other Errors

| Code | Error                        | Description                              |
| ---- | ---------------------------- | ---------------------------------------- |
| 631  | FallibleExpr in return/abort | Return or abort with fallible expression |
| 701  | Undefined variable           | Reference to undefined variable          |
| 801  | DeprecationWarning           | Use of deprecated feature (warning)      |
| 900  | UnusedCode                   | Unused expression result (warning)       |

### Error Handling Decision

```
Fallible function call?
  ├─ Event should be dropped on failure → use `!`  (parse_json!(.raw))
  ├─ Has a sensible default            → use `??` (parse_json(.raw) ?? {})
  └─ Need to handle error explicitly   → use `, err =`
```

### Empty Values by Type

When coalescing, use the correct empty value:

| Type      | Empty Value               |
| --------- | ------------------------- |
| String    | `""`                      |
| Integer   | `0`                       |
| Float     | `0.0`                     |
| Boolean   | `false`                   |
| Array     | `[]`                      |
| Object    | `{}`                      |
| Null      | `null`                    |
| Timestamp | `t'1970-01-01T00:00:00Z'` |

## Common Patterns

### Parse Syslog

```coffee
. = parse_syslog!(.message)
```

### Parse JSON Log

```coffee
. |= object!(parse_json!(.message))
del(.message)
```

### Parse Key-Value (logfmt)

```coffee
. = parse_key_value!(.message)
```

### Multiple Parsing Strategies

```coffee
structured =
    parse_syslog(.message) ??
    parse_common_log(.message) ??
    parse_glog(.message) ??
    parse_klog(.message) ??
    parse_json(.message) ?? {}

. = merge(., structured)
```

### Custom Log Parsing with Regex

```coffee
. |= parse_regex!(.message, r'^(?P<timestamp>\S+) (?P<level>\w+) (?P<msg>.*)$')
.timestamp = parse_timestamp!(.timestamp, format: "%Y-%m-%dT%H:%M:%S%.fZ")
.level = upcase!(.level)
del(.message)
```

### Add/Remove/Rename Fields

```coffee
.environment = "production"             # add
del(.debug_info)                        # remove
.hostname = del(.host)                  # rename (move)
```

### Conditional Processing

```coffee
if .status_code >= 400 && .status_code < 500 {
    .severity = "warning"
} else if .status_code >= 500 {
    .severity = "error"
} else {
    .severity = "info"
}
```

### Metric Tag Modification

```coffee
.tags.environment = "production"
.tags.region = "us-east-1"
del(.tags.debug)
```

### Type Checking and Guards

```coffee
if is_string(.value) {
    .value = upcase(.value)
} else if is_integer(.value) {
    .value = to_string(.value)
}
```

### Iterating Arrays and Objects

VRL has no `for`/`while` loop syntax — use the closure-based iteration functions:

```coffee
# Iterate over array items (side effects only, returns null)
for_each(.tags) -> |_index, tag| {
    log("tag: " + tag, level: "debug")
}

# Transform array values
.tags = map_values(.tags) -> |tag| { upcase(tag) }

# Filter array (keep elements where closure returns true)
.errors = filter(.events) -> |_index, event| {
    event.level == "error"
}

# Iterate over object keys and values
for_each(.labels) -> |key, value| {
    log(key + "=" + value, level: "debug")
}

# Remap object keys
.labels = map_keys(.labels) -> |key| { downcase(key) }

# Remap object values
.headers = map_values(.headers) -> |value| { downcase(value) }
```

> `for`, `while`, and `loop` are reserved keywords but **not usable** as loop constructs.
> All iteration in VRL goes through functions with closures.

### Enrichment with External Data

```coffee
# CSV enrichment (requires enrichment table in Vector config)
row = get_enrichment_table_record!("ips", {"ip": .src_ip})
.geo_city = row.city
.geo_country = row.country
```

## Function Reference

See `vrl-functions.md` in this directory for the comprehensive function reference organized by category (200+ functions across 20+ categories).

| Category    | Key Functions                                                            | Purpose                  |
| ----------- | ------------------------------------------------------------------------ | ------------------------ |
| Parse       | `parse_json`, `parse_syslog`, `parse_regex`, `parse_key_value`           | Log parsing              |
| String      | `upcase`, `downcase`, `contains`, `replace`, `split`, `strip_whitespace` | String manipulation      |
| Object      | `keys`, `values`, `merge`, `set`, `remove`, `flatten`                    | Object manipulation      |
| Array       | `push`, `append`, `filter`, `map_values`, `flatten`                      | Array operations         |
| Coerce      | `to_string`, `to_int`, `to_float`, `to_bool`, `to_timestamp`             | Type conversion          |
| Codec       | `encode_base64`, `decode_base64`, `encode_json`, `decode_gzip`           | Encoding/decoding        |
| Crypto      | `sha2`, `md5`, `hmac`, `encrypt`, `decrypt`                              | Cryptographic ops        |
| IP          | `ip_subnet`, `ip_to_ipv6`, `ip_cidr_contains`                            | IP address handling      |
| Timestamp   | `now`, `format_timestamp`, `parse_timestamp`                             | Time operations          |
| Enrichment  | `get_enrichment_table_record`, `find_enrichment_table_records`           | External data lookup     |
| Diagnostics | `log`, `assert`, `assert_eq`                                             | Debugging and assertions |
| Type        | `is_string`, `is_integer`, `type_def`, `kind`                            | Type introspection       |

## Debugging VRL

### Use `log()` for Runtime Debugging

```coffee
log(.message, level: "debug")
log("parsed value: " + to_string(.count), level: "info")
```

### Use `assert` / `assert_eq` for Invariants

```coffee
assert!(.level != null, message: "level field required")
assert_eq!(.environment, "production")
```

### Common Debugging Workflow

1. Check compile errors — VRL gives specific error codes (see table above)
1. Use the standalone `vrl` CLI to test expressions interactively
1. Add `log()` calls to inspect intermediate values
1. Use `vector vrl` or the standalone `vrl` REPL to iterate
1. Use `vector tap` to inspect events flowing through pipeline

### Validating Scripts with the CLI

```bash
# Quick validation — compilation errors are printed with source context
vrl --program transform.vrl

# Test with sample data
echo '{"message":"test log line"}' | vrl --program transform.vrl --input /dev/stdin

# Test with a file of sample events
vrl --program transform.vrl --input sample_events.jsonl --print-object
```

## Quick Reference Card

```
Path:       .field    .nested.field    .array[0]    %metadata
String:     "hello"   "template: {{ var }}"
Regex:      r'pattern'
Timestamp:  t'2021-02-11T10:32:50Z'
Coalesce:   .x ?? .y ?? "default"
Abort:      parse_json!(.msg)           # ! = abort on error
Assign err: val, err = parse_json(.msg)
Delete:     del(.field)
Merge:      . |= object
Type check: is_string(.x)   is_integer(.x)
Coerce:     to_string!(.x)  to_int!(.x)
Log:        log("debug msg", level: "debug")

CLI:        vrl --program script.vrl --input data.jsonl
REPL:       vrl
Validate:   vrl --program script.vrl
```

## Common Mistakes

### ❌ There is NO `coalesce()` function in VRL

VRL does not have a `coalesce()` function. Use the `??` operator to chain fallbacks:

```coffee
# WRONG — coalesce() does not exist
result = coalesce(parse_syslog(.msg), parse_json(.msg))

# CORRECT — use ?? operator chain
result = parse_syslog(.msg) ?? parse_json(.msg) ?? {}
```

### ❌ Wrong `, err =` syntax

The error variable goes on the LEFT side with the result, not the right:

```coffee
# WRONG
.parsed = parse_json(.raw), err = .raw

# CORRECT — both result and err on the left of =
.parsed, err = parse_json(.raw)
```

### ❌ No string indexing/slicing syntax

VRL has no `string[7:]` or bracket-based string slicing. Use `slice()`:

```coffee
# WRONG — no bracket slicing
.token = .auth_header[7:]

# CORRECT — use slice() function
.token = slice!(.auth_header, 7)
```

### ❌ Error 100 vs 103 confusion

- **Error 103**: Unhandled fallible assignment — a **specific assignment** uses a fallible function without handling
- **Error 630**: Fallible expression used as argument to another function

Both are fixed the same way (`!`, `??`, or `, err =`) but 103 points to a specific line.

### ❌ `parse_key_value` vs `parse_logfmt`

These are **separate functions** — `parse_logfmt` follows the strict logfmt spec (space-delimited, `=` separator, quoted values). `parse_key_value` is more flexible with configurable delimiters:

```coffee
# parse_key_value — flexible, custom delimiters
. = parse_key_value!(.msg)                                    # default: space + =
. = parse_key_value!(.msg, field_delimiter: ",", key_value_delimiter: ":")  # custom

# parse_logfmt — strict logfmt spec only
. = parse_logfmt!(.msg)
```

### ❌ All parse functions require their input as an argument

```coffee
# WRONG — missing argument
. = parse_json()

# CORRECT — pass the field to parse
. = parse_json!(.message)
```

## WebAssembly Support

VRL can be compiled for the `wasm32-unknown-unknown` target:

```sh
cargo check --target wasm32-unknown-unknown --no-default-features --features stdlib
```

Most stdlib functions work in WASM. The following functions **compile but abort at runtime** due to I/O, system calls, or native dependencies:

- `dns_lookup`
- `get_hostname`
- `http_request`
- `log`
- `parse_grok` / `parse_groks`
- `reverse_dns`
- `validate_json_schema`

The `datadog_grok` feature is **excluded entirely** when targeting `wasm32`.

## Feature Flags

The VRL crate uses Cargo feature flags to control which function groups are available. Relevant flags:

| Feature                    | Functions enabled                                           |
| -------------------------- | ----------------------------------------------------------- |
| `enable_env_functions`     | `get_env_var`                                               |
| `enable_system_functions`  | `get_hostname`, `get_timezone_name`, `now`                  |
| `enable_network_functions` | `dns_lookup`, `reverse_dns`, `http_request`, `community_id` |
| `enable_crypto_functions`  | `encrypt`, `decrypt`, `encrypt_ip`, `decrypt_ip`            |

The default feature set enables all four groups. When embedding VRL in restricted environments (e.g. WASM, sandboxed pipelines), disable these features explicitly.

## External References

- [VRL Overview](https://vector.dev/docs/reference/vrl/)
- [VRL Functions](https://vector.dev/docs/reference/vrl/functions/)
- [VRL Errors](https://vector.dev/docs/reference/vrl/errors/) — also at `https://errors.vrl.dev/<code>`
- [VRL Examples](https://vector.dev/docs/reference/vrl/examples/)
- [VRL Expressions](https://vector.dev/docs/reference/vrl/expressions/)
- [Vector VRL CLI](https://vector.dev/docs/reference/cli/#vrl)
- [VRL GitHub Repository](https://github.com/vectordotdev/vrl)
- [VRL Crate on crates.io](https://crates.io/crates/vrl)

See `vrl-install.md` in this directory for local installation instructions (cargo install, build from source, feature flags).
