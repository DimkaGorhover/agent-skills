---
name: helm-chart-structuring
description: Use when creating, extending, or reviewing Helm charts in the rke2-deployments/helm-charts repository. Triggers when adding new chart files, new templates, new values keys, or a new chart from scratch.
---

# Helm Chart Structuring — Palefat/RKE2 Repository

## When to Use

- Creating a new Helm chart from scratch in the `rke2-deployments/helm-charts` repository
- Adding new templates, values keys, or dependencies to an existing chart
- Reviewing a chart for layout compliance, missing templates, or schema issues
- Setting up `ct lint`, ArgoCD rendering, or stakater Reloader annotations

## When NOT to Use

- Generic Helm questions unrelated to the palefat/rke2-deployments repository structure
- Charts for other repositories that don't use `palefat-common` and bitnami `common` dependencies
- Helm chart unit testing — use the `helm-chart-unittest` skill instead

## Overview

Every application chart in `helm-charts/` follows a strict, repeatable layout.
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
    email: <email@temabit.com>
dependencies:
  - name: common
    repository: https://nexus.fozzy.lan/repository/helm-hosted-bitnami/
    tags:
      - bitnami-common
    version: 2.x.x
  - name: palefat-common
    repository: file://../palefat-common
    tags:
      - palefat-common
    version: x.x.x
```

**Rules:**

- Both `common` (bitnami) and `palefat-common` are **always** required.
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
  registry: nexus.fozzy.lan
  repository: palefat/<app>
  pullPolicy: Always # or IfNotPresent for pinned tags

logLevel: debug # app log level

caBundle: # mount internal CA bundle
  secret:
    name: fozzy-certs-bundle

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

Render it in templates via `palefat.common.env-var`.

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
      "required": ["global", "port", "image", "portName", "resources"],
      "properties": {
        "global": {
          "$ref": "https://temabit-fozzy-group.github.io/helm-json-schemas/helm/Global.json"
        },
        "image": {
          "$ref": "https://temabit-fozzy-group.github.io/helm-json-schemas/helm/Image.json"
        },
        "resources": {
          "$ref": "https://temabit-fozzy-group.github.io/helm-json-schemas/k8s/Resources.json"
        },
        "livenessProbe": {
          "$ref": "https://temabit-fozzy-group.github.io/helm-json-schemas/helm/Probe.json"
        },
        "readinessProbe": {
          "$ref": "https://temabit-fozzy-group.github.io/helm-json-schemas/helm/Probe.json"
        },
        "startupProbe": {
          "$ref": "https://temabit-fozzy-group.github.io/helm-json-schemas/helm/Probe.json"
        },
        "pdb": {
          "$ref": "https://temabit-fozzy-group.github.io/helm-json-schemas/helm/PodDisruptionBudget.json"
        },
        "commonLabels": {
          "$ref": "https://temabit-fozzy-group.github.io/helm-json-schemas/k8s/Labels.json"
        },
        "commonAnnotations": {
          "$ref": "https://temabit-fozzy-group.github.io/helm-json-schemas/k8s/Annotations.json"
        },
        "podLabels": {
          "$ref": "https://temabit-fozzy-group.github.io/helm-json-schemas/k8s/Labels.json"
        },
        "podAnnotations": {
          "$ref": "https://temabit-fozzy-group.github.io/helm-json-schemas/k8s/Annotations.json"
        },
        "port": { "type": "integer", "default": 8080 },
        "portName": { "type": "string", "default": "http" },
        "nameOverride": { "type": "string" },
        "fullnameOverride": { "type": "string" }
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
| `palefat.common.image`            | palefat-common | full `registry/repo:tag` string         |
| `palefat.common.imagePullPolicy`  | palefat-common | pull policy (always for `latest`)       |
| `palefat.common.tpl`              | palefat-common | render values that may contain `{{ }}`  |
| `palefat.common.container.env`    | palefat-common | locale + k8s downward-API envs          |
| `palefat.common.env-var`          | palefat-common | env var supporting secret/configmap ref |

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
    {{- include "palefat.common.tpl" (dict "value" .Values.commonLabels "context" .) | nindent 4 }}
    {{- end }}
  {{- if or $reloaderSecretNames .Values.commonAnnotations }}
  annotations:
    secret.reloader.stakater.com/reload: {{ $reloaderSecretNames | join "," | quote }}
    {{- if .Values.commonAnnotations }}
    {{- include "palefat.common.tpl" (dict "value" .Values.commonAnnotations "context" .) | nindent 4 }}
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
        {{- include "palefat.common.tpl" (dict "value" .Values.commonLabels "context" .) | nindent 8 }}
        {{- end }}
        {{- if .Values.podLabels }}
        {{- include "palefat.common.tpl" (dict "value" .Values.podLabels "context" .) | nindent 8 }}
        {{- end }}
      annotations:
        {{- if .Values.podAnnotations }}
        {{- include "palefat.common.tpl" (dict "value" .Values.podAnnotations "context" .) | nindent 8 }}
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
          image: {{ include "palefat.common.image" (dict "image" .Values.image "ctx" .) }}
          imagePullPolicy: {{ include "palefat.common.imagePullPolicy" (dict "image" .Values.image "ctx" .) }}
          env:
            {{- include "palefat.common.container.env" . | nindent 12 }}
          ports:
            - name: {{ .Values.portName | quote }}
              containerPort: {{ .Values.port }}
              protocol: TCP
          {{- with .Values.resources }}
          resources:
            {{- include "palefat.common.tpl" (dict "value" . "context" $) | nindent 12 }}
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
        {{- with .Values.caBundle }}{{- with .secret }}
        - name: ca-cert-pem
          secret:
            secretName: {{ .name | quote }}
        {{- end }}{{- end }}
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
    {{- include "palefat.common.tpl" (dict "value" . "context" .) | nindent 4 }}
    {{- end }}
  {{- with .Values.commonAnnotations }}
  annotations:
    {{- include "palefat.common.tpl" (dict "value" . "context" .) | nindent 4 }}
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
    {{- include "palefat.common.tpl" (dict "value" . "context" .) | nindent 4 }}
    {{- end }}
  {{- with .Values.commonAnnotations }}
  annotations:
    {{- include "palefat.common.tpl" (dict "value" . "context" .) | nindent 4 }}
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
    {{- include "palefat.common.tpl" (dict "value" . "context" $) | nindent 4 }}
    {{- end }}
  {{- with .Values.commonAnnotations }}
  annotations:
    {{- include "palefat.common.tpl" (dict "value" . "context" $) | nindent 4 }}
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
    {{- include "palefat.common.tpl" (dict "value" . "context" .) | nindent 4 }}
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
        {{- include "palefat.common.tpl" (dict "value" . "context" $) | nindent 8 }}
      {{- end }}
      metricRelabelings:
        {{- with $smon.dropMetricsLabels }}
        - action: labeldrop
          regex: {{ printf "^(%s)$" (join "|" .) | quote }}
        {{- end }}
        - { action: replace, targetLabel: job,       replacement: {{ $fullname | quote }} }
        - { action: replace, targetLabel: namespace,  replacement: {{ $ns | quote }} }
        {{- with $smon.metricRelabelings }}
        {{- include "palefat.common.tpl" (dict "value" . "context" $) | nindent 8 }}
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
work_dir=/Volumes/RAMDisk/temabit/helm_chart_$(name)
deps_dir=$(shell pwd)/charts

clean:
	rm -rf $(work_dir) $(shell pwd)/Chart.lock $(deps_dir)
	helm dependency build --skip-refresh
	for file in $$(ls -1 $(deps_dir)/*.tgz); do tar -xzf $${file} -C $(deps_dir) && rm -rf $${file}; done

test:
	helm unittest --color --debug --strict $(shell pwd)

_render:
	mkdir -p $(work_dir)
	helm template $(shell yq '.metadata.name' ../../argocd/projects/<project>/apps/$(name).yaml) \
		--namespace $(shell yq '.spec.destination.namespace' ../../argocd/projects/<project>/apps/$(name).yaml) \
		$$(text="" && sep="" && for i in $$(kubectl api-versions); do text="$${text}$${sep}--api-versions $${i}" && sep=" "; done; echo -n "$${text}") \
		--values $(shell pwd)/values.yaml \
		-f <(yq '.spec.source.helm.values' ../../argocd/projects/<project>/apps/$(name).yaml | yq) \
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

Replace `<project>` with the ArgoCD project name (e.g. `monitoring`).

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
    name: fozzy-certs-bundle-test
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
| Missing `bitnami-common` dep                  | Always add both bitnami/common AND palefat-common                |
| `additionalProperties: true` on leaf objects  | Set to `false` where schema is stable                            |
| Secrets mounted as env vars inline            | Use `palefat.common.env-var` with secret ref pattern             |
| Not adding secret name to Reloader annotation | Collect all secret names into `$reloaderSecretNames` list        |
| `charts/*.tgz` committed                      | Run `make clean` — only directories go in `charts/`              |
| Probes hard-coded                             | Always support override via values (enabled + all timing fields) |
| Missing `ci/test-values.yaml`                 | Required by `ct lint` — cover all optional blocks                |
| Using `tpl` directly                          | Use `palefat.common.tpl` — handles primitives and objects safely |
| Missing `---` at top of YAML files            | yamllint will fail on missing document start                     |
