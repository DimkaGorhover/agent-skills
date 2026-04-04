---
name: vector-remap-language
description: Use when writing, debugging, or reviewing Vector Remap Language (VRL) scripts for data transformation in Vector pipelines. Triggers on VRL syntax questions, compile-time errors (100-801), fallible function handling, type coercion, path expressions, or event manipulation in vector.dev remap transforms.
---

# Vector Remap Language (VRL)

## Overview

VRL is an **expression-oriented**, **fail-safe**, **stateless** language for transforming observability data in [Vector](https://vector.dev) pipelines. Every expression returns a value. All errors must be handled at compile time. No custom functions, no recursion, no I/O, no state across events.

## When to Use

- Writing `remap` transforms in Vector config
- Debugging VRL compile-time errors (codes 100–801)
- Parsing logs (syslog, JSON, key-value, custom formats)
- Coercing types, enriching events, routing data
- Understanding VRL's type safety and error handling model

## Core Concepts

### Events

VRL operates on a single **event** (log or metric) at a time. Access fields via path expressions:

```coffee
# Event root
.message           # top-level field
.host.name         # nested field
.tags[0]           # array index
.tags[0].name      # nested in array

# Metadata (read-only in most contexts)
%custom_metadata_field
```

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
    .value = upcase!(.value)  # compiler knows it's string here
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
# ERROR 100: unhandled fallible assignment
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

### Common Compile-Time Errors

| Code    | Error                         | Fix                                   |
| ------- | ----------------------------- | ------------------------------------- |
| 100     | Unhandled root runtime error  | Add `!`, `??`, or `, err =`           |
| 101     | Malformed regex literal       | Check regex syntax in `r'...'`        |
| 102     | Non-boolean if predicate      | Ensure condition is boolean           |
| 103     | Unhandled fallible assignment | Handle with `!`, `??`, or `, err =`   |
| 104     | Unnecessary error assignment  | Remove `, err =` from infallible call |
| 105     | Undefined function            | Check function name spelling          |
| 110     | Invalid argument type         | Pass correct type                     |
| 203     | Unrecognized token            | Fix syntax                            |
| 204     | Unexpected character          | Check for typos                       |
| 300–315 | Type errors                   | Use type coercion or guards           |
| 620     | Aborting infallible function  | Remove `!` from infallible call       |
| 701     | Undefined variable            | Define variable before use            |

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

### Emit Multiple Logs from JSON Array

```coffee
# In Vector config, use `remap` with array unwrapping
. = parse_json!(.message)
# Use Vector's `route` + conditions, or restructure upstream
```

### Type Checking and Guards

```coffee
if is_string(.value) {
    .value = upcase!(.value)
} else if is_integer(.value) {
    .value = to_string(.value)
}
```

### Enrichment with External Data

```coffee
# CSV enrichment (requires enrichment table in Vector config)
row = get_enrichment_table_record!("ips", {"ip": .src_ip})
.geo_city = row.city
.geo_country = row.country
```

## Function Reference

See `vrl-functions.md` in this directory for the comprehensive function reference organized by category (190+ functions across 20 categories).

**Quick category overview:**

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
1. Add `log()` calls to inspect intermediate values
1. Use `vector vrl` CLI to test expressions interactively
1. Use `vector tap` to inspect events flowing through pipeline

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

- **Error 100**: Unhandled root runtime error — the **root expression** of the program is fallible
- **Error 103**: Unhandled fallible assignment — a **specific assignment** uses a fallible function without handling

Both are fixed the same way (`!`, `??`, or `, err =`) but 103 points to a specific line, while 100 means the whole program's root can error.

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

## External References

- [VRL Overview](https://vector.dev/docs/reference/vrl/)
- [VRL Functions](https://vector.dev/docs/reference/vrl/functions/)
- [VRL Errors](https://vector.dev/docs/reference/vrl/errors/)
- [VRL Examples](https://vector.dev/docs/reference/vrl/examples/)
- [VRL Expressions](https://vector.dev/docs/reference/vrl/expressions/)
- [Vector VRL CLI](https://vector.dev/docs/reference/cli/#vrl)
