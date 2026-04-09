---
name: helm-chart-structuring
description: Use when creating, extending, or reviewing application Helm charts. Covers chart layout, values/schema design, template conventions, and reusable helper-library patterns (bitnami common and custom library charts).
metadata:
  author: d.horkhover
  version: 1.0.0
---

# Helm Chart Structuring

## When to Use

- Creating a new application Helm chart from scratch
- Adding new templates, values keys, schema definitions, or dependencies to an existing chart
- Reviewing a chart for layout consistency, schema quality, rendering safety, and operational defaults
- Setting up lint/render workflows (`ct lint`, `helm template`) and optional ArgoCD integration
- Defining or consuming shared helper-library functions (for example, bitnami `common` plus a custom org library)

## When NOT to Use

- Generic Kubernetes troubleshooting unrelated to Helm chart authoring
- Helm unit-test design and assertions — use the `helm-chart-unittest` skill instead
- Infrastructure provisioning topics outside chart structure (Terraform modules, cluster bootstrap, etc.)

## Overview

Every application chart follows a strict, repeatable layout.
Deviation from this layout breaks `ct lint`, ArgoCD rendering, and stakater Reloader.

______________________________________________________________________

## Required Directory Layout

```
helm-charts/<chart-name>/
  .helmignore          # Standard helm ignore
  Chart.yaml           # Chart metadata + dependencies
  Chart.lock           # Committed after dep build
  Makefile             # Standard targets (see below)
  values.yaml          # Default values
  values.schema.json   # JSON Schema for values validation
  charts/              # Extracted deps (not tarballs)
  ci/
    test-values.yaml   # ci overrides for ct lint
  templates/
    Deployment.yaml          # or StatefulSet/DaemonSet
    Service.yaml
    ServiceAccount.yaml
    ServiceMonitor.yaml      # when metrics.enabled
    PodDisruptionBudget.yaml # when pdb.create
```

______________________________________________________________________

## Chart.yaml

```yaml
---
apiVersion: v2
name: <chart-name>
description: <chart-name>
type: application
version: 0.0.1
appVersion: <app-semver>
maintainers:
  - name: <Full Name>
    email: <email@example.com>
dependencies:
  - name: common
    repository: https://nexus.example.com/repository/helm-hosted-bitnami/
    tags:
      - bitnami-common
    version: 2.x.x
  - name: company-common
    repository: file://../company-common
    tags:
      - company-common
    version: x.x.x
```

**Rules:**

- Both `common` (bitnami) and `company-common` are **always** required.
- `Chart.lock` must be committed after `helm dependency build --skip-refresh`.
- Extracted deps go in `charts/` as directories, not `.tgz` files.

______________________________________________________________________

## values.yaml — Standard Keys

```yaml
---
global:
  revisionHistoryLimit: 1 # keep rollout history short

config: {} # app-specific config block

port: 8080
portName: http

image:
  registry: nexus.example.com
  repository: company/<app>
  pullPolicy: Always # or IfNotPresent for pinned tags

logLevel: debug # app log level

caBundle: # mount internal CA bundle
  secret:
    name: example-certs-bundle

resources:
  requests:
    cpu: "0.1"
    memory: 32Mi
    ephemeral-storage: 128Mi
  limits:
    cpu: "0.5"
    memory: 256Mi
    ephemeral-storage: 128Mi

rbac:
  create: true

startupProbe:
  enabled: true
livenessProbe:
  enabled: true
readinessProbe:
  enabled: true
  initialDelaySeconds: 180

pdb:
  create: true
  maxUnavailable: 0

metrics:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: 1m
    scrapeTimeout: 20s
    honorLabels: true
    labels:
      release: prometheus-stack
    annotations: {}
    dropMetricsLabels:
      - endpoint
      - instance
      - service
      - pod
      - container
    relabelings: []
    metricRelabelings: []
```

**Secret reference pattern** — used for any config that may come from a Secret or ConfigMap:

```yaml
config:
  somePassword:
    secret:
      name: my-secret
      key: PASSWORD
# OR plaintext:
  somePassword: "literal-value"
```

Render it in templates via `company.common.env-var`.

______________________________________________________________________

## values.schema.json

Validate values with hosted schemas. Always start from this skeleton:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$ref": "#/definitions/MyChartValues",
  "definitions": {
    "MyChartValues": {
      "type": "object",
      "title": "My Chart Values",
      "additionalProperties": true,
      "required": [
        "global",
        "port",
        "image",
        "portName",
        "resources"
      ],
      "properties": {
        "global": {
          "$ref": "https://DimkaGorhover.github.io/helm-json-schemas/helm/Global.json"
        },
        "image": {
          "$ref": "https://DimkaGorhover.github.io/helm-json-schemas/helm/Image.json"
        },
        "resources": {
          "$ref": "https://DimkaGorhover.github.io/helm-json-schemas/k8s/Resources.json"
        },
        "livenessProbe": {
          "$ref": "https://DimkaGorhover.github.io/helm-json-schemas/helm/Probe.json"
        },
        "readinessProbe": {
          "$ref": "https://DimkaGorhover.github.io/helm-json-schemas/helm/Probe.json"
        },
        "startupProbe": {
          "$ref": "https://DimkaGorhover.github.io/helm-json-schemas/helm/Probe.json"
        },
        "pdb": {
          "$ref": "https://DimkaGorhover.github.io/helm-json-schemas/helm/PodDisruptionBudget.json"
        },
        "commonLabels": {
          "$ref": "https://DimkaGorhover.github.io/helm-json-schemas/k8s/Labels.json"
        },
        "commonAnnotations": {
          "$ref": "https://DimkaGorhover.github.io/helm-json-schemas/k8s/Annotations.json"
        },
        "podLabels": {
          "$ref": "https://DimkaGorhover.github.io/helm-json-schemas/k8s/Labels.json"
        },
        "podAnnotations": {
          "$ref": "https://DimkaGorhover.github.io/helm-json-schemas/k8s/Annotations.json"
        },
        "port": {
          "type": "integer",
          "default": 8080
        },
        "portName": {
          "type": "string",
          "default": "http"
        },
        "nameOverride": {
          "type": "string"
        },
        "fullnameOverride": {
          "type": "string"
        }
      }
    }
  }
}
```

- Set `"additionalProperties": false` on sub-objects that are fully controlled.
- Use `allOf` + `if/then` to conditionally require sub-keys (e.g. `serviceMonitor` required when `metrics.enabled: true`).

______________________________________________________________________

## Template Conventions

### File naming

PascalCase — `Deployment.yaml`, `Service.yaml`, `ServiceAccount.yaml`, `ServiceMonitor.yaml`, `PodDisruptionBudget.yaml`.

### Helper functions

| Helper                            | Source         | Purpose                                 |
| --------------------------------- | -------------- | --------------------------------------- |
| `common.names.fullname`           | bitnami        | `<release>-<chart>` name                |
| `common.names.namespace`          | bitnami        | `.Release.Namespace`                    |
| `common.names.name`               | bitnami        | chart short name                        |
| `common.labels.standard`          | bitnami        | standard k8s labels                     |
| `common.labels.matchLabels`       | bitnami        | selector labels                         |
| `common.images.renderPullSecrets` | bitnami        | imagePullSecrets                        |
| `company.common.image`            | company-common | full `registry/repo:tag` string         |
| `company.common.imagePullPolicy`  | company-common | pull policy (always for `latest`)       |
| `company.common.tpl`              | company-common | render values that may contain `{{ }}`  |
| `company.common.container.env`    | company-common | locale + k8s downward-API envs          |
| `company.common.env-var`          | company-common | env var supporting secret/configmap ref |

### Deployment.yaml — full pattern

```yaml
{{- $fullname := include "common.names.fullname" . -}}

{{- $reloaderSecretNames := list -}}
{{- with .Values.caBundle -}}
  {{- with .secret -}}
    {{- $reloaderSecretNames = append $reloaderSecretNames .name -}}
  {{- end -}}
{{- end -}}
{{- $reloaderSecretNames = append $reloaderSecretNames .Values.config.someSecret.name -}}
{{- $reloaderSecretNames = $reloaderSecretNames | sortAlpha | uniq -}}

apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ $fullname | quote }}
  namespace: {{ include "common.names.namespace" . | quote }}
  labels:
    {{- include "common.labels.standard" . | nindent 4 }}
    {{- if .Values.commonLabels }}
    {{- include "company.common.tpl" (dict "value" .Values.commonLabels "context" .) | nindent 4 }}
    {{- end }}
  {{- if or $reloaderSecretNames .Values.commonAnnotations }}
  annotations:
    secret.reloader.stakater.com/reload: {{ $reloaderSecretNames | join "," | quote }}
    {{- if .Values.commonAnnotations }}
    {{- include "company.common.tpl" (dict "value" .Values.commonAnnotations "context" .) | nindent 4 }}
    {{- end }}
  {{- end }}
spec:
  revisionHistoryLimit: {{ .Values.global.revisionHistoryLimit | default 10 }}
  selector:
    matchLabels:
      {{- include "common.labels.matchLabels" . | nindent 6 }}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
  replicas: 1
  template:
    metadata:
      labels:
        {{- include "common.labels.standard" . | nindent 8 }}
        {{- if .Values.commonLabels }}
        {{- include "company.common.tpl" (dict "value" .Values.commonLabels "context" .) | nindent 8 }}
        {{- end }}
        {{- if .Values.podLabels }}
        {{- include "company.common.tpl" (dict "value" .Values.podLabels "context" .) | nindent 8 }}
        {{- end }}
      annotations:
        {{- if .Values.podAnnotations }}
        {{- include "company.common.tpl" (dict "value" .Values.podAnnotations "context" .) | nindent 8 }}
        {{- end }}
    spec:
      enableServiceLinks: false
      hostNetwork: false
      dnsPolicy: ClusterFirstWithHostNet
      restartPolicy: Always
      {{- if .Values.rbac.create }}
      serviceAccountName: {{ $fullname | quote }}
      {{- end }}
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - podAffinityTerm:
                topologyKey: kubernetes.io/hostname
                labelSelector:
                  matchLabels:
                    {{- include "common.labels.matchLabels" . | nindent 20 }}
              weight: 1
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              {{- include "common.labels.matchLabels" . | nindent 14 }}
      {{- include "common.images.renderPullSecrets" (dict "images" (list .Values.image) "context" .) | nindent 6 }}
      containers:
        - name: {{ include "common.names.name" . | quote }}
          image: {{ include "company.common.image" (dict "image" .Values.image "ctx" .) }}
          imagePullPolicy: {{ include "company.common.imagePullPolicy" (dict "image" .Values.image "ctx" .) }}
          env:
            {{- include "company.common.container.env" . | nindent 12 }}
          ports:
            - name: {{ .Values.portName | quote }}
              containerPort: {{ .Values.port }}
              protocol: TCP
          {{- with .Values.resources }}
          resources:
            {{- include "company.common.tpl" (dict "value" . "context" $) | nindent 12 }}
          {{- end }}
          {{- with .Values.startupProbe }}{{- if .enabled }}
          startupProbe:
            httpGet:
              port: {{ $.Values.portName | quote }}
              path: /liveness
            initialDelaySeconds: {{ .initialDelaySeconds | default 5 }}
            periodSeconds:       {{ .periodSeconds | default 5 }}
            timeoutSeconds:      {{ .timeoutSeconds | default 1 }}
            successThreshold:    {{ .successThreshold | default 1 }}
            failureThreshold:    {{ .failureThreshold | default 5 }}
          {{- end }}{{- end }}
          {{- with .Values.livenessProbe }}{{- if .enabled }}
          livenessProbe:
            httpGet:
              port: {{ $.Values.portName | quote }}
              path: /liveness
            initialDelaySeconds: {{ .initialDelaySeconds | default 5 }}
            periodSeconds:       {{ .periodSeconds | default 5 }}
            timeoutSeconds:      {{ .timeoutSeconds | default 1 }}
            successThreshold:    {{ .successThreshold | default 1 }}
            failureThreshold:    {{ .failureThreshold | default 5 }}
          {{- end }}{{- end }}
          {{- with .Values.readinessProbe }}{{- if .enabled }}
          readinessProbe:
            httpGet:
              port: {{ $.Values.portName | quote }}
              path: /readiness
            initialDelaySeconds: {{ .initialDelaySeconds | default 120 }}
            periodSeconds:       {{ .periodSeconds | default 5 }}
            timeoutSeconds:      {{ .timeoutSeconds | default 2 }}
            successThreshold:    {{ .successThreshold | default 1 }}
            failureThreshold:    {{ .failureThreshold | default 5 }}
          {{- end }}{{- end }}
          volumeMounts:
            {{- with .Values.caBundle }}{{- with .secret }}
            - name: ca-cert-pem
              subPath: {{ coalesce .key "ca-certificates.crt" | quote }}
              mountPath: /etc/ssl/certs/ca-certificates.crt
              readOnly: true
            {{- end }}{{- end }}
            - { name: tmp, subPath: tmp,     mountPath: /tmp }
            - { name: tmp, subPath: dev/shm, mountPath: /dev/shm }
      volumes:
        - name: tmp
          emptyDir:
            medium: Memory
        {{- with .Values.caBundle }}
        {{- with .secret }}
        - name: ca-cert-pem
          secret:
            secretName: {{ .name | quote }}
        {{- end }}
        {{- end }}
```

### Service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "common.names.fullname" . | quote }}
  namespace: {{ include "common.names.namespace" . }}
  labels:
    {{- include "common.labels.standard" . | nindent 4 }}
    {{- with .Values.commonLabels }}
    {{- include "company.common.tpl" (dict "value" . "context" $) | nindent 4 }}
    {{- end }}
  {{- with .Values.commonAnnotations }}
  annotations:
    {{- include "company.common.tpl" (dict "value" . "context" $) | nindent 4 }}
  {{- end }}
spec:
  type: ClusterIP
  ports:
    - name: {{ .Values.portName | quote }}
      port: {{ .Values.port }}
      targetPort: {{ .Values.portName | quote }}
  selector:
    {{- include "common.labels.matchLabels" . | nindent 4 }}
```

### ServiceAccount.yaml

```yaml
{{- if .Values.rbac.create }}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "common.names.fullname" . | quote }}
  namespace: {{ include "common.names.namespace" . | quote }}
  labels:
    {{- include "common.labels.standard" . | nindent 4 }}
    {{- with .Values.commonLabels }}
    {{- include "company.common.tpl" (dict "value" . "context" $) | nindent 4 }}
    {{- end }}
  {{- with .Values.commonAnnotations }}
  annotations:
    {{- include "company.common.tpl" (dict "value" . "context" $) | nindent 4 }}
  {{- end }}
{{- end }}
```

### PodDisruptionBudget.yaml

```yaml
{{- if .Values.pdb }}
{{- if .Values.pdb.create }}
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ include "common.names.fullname" . | quote }}
  namespace: {{ include "common.names.namespace" $ }}
  labels:
    {{- include "common.labels.standard" $ | nindent 4 }}
    {{- with .Values.commonLabels }}
    {{- include "company.common.tpl" (dict "value" . "context" $) | nindent 4 }}
    {{- end }}
  {{- with .Values.commonAnnotations }}
  annotations:
    {{- include "company.common.tpl" (dict "value" . "context" $) | nindent 4 }}
  {{- end }}
spec:
  maxUnavailable: {{ .Values.pdb.maxUnavailable | default 0 }}
  selector:
    matchLabels:
      {{- include "common.labels.matchLabels" $ | nindent 6 }}
{{- end }}
{{- end }}
```

### ServiceMonitor.yaml

```yaml
{{- if .Values.metrics.enabled }}
{{- if .Values.metrics.serviceMonitor.enabled }}
{{- $smon := .Values.metrics.serviceMonitor }}
{{- $fullname := include "common.names.fullname" . -}}
{{- $ns := include "common.names.namespace" . -}}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ $fullname | trunc 63 | trimSuffix "-" | quote }}
  namespace: {{ $ns | quote }}
  labels:
    {{- include "common.labels.standard" $ | nindent 4 }}
    {{- with $smon.labels }}
    {{- include "company.common.tpl" (dict "value" . "context" $) | nindent 4 }}
    {{- end }}
spec:
  selector:
    matchLabels:
      {{- include "common.labels.matchLabels" $ | nindent 6 }}
  jobLabel: {{ $fullname | quote }}
  endpoints:
    - port: {{ .Values.portName | quote }}
      path: /metrics
      scheme: http
      interval: {{ $smon.interval | default "1m" | quote }}
      scrapeTimeout: {{ $smon.scrapeTimeout | default "10s" | quote }}
      {{- with $smon.relabelings }}
      relabelings:
        {{- include "company.common.tpl" (dict "value" . "context" $) | nindent 8 }}
      {{- end }}
      metricRelabelings:
        {{- with $smon.dropMetricsLabels }}
        - action: labeldrop
          regex: {{ printf "^(%s)$" (join "|" .) | quote }}
        {{- end }}
        - { action: replace, targetLabel: job,       replacement: {{ $fullname | quote }} }
        - { action: replace, targetLabel: namespace,  replacement: {{ $ns | quote }} }
        {{- with $smon.metricRelabelings }}
        {{- include "company.common.tpl" (dict "value" . "context" $) | nindent 8 }}
        {{- end }}
  namespaceSelector:
    matchNames:
      - {{ $ns | quote }}
{{- end }}
{{- end }}
```

______________________________________________________________________

## Makefile — Standard Targets

```makefile
SHELL := /bin/bash -e -u -o pipefail -o errexit -o nounset -c

name=$(shell pwd | rev | cut -d '/' -f 1 | rev)
work_dir=/tmp/helm_chart_$(name)
deps_dir=$(shell pwd)/charts

clean:
	rm -rf $(work_dir) $(shell pwd)/Chart.lock $(deps_dir)
	helm dependency build --skip-refresh
	for file in $$(ls -1 $(deps_dir)/*.tgz); do tar -xzf $${file} -C $(deps_dir) && rm -rf $${file}; done

test:
	helm unittest --color --debug --strict $(shell pwd)

_render:
	mkdir -p $(work_dir)
	helm template $(name) \
		--namespace default \
		$$(text="" && sep="" && for i in $$(kubectl api-versions); do text="$${text}$${sep}--api-versions $${i}" && sep=" "; done; echo -n "$${text}") \
		--values $(shell pwd)/values.yaml \
		$(shell pwd) > $(work_dir)/$(name)-helm-all.yaml

render:
	time make _render

ct:
	ct lint \
		--helm-dependency-extra-args='--skip-refresh' \
		--charts=$(shell pwd) \
		--validate-maintainers=false \
		--validate-chart-schema=true \
		--remote=origin \
		--target-branch=$(shell git branch --show-current -q) \
		--validate-yaml=false \
		--print-config=true \
		--debug=true \
		--lint-conf $(shell cd ../.. && pwd)/.yamllint.yaml
```

> **ArgoCD variant**: If your charts are deployed via ArgoCD in a monorepo alongside ArgoCD Applications,
> you can derive the release name and namespace from the Application manifest:
>
> ```makefile
> _render:
> 	mkdir -p $(work_dir)
> 	helm template $(shell yq '.metadata.name' path/to/argocd/apps/$(name).yaml) \
> 		--namespace $(shell yq '.spec.destination.namespace' path/to/argocd/apps/$(name).yaml) \
> 		... (rest of flags) ...
> ```

______________________________________________________________________

## ci/test-values.yaml

Must exercise every optional path to ensure `ct lint` succeeds:

```yaml
---
nameOverride: ""
fullnameOverride: ""

global:
  revisionHistoryLimit: 13

caBundle:
  secret:
    name: example-certs-bundle-test
    key: ca-certificates.crt

image:
  pullPolicy: Never

commonLabels:
  common-label-test: common-label-test
commonAnnotations:
  common-annotation-test: common-annotation-test
podLabels:
  pod-label-test: pod-label-test
podAnnotations:
  pod-annotation-test: pod-annotation-test

startupProbe:
  enabled: true
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 10
  successThreshold: 10
  failureThreshold: 10

livenessProbe:
  enabled: true
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 10
  successThreshold: 10
  failureThreshold: 10

readinessProbe:
  enabled: true
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 10
  successThreshold: 10
  failureThreshold: 10
```

______________________________________________________________________

## YAML Style Rules

- **Indentation**: 2 spaces — enforced by yamllint
- **Line length**: ~120 chars (warning)
- **Start every file** with `---`
- **Resource names**: lowercase, `-` separators, max 63 chars
- **Values keys**: camelCase namespaced (`image.tag`, `replicaCount`, `resources.requests.cpu`)
- **Multi-resource files**: use `---` separators between resources
- **No trailing whitespace**

______________________________________________________________________

## Security Defaults (always apply)

| Field                   | Value                             | Reason                       |
| ----------------------- | --------------------------------- | ---------------------------- |
| `enableServiceLinks`    | `false`                           | Prevent env var leakage      |
| `hostNetwork`           | `false`                           | Network isolation            |
| `dnsPolicy`             | `ClusterFirstWithHostNet`         | Works with hostNetwork false |
| `/tmp` volume           | `emptyDir: { medium: Memory }`    | No host disk writes          |
| `/dev/shm` volume       | same emptyDir via subPath         | Shared memory isolation      |
| `rbac.create: true`     | ServiceAccount created by default | Least privilege              |
| `pdb.maxUnavailable: 0` | Zero disruption by default        | HA guarantee                 |

______________________________________________________________________

## Common Mistakes

| Mistake                                       | Fix                                                              |
| --------------------------------------------- | ---------------------------------------------------------------- |
| Missing `bitnami-common` dep                  | Always add both bitnami/common AND company-common                |
| `additionalProperties: true` on leaf objects  | Set to `false` where schema is stable                            |
| Secrets mounted as env vars inline            | Use `company.common.env-var` with secret ref pattern             |
| Not adding secret name to Reloader annotation | Collect all secret names into `$reloaderSecretNames` list        |
| `charts/*.tgz` committed                      | Run `make clean` — only directories go in `charts/`              |
| Probes hard-coded                             | Always support override via values (enabled + all timing fields) |
| Missing `ci/test-values.yaml`                 | Required by `ct lint` — cover all optional blocks                |
| Using `tpl` directly                          | Use `company.common.tpl` — handles primitives and objects safely |
| Missing `---` at top of YAML files            | yamllint will fail on missing document start                     |

______________________________________________________________________

## company-common Library Reference

The `company-common` dependency provides a set of reusable Go template helpers.
Copy these into your own `company-common` library chart under `templates/`.
Rename the `company.common.*` prefix to match your library chart name.

### `company.common.tpl` — safe template wrapper

Renders a value that may contain `{{ }}` Go template expressions.
Handles all primitive types (string, int, bool, float) plus objects/maps safely.
Use this instead of the built-in `tpl` everywhere — it avoids errors on non-string values.

```gotemplate
{{- define "company.common.tpl" -}}
{{- $value := "" -}}
{{- $ctx := "" -}}
{{- if has (typeOf .) (list "list" "slice" "[]interface {}") -}}
  {{- $value = index . 0 -}}
  {{- $ctx = index . 1 -}}
{{- else -}}
  {{- $value = .value -}}
  {{- $ctx = default .ctx .context -}}
{{- end -}}
{{- if has (typeOf $value) (list "float32" "float64" "int" "int8" "int16" "int32" "int64" "bool" "rune" "uint" "uint8" "uint16" "uint32" "uint64") -}}
  {{- $value -}}
{{- else if has (typeOf $value) (list "string") -}}
  {{- $value = toString $value -}}
  {{- if contains "{{" $value -}}{{- $value = tpl $value $ctx -}}{{- end -}}
  {{- $value -}}
{{- else -}}
  {{- $value = toYaml $value -}}
  {{- if contains "{{" $value -}}{{- $value = tpl $value $ctx -}}{{- end -}}
  {{- $value -}}
{{- end -}}
{{- end -}}
```

### `company.common.appVersion` — chart app version

Returns `.Values.appVersionOverride` if set (supports Go template expressions), otherwise `.Chart.AppVersion`.

```gotemplate
{{- define "company.common.appVersion" -}}
{{- $version := .Values.appVersionOverride -}}
{{- if $version -}}
  {{- $version = tpl $version . -}}
{{- else -}}
  {{- $version = .Chart.AppVersion -}}
{{- end -}}
{{- $version -}}
{{- end -}}
```

### `company.common.image` — full image reference

Builds the full `[registry/]repository:tag[@sha256:digest]` image string.

```gotemplate
{{/*
image:
  registry: docker.io        # optional
  repository: minio/sidekick # required
  tag: latest                # optional — falls back to appVersionOverride / Chart.AppVersion
  sha256: abc123             # optional
*/}}
{{- define "company.common.image" -}}
{{- $ctx := .ctx | default .context -}}
{{- $repository := include "company.common.tpl" (list (.image.repository | toString) $ctx) -}}
{{- $tag := include "company.common.image.version" . -}}
{{- $image := printf "%s:%s" $repository $tag -}}
{{- if .image.registry -}}
  {{- $registry := include "company.common.tpl" (list (.image.registry | toString) $ctx) -}}
  {{- $image = printf "%s/%s" $registry $image -}}
{{- end -}}
{{- with .image.sha256 -}}
  {{- $sha256 := include "company.common.tpl" (list (. | toString) $ctx) | trimPrefix "@" | trimPrefix "sha256:" -}}
  {{- $image = printf "%s@sha256:%s" $image $sha256 -}}
{{- end -}}
{{- $image -}}
{{- end -}}

{{- define "company.common.image.version" -}}
{{- $ctx := .ctx | default .context -}}
{{- include "company.common.tpl" (list (.image.tag | default $ctx.Values.appVersionOverride | default $ctx.Chart.AppVersion | toString) $ctx) -}}
{{- end -}}
```

### `company.common.imagePullPolicy` — smart pull policy

Returns `Always` when tag is empty or `latest`; `IfNotPresent` otherwise.
Respects `image.pullPolicy` override.

```gotemplate
{{- define "company.common.imagePullPolicy" -}}
{{- $ctx := coalesce (index . "ctx") (index . "context") -}}
{{- $image := index . "image" -}}
{{- if $image.pullPolicy -}}
  {{- include "company.common.tpl" (list ($image.pullPolicy | toString) $ctx) -}}
{{- else -}}
  {{- $tag := (include "company.common.image.version" . | trim) -}}
  {{- if or (eq $tag "") (eq $tag "latest") -}}
    {{- "Always" -}}
  {{- else -}}
    {{- "IfNotPresent" -}}
  {{- end -}}
{{- end -}}
{{- end -}}
```

### `company.common.imagePullSecrets` — image pull secrets list

Merges `global.imagePullSecrets` with per-image `pullSecrets`.

```gotemplate
{{- define "company.common.imagePullSecrets" -}}
{{- $pullSecrets := list -}}
{{- $context := .context | default .ctx -}}
{{- if and $context.Values.global $context.Values.global.imagePullSecrets -}}
  {{- range $context.Values.global.imagePullSecrets -}}
    {{- $pullSecrets = append $pullSecrets (include "company.common.tpl" (list . $context)) -}}
  {{- end -}}
{{- end -}}
{{- if .images -}}
  {{- range .images -}}
    {{- if .pullSecrets -}}
      {{- range .pullSecrets -}}
        {{- $pullSecrets = append $pullSecrets (include "company.common.tpl" (list . $context)) -}}
      {{- end -}}
    {{- end -}}
  {{- end -}}
{{- end -}}
{{- $pullSecrets = uniq $pullSecrets -}}
{{- if (not (empty $pullSecrets)) -}}
imagePullSecrets:
  {{- range $pullSecrets }}
  - name: {{ . | quote }}
  {{- end }}
{{- end }}
{{- end -}}
```

### `company.common.env-var` — flexible env var

Renders a single env var entry supporting four forms:

| Form | `conf` value                             | Result                      |
| ---- | ---------------------------------------- | --------------------------- |
| 1    | `"literal"` or primitive                 | `value: "literal"`          |
| 2    | `{ value: "..." }`                       | `value: "..."`              |
| 3    | `{ secret: { name: "s", key: "k" } }`    | `valueFrom.secretKeyRef`    |
| 4    | `{ configMap: { name: "m", key: "k" } }` | `valueFrom.configMapKeyRef` |

```gotemplate
{{- define "company.common.env-var" -}}
{{- $name := .name -}}
{{- $conf := .conf -}}
{{- $def := .default -}}
{{- $context := .ctx -}}
- name: {{ $name | quote }}
{{- if has (typeOf $conf) (list "string" "float32" "float64" "int" "int8" "int16" "int32" "int64" "bool") }}
  value: {{ include "company.common.tpl" (list ($conf | toString) $context) | quote }}
{{- else if and $conf $conf.secret $conf.secret.name }}
  valueFrom:
    secretKeyRef:
      name: {{ include "company.common.tpl" (list $conf.secret.name $context) | quote }}
      key: {{ $conf.secret.key | default $name | quote }}
{{- else if and $conf $conf.configMap $conf.configMap.name }}
  valueFrom:
    configMapKeyRef:
      name: {{ include "company.common.tpl" (list $conf.configMap.name $context) | quote }}
      key: {{ $conf.configMap.key | default $name | quote }}
{{- else if and $conf $conf.value }}
  value: {{ include "company.common.tpl" (list ($conf.value | toString) $context) | quote }}
{{- else if $def }}
  value: {{ include "company.common.tpl" (list ($def | toString) $context) | quote }}
{{- end }}
{{- end -}}
```

### `company.common.container.env` — standard container env vars

Injects locale vars (`LANG`, `LANGUAGE`, `LC_ALL`, `TZ`) and Kubernetes downward-API vars
(`POD_NAMESPACE`, `POD_NAME`, `POD_IP`, `POD_UID`).
Override `TZ` to your target timezone.

```gotemplate
{{- define "company.common.container.localeEnvs" -}}
- { name: LANG,     value: "en_US.UTF-8" }
- { name: LANGUAGE, value: "en_US:en" }
- { name: LC_ALL,   value: "en_US.UTF-8" }
- { name: TZ,       value: "UTC" }
{{- end -}}

{{- define "company.common.container.k8sEnvs" -}}
- { name: POD_NAMESPACE, valueFrom: { fieldRef: { fieldPath: metadata.namespace } } }
- { name: POD_NAME,      valueFrom: { fieldRef: { fieldPath: metadata.name } } }
- { name: POD_IP,        valueFrom: { fieldRef: { fieldPath: status.podIP } } }
- { name: POD_UID,       valueFrom: { fieldRef: { fieldPath: metadata.uid } } }
{{- end -}}

{{- define "company.common.container.env" -}}
{{ include "company.common.container.localeEnvs" . }}
{{ include "company.common.container.k8sEnvs" . }}
{{- end -}}
```

### Additional helpers (recommended additions)

The following helpers from the original library are **not shown above** but are commonly needed.
Add them to your library chart if your charts use them.

#### `company.common.fixInt64` — normalize float-to-int in YAML

Helm renders whole numbers as `float64` (e.g. `1.00000`). Use this when setting integer values
in properties files or JSON output:

```gotemplate
{{- define "company.common.fixInt64" -}}
{{- $v := . -}}
{{- if and (has (typeOf $v) (list "float64" "float32" "float")) (eq (printf "%f" (ceil $v)) (printf "%f" (floor $v))) -}}
  {{- $v = printf "%d" ($v | int64) -}}
{{- end -}}
{{- $v -}}
{{- end -}}
```

#### `company.common.renderIndentProps` — space-aligned property files

Renders a map as space-indented `key   value` lines (useful for Spark/JVM config files).
Keys are padded with spaces so values align:

```gotemplate
{{/*
Usage:
  {{ include "company.common.renderIndentProps" (dict "props" .Values.sparkConf "ctx" $) }}
*/}}
{{- define "company.common.renderIndentProps" -}}
{{- $props := coalesce (index . "props") (index . "properties") -}}
{{- $ctx := coalesce (index . "ctx") (index . "context") -}}
{{- $longest := 0 -}}
{{- range $key, $value := $props -}}
  {{- $longest = max $longest (len $key) -}}
{{- end -}}
{{- $text := "" -}}
{{- range $key, $value := $props -}}
  {{- $space := "   " -}}
  {{- range until (sub $longest (len $key) | int) -}}
    {{- $space = print $space " " -}}
  {{- end -}}
  {{- $text = printf "%s\n%v%s%v" $text $key $space $value -}}
{{- end -}}
{{- include "company.common.tpl" (list $text $ctx) | trim -}}
{{- end -}}
```

#### `company.common.flatMap` — flatten nested map to JSON object

Converts a nested Go map to a flat `{"a.b.c": "value"}` JSON object.
Useful for rendering Spark configuration as a flat JSON blob:

```gotemplate
{{- define "company.common.flatMap" -}}
{{- $data := include "company.common.internal.recurseFlattenMap" (list . "") | trimSuffix "," -}}
{{- print "{" $data "}" -}}
{{- end -}}

{{- define "company.common.internal.recurseFlattenMap" -}}
{{- $map := index . 0 -}}
{{- $label := index . 1 -}}
{{- range $key, $val := $map -}}
  {{- $sublabel := $key -}}
  {{- if $label -}}
    {{- $sublabel = list $label $key | join "." -}}
  {{- end -}}
  {{- if kindOf $val | eq "map" -}}
    {{- include "company.common.internal.recurseFlattenMap" (list $val $sublabel) -}}
  {{- else -}}
    {{- if has (typeOf $val) (list "bool" "float32" "float64" "int" "int8" "int16" "int32" "int64") -}}
    {{- else -}}
      {{- $val = $val | quote -}}
    {{- end -}}
    {{- printf "%v: %v," ($sublabel | quote) ($val) -}}
  {{- end -}}
{{- end -}}
{{- end -}}
```
