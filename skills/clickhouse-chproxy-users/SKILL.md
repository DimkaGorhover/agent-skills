---
name: clickhouse-chproxy-users
description: Use when configuring chproxy user authentication, wildcard passthrough, heartbeat users, or LDAP integration with ClickHouse. Triggers when setting up chproxy clusters, users, or dealing with 401 probe failures.
metadata:
  author: d.horkhover
  version: 1.0.0
---

# chproxy User Auth & Wildcard Passthrough

## When to Use

- Configuring chproxy ingress users with wildcard passthrough (`is_wildcarded: true`)
- Setting up LDAP passthrough authentication through chproxy to ClickHouse
- Diagnosing `401` probe failures on chproxy in Kubernetes (liveness/readiness)
- Configuring a dedicated heartbeat user for non-`/ping` health check endpoints
- Reviewing or writing chproxy cluster user configuration

## When NOT to Use

- ClickHouse configuration unrelated to chproxy (schema design, query tuning, replication)
- Non-chproxy ClickHouse proxies or load balancers
- General LDAP/authentication debugging outside the chproxy layer

## How `is_wildcarded: true` Works (passthrough mode)

When a chproxy ingress user has `is_wildcarded: true`, chproxy does **not** validate the incoming password. Instead it:

1. Matches the client's username against the wildcard pattern (`*`, `prefix*`, `*suffix`)
1. Deep-copies the cluster user template
1. Overwrites `cu.name = incoming_username`, `cu.password = incoming_password`
1. Forwards the request to ClickHouse with the **original client credentials**

Source: `proxy.go:871-889`, `scope.go:437-443`

**The `to_user: "*"` cluster user acts as a template only** — its name/password are replaced by the client's. ClickHouse receives the real user credentials, enabling LDAP or any native ClickHouse auth to work transparently.

## Security Constraint: Empty / `default` User Blocked

`proxy.go:831-833`:

```go
case name == "" || name == defaultUser:
    // default user can't work with the wildcarded feature for security reasons
    found = false
```

Empty username or `"default"` **always returns 401** in wildcard mode. This means:

- **Kubernetes liveness/readiness probes using `httpGet /ping` with no credentials will always fail** (401)
- Use `tcpSocket` probes or disable probes entirely for chproxy in wildcard mode

## Heartbeat Behavior

Source: `internal/heartbeat/heartbeat.go:55-95`

- Default heartbeat request: `GET /ping` — **no auth sent** (ClickHouse `/ping` is unauthenticated)
- Custom heartbeat requests: auth is sent using `heartbeat.user` / `heartbeat.password`
- If `heartbeat.request != "/ping"` and no `heartbeat.user` set → **config validation panics**
- If cluster uses only wildcarded users → heartbeat cannot use wildcard passthrough → must set explicit `heartbeat.user`

Source: `proxy.go:746-765`:

```
if heartbeat.Request != "/ping" && len(heartbeat.User) == 0 {
    // config rejected for wildcarded clusters
}
```

## Minimal Wildcard Passthrough Config

```yaml
allow_ping: true

server:
  http:
    listen_addr: ":9090"
    allowed_networks:
      - "172.17.0.0/16"

users:
  - name: "*"
    to_cluster: "default"
    to_user: "*"
    is_wildcarded: true

clusters:
  - name: "default"
    scheme: "http"
    nodes:
      - "clickhouse-shard0-0.clickhouse-headless.clickhouse.svc:8123"
    users:
      - name: "*"
    # No heartbeat section = uses /ping (no auth required)
```

ClickHouse receives the actual LDAP username + password from the client. No cluster user password needed in chproxy config.

## When Heartbeat Needs Auth (non-`/ping` endpoint)

Add a dedicated local ClickHouse user (non-LDAP) just for heartbeat:

```yaml
clusters:
  - name: "default"
    nodes:
      - "clickhouse:8123"
    users:
      - name: "*"
    heartbeat:
      interval: 5s
      timeout: 3s
      request: "/?query=SELECT+1"
      response: "1\n"
      user: chproxy_heartbeat
      password: "${CHPROXY_HEARTBEAT_PASSWORD}"
```

Create the ClickHouse user as a local (non-LDAP) user so chproxy can authenticate for heartbeat checks only.

## Helm Chart Pattern

In Helm-managed chproxy deployments, gate probes behind values flags
(e.g. `chproxy.livenessProbe.enabled` / `chproxy.readinessProbe.enabled`).

Default these flags to `false` because unauthenticated `httpGet /ping` probes
always return 401 with no credentials in wildcard passthrough mode.

To re-enable probes safely, use one of these patterns:

1. `tcpSocket` probes (port-level check, no auth required)
1. A dedicated non-wildcarded chproxy user with a known password used by authenticated HTTP probes

## References

- `proxy.go:820-889` — `getUser` + `generateWildcardedUserInformation`
- `scope.go:391-400` — `/ping` forwarded without auth rewrite
- `internal/heartbeat/heartbeat.go` — heartbeat auth logic
- `config/config.go` — `HeartBeat` struct fields: `User`, `Password`, `Request`, `Response`, `Interval`, `Timeout`
- [chproxy wildcard docs](https://www.chproxy.org/use-cases/wildcarded/)
