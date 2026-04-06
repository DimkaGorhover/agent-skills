---
name: dockerfile-fnox
description: >-
  Use when installing fnox (Fort Knox secrets manager) in a Dockerfile. Triggers when
  adding fnox to Alpine, Debian, Ubuntu, or Rocky Linux images, writing fnox exec
  entrypoints, or hitting glibc/musl compatibility errors with fnox on Alpine.
---

# Installing fnox in Dockerfiles

## Overview

[fnox](https://fnox.jdx.dev) is a Rust-based CLI secrets manager. It ships as a single static binary
via GitHub Releases. Only glibc (`linux-gnu`) builds are released — no musl builds exist.

Recipes use the [heredoc `RUN` syntax](https://docs.docker.com/reference/dockerfile/#here-documents)
(requires Docker Engine 23.0+ or `# syntax=docker/dockerfile:1.23`).

## When to Use

- Writing a `Dockerfile` that needs `fnox` to manage secrets at build or runtime
- Adding `fnox exec` to a container entrypoint
- CI pipeline images that pull secrets from age/AWS/1Password/etc.
- Any base image: Alpine, Debian, Ubuntu, Rocky Linux, RHEL

## When NOT to Use

- Installing fnox on a developer workstation — use `mise use -g fnox` instead
- Configuring fnox providers, backends, or `fnox.toml` structure — this skill only covers binary installation

## Key Facts

| Fact                       | Detail                                                                                          |
| -------------------------- | ----------------------------------------------------------------------------------------------- |
| Only glibc builds          | `linux-gnu` only — no musl/Alpine-native builds                                                 |
| Alpine needs compat        | Install `libc6-compat` before running the binary                                                |
| Architectures              | `x86_64` (amd64) and `aarch64` (arm64)                                                          |
| Download URL pattern       | `https://github.com/jdx/fnox/releases/download/v{VERSION}/fnox-{ARCH}-unknown-linux-gnu.tar.gz` |
| TARGETARCH mapping         | Docker `amd64` → `x86_64`, Docker `arm64` → `aarch64`                                           |
| Binary location in tarball | `fnox` binary at archive root                                                                   |

## Recipes

### Alpine

```dockerfile
ARG FNOX_VERSION=1.20.0
RUN <<'EOD'
set -e
apk add --no-cache libc6-compat curl tar
ARCH=$([ "$(uname -m)" = "aarch64" ] && echo "aarch64" || echo "x86_64")
curl -fsSL "https://github.com/jdx/fnox/releases/download/v${FNOX_VERSION}/fnox-${ARCH}-unknown-linux-gnu.tar.gz" \
  | tar -xz -C /usr/local/bin
chmod +x /usr/local/bin/fnox
fnox --version
EOD
```

> `libc6-compat` is required — the glibc binary segfaults or errors without it on musl Alpine.

### Debian / Ubuntu

```dockerfile
ARG FNOX_VERSION=1.20.0
RUN <<'EOD'
set -e
apt-get update
apt-get install -y --no-install-recommends curl ca-certificates
rm -rf /var/lib/apt/lists/*
ARCH=$([ "$(uname -m)" = "aarch64" ] && echo "aarch64" || echo "x86_64")
curl -fsSL "https://github.com/jdx/fnox/releases/download/v${FNOX_VERSION}/fnox-${ARCH}-unknown-linux-gnu.tar.gz" \
  | tar -xz -C /usr/local/bin
chmod +x /usr/local/bin/fnox
fnox --version
EOD
```

### Rocky Linux / RHEL / AlmaLinux

```dockerfile
ARG FNOX_VERSION=1.20.0
RUN <<'EOD'
set -e
dnf install -y curl tar gzip
dnf clean all
ARCH=$([ "$(uname -m)" = "aarch64" ] && echo "aarch64" || echo "x86_64")
curl -fsSL "https://github.com/jdx/fnox/releases/download/v${FNOX_VERSION}/fnox-${ARCH}-unknown-linux-gnu.tar.gz" \
  | tar -xz -C /usr/local/bin
chmod +x /usr/local/bin/fnox
fnox --version
EOD
```

### Multi-arch build with `--platform` / `TARGETARCH`

Use `TARGETARCH` (set by Docker BuildKit) instead of `uname -m` for cross-compilation:

```dockerfile
# For Alpine: add `RUN apk add --no-cache libc6-compat` before this block
ARG FNOX_VERSION=1.20.0
ARG TARGETARCH
RUN <<'EOD'
set -e
ARCH=$([ "${TARGETARCH}" = "arm64" ] && echo "aarch64" || echo "x86_64")
curl -fsSL "https://github.com/jdx/fnox/releases/download/v${FNOX_VERSION}/fnox-${ARCH}-unknown-linux-gnu.tar.gz" \
  | tar -xz -C /usr/local/bin
chmod +x /usr/local/bin/fnox
EOD
```

> `TARGETARCH` is only populated in multi-stage or `docker buildx` builds. For single-arch builds, `uname -m` is more
> reliable.

## Common Mistakes

| Mistake                                     | Fix                                                                     |
| ------------------------------------------- | ----------------------------------------------------------------------- |
| Forgetting `libc6-compat` on Alpine         | `apk add --no-cache libc6-compat` before running the binary             |
| Using `$TARGETARCH` in non-BuildKit builds  | Falls back to empty string → wrong URL. Use `uname -m` for single-arch. |
| Pinning no version (`latest` redirect)      | Always pin `FNOX_VERSION` ARG for reproducible builds                   |
| Missing `ca-certificates` on minimal Debian | HTTPS download fails without it — install alongside `curl`              |
| Expecting a musl build                      | None exist. Use `libc6-compat` on Alpine instead.                       |
| Heredoc on old Docker                       | Requires Docker Engine 23.0+ or `# syntax=docker/dockerfile:1.23`       |
