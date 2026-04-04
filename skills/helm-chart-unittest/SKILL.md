---
name: helm-chart-unittest
description: Use when writing, reviewing, or extending helm-unittest test files for Helm charts. Covers file structure, assertion patterns, test values, multi-document templates, and conditional rendering.
---

# Helm Chart Unit Testing (helm-unittest)

## When to Use

- Writing new `helm-unittest` test files for Helm charts following the company-common + bitnami pattern
- Reviewing or extending existing test suites (`_test.yaml` files)
- Debugging assertion failures in `helm unittest` output
- Adding coverage for conditional rendering, multi-document templates, or CRD-gated resources

## When NOT to Use

- Helm charts that don't follow the company-common + bitnami layout used by this skill
- Writing Helm chart templates themselves — use the `helm-chart-structuring` skill instead
- Other Helm testing frameworks (Terratest, chart-testing `ct`)

This skill captures the patterns for writing `helm-unittest` test suites for complex multi-component charts.

## File Layout

```
helm-charts/<chart>/
└── tests/
    ├── <component>_test.yaml          # snake_case, _test.yaml suffix
    ├── <other-component>_test.yaml
    └── values/
        └── <component>-test-values.yaml   # kebab-case, -test-values.yaml suffix
```

**Naming rules:**

- Test files: `snake_case` with `_test.yaml` suffix (e.g., `metrics_proxy_test.yaml`)
- Values files: `kebab-case` with `-test-values.yaml` suffix (e.g., `metrics-proxy-test-values.yaml`)
- Values files live in `tests/values/` subdirectory

## Test File Structure

Every test file starts with this top-level structure:

```yaml
---
suite: <component-name>           # human-readable suite name, kebab-case
templates:                        # ALL templates the suite may reference
  - path/to/Template.yaml
  - path/to/other/Resource.yaml
  - configs/shared-config.yaml   # include shared configs even if not directly tested

release:
  name: <chart-release-name>     # e.g. "my-app", "my-service"
  namespace: <target-namespace>  # e.g. "my-app", "production"

# Optional — override chart metadata for version-sensitive label assertions
chart:
  version: 8.8.9
  appVersion: 7.7.7

values:
  - values/<component>-test-values.yaml   # path relative to tests/ dir

tests:
  - it: <test description>
    ...
```

## Individual Test Structure

```yaml
tests:
  - it: <plain-english description of what is being verified>
    template: path/to/Template.yaml    # required - which template to render
    documentIndex: 0                   # optional - for multi-document templates
    set:                               # optional - inline value overrides
      key: value
      nested.key: value
    capabilities:                      # optional - for CRD-gated resources
      apiVersions:
        - monitoring.coreos.com/v1
    asserts:
      - <assertion>
      - <assertion>
```

## Assertion Reference

### Kind and existence

```yaml
# Verify resource kind (always first assertion)
- isKind:
    of: Deployment

# Assert no documents rendered (conditional/disabled resources)
- hasDocuments:
    count: 0
```

### Exact equality

```yaml
# Short form (use for metadata fields)
- equal: { path: metadata.name, value: vault-metrics-proxy }
- equal: { path: metadata.namespace, value: vault }
- equal: { path: spec.type, value: ClusterIP }
- equal: { path: spec.replicas, value: 3 }

# Long form (use for complex objects)
- equal:
    path: metadata.labels
    value:
      app.kubernetes.io/instance: minio-v2
      app.kubernetes.io/managed-by: Helm
      app.kubernetes.io/name: minio
      helm.sh/chart: minio-8.8.9
      app.kubernetes.io/component: sidekick

# Annotation with dotted key — use bracket notation
- equal:
    path: metadata.annotations["secret.reloader.stakater.com/reload"]
    value: vault-root-token-test
```

### List assertions

```yaml
# Length check
- lengthEqual:
    path: spec.template.spec.containers
    count: 1

# Contains item (use for env vars, ports, volumeMounts, args)
- contains:
    path: spec.template.spec.containers[0].env
    content:
      name: AIRFLOW__DATABASE__SQL_ALCHEMY_POOL_ENABLED
      value: "True"

# Contains with count (asserts exactly N matches)
- contains:
    path: spec.template.spec.containers[0].args
    content: --host-balance=least
    count: 1
```

### Regex match (for ConfigMap embedded YAML)

```yaml
# Use matchRegex when asserting on ConfigMap data that contains rendered YAML
- matchRegex:
    path: data["pod_template.yaml"]
    pattern: '- name:\s*AIRFLOW__DATABASE__SQL_ALCHEMY_POOL_SIZE\s+value:\s*"5"'
```

## Standard Test Sequence

Every component test file should follow this order:

1. **Kind + metadata** — `isKind`, `metadata.name`, `metadata.namespace`
1. **Namespace override** — verify `namespaceOverride` works
1. **Name override** — verify `fullnameOverride` changes the resource name
1. **Default values** — verify defaults from test values file render correctly
1. **Value overrides** — verify `set:` overrides are applied correctly
1. **Conditional rendering** — use `hasDocuments: { count: 0 }` for `enabled: false` paths
1. **Related resources** — test PDB, Service, Ingress, ServiceMonitor in separate `it:` blocks

### Canonical metadata test

```yaml
- it: deployment should have the correct metadata name
  template: webserver/Deployment.yaml
  set:
    fullnameOverride: af
  asserts:
    - isKind:
        of: Deployment
    - equal:
        path: metadata.name
        value: af-webserver
    - equal:
        path: metadata.namespace
        value: airflow-ns

- it: deployment namespace
  template: webserver/Deployment.yaml
  set:
    namespaceOverride: dev
  asserts:
    - equal:
        path: metadata.namespace
        value: dev
```

### PDB test

```yaml
- it: validate pdb
  template: scheduler/pdb.yaml
  asserts:
    - equal:
        path: metadata.name
        value: airflow-scheduler
    - equal:
        path: metadata.namespace
        value: airflow-ns
    - equal:
        path: spec.maxUnavailable
        value: 0
```

### Service port test

```yaml
- it: validate service ports
  template: webserver/Service.yaml
  set:
    webserver:
      port: 4567
  asserts:
    - lengthEqual:
        path: spec.ports
        count: 1
    - equal:
        path: spec.ports[0].name
        value: http
    - equal:
        path: spec.ports[0].port
        value: 4567
    - equal:
        path: spec.ports[0].targetPort
        value: http
```

### Ingress tests

```yaml
- it: validate ingress class name
  template: webserver/ingress.yaml
  set:
    webserver:
      ingress:
        enabled: true
        ingressClassName: traefik
  asserts:
    - equal:
        path: spec.ingressClassName
        value: traefik

- it: validate ingress tls config
  template: webserver/ingress.yaml
  set:
    webserver:
      ingress:
        enabled: true
        hostname: test.host.name
        tlsSecretName: tls-secret-name
  asserts:
    - lengthEqual:
        path: spec.tls
        count: 1
    - equal:
        path: spec.tls[0].hosts[0]
        value: test.host.name
    - equal:
        path: spec.tls[0].secretName
        value: tls-secret-name

- it: validate ingress rules
  template: webserver/ingress.yaml
  set:
    webserver:
      ingress:
        enabled: true
        path: /path
        hostname: test.host.name
  asserts:
    - lengthEqual:
        path: spec.rules
        count: 1
    - equal:
        path: spec.rules[0].http.paths[0].path
        value: /path
    - equal:
        path: spec.rules[0].http.paths[0].pathType
        value: Prefix
    - equal:
        path: spec.rules[0].http.paths[0].backend.service
        value:
          name: airflow-webserver-cs
          port: { name: http }
```

### Env var override test (default → component override)

```yaml
# Test 1: defaults from values file
- it: Should set the correct values (common) for sql alchemy pool
  template: scheduler/Deployment.yaml
  asserts:
    - contains:
        path: spec.template.spec.containers[0].env
        content:
          name: AIRFLOW__DATABASE__SQL_ALCHEMY_POOL_SIZE
          value: "5"

# Test 2: component-level override
- it: Should correctly override sql alchemy pool for 'scheduler' component
  template: scheduler/Deployment.yaml
  set:
    scheduler:
      config:
        database:
          pool:
            size: 10
  asserts:
    - contains:
        path: spec.template.spec.containers[0].env
        content:
          name: AIRFLOW__DATABASE__SQL_ALCHEMY_POOL_SIZE
          value: "10"
```

### Multi-document template (documentIndex)

```yaml
# When a template renders multiple documents (e.g. one per team/item)
- it: first document has correct name
  template: worker/DeploymentPerTeam.yaml
  documentIndex: 0
  asserts:
    - isKind:
        of: StatefulSet
    - equal:
        path: metadata.name
        value: "airflow-worker-team-0"

- it: second document has correct name
  template: worker/DeploymentPerTeam.yaml
  documentIndex: 1
  asserts:
    - isKind:
        of: StatefulSet
    - equal:
        path: metadata.name
        value: "airflow-worker-team-1"
```

### CRD-gated resources (capabilities)

```yaml
# Resource only renders when CRD is available
- it: podmonitor should render when capability present
  template: templates/metrics-proxy/PodMonitor.yaml
  capabilities:
    apiVersions:
      - monitoring.coreos.com/v1
  asserts:
    - isKind:
        of: PodMonitor
    - equal:
        path: metadata.name
        value: vault-metrics-proxy

- it: podmonitor should not render without monitoring.coreos.com/v1 capability
  template: templates/metrics-proxy/PodMonitor.yaml
  asserts:
    - hasDocuments:
        count: 0
```

### VolumeMount containment test

```yaml
- it: main container should mount nginx-work read-only
  template: templates/metrics-proxy/StatefulSet.yaml
  asserts:
    - contains:
        path: spec.template.spec.containers[0].volumeMounts
        content:
          name: nginx-work
          mountPath: /etc/nginx/conf.d
          readOnly: true
```

### secretKeyRef env var test

```yaml
- it: init container should have VAULT_TOKEN from secret
  template: templates/metrics-proxy/StatefulSet.yaml
  asserts:
    - contains:
        path: spec.template.spec.initContainers[0].env
        content:
          name: VAULT_TOKEN
          valueFrom:
            secretKeyRef:
              name: vault-root-token-test
              key: token
```

## Test Values File Patterns

Keep test values minimal — only what is needed to enable and configure the component:

```yaml
---
# Enable the component being tested
sidekick:
  enabled: true
  port: 8888
  portName: port0
  replicas: 4
  image:
    registry: ghcr.io
    repository: org/my-sidecar
    tag: 0.1.86      # pin explicit tag for reproducibility
    pullPolicy: IfNotPresent
  pdb:
    create: true
    maxUnavailable: 1

# Add labels/annotations for assertion verification
commonAnnotations:
  unittest: sidekick
commonLabels:
  unittest: sidekick
```

**Rules for test values:**

- Pin image tags explicitly — never use `latest` in test values
- Enable only the feature/component under test (e.g. `sidekick.enabled: true`)
- Include feature flags like `metrics.serviceMonitor.enabled: true` if testing ServiceMonitor
- Add `commonLabels`/`commonAnnotations` when you need to assert on labels/annotations

## Running Tests

```bash
# Run all tests for a chart
cd helm-charts/<chart> && make test

# Run with helm-unittest directly
helm unittest ./

# Filter to a specific test file
helm unittest ./ --file tests/<component>_test.yaml

# Run from repo root (all charts)
make test
```

## Checklist When Adding a New Test File

- [ ] File named `<component>_test.yaml` in `tests/`
- [ ] Values file named `<component>-test-values.yaml` in `tests/values/`
- [ ] `templates:` block includes ALL templates the suite uses (including shared configs)
- [ ] `release.name` and `release.namespace` match the real ArgoCD Application values
- [ ] First test asserts `isKind` + `metadata.name` + `metadata.namespace`
- [ ] Separate tests for namespace override and name override
- [ ] Default value tests before override tests
- [ ] `hasDocuments: { count: 0 }` test for every `enabled: false` conditional path
- [ ] CRD-gated resources tested both with and without `capabilities:`
- [ ] Multi-document templates use `documentIndex:`
- [ ] No secrets or cluster credentials in test values
