# gocognit Installation

## Go Install (recommended)

```bash
go install github.com/uudashr/gocognit/cmd/gocognit@latest
```

Installs the binary to `$GOPATH/bin` (default `~/go/bin`). Ensure this is on your `PATH`:

```bash
export PATH="$PATH:$(go env GOPATH)/bin"
```

## Specific Version

```bash
go install github.com/uudashr/gocognit/cmd/gocognit@v1.2.1
```

Check latest release at <https://github.com/uudashr/gocognit/releases>.

## Go Get (add as project dependency)

```bash
go get github.com/uudashr/gocognit/cmd/gocognit
```

## Homebrew (macOS/Linux)

Not in the official tap — use `go install` above.

## Docker (no local install)

```bash
docker run --rm -v "$PWD:/src" -w /src \
	golang:latest \
	sh -c "go install github.com/uudashr/gocognit/cmd/gocognit@latest && gocognit -over 15 ./..."
```

## CI/CD

### GitHub Actions

```yaml
  - name: Install gocognit
    run: go install github.com/uudashr/gocognit/cmd/gocognit@latest

  - name: Check cognitive complexity
    run: gocognit -over 15 ./...
```

Pin a specific version to avoid unexpected failures:

```yaml
  - name: Install gocognit
    run: go install github.com/uudashr/gocognit/cmd/gocognit@v1.2.1
```

### GitLab CI

```yaml
complexity:
  stage: lint
  image: golang:1.22
  script:
    - go install github.com/uudashr/gocognit/cmd/gocognit@latest
    - gocognit -over 15 ./...
```

### Makefile

```makefile
.PHONY: install-tools
install-tools:
	go install github.com/uudashr/gocognit/cmd/gocognit@latest

.PHONY: complexity
complexity:
	gocognit -over 15 -avg ./...
```

## Verify Installation

```bash
gocognit -h
# Calculate cognitive complexities of Go functions.
# ...
```
