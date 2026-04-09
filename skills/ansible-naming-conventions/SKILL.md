---
name: ansible-naming-conventions
description: Use when writing, reviewing, or structuring Ansible code — roles, variables, tasks, handlers, playbooks, inventory groups, or tags. Triggers on naming inconsistencies, variable collision concerns, ansible-lint naming errors, or starting a new Ansible project.
metadata:
  author: d.horkhover
  version: 1.0.0
---

# Ansible Naming Conventions

## When to Use

- Writing new Ansible roles, playbooks, or inventory files from scratch
- Reviewing existing Ansible code for naming inconsistencies or variable collisions
- Structuring handlers, tasks, tags, or inventory groups in a project
- Resolving `ansible-lint` naming errors (`name[casing]`, `var-naming`, `role-name`)
- Starting or onboarding a new Ansible project

## When NOT to Use

- Non-Ansible automation (shell scripts, Terraform, Helm) — use the relevant skill instead
- One-off ad-hoc commands where no persistent code is being written
- Projects with an established, enforced naming standard that differs from these conventions — follow their standard instead

## Overview

Consistent naming in Ansible prevents variable collisions, clarifies intent in logs, and makes large multi-role projects maintainable. The core rule: **prefix variables with role name**, name tasks after **desired state** (not action), and use **lowercase with underscores** for most identifiers.

## Quick Reference

| Element          | Convention                              | Example                                         |
| ---------------- | --------------------------------------- | ----------------------------------------------- |
| Roles            | `lowercase_underscores`                 | `redis_server`, `ssl_certificates`              |
| Variables        | `role_prefix_name`                      | `nginx_worker_processes`, `postgresql_port`     |
| Boolean vars     | `enable_`/`is_`/`has_` prefix           | `nginx_ssl_enabled`, `app_debug_mode`           |
| Tasks            | Sentence case, desired state            | `Ensure nginx is installed`                     |
| Handlers         | Action description (prefixed if shared) | `Restart nginx`, `nginx - reload configuration` |
| Playbooks        | `lowercase-hyphens.yml`                 | `deploy-application.yml`                        |
| Templates        | Mirror config filename + `.j2`          | `nginx.conf.j2`, `ssl-params.conf.j2`           |
| Inventory groups | `lowercase_underscores`                 | `webservers`, `db_servers`, `app_servers`       |
| Tags             | `lowercase_underscores`                 | `packages`, `firewall`, `configuration`         |

______________________________________________________________________

## Role Naming

Lowercase with underscores. Describe the **software or function**, never the action:

```text
# GOOD: Function/software-based names
roles/
  nginx/
  postgresql/
  redis_server/
  ssl_certificates/
  monitoring_agent/
  firewall_rules/
  backup_client/

# BAD: Wrong casing, hyphens, action verbs, vague
roles/
  InstallNginx/       # PascalCase + action verb
  setup-postgres/     # Hyphens instead of underscores
  doFirewallStuff/    # camelCase + vague
  role1/              # Meaningless
```

For application-specific roles, prefix with the app name:

```text
roles/
  myapp_backend/
  myapp_frontend/
  myapp_worker/
```

______________________________________________________________________

## Variable Naming

**Always prefix with the role name** to prevent silent collision when multiple roles are loaded:

```yaml
# roles/nginx/defaults/main.yml
nginx_worker_processes: auto
nginx_worker_connections: 1024
nginx_log_dir: /var/log/nginx
nginx_ssl_enabled: true
nginx_ssl_protocols: "TLSv1.2 TLSv1.3"
nginx_vhosts: []

# roles/postgresql/defaults/main.yml
postgresql_version: 15
postgresql_port: 5432
postgresql_max_connections: 200
postgresql_data_dir: /var/lib/postgresql/15/main
postgresql_log_dir: /var/log/postgresql
```

Without prefixing, variables shadow each other silently:

```yaml
# BAD: Both roles define the same bare variable names

# roles/nginx/defaults/main.yml
port: 80
log_dir: /var/log/nginx

# roles/postgresql/defaults/main.yml
port: 5432        # Silently overrides nginx port!
log_dir: /var/log/pg  # Silently overrides nginx log_dir!
```

### Boolean Variables

Use `is_`, `has_`, or `enable_` prefixes so intent is unambiguous:

```yaml
# GOOD: Clear boolean semantics
nginx_ssl_enabled: true
nginx_gzip_enabled: false
app_debug_mode: false
backup_compression_enabled: true
monitoring_alerts_enabled: true

# BAD: Ambiguous—is it config object or a flag?
nginx_ssl: true # SSL config or toggle?
compress: false # Compress what?
debug: true # Which component?
```

______________________________________________________________________

## Task Naming

Every task **must** have a `name`. Use **sentence case** and describe the **desired state**, not the imperative action:

```yaml
# GOOD: State-oriented, sentence case
- name: Ensure nginx is installed
  ansible.builtin.apt:
    name: nginx
    state: present

- name: Ensure nginx configuration is deployed
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf

- name: Ensure nginx service is running and enabled
  ansible.builtin.service:
    name: nginx
    state: started
    enabled: yes

# BAD: Action-oriented, missing, or vague
- name: Install nginx # Imperative, not state
  ansible.builtin.apt:
    name: nginx
    state: present

- ansible.builtin.template: # No name at all!
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf

- name: do stuff # Vague, wrong casing
  ansible.builtin.service:
    name: nginx
    state: started
```

______________________________________________________________________

## Handler Naming

Name handlers by the **action they perform**. Prefix with role name when a role may be included multiple times (prevents cross-role handler conflicts):

```yaml
# roles/nginx/handlers/main.yml

# Simple names (single-role context)
- name: Restart nginx
  ansible.builtin.service:
    name: nginx
    state: restarted

- name: Reload nginx
  ansible.builtin.service:
    name: nginx
    state: reloaded

- name: Validate nginx configuration
  ansible.builtin.command: nginx -t
  changed_when: false

# Prefixed names (multi-include or shared-role context)
- name: nginx - restart service
  ansible.builtin.service:
    name: nginx
    state: restarted

- name: nginx - reload configuration
  ansible.builtin.service:
    name: nginx
    state: reloaded
```

______________________________________________________________________

## Playbook and File Naming

**Playbooks**: `lowercase-hyphens.yml`
**Templates**: mirror the output config filename + `.j2`

```text
playbooks/
  site.yml                    # Master playbook
  webservers.yml              # Host-targeted
  dbservers.yml
  deploy-application.yml      # Action-targeted
  setup-monitoring.yml
  rolling-update.yml

roles/nginx/templates/
  nginx.conf.j2
  default-site.conf.j2
  ssl-params.conf.j2
```

______________________________________________________________________

## Inventory Group Naming

`lowercase_underscores`. Name by **function**, never by hostname or physical location:

```yaml
# inventories/production/hosts.yml
all:
  children:
    webservers:
      hosts:
        web01.example.com:
        web02.example.com:
    app_servers:
      hosts:
        app01.example.com:
        app02.example.com:
    db_servers:
      hosts:
        db01.example.com:
    monitoring_servers:
      hosts:
        mon01.example.com:
```

Location-based groups are fine as **secondary nested groupings**:

```yaml
all:
  children:
    dc_east:
      children:
        webservers_east:
          hosts:
            web01.east.example.com:
        db_servers_east:
          hosts:
            db01.east.example.com:
    dc_west:
      children:
        webservers_west:
          hosts:
            web01.west.example.com:
```

______________________________________________________________________

## Tag Naming

`lowercase_underscores`. Apply consistent semantic categories across the whole project:

```yaml
- name: Install base packages
  ansible.builtin.apt:
    name: "{{ common_packages }}"
    state: present
  tags:
    - common
    - packages
    - install

- name: Configure firewall rules
  ansible.posix.firewalld:
    service: http
    state: enabled
    permanent: yes
  tags:
    - security
    - firewall
    - configuration

- name: Deploy application code
  ansible.builtin.git:
    repo: "{{ app_repo }}"
    dest: "{{ app_dir }}"
  tags:
    - deploy
    - application
```

______________________________________________________________________

## Enforcement with ansible-lint

Configure `.ansible-lint` and run in CI to catch violations automatically:

```yaml
# .ansible-lint
enable_list:
  - name[casing]
  - name[template]
  - role-name
  - var-naming

var_naming_pattern: "^[a-z_][a-z0-9_]*$"

warn_list:
  - name[missing]

skip_list: []
```

```bash
# Check all roles and playbooks, fail on any violation
ansible-lint roles/ playbooks/ --strict
```

______________________________________________________________________

## Common Mistakes

| Mistake                              | Correct                             |
| ------------------------------------ | ----------------------------------- |
| `port: 5432` in role variables       | `postgresql_port: 5432`             |
| `log_dir: /var/log/nginx` (bare var) | `nginx_log_dir: /var/log/nginx`     |
| `nginx_ssl: true` (ambiguous)        | `nginx_ssl_enabled: true`           |
| `- name: Install nginx`              | `- name: Ensure nginx is installed` |
| Task with no `name` field            | Always add a descriptive `name`     |
| `roles/InstallNginx/`                | `roles/nginx/`                      |
| `roles/setup-postgres/`              | `roles/postgresql/`                 |
| Playbook `SetupMonitoring.yaml`      | `setup-monitoring.yml`              |
| Inventory group `Web-Servers`        | `webservers` or `web_servers`       |
| Handler conflicts across roles       | Prefix: `nginx - restart service`   |
| Tags like `FW`, `Deploy`             | `firewall`, `deploy`                |
