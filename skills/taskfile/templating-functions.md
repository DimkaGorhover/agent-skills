# Taskfile Templating Functions Reference

Taskfile uses Go's `text/template` with the [Slim Sprig](https://go-task.github.io/slim-sprig/) function library plus Taskfile-specific additions. All template expressions use `{{...}}` syntax.

## Taskfile-Specific Functions

| Function   | Description                        | Example                               |
| ---------- | ---------------------------------- | ------------------------------------- |
| `OS`       | Runtime GOOS                       | `{{OS}}` → `linux`                    |
| `ARCH`     | Runtime GOARCH                     | `{{ARCH}}` → `amd64`                  |
| `exeExt`   | `.exe` on Windows, empty otherwise | `bin/app{{exeExt}}`                   |
| `fromJson` | Parse JSON string to object        | `{{fromJson .JSON_STR}}`              |
| `fromYaml` | Parse YAML string to object        | `{{fromYaml .YAML_STR}}`              |
| `toJson`   | Serialize to JSON                  | `{{toJson .OBJ}}`                     |
| `toYaml`   | Serialize to YAML                  | `{{toYaml .OBJ}}`                     |
| `joinPath` | OS-aware path join                 | `{{joinPath .ROOT_DIR "bin" "app"}}`  |
| `relPath`  | Relative path from base            | `{{relPath .ROOT_DIR .TASKFILE_DIR}}` |
| `merge`    | Deep merge maps (last wins)        | `{{merge .A .B}}`                     |
| `spew`     | Debug dump any value               | `{{spew .MY_VAR}}`                    |

## String Functions

| Function          | Description                        | Example                                      |
| ----------------- | ---------------------------------- | -------------------------------------------- |
| `trim`            | Remove leading/trailing whitespace | `{{trim " hi "}}` → `hi`                     |
| `trimPrefix`      | Remove prefix                      | `{{trimPrefix "v" "v1.2"}}` → `1.2`          |
| `trimSuffix`      | Remove suffix                      | `{{trimSuffix ".go" "main.go"}}` → `main`    |
| `upper`           | Uppercase                          | `{{upper "hello"}}` → `HELLO`                |
| `lower`           | Lowercase                          | `{{lower "HELLO"}}` → `hello`                |
| `title`           | Title Case                         | `{{title "hello world"}}` → `Hello World`    |
| `contains`        | String contains                    | `{{if contains "test" .FILE}}...{{end}}`     |
| `hasPrefix`       | Starts with                        | `{{if hasPrefix "v" .TAG}}...{{end}}`        |
| `hasSuffix`       | Ends with                          | `{{if hasSuffix ".go" .FILE}}...{{end}}`     |
| `replace`         | Replace all                        | `{{replace "-" "_" .NAME}}`                  |
| `repeat`          | Repeat N times                     | `{{repeat 3 "ab"}}` → `ababab`               |
| `substr`          | Substring                          | `{{substr 0 5 "hello world"}}` → `hello`     |
| `nospace`         | Remove all whitespace              | `{{nospace "hello world"}}` → `helloworld`   |
| `trunc`           | Truncate                           | `{{trunc 5 "hello world"}}` → `hello`        |
| `abbrev`          | Truncate with ellipsis             | `{{abbrev 8 "hello world"}}` → `hello...`    |
| `quote`           | Wrap in double quotes              | `{{quote .VAL}}`                             |
| `squote`          | Wrap in single quotes              | `{{squote .VAL}}`                            |
| `cat`             | Concatenate with spaces            | `{{cat "a" "b" "c"}}` → `a b c`              |
| `indent`          | Indent each line                   | `{{indent 4 .TEXT}}`                         |
| `nindent`         | Newline + indent                   | `{{nindent 4 .TEXT}}`                        |
| `split`           | Split to map (.0, .1)              | `{{(split ":" .PAIR)._0}}`                   |
| `splitList`       | Split to array                     | `{{range splitList "," .CSV}}...{{end}}`     |
| `join`            | Join array                         | `{{join "," .LIST}}`                         |
| `default`         | Default value                      | `{{.PORT \| default "8080"}}`                |
| `coalesce`        | First non-empty value              | `{{coalesce .A .B "fallback"}}`              |
| `regexMatch`      | Regex test                         | `{{if regexMatch "^v[0-9]" .TAG}}...{{end}}` |
| `regexReplaceAll` | Regex replace                      | `{{regexReplaceAll "[^a-z]" .NAME ""}}`      |

## List Functions

| Function    | Description          | Example                          |
| ----------- | -------------------- | -------------------------------- |
| `list`      | Create list          | `{{list "a" "b" "c"}}`           |
| `first`     | First element        | `{{first .LIST}}`                |
| `last`      | Last element         | `{{last .LIST}}`                 |
| `rest`      | All except first     | `{{rest .LIST}}`                 |
| `initial`   | All except last      | `{{initial .LIST}}`              |
| `append`    | Append element       | `{{append .LIST "d"}}`           |
| `prepend`   | Prepend element      | `{{prepend .LIST "z"}}`          |
| `concat`    | Merge lists          | `{{concat .LIST1 .LIST2}}`       |
| `reverse`   | Reverse list         | `{{reverse .LIST}}`              |
| `uniq`      | Remove duplicates    | `{{uniq .LIST}}`                 |
| `without`   | Remove elements      | `{{without .LIST "bad"}}`        |
| `has`       | Contains element     | `{{if has "x" .LIST}}...{{end}}` |
| `compact`   | Remove empty strings | `{{compact .LIST}}`              |
| `slice`     | Sublist              | `{{slice .LIST 1 3}}`            |
| `sortAlpha` | Sort alphabetically  | `{{sortAlpha .LIST}}`            |
| `index`     | Access by index      | `{{index .LIST 0}}`              |
| `len`       | Length               | `{{len .LIST}}`                  |

## Math Functions

| Function | Description      | Example                    |
| -------- | ---------------- | -------------------------- |
| `add`    | Addition         | `{{add 1 2}}` → `3`        |
| `sub`    | Subtraction      | `{{sub 5 2}}` → `3`        |
| `mul`    | Multiplication   | `{{mul 3 4}}` → `12`       |
| `div`    | Integer division | `{{div 10 3}}` → `3`       |
| `mod`    | Modulo           | `{{mod 10 3}}` → `1`       |
| `max`    | Maximum          | `{{max 1 2 3}}` → `3`      |
| `min`    | Minimum          | `{{min 1 2 3}}` → `1`      |
| `add1`   | Increment        | `{{add1 5}}` → `6`         |
| `ceil`   | Ceiling          | `{{ceil 1.5}}` → `2`       |
| `floor`  | Floor            | `{{floor 1.5}}` → `1`      |
| `round`  | Round            | `{{round 1.55 1}}` → `1.6` |

## Date Functions

| Function     | Description           | Example                                |
| ------------ | --------------------- | -------------------------------------- |
| `now`        | Current time          | `{{now}}`                              |
| `date`       | Format time           | `{{now \| date "2006-01-02"}}`         |
| `dateInZone` | Format in timezone    | `{{dateInZone "15:04" (now) "UTC"}}`   |
| `dateModify` | Add/subtract duration | `{{now \| dateModify "-24h"}}`         |
| `ago`        | Duration since time   | `{{ago .TIMESTAMP}}`                   |
| `toDate`     | Parse date string     | `{{toDate "2006-01-02" "2024-01-15"}}` |

Go date format reference: `2006-01-02T15:04:05Z07:00` (Mon Jan 2 15:04:05 MST 2006).

## System and Path Functions

| Function    | Description             | Example                           |
| ----------- | ----------------------- | --------------------------------- |
| `env`       | Read env variable       | `{{env "HOME"}}`                  |
| `expandenv` | Expand `$VAR` in string | `{{expandenv "$HOME/bin"}}`       |
| `base`      | Base filename           | `{{base "/a/b/c.go"}}` → `c.go`   |
| `dir`       | Directory               | `{{dir "/a/b/c.go"}}` → `/a/b`    |
| `ext`       | Extension               | `{{ext "file.tar.gz"}}` → `.gz`   |
| `clean`     | Clean path              | `{{clean "/a//b/../c"}}` → `/a/c` |
| `isAbs`     | Is absolute path        | `{{if isAbs .PATH}}...{{end}}`    |

## Data and Encoding Functions

| Function       | Description    | Example                   |
| -------------- | -------------- | ------------------------- |
| `toJson`       | To JSON        | `{{toJson .OBJ}}`         |
| `toPrettyJson` | To pretty JSON | `{{toPrettyJson .OBJ}}`   |
| `fromJson`     | Parse JSON     | `{{(fromJson .STR).key}}` |
| `toYaml`       | To YAML        | `{{toYaml .OBJ}}`         |
| `fromYaml`     | Parse YAML     | `{{(fromYaml .STR).key}}` |
| `b64enc`       | Base64 encode  | `{{b64enc "hello"}}`      |
| `b64dec`       | Base64 decode  | `{{b64dec .ENCODED}}`     |
| `sha256sum`    | SHA-256 hash   | `{{sha256sum .INPUT}}`    |

## Logic and Flow

| Function    | Description             | Example                           |
| ----------- | ----------------------- | --------------------------------- |
| `eq`        | Equal                   | `{{if eq .A .B}}...{{end}}`       |
| `ne`        | Not equal               | `{{if ne .ENV "prod"}}...{{end}}` |
| `lt` / `le` | Less than / or equal    | `{{if lt .COUNT 10}}...{{end}}`   |
| `gt` / `ge` | Greater than / or equal | `{{if gt .COUNT 0}}...{{end}}`    |
| `and`       | Logical AND             | `{{if and .A .B}}...{{end}}`      |
| `or`        | Logical OR              | `{{if or .A .B}}...{{end}}`       |
| `not`       | Logical NOT             | `{{if not .SKIP}}...{{end}}`      |
| `empty`     | Is zero/nil/empty       | `{{if empty .VAL}}...{{end}}`     |
| `ternary`   | Conditional value       | `{{ternary "yes" "no" .BOOL}}`    |

## Type Conversion

| Function    | Description         | Example                      |
| ----------- | ------------------- | ---------------------------- |
| `toString`  | Convert to string   | `{{toString 42}}` → `"42"`   |
| `toStrings` | List to string list | `{{toStrings .LIST}}`        |
| `atoi`      | String to int       | `{{atoi "42"}}` → `42`       |
| `int64`     | Convert to int64    | `{{int64 .VAL}}`             |
| `float64`   | Convert to float64  | `{{float64 .VAL}}`           |
| `kindOf`    | Type name           | `{{kindOf .VAL}}` → `string` |
| `typeOf`    | Full type           | `{{typeOf .VAL}}`            |

## Dict (Map) Functions

| Function | Description      | Example                              |
| -------- | ---------------- | ------------------------------------ |
| `dict`   | Create map       | `{{dict "a" 1 "b" 2}}`               |
| `get`    | Get value by key | `{{get .MAP "key"}}`                 |
| `set`    | Set key-value    | `{{set .MAP "key" "val"}}`           |
| `unset`  | Remove key       | `{{unset .MAP "key"}}`               |
| `hasKey` | Key exists       | `{{if hasKey .MAP "key"}}...{{end}}` |
| `keys`   | All keys         | `{{keys .MAP}}`                      |
| `values` | All values       | `{{values .MAP}}`                    |
| `merge`  | Deep merge maps  | `{{merge .A .B}}`                    |
| `pick`   | Keep only keys   | `{{pick .MAP "a" "b"}}`              |
| `omit`   | Remove keys      | `{{omit .MAP "secret"}}`             |

## UUID

| Function | Description | Example                       |
| -------- | ----------- | ----------------------------- |
| `uuidv4` | Random UUID | `{{uuidv4}}` → `a1b2c3d4-...` |

## Template Syntax Quick Reference

```yaml
# Conditionals
'{{if eq .ENV "prod"}}production{{else}}development{{end}}'

# Range over list
'{{range .LIST}}{{.}} {{end}}'

# Range with index
'{{range $i, $v := .LIST}}{{$i}}: {{$v}} {{end}}'

# Pipeline (chaining)
'{{.NAME | upper | trimPrefix "V"}}'

# Variable assignment
'{{$name := .FIRST | upper}}'

# Whitespace trimming
'{{- .VAL -}}'
```
