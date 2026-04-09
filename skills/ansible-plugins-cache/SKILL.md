---
name: ansible-plugins-cache
description: >-
  Use when selecting, configuring, or troubleshooting Ansible cache plugins for fact or inventory
  caching. Triggers on cache plugin selection, fact_caching configuration, inventory caching setup,
  cache backend comparison (memory/jsonfile/yaml/redis/memcached/mongodb), or cache-related
  performance questions.
metadata:
  author: d.horkhover
  version: 1.0.0
---

# Ansible Cache Plugins

## When to Use

- Selecting a cache plugin for fact caching or inventory caching
- Configuring `fact_caching` in `ansible.cfg` or environment variables
- Enabling and tuning inventory cache for plugins like `aws_ec2`
- Comparing cache backends (filesystem vs. in-memory vs. database)
- Troubleshooting stale facts or cache expiry issues
- Setting up Redis or Memcached as a shared cache for distributed Ansible runs

## When NOT to Use

- General Ansible role/playbook authoring — use `ansible-naming-conventions` instead
- Writing custom cache plugins (see the [developer guide](https://docs.ansible.com/projects/ansible/latest/dev_guide/developing_plugins.html#developing-cache-plugins))
- Cache-unrelated performance tuning (forks, pipelining, mitogen)

## Overview

Cache plugins allow Ansible to store gathered facts or inventory source data without the performance
hit of re-retrieving them from managed nodes or cloud APIs. Two independent caches exist:

| Cache type          | Default        | Config section | Key setting    |
| ------------------- | -------------- | -------------- | -------------- |
| **Fact cache**      | Always on      | `[defaults]`   | `fact_caching` |
| **Inventory cache** | Off by default | `[inventory]`  | `cache_plugin` |

Only **one** cache plugin can be active per cache type at a time. If inventory caching is enabled
without an explicit `cache_plugin`, Ansible falls back to the configured fact cache plugin.

> **Important:** The internal format of cached data is an implementation detail of each plugin.
> Never read or modify cache files/DB entries directly — always interact with facts inside a playbook.

______________________________________________________________________

## Plugin Reference

### ansible.builtin.memory

**FQCN:** `ansible.builtin.memory` | **Short name:** `memory`
**Part of:** `ansible-core` (always available) | **Default fact cache plugin**

RAM-backed, non-persistent. Data lives only for the duration of the current Ansible execution.
No configuration options required.

```ini
# ansible.cfg
[defaults]
fact_caching = memory
```

**Use when:** you want the default behavior; caching across runs is not needed.

______________________________________________________________________

### ansible.builtin.jsonfile

**FQCN:** `ansible.builtin.jsonfile` | **Short name:** `jsonfile`
**Part of:** `ansible-core` (always available)

Stores one JSON file per host on the local controller filesystem. Human-readable and easy to inspect.

**Parameters:**

| Parameter  | INI key (`[defaults]`)    | Env var                           | Default | Required |
| ---------- | ------------------------- | --------------------------------- | ------- | -------- |
| `_uri`     | `fact_caching_connection` | `ANSIBLE_CACHE_PLUGIN_CONNECTION` | —       | ✅       |
| `_prefix`  | `fact_caching_prefix`     | `ANSIBLE_CACHE_PLUGIN_PREFIX`     | —       |          |
| `_timeout` | `fact_caching_timeout`    | `ANSIBLE_CACHE_PLUGIN_TIMEOUT`    | `86400` |          |

```ini
# ansible.cfg
[defaults]
fact_caching            = jsonfile
fact_caching_connection = /tmp/ansible_cache
fact_caching_timeout    = 3600
```

```bash
# Environment variable equivalents
export ANSIBLE_CACHE_PLUGIN=jsonfile
export ANSIBLE_CACHE_PLUGIN_CONNECTION=/tmp/ansible_cache
export ANSIBLE_CACHE_PLUGIN_TIMEOUT=3600
```

**Use when:** you need persistent, human-readable per-host facts on a single controller.

______________________________________________________________________

### ansible.netcommon.memory

**FQCN:** `ansible.netcommon.memory` | **Short name:** `memory` (use FQCN to avoid collision with `ansible.builtin.memory`)
**Collection:** `ansible.netcommon` (≥ 2.0.0)

RAM-backed, non-persistent. Functionally identical to `ansible.builtin.memory` but tailored
for networking use cases (works well with network resource modules that populate structured facts).

```bash
ansible-galaxy collection install ansible.netcommon
```

```ini
# ansible.cfg
[defaults]
fact_caching = ansible.netcommon.memory
```

**Use when:** working with `ansible.netcommon` network modules and want cache semantics
aligned with that collection.

______________________________________________________________________

### community.general.yaml

**FQCN:** `community.general.yaml` | **Short name:** `community.general.yaml`
**Collection:** `community.general` (≥ 1.0.0)

Stores one YAML file per host on the local controller filesystem. Identical behavior to
`jsonfile` but produces YAML-formatted files — more readable for deeply nested facts.

**Parameters:**

| Parameter  | INI key (`[defaults]`)    | Env var                           | Default | Required |
| ---------- | ------------------------- | --------------------------------- | ------- | -------- |
| `_uri`     | `fact_caching_connection` | `ANSIBLE_CACHE_PLUGIN_CONNECTION` | —       | ✅       |
| `_prefix`  | `fact_caching_prefix`     | `ANSIBLE_CACHE_PLUGIN_PREFIX`     | —       |          |
| `_timeout` | `fact_caching_timeout`    | `ANSIBLE_CACHE_PLUGIN_TIMEOUT`    | `86400` |          |

```bash
ansible-galaxy collection install community.general
```

```ini
# ansible.cfg
[defaults]
fact_caching            = community.general.yaml
fact_caching_connection = /tmp/ansible_cache
fact_caching_timeout    = 86400
```

**Use when:** human-readable fact files are preferred over JSON (e.g., for auditing or diffing).

______________________________________________________________________

### community.general.pickle

**FQCN:** `community.general.pickle` | **Short name:** `community.general.pickle`
**Collection:** `community.general` (≥ 1.0.0)

Stores one Python pickle file per host on the local controller filesystem. Binary format —
fastest read/write of all filesystem plugins, but not human-readable.

**Parameters:**

| Parameter  | INI key (`[defaults]`)    | Env var                           | Default   | Required |
| ---------- | ------------------------- | --------------------------------- | --------- | -------- |
| `_uri`     | `fact_caching_connection` | `ANSIBLE_CACHE_PLUGIN_CONNECTION` | —         | ✅       |
| `_prefix`  | `fact_caching_prefix`     | `ANSIBLE_CACHE_PLUGIN_PREFIX`     | —         |          |
| `_timeout` | `fact_caching_timeout`    | `ANSIBLE_CACHE_PLUGIN_TIMEOUT`    | `86400.0` |          |

```bash
ansible-galaxy collection install community.general
```

```ini
# ansible.cfg
[defaults]
fact_caching            = community.general.pickle
fact_caching_connection = /tmp/ansible_cache
fact_caching_timeout    = 86400
```

> ⚠️ Pickle files are not portable across Python versions. Avoid if your control node Python
> version may change, or if you share the cache directory across controllers.

**Use when:** maximum I/O performance on a single controller; human readability not required.

______________________________________________________________________

### community.general.memcached

**FQCN:** `community.general.memcached` | **Short name:** `community.general.memcached`
**Collection:** `community.general`
**Requires:** `memcache` Python library — `pip install python-memcached` (community.general < 9.x)
or `pip install pymemcache` (community.general ≥ 9.x; run `ansible-doc -t cache community.general.memcached`
to confirm the requirement for your installed version)

Stores JSON per-host records in Memcached. Shared across multiple controllers.

**Parameters:**

| Parameter  | INI key (`[defaults]`)    | Env var                           | Default           | Required |
| ---------- | ------------------------- | --------------------------------- | ----------------- | -------- |
| `_uri`     | `fact_caching_connection` | `ANSIBLE_CACHE_PLUGIN_CONNECTION` | `127.0.0.1:11211` |          |
| `_prefix`  | `fact_caching_prefix`     | `ANSIBLE_CACHE_PLUGIN_PREFIX`     | `ansible_facts`   |          |
| `_timeout` | `fact_caching_timeout`    | `ANSIBLE_CACHE_PLUGIN_TIMEOUT`    | `86400`           |          |

`_uri` is a **list** — specify multiple Memcached nodes for connection pooling:

```ini
# ansible.cfg — single node
[defaults]
fact_caching            = community.general.memcached
fact_caching_connection = 127.0.0.1:11211
fact_caching_timeout    = 3600

# Multiple nodes (comma-separated)
fact_caching_connection = 192.168.1.10:11211,192.168.1.11:11211
```

```bash
# community.general < 9.x
pip install python-memcached
# community.general >= 9.x
pip install pymemcache
ansible-galaxy collection install community.general
```

**Use when:** you need a shared, distributed cache without persistence requirements and already
operate a Memcached cluster. Set `_timeout = 0` to disable expiry.

______________________________________________________________________

### community.general.redis

**FQCN:** `community.general.redis` | **Short name:** `community.general.redis`
**Collection:** `community.general`
**Requires:** `redis>=2.4.5` Python library (`pip install redis`); Redis Sentinel requires `redis>=2.9.0`

Stores JSON per-host records in Redis. Persistent, shared, and supports Redis Sentinel for HA.

**Parameters:**

| Parameter                | INI key (`[defaults]`)           | Env var                           | Default              | Required |
| ------------------------ | -------------------------------- | --------------------------------- | -------------------- | -------- |
| `_uri`                   | `fact_caching_connection`        | `ANSIBLE_CACHE_PLUGIN_CONNECTION` | —                    | ✅       |
| `_prefix`                | `fact_caching_prefix`            | `ANSIBLE_CACHE_PLUGIN_PREFIX`     | `ansible_facts`      |          |
| `_timeout`               | `fact_caching_timeout`           | `ANSIBLE_CACHE_PLUGIN_TIMEOUT`    | `86400`              |          |
| `_keyset_name`           | `fact_caching_redis_keyset_name` | `ANSIBLE_CACHE_REDIS_KEYSET_NAME` | `ansible_cache_keys` |          |
| `_sentinel_service_name` | `fact_caching_redis_sentinel`    | `ANSIBLE_CACHE_REDIS_SENTINEL`    | —                    |          |

**`_uri` format:** `host:port:db:password`

```ini
# ansible.cfg — basic
[defaults]
fact_caching            = community.general.redis
fact_caching_connection = localhost:6379:0:
fact_caching_timeout    = 86400

# TLS
fact_caching_connection = tls://localhost:6379:0:mysecretpassword

# Redis Sentinel (HA) — requires redis>=2.9.0; use ; as separator between sentinel hosts
fact_caching_connection      = sentinel1:26379;sentinel2:26379;0:mypassword
fact_caching_redis_sentinel  = mymaster
```

```bash
pip install redis
ansible-galaxy collection install community.general
```

**Use when:** you need persistent, distributed fact caching across multiple controllers, or require
Redis Sentinel for high availability. Set `_timeout = 0` for facts that never expire.

______________________________________________________________________

### community.mongodb.mongodb

**FQCN:** `community.mongodb.mongodb` | **Short name:** `community.mongodb.mongodb`
**Collection:** `community.mongodb` (≥ 1.0.0)
**Requires:** `pymongo>=3` Python library (`pip install pymongo`)

Stores per-host records in MongoDB. Persistent and shared, backed by a MongoDB connection URI.

**Parameters:**

| Parameter  | INI key (`[defaults]`)    | Env var                           | Default                        | Required |
| ---------- | ------------------------- | --------------------------------- | ------------------------------ | -------- |
| `_uri`     | `fact_caching_connection` | `ANSIBLE_CACHE_PLUGIN_CONNECTION` | `mongodb://localhost:27017/` ¹ |          |
| `_prefix`  | `fact_caching_prefix`     | `ANSIBLE_CACHE_PLUGIN_PREFIX`     | `ansible_facts`                |          |
| `_timeout` | `fact_caching_timeout`    | `ANSIBLE_CACHE_PLUGIN_TIMEOUT`    | `86400`                        |          |

¹ If `_uri` is omitted, the plugin defaults to `mongodb://localhost:27017/`. Always set this
explicitly in production.

`_uri` is a standard [MongoDB Connection String URI](https://www.mongodb.com/docs/manual/reference/connection-string/).

```ini
# ansible.cfg
[defaults]
fact_caching            = community.mongodb.mongodb
fact_caching_connection = mongodb://localhost:27017/ansible_cache
fact_caching_timeout    = 86400
```

```bash
pip install pymongo
ansible-galaxy collection install community.mongodb
```

**Use when:** your infrastructure already runs MongoDB and you want Ansible facts stored
alongside other operational data.

______________________________________________________________________

## Plugin Comparison

| Plugin                        | Persistent | Shared | Format    | Requires                           | Best for                                      |
| ----------------------------- | ---------- | ------ | --------- | ---------------------------------- | --------------------------------------------- |
| `ansible.builtin.memory`      | ❌         | ❌     | In-memory | Nothing (built-in)                 | Default; single-run, no persistence needed    |
| `ansible.builtin.jsonfile`    | ✅         | ❌     | JSON      | Nothing (built-in)                 | Single controller, readable files             |
| `ansible.netcommon.memory`    | ❌         | ❌     | In-memory | `ansible.netcommon`                | Network modules, transient facts              |
| `community.general.yaml`      | ✅         | ❌     | YAML      | `community.general`                | Single controller, auditable/diffable files   |
| `community.general.pickle`    | ✅         | ❌     | Binary    | `community.general`                | Single controller, maximum I/O speed          |
| `community.general.memcached` | ❌         | ✅     | JSON      | `python-memcached` or `pymemcache` | Multi-controller, ephemeral shared cache      |
| `community.general.redis`     | ✅         | ✅     | JSON      | `redis>=2.4.5`                     | Multi-controller, persistent, HA via Sentinel |
| `community.mongodb.mongodb`   | ✅         | ✅     | BSON/JSON | `pymongo>=3`                       | Orgs already operating MongoDB                |

______________________________________________________________________

## Inventory Cache Configuration

Inventory caching is disabled by default. Enable it separately from fact caching:

```ini
# ansible.cfg
[inventory]
cache        = True
cache_plugin = community.general.redis
```

Or per-inventory-plugin YAML config:

```yaml
# aws_ec2.yaml
plugin: aws_ec2
cache: true
cache_plugin: community.general.redis
cache_connection: localhost:6379:0:
cache_timeout: 3600
cache_prefix: aws_inventory
```

If no `cache_plugin` is set under `[inventory]`, Ansible reuses the `fact_caching` plugin.

______________________________________________________________________

## Common Patterns

### Clear the cache

```bash
# Filesystem plugins (jsonfile, yaml, pickle)
rm -rf /tmp/ansible_cache/*

# Redis
redis-cli -n 0 KEYS "ansible_facts*" | xargs redis-cli -n 0 DEL

# Force refresh in a single run (bypass fact cache only)
ansible-playbook site.yml --flush-cache
# Note: --flush-cache clears the fact cache only, not the inventory cache.
# To refresh inventory cache, delete the cache files/DB entries directly
# or re-run with ANSIBLE_INVENTORY_CACHE=False for that run.
```

### Disable timeout (never expire)

Set `fact_caching_timeout = 0` for memcached, redis, yaml, pickle, and mongodb plugins.
The `jsonfile` plugin uses `86400` as default; set to `0` to disable.

### Using FQCN (collection-based plugins)

```ini
[defaults]
fact_caching = community.general.redis
```

Using the FQCN is recommended to avoid ambiguity when multiple collections provide plugins
with the same short name (e.g., `memory` exists in both `ansible.builtin` and `ansible.netcommon`).

### Environment variable override (CI/CD)

```bash
export ANSIBLE_CACHE_PLUGIN=community.general.redis
export ANSIBLE_CACHE_PLUGIN_CONNECTION=redis.internal:6379:0:
export ANSIBLE_CACHE_PLUGIN_TIMEOUT=7200
ansible-playbook site.yml
```

______________________________________________________________________

## Discovery Commands

```bash
# List all available cache plugins
ansible-doc -t cache -l

# Show plugin parameters and examples
ansible-doc -t cache ansible.builtin.jsonfile
ansible-doc -t cache community.general.redis

# Check if a collection is installed
ansible-galaxy collection list | grep community.general
```
