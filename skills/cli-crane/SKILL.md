---
name: cli-crane
description: Use when performing registry-direct operations with the crane CLI, such as copying/promoting images, inspecting manifests/configs, mutating metadata, rebasing images, or creating/filtering multi-arch indexes without a Docker daemon.
metadata:
  author: d.horkhover
  version: 1.0.0
---

# crane

## Overview

`crane` is a daemonless CLI for OCI/Docker registries and images. Use it when you need registry-side operations (copy, tag, inspect, mutate, rebase, index management) without local Docker state.

## When to Use

- Copying images between registries without pulling locally
- Inspecting image manifests, configs, digests without `docker pull`
- Tagging, deleting, listing images in remote registries
- Mutating image metadata (labels, entrypoint, env) without rebuilding
- Building or filtering multi-arch indexes (manifest lists)
- Appending layers to existing images
- Rebasing images onto new base images

**NOT for:** Building images from Dockerfiles (use `docker build`, `ko`, `buildpacks`).

## Installation

```sh
# Primary install path (macOS)
brew install crane

# Alternatives: go install, setup-crane action, or container image
# See: https://github.com/google/go-containerregistry/tree/main/cmd/crane
```

## Quick Reference

| Command                                                  | Purpose                                           |
| -------------------------------------------------------- | ------------------------------------------------- |
| `crane ls <repo>`                                        | List tags in a repo                               |
| `crane digest <image>`                                   | Get image digest (sha256)                         |
| `crane digest --tarball <path.tar>`                      | Get digest from local tarball                     |
| `crane manifest <image>`                                 | Get raw image manifest JSON                       |
| `crane config <image>`                                   | Get image config JSON                             |
| `crane copy <src> <dst>`                                 | Copy image between registries (digest-preserving) |
| `crane tag <image> <tag>`                                | Tag a remote image efficiently                    |
| `crane pull <image> <path> --format oci`                 | Pull image in tarball/legacy/oci formats          |
| `crane push <path> <image>`                              | Push OCI layout directory or docker-style tarball |
| `crane delete <image>`                                   | Delete image from registry                        |
| `crane export <image> -`                                 | Export image filesystem as tar to stdout          |
| `crane append -f <tar> -t <image>`                       | Append layer(s) to image                          |
| `crane mutate <image> --label k=v`                       | Mutate image metadata                             |
| `crane rebase <image> --old_base <old> --new_base <new>` | Rebase onto new base                              |
| `crane catalog <registry>`                               | List repos (best-effort; registry support varies) |
| `crane blob <repo@sha256:blobDigest>`                    | Fetch raw blob content by digest                  |
| `crane flatten <image> -t <dst>`                         | Flatten all layers into one                       |
| `crane validate --remote <image>`                        | Validate remote image is well-formed              |

## Auth

```sh
crane auth login <registry> -u <user> -p <password>
cat /path/to/pass | crane auth login <registry> -u <user> --password-stdin
crane auth login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
crane auth token <repo>       # Get token
crane auth token -H --push --mount src/repo target/repo
crane auth get <repo>         # Credential helper output
```

## Global Flags

```
--platform linux/amd64      # Select platform; multi-arch images default to all-platform behavior
--insecure                   # Allow HTTP (no TLS)
--allow-nondistributable-artifacts
-v, --verbose                # Debug logs
```

Note: for some operations on multi-arch images, set `--platform` explicitly to avoid ambiguous/all-platform behavior.

## Recipes

### Inspect without pulling

```sh
crane manifest ubuntu:22.04 | jq -r
crane config ubuntu:22.04 | jq -r '.config.Env'
crane digest ubuntu:22.04
```

### List and filter files in an image

```sh
crane export ubuntu - | tar -tvf - | grep /etc/
crane export ubuntu - | tar -xOf - etc/passwd   # Extract single file (no leading /)
```

### Promote image across registries

```sh
crane copy gcr.io/myproject/app:v1.2.3 registry.example.com/myproject/app:v1.2.3
crane copy --all-tags gcr.io/myproject/app registry.example.com/myproject/app
# avoid overwriting tags in destination:
crane copy --no-clobber gcr.io/myproject/app:v1 registry.example.com/myproject/app:v1
```

### Diff two images

```sh
diff <(crane config app:1.0 | jq) <(crane config app:2.0 | jq)
diff <(crane export app:1.0 - | tar -tvf - | sort) <(crane export app:2.0 - | tar -tvf - | sort)
```

### Pin image by digest

```sh
crane digest ubuntu:22.04
# Use sha256:... in manifests for reproducible builds
```

### Bundle directory into image

```sh
crane append -f <(tar -f - -c ./dist/) -t registry.example.com/app:latest -b scratch
```

### Chain append + mutate

```sh
set -euo pipefail
crane mutate $(
  crane append -f <(tar -f - -c ./dist/) -t ${IMAGE}
) --entrypoint=/dist/server
```

### Multi-platform index

```sh
# Create from existing platform images
crane index append -t registry.example.com/app:latest \
  -m registry.example.com/app:amd64@sha256:... \
  -m registry.example.com/app:arm64@sha256:...

# Filter platforms from existing multi-arch image
crane index filter ubuntu --platform linux/amd64 --platform linux/arm64 -t my-registry/ubuntu

# In-place filter (digest changes):
crane index filter my-registry/ubuntu:tag --platform linux/amd64
```

`index append` infers platforms from referenced image configs when possible. `index filter` and append operations change digest values.

### Rebase onto new base

```sh
crane rebase myapp:latest \
  --old_base ubuntu:20.04 \
  --new_base ubuntu:22.04 \
  --tag myapp:rebased
```

### Get image total size

```sh
crane manifest gcr.io/buildpacks/builder:v1 \
  | jq '(.config.size // 0) + (([.layers[].size] | add) // 0)' \
  | numfmt --to=iec
```

### Mutate image metadata

```sh
crane mutate ubuntu:22.04 \
  --label maintainer=team@example.com \
  --label version=1.2.3 \
  -e APP_ENV=production \
  -e LOG_LEVEL=info \
  --entrypoint /bin/server \
  --tag registry.example.com/ubuntu-custom:latest
```

Without `--tag`, mutate pushes by digest and does not move existing tags.

## Common Mistakes

| Mistake                                         | Fix                                                              |
| ----------------------------------------------- | ---------------------------------------------------------------- |
| `crane export` path with leading `/`            | Remove `/` — use `etc/passwd` not `/etc/passwd`                  |
| Expecting `crane copy` to retag locally         | It operates purely on registries, no local state                 |
| Using `crane pull` when you just need digest    | Use `crane digest` — no download needed                          |
| Multi-arch: forgetting `--platform` returns all | Add `--platform linux/amd64` to get specific manifest            |
| `crane mutate` without `--tag`                  | Without `--tag`, pushes by digest to original repo               |
| Expecting `crane flatten` to preserve history   | Flattening is lossy: new digest and no original layer provenance |
| Assuming registry catalog is universal          | `catalog` support is registry-dependent; treat as best-effort    |

## CI/CD Pattern (GitLab)

```yaml
docker-tag-latest:
  image:
    name: gcr.io/go-containerregistry/crane:debug
    entrypoint: [""]
  script:
    - crane auth login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - crane tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA latest
```

## Notes

- Auth lookup follows keychain discovery (Docker config/helpers with Podman auth fallbacks).
- `crane tag` and `crane copy` are related but not interchangeable: tag is same-repo retagging and usually faster; copy handles src→dst promotion.
- `catalog` availability is registry-dependent; treat it as best-effort.
- Index operations may preserve or mix OCI/Docker media types depending on source artifacts and flags.
