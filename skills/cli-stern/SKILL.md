---
name: cli-stern
description: >
  Use when tailing or aggregating logs from multiple Kubernetes pods, containers, or namespaces
  simultaneously — filtering by pod name regex, label selector, container state, or resource type;
  excluding noisy sidecars; formatting JSON logs; or piping structured output to jq.
metadata:
  author: d.horkhover
  version: 1.0.0
---

# stern

## Overview

`stern` tails logs from multiple Kubernetes pods and containers simultaneously. Pod names are matched
by a regular expression or a `<resource>/<name>` selector. New pods matching the query are picked up
automatically; deleted pods are dropped. Each pod/container is color-coded for quick visual scanning.

For installation see [installation.md](installation.md). For in-cluster use, RBAC setup is required — see [installation.md](installation.md#rbac-running-inside-kubernetes-pods).

> **`--no-follow` concurrency note:** Without `--follow`, stern defaults to max 5 concurrent log streams. Use `--max-log-requests` to raise it or set `--no-follow` together with `--since` to bound the output.

## When to Use

- Watching logs across many pods at once (e.g., all replicas of a deployment)
- Filtering log lines by regex (`--include` / `--exclude`)
- Excluding sidecar noise (`--exclude-container istio-proxy`)
- Tailing logs across all namespaces during an incident
- Piping structured JSON logs to `jq` for analysis
- Replaying recent logs without `--follow` (`--no-follow --since 5m`)

**NOT for:** Single-pod log tailing where `kubectl logs` is sufficient.

## Quick Reference

| Command                  | Purpose                               |
| ------------------------ | ------------------------------------- |
| `stern .`                | Tail all pods in current namespace    |
| `stern . -A`             | Tail all pods in all namespaces       |
| `stern <regex>`          | Tail pods matching regex              |
| `stern deployment/nginx` | Tail all pods of a deployment         |
| `stern job/myjob`        | Tail all pods of a Job                |
| `stern pod/mypod`        | Tail a specific pod by name           |
| `stern . -n <ns>`        | Tail specific namespace               |
| `stern . -l app=web`     | Filter by label selector              |
| `stern . -c <regex>`     | Limit to containers matching regex    |
| `stern . -e <regex>`     | Exclude log lines matching regex      |
| `stern . -i <regex>`     | Include only log lines matching regex |
| `stern . -H <regex>`     | Highlight matching log lines          |
| `stern . -t`             | Add timestamps                        |
| `stern . -s 15m`         | Show logs from last 15 minutes        |
| `stern . --tail 100`     | Show last 100 lines then follow       |
| `stern . --no-follow`    | Print logs and exit                   |
| `stern . -o json`        | Output as JSON (pipe to jq)           |
| `stern . -o raw`         | Raw log lines only                    |

## Config File

### Tail all pods across all namespaces

```sh
stern . --all-namespaces
```

### Watch a deployment's pods

```sh
stern deployment/nginx
# or by regex
stern nginx-
```

### Exclude noisy sidecars

```sh
stern -n staging --exclude-container 'istio-proxy|filebeat' .
```

### Show only errors in the last 15 minutes

```sh
stern . -s 15m -i 'error|ERROR|FATAL'
```

### Pipe JSON logs to jq

```sh
stern backend -o raw | jq '.level, .msg'
# or with stern's json output (adds pod/container metadata)
stern backend -o json | jq '{pod: .podName, msg: .message}'
```

### Replay recent logs sorted by timestamp

```sh
stern . --since 5m --no-follow --only-log-lines -A -t | sort -k4
```

### Tail with timestamps in a specific timezone

```sh
stern auth -t=short --timezone America/New_York
```

### Custom Go template (JSON log parsing)

```sh
# Parse JSON and show level + message
stern --template='{{.PodName}}/{{.ContainerName}} {{with $d := .Message | tryParseJSON}}[{{$d.level}}] {{$d.message}}{{else}}{{.Message}}{{end}}{{"\n"}}' backend
```

### Pretty-print JSON logs

```sh
stern --template='{{.Message | prettyJSON}}{{"\n"}}' backend
```

### Use interactive pod selector

```sh
stern -p # prompts for app.kubernetes.io/instance value
```

### Run from container (minikube example)

```sh
docker run --rm \
	-v "$HOME/.minikube:$HOME/.minikube" \
	-v "$HOME/.kube:/$HOME/.kube" \
	-e KUBECONFIG="$HOME/.kube/config" \
	ghcr.io/stern/stern deployment/nginx
```

## Config File

Default path: `~/.config/stern/config.yaml` (override with `--config` or `STERNCONFIG` env var).

```yaml
# Set persistent defaults
tail: 10
max-log-requests: 999
timestamps: short
# Colors: comma-separated SGR sequences
pod-colors: 32,33,34,35,36,37
container-colors: 32;4,33;4,34;4,35;4,36;4,37;4
```

## Custom Template Variables

| Property          | Type        | Description                   |
| ----------------- | ----------- | ----------------------------- |
| `.Message`        | string      | The log line                  |
| `.PodName`        | string      | Pod name                      |
| `.ContainerName`  | string      | Container name                |
| `.Namespace`      | string      | Namespace                     |
| `.NodeName`       | string      | Node the pod is scheduled on  |
| `.Labels`         | map         | Pod labels                    |
| `.Annotations`    | map         | Pod annotations               |
| `.PodColor`       | color.Color | Auto-assigned pod color       |
| `.ContainerColor` | color.Color | Auto-assigned container color |

Key template functions: `parseJSON`, `tryParseJSON`, `prettyJSON`, `extractJSONParts`,
`tryExtractJSONParts`, `toRFC3339Nano`, `toTimestamp`, `levelColor`, `bunyanLevelColor`,
`color`, `json`. Run `stern --help` for the full list.

## Shell Completion

```sh
# zsh
source <(stern --completion=zsh)

# bash
source <(stern --completion=bash)

# fish
stern --completion=fish | source
```

If installed via Krew:

```sh
source <(kubectl stern --completion bash)
complete -o default -F __start_stern kubectl stern
```

## Common Mistakes

| Mistake                                          | Fix                                                                                  |
| ------------------------------------------------ | ------------------------------------------------------------------------------------ |
| Too many concurrent streams crash cluster        | Set `--max-log-requests 20` or lower                                                 |
| `--no-follow` returns immediately with no output | Add `--since 1h` — default window is 48h but no-follow default concurrency is only 5 |
| Regex matches too broadly                        | Use `^myapp-` anchors; test with `stern --no-follow --tail 0` first                  |
| Missing container logs in multi-container pods   | Default `--container .*` matches all; use `-c specific-name` to narrow               |
| Timestamps in wrong timezone                     | Set `--timezone` or configure it in `~/.config/stern/config.yaml`                    |
| `--only-log-lines` loses pod context             | Only use when piping to tools that don't need origin metadata                        |
| `stern` and `kubectl stern` behave differently   | Krew installs as a `kubectl` plugin; completions need separate setup (see above)     |
