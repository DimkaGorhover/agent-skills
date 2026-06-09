---
name: cli-taskfile
description: Use when writing, debugging, or reviewing Taskfile.yml configurations for task automation and build workflows. Triggers on Taskfile syntax questions, task dependency ordering, variable resolution, fingerprinting/caching, includes, environment setup, or CI/CD integration with go-task/task.
metadata:
  author: d.horkhover
  version: 1.0.0
---

# Taskfile

## Overview

Taskfile is a YAML-based task runner and build tool (alternative to Make). Tasks are defined in `Taskfile.yml` using Go template syntax for variables. Core strengths: parallel dependency execution, file fingerprinting to skip up-to-date work, dotenv support, cross-platform commands, and composable includes with namespacing.

## When to Use

- Writing or scaffolding a new `Taskfile.yml`
- Debugging task execution order, variable resolution, or caching
- Adding fingerprinting (`sources`/`generates`/`status`) to skip unnecessary work
- Structuring monorepo builds with `includes` and namespaces
- Integrating Taskfile into CI/CD pipelines
- Converting Makefiles to Taskfiles
- Reviewing Taskfile configurations for best practices

## When NOT to Use

- Projects already using `make` and no migration is requested — don't convert without being asked
- Single-command scripts where a shell script or `Makefile` one-liner suffices
- Non-YAML task runners (e.g., `nx`, `turborepo`) — use their native documentation instead

## Quick Reference

```yaml
version: '3'                     # Required — schema version

vars:                            # Global variables
  NAME: value
  DYNAMIC:
    sh: |-
      git rev-parse --short HEAD

env:                             # Global environment variables
  GO111MODULE: on

dotenv: ['.env', '.env.local']   # Load .env files (first wins)

set: [errexit, pipefail]         # Global shell options
shopt: [globstar]                # Global bash shopt options

includes:                        # Import other Taskfiles
  docker: ./docker/Taskfile.yml

tasks:
  task-name:
    desc: Human-readable description
    summary: |-
      Longer multi-line explanation
      shown with --summary flag
    aliases: [tn]
    dir: ./subdir
    deps: [other-task]
    cmds:
      - |-
        echo "{{.NAME}}"
    vars:
      LOCAL: value
    env:
      KEY: val
    sources:
      - src/**/*.go
    generates:
      - bin/app
    method: checksum              # checksum (default) | timestamp | none
    status:
      - test -f bin/app
    preconditions:
      - sh: |-
          test -f .env
        msg: >-
          .env file required
    requires:
      vars:
        - name: ENV
          enum: [dev, staging, prod]
    if: '{{eq .ENV "prod"}}'
    prompt: 'Deploy to production?'
    platforms: [linux, darwin]
    set: [errexit, nounset, pipefail]
    shopt: [globstar]
    internal: false
    silent: false
    interactive: false
    run: always                   # always | once | when_changed
    ignore_error: false
```

### Supported File Names (priority order)

1. `Taskfile.yml` / `taskfile.yml`
1. `Taskfile.yaml` / `taskfile.yaml`
1. `Taskfile.dist.yml` / `taskfile.dist.yml`
1. `Taskfile.dist.yaml` / `taskfile.dist.yaml`

`.dist` variants are committed to git; users override with `Taskfile.yml` (gitignored). Task walks up the directory tree to find a Taskfile (like `git`).

## Variables

### Types and Dynamic Variables

```yaml
vars:
  STRING: 'Hello'
  BOOL: true
  INT: 42
  FLOAT: 3.14
  ARRAY: [1, 2, 3]
  MAP:
    map: { A: 1, B: 2 }          # maps require `map:` subkey
  GIT_COMMIT:
    sh: |-
      git log -n 1 --format=%h  # dynamic — runs shell command
```

### Resolution Order (highest priority first)

1. Variables declared in the task definition
1. Variables passed when calling a task from another task
1. Variables of the included Taskfile
1. Variables of the inclusion definition
1. Global variables (`vars:` at root)
1. Environment variables

### Special Variables

| Variable                | Description                               |
| ----------------------- | ----------------------------------------- |
| `{{.TASK}}`             | Current task name                         |
| `{{.ALIAS}}`            | Alias used to call the task               |
| `{{.ROOT_TASKFILE}}`    | Absolute path of root Taskfile            |
| `{{.ROOT_DIR}}`         | Root Taskfile directory                   |
| `{{.TASKFILE}}`         | Current Taskfile path                     |
| `{{.TASKFILE_DIR}}`     | Current Taskfile directory                |
| `{{.TASK_DIR}}`         | Task's `dir:` value                       |
| `{{.USER_WORKING_DIR}}` | Directory where `task` was invoked        |
| `{{.CHECKSUM}}`         | Checksum of `sources` files               |
| `{{.TIMESTAMP}}`        | `time.Time` of last run                   |
| `{{.CLI_ARGS}}`         | Args after `--` as single string          |
| `{{.CLI_ARGS_LIST}}`    | Args after `--` as array                  |
| `{{.CLI_FORCE}}`        | `true` if `--force` used                  |
| `{{.CLI_SILENT}}`       | `true` if `--silent` used                 |
| `{{.CLI_VERBOSE}}`      | `true` if `--verbose` used                |
| `{{.CLI_OFFLINE}}`      | `true` if `--offline` used                |
| `{{.CLI_ASSUME_YES}}`   | `true` if `--yes` used                    |
| `{{.ITEM}}`             | Current loop item                         |
| `{{.EXIT_CODE}}`        | Last command exit code (in deferred)      |
| `{{OS}}`                | Runtime OS (`linux`, `darwin`, `windows`) |
| `{{ARCH}}`              | Architecture (`amd64`, `arm64`)           |
| `{{.TASK_VERSION}}`     | Installed Task version                    |
| `{{.TASK_EXE}}`         | Path to task executable                   |

### Passing Variables and Preserving Types

```yaml
tasks:
  caller:
    vars:
      LIST: [A, B, C]
    cmds:
      - task: callee
        vars:
          NAME: "World"            # pass by value (stringified)
          LIST:
            ref: .LIST             # pass by reference (preserves type)

  callee:
    requires:
      vars:
        - NAME
        - name: ENV
          enum: [dev, staging, prod]
    cmds:
      - |-
        echo "Hello, {{.NAME}}"
      - |-
        echo {{index .LIST 0}}   # outputs "A"
```

### Templating (Go templates + Sprig)

All Sprig functions available: https://masterminds.github.io/sprig/

Additional Taskfile-specific functions: `OS`, `ARCH`, `exeExt`, `fromJson`, `fromYaml`, `joinPath`, `relPath`, `merge`, `spew`.

See `templating-functions.md` in this directory for the complete function reference.

```yaml
vars:
  USER: '{{.USER | default "World"}}'
cmds:
  - echo '{{if eq .ENV "prod"}}Production{{else}}Development{{end}}'
```

## Environment Variables and Dotenv

```yaml
version: '3'

env:
  GLOBAL_VAR: global_value

dotenv:
  - .env.local        # highest priority (first wins)
  - '.env.{{.ENV}}'   # template expansion supported
  - .env              # base defaults

tasks:
  build:
    env:
      LOCAL_VAR: value   # overrides dotenv
    cmds:
      - |-
        echo "$GLOBAL_VAR $LOCAL_VAR"
```

**Note:** `dotenv` is NOT supported inside included Taskfiles. Explicit `env:` keys override dotenv values.

## Dependencies and Execution

```yaml
tasks:
  build:
    deps: [lint, test]       # parallel — lint and test run simultaneously
    cmds:
      - task: compile        # serial — runs after deps complete
      - task: package        # serial — runs after compile

  compile:
    cmds:
      - |-
        go build ./...
```

**Key rules:**

- `deps` run in **parallel** (not serial)
- Each `cmd` runs in a **separate shell** — no shared state between commands
- Use multiline `|` for commands that need shared shell state
- `task:` in `cmds` runs serially; `task:` in `deps` runs in parallel
- Cross-Taskfile calls: use `:` prefix (e.g., `task: :root-task-name`)

### Deferred Commands (cleanup)

```yaml
tasks:
  serve:
    cmds:
      - defer: rm -f server.pid    # runs on exit (LIFO order)
      - defer: { task: cleanup }   # can defer task calls too
      - |-
        ./start-server.sh
```

`{{.EXIT_CODE}}` is available in deferred commands.

### Prompt (interactive confirmation)

```yaml
tasks:
  deploy:
    prompt: 'Deploy to production? (y/n)'
    cmds:
      - |-
        ./deploy.sh
```

Skip prompts with `task --yes deploy` or `CLI_ASSUME_YES`.

## Preventing Unnecessary Work

### Fingerprinting (sources + generates)

```yaml
tasks:
  build:
    cmds:
      - go build -o bin/app ./...
    sources:
      - ./**/*.go
      - go.mod
      - exclude: ./**/*_test.go  # exclude from fingerprint
    generates:
      - bin/app
    method: checksum   # checksum (default) | timestamp | none
```

When sources haven't changed → prints `Task "build" is up to date`. Checksums stored in `.task/` (add to `.gitignore`).

### Status Checks (programmatic)

```yaml
tasks:
  install-deps:
    cmds:
      - |-
        npm install
    status:
      - |-
        test -d node_modules
      - |-
        test -f node_modules/.package-lock.json
```

All status commands must return exit code 0 for task to be considered up-to-date.

### Preconditions vs if vs status

| Mechanism       | On false                       | Use case                        |
| --------------- | ------------------------------ | ------------------------------- |
| `preconditions` | **Fails** task + dependents    | Guards — "X must be true"       |
| `if`            | **Skips** silently (continues) | Conditional — "only run when X" |
| `status`        | **Skips** as up-to-date        | Caching — "already done"        |

```yaml
tasks:
  deploy:
    preconditions:
      - sh: |-
          test -f .env
        msg: >-
          Missing .env file
      - sh: |-
          [ -n "$AWS_PROFILE" ]
        msg: >-
          AWS_PROFILE not set
    if: '[ "$CI" = "true" ]'
    cmds:
      - ./deploy.sh

  build:
    cmds:
      - cmd: |-
          echo "Production"
        if: '{{eq .ENV "prod"}}'
      - cmd: |-
          echo "Development"
        if: '{{ne .ENV "prod"}}'
```

## Including Other Taskfiles

### Basic Include

```yaml
version: '3'

includes:
  docker: ./docker/Taskfile.yml
  docs:
    taskfile: ./docs/Taskfile.yml
    dir: ./docs                     # run tasks in docs/ directory
```

Call with namespace: `task docker:build`, `task docs:serve`.

### Include with Variables

```yaml
includes:
  backend:
    taskfile: ./taskfiles/Docker.yml
    vars:
      DOCKER_IMAGE: backend

  frontend:
    taskfile: ./taskfiles/Docker.yml
    vars:
      DOCKER_IMAGE: frontend
```

### Include Options

```yaml
includes:
  utils:
    taskfile: ./Utils.yml
    optional: true      # don't fail if file missing
    internal: true      # hide all included tasks from --list
    flatten: true       # no namespace prefix
    excludes: [cleanup] # exclude specific tasks
    aliases: [u]        # shorter namespace
```

### OS-Specific Includes

```yaml
includes:
  build: ./Taskfile_{{OS}}.yml
```

## Looping

### Static List

```yaml
tasks:
  lint:
    cmds:
      - for: ['./pkg', './cmd', './internal']
        cmd: |-
          golangci-lint run {{.ITEM}}/...
```

### Loop with `as:` (rename ITEM)

```yaml
tasks:
  build:
    cmds:
      - for: [api, web, worker]
        as: SERVICE
        cmd: |-
          docker build -t {{.SERVICE}} ./{{.SERVICE}}
```

### Loop Over Variable

```yaml
tasks:
  build:
    vars:
      SERVICES: [api, web, worker]
    cmds:
      - for:
          var: SERVICES
        cmd: docker build -t {{.ITEM}} ./{{.ITEM}}
```

### Matrix (all permutations)

```yaml
tasks:
  cross-build:
    cmds:
      - for:
          matrix:
            OS: [linux, darwin, windows]
            ARCH: [amd64, arm64]
        cmd: GOOS={{.ITEM.OS}} GOARCH={{.ITEM.ARCH}} go build -o bin/app-{{.ITEM.OS}}-{{.ITEM.ARCH}}
```

### Loop with Source Globs

```yaml
tasks:
  format:
    vars:
      GOFILES:
        sh: find . -name '*.go' -not -path './vendor/*'
    cmds:
      - for:
          var: GOFILES
        cmd: |-
          gofmt -w {{.ITEM}}
```

### Loop with `if`

```yaml
tasks:
  process:
    cmds:
      - for: ['a', 'b', 'c']
        cmd: echo "{{.ITEM}}"
        if: '[ "{{.ITEM}}" != "b" ]'   # skips "b"
```

## Platform-Specific Tasks

```yaml
tasks:
  install:
    platforms: [darwin]           # only macOS
    cmds:
      - brew install foo

  install-linux:
    platforms: [linux/amd64]     # OS/arch combo
    cmds:
      - |-
        apt-get install foo

  build:
    cmds:
      - cmd: echo "Windows"
        platforms: [windows]     # per-command platform filter
      - cmd: echo "Unix"
        platforms: [linux, darwin]
```

Values are Go `GOOS`/`GOARCH`. Mismatched tasks are silently skipped.

## Shell Options

```yaml
version: '3'

set: [errexit, pipefail]       # global shell options
shopt: [globstar]              # global bash shopt options

tasks:
  build:
    set: [errexit, nounset, pipefail]   # task-level override
    shopt: [globstar]
    cmds:
      - |-
        echo "$REQUIRED_VAR"
      - |-
        echo **/*.go
```

Available `set:` values: `errexit`, `nounset`, `pipefail`, `xtrace`, `allexport`, `noglob`, `noclobber`.

Available `shopt:` values: `globstar`, `nullglob`, `expand_aliases`.

## Output Modes

```yaml
version: '3'

output: prefixed    # interleaved (default) | group | prefixed

tasks:
  server:
    prefix: srv     # custom prefix for 'prefixed' mode
    cmds:
      - |-
        ./start-server.sh
```

### Group Mode (CI-friendly)

```yaml
output:
  group:
    begin: '::group::{{.TASK}}'
    end: '::endgroup::'
    error_only: true              # only show output on failure
```

## Run Modes

| Mode           | Behavior                                                           |
| -------------- | ------------------------------------------------------------------ |
| `always`       | Default — always runs                                              |
| `once`         | Run once per `task` invocation regardless of how many times called |
| `when_changed` | Run once per unique set of variables                               |

```yaml
tasks:
  install-deps:
    run: once
    cmds:
      - |-
        npm install
```

## Configuration (.taskrc.yml)

Config files searched in order (highest priority first):

1. Project directory `.taskrc.yml`
1. Parent directories up to `$HOME`
1. `$HOME/.taskrc.yml`
1. `$XDG_CONFIG_HOME/task/taskrc.yml`

```yaml
# .taskrc.yml
verbose: false
silent: false
color: true
concurrency: 4
failfast: true
interactive: false
disable-fuzzy: false

experiments:
  REMOTE_TASKFILES: 1
```

## CLI Reference

```
task [options] [tasks...] [-- CLI_ARGS...]
```

| Flag            | Short | Description                                     |
| --------------- | ----- | ----------------------------------------------- |
| `--list`        | `-l`  | List tasks with descriptions                    |
| `--list-all`    | `-a`  | List all tasks (including internal)             |
| `--init`        | `-i`  | Create new Taskfile.yml                         |
| `--force`       | `-f`  | Force run even if up-to-date                    |
| `--dry`         | `-n`  | Print commands without executing                |
| `--watch`       | `-w`  | Watch sources and re-run on change              |
| `--parallel`    | `-p`  | Run CLI tasks in parallel                       |
| `--verbose`     | `-v`  | Enable verbose output                           |
| `--silent`      | `-s`  | Suppress command echoing                        |
| `--dir`         | `-d`  | Set working directory                           |
| `--taskfile`    | `-t`  | Specify Taskfile path                           |
| `--global`      | `-g`  | Use `$HOME/Taskfile.yml`                        |
| `--summary`     |       | Show task summary                               |
| `--status`      |       | Check if tasks are up-to-date                   |
| `--json`        |       | JSON output (with `--list`)                     |
| `--concurrency` | `-C`  | Limit parallel task count                       |
| `--output`      | `-o`  | Output mode: `interleaved`, `group`, `prefixed` |
| `--interval`    | `-I`  | Watch interval (default: `5s`)                  |
| `--failfast`    | `-F`  | Stop on first dependency failure                |
| `--yes`         | `-y`  | Auto-confirm prompts                            |
| `--color`       | `-c`  | Toggle colored output                           |
| `--exit-code`   | `-x`  | Pass through command exit codes                 |
| `--offline`     |       | Disable remote Taskfile fetching                |

### Exit Codes

| Code | Meaning                          |
| ---- | -------------------------------- |
| 0    | Success                          |
| 1    | Unknown error                    |
| 100  | No Taskfile found                |
| 101  | Taskfile already exists (--init) |
| 102  | Invalid Taskfile                 |
| 200  | Task not found                   |
| 201  | Command execution error          |
| 202  | Attempted to run internal task   |
| 203  | Duplicate task definition        |
| 204  | Task recursion limit exceeded    |
| 205  | Task cancelled by user           |
| 206  | Missing required variable        |
| 207  | Variable has incorrect value     |

## Common Patterns

### Go Project Build

```yaml
version: '3'

vars:
  VERSION:
    sh: |-
      git describe --tags --always --dirty
  COMMIT:
    sh: |-
      git rev-parse --short HEAD

tasks:
  build:
    desc: Build the binary
    cmds:
      - |-
        go build -ldflags="-X main.version={{.VERSION}} -X main.commit={{.COMMIT}}" -o bin/app ./cmd/app
    sources:
      - ./**/*.go
      - go.mod
      - go.sum
    generates:
      - bin/app

  test:
    desc: Run tests
    cmds:
      - |-
        go test -race -coverprofile=coverage.out ./...

  lint:
    desc: Run linter
    cmds:
      - |-
        golangci-lint run ./...

  default:
    desc: Build and test
    deps: [lint, test]
    cmds:
      - task: build
```

### Docker Workflow

```yaml
version: '3'

vars:
  IMAGE: myapp
  TAG:
    sh: git describe --tags --always

tasks:
  docker:build:
    desc: Build Docker image
    cmds:
      - docker build -t {{.IMAGE}}:{{.TAG}} .
    sources:
      - Dockerfile
      - ./**/*.go

  docker:push:
    desc: Push Docker image
    cmds:
      - docker push {{.IMAGE}}:{{.TAG}}
    preconditions:
      - sh: |-
          docker image inspect {{.IMAGE}}:{{.TAG}} > /dev/null 2>&1
        msg: >-
          Image not built. Run 'task docker:build' first.
```

### Deploy with Guards

```yaml
tasks:
  deploy:
    desc: Deploy to target environment
    requires:
      vars:
        - name: ENV
          enum: [dev, staging, prod]
    preconditions:
      - sh: |-
          test -f .env.{{.ENV}}
        msg: "Missing .env.{{.ENV}} file"
      - sh: |-
          kubectl config current-context | grep -q {{.ENV}}
        msg: "Wrong kubectl context for {{.ENV}}"
    prompt: '{{if eq .ENV "prod"}}Deploy to PRODUCTION?{{end}}'
    if: '{{ne .ENV ""}}'
    cmds:
      - kubectl apply -f k8s/{{.ENV}}/
```

### CLI Args Passthrough

```yaml
tasks:
  run:
    desc: "Run app with args: task run -- --port 8080"
    cmds:
      - |-
        go run ./cmd/app {{.CLI_ARGS}}

  test:
    desc: "Run tests: task test -- -run TestFoo -v"
    cmds:
      - |-
        go test {{.CLI_ARGS}} ./...
```

### Monorepo with Includes

```yaml
version: '3'

includes:
  api:
    taskfile: ./services/api/Taskfile.yml
    dir: ./services/api
  web:
    taskfile: ./services/web/Taskfile.yml
    dir: ./services/web
  shared:
    taskfile: ./libs/shared/Taskfile.yml
    dir: ./libs/shared
    flatten: true      # no namespace, tasks available directly
    excludes: [internal-task]

tasks:
  build:
    desc: Build all services
    deps: [api:build, web:build]

  test:
    desc: Test everything
    deps: [api:test, web:test, shared:test]
```

### Reusable Internal Task

```yaml
tasks:
  _build-service:
    internal: true
    dir: '{{.SERVICE_DIR}}'
    cmds:
      - |-
        docker build -t {{.SERVICE_NAME}}:latest .

  build-api:
    cmds:
      - task: _build-service
        vars:
          SERVICE_DIR: ./services/api
          SERVICE_NAME: api

  build-web:
    cmds:
      - task: _build-service
        vars:
          SERVICE_DIR: ./services/web
          SERVICE_NAME: web
```

### CI/CD (GitHub Actions)

```yaml
version: '3'

output:
  group:
    begin: '::group::{{.TASK}}'
    end: '::endgroup::'

tasks:
  ci:
    desc: Full CI pipeline
    cmds:
      - task: lint
      - task: test
      - task: build
```

### Cross-Platform Build

```yaml
tasks:
  build:
    desc: Build for all platforms
    cmds:
      - for:
          matrix:
            OS: [linux, darwin, windows]
            ARCH: [amd64, arm64]
        cmd: >-
          GOOS={{.ITEM.OS}}
          GOARCH={{.ITEM.ARCH}}
          go build -o bin/app-{{.ITEM.OS}}-{{.ITEM.ARCH}}{{if eq .ITEM.OS "windows"}}.exe{{end}}
          ./cmd/app
```

### Global Taskfile ($HOME/Taskfile.yml)

```yaml
version: '3'

tasks:
  scratch:
    desc: Create a temp directory
    dir: '{{.USER_WORKING_DIR}}'
    cmds:
      - |-
        DIR=$(mktemp -d)
        echo "Created: $DIR"

  ports:
    desc: Show listening ports
    cmds:
      - |-
        lsof -iTCP -sTCP:LISTEN -n -P
```

Run with `task -g scratch`.

## Common Mistakes

| Mistake                                    | Correct                                                               |
| ------------------------------------------ | --------------------------------------------------------------------- |
| Missing `version: '3'`                     | Always include `version: '3'` as first line                           |
| Using `deps` for sequential tasks          | `deps` run in parallel — use `cmds` with `task:` calls for serial     |
| Expecting shell state between `cmds`       | Each `cmd` is a separate shell — use multiline \`                     |
| `dotenv` in included Taskfile              | `dotenv` is only supported at the root Taskfile level                 |
| Bare `{{.VAR}}` in cmd string              | Quote: `'{{.VAR}}'` to prevent YAML parsing issues                    |
| `sources` without `generates`              | Both work alone, but `generates` improves fingerprint accuracy        |
| Using `status` when `preconditions` needed | `status`: up-to-date check (skips). `preconditions`: guard (fails)    |
| Committing `.task/` directory              | Add `.task/` to `.gitignore` — it stores checksums                    |
| Template `{{` in shell commands            | Use `{{ "{{" }}` to escape literal double braces in Go templates      |
| Map variable without `map:` subkey         | Maps require `map:` — `MY_MAP: map: {a: 1}` not `MY_MAP: {a: 1}`      |
| Passing arrays via template                | Use `ref:` to preserve type — templates stringify everything          |
| Missing `desc` or `summary`                | Tasks without `desc` are hidden from `--list`                         |
| Relative paths in included tasks           | Use `{{.USER_WORKING_DIR}}` or `{{.TASKFILE_DIR}}` for reliable paths |
| Overlong inline templates                  | Extract to `vars:` block — keep `cmds` readable                       |

## Schema and Editor Integration

```yaml
# Top of Taskfile.yml — enables autocompletion
# yaml-language-server: $schema=https://taskfile.dev/schema.json
version: '3'
```

Install [Task extension](https://marketplace.visualstudio.com/items?itemName=task.vscode-task) + [YAML extension](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml) for VS Code.

Or in `.vscode/settings.json`:

```json
{
  "yaml.schemas": {
    "https://taskfile.dev/schema.json": [
      "**/Taskfile.yml"
    ]
  }
}
```

## External References

- [Taskfile Guide](https://taskfile.dev/docs/guide)
- [Schema Reference](https://taskfile.dev/docs/reference/schema)
- [CLI Reference](https://taskfile.dev/docs/reference/cli)
- [Config Reference](https://taskfile.dev/docs/reference/config)
- [Templating Reference](https://taskfile.dev/docs/reference/templating)
- [Sprig Template Functions](https://masterminds.github.io/sprig/)
- [JSON Schema](https://taskfile.dev/schema.json)
- [LLM-Optimized Docs](https://taskfile.dev/llms-full.txt)
