---
name: terraform-actions
description: Use when implementing Terraform action block workflows and action_trigger lifecycle hooks for after_create/after_update day-2 operations, including -invoke runs.
---

# Terraform Actions

## When to Use

- You need Terraform 1.14+ `action` block support for non-CRUD operations that should run during infrastructure workflows.
- You are adding `action_trigger` rules in a resource `lifecycle` block with `after_create` or `after_update` events.
- You want to replace `local-exec` provisioners or pseudo data-source hacks for day-2 operations.
- You need side-effect triggers such as Lambda invocations, Ansible playbook runs, cache invalidations, webhooks, or service restarts.
- You need to execute an action directly via CLI with `terraform plan -invoke=...` or `terraform apply -invoke=...`.

## When NOT to Use

- You need result data from the operation for downstream expressions; use an ephemeral resource instead.
- You are modeling normal CRUD-managed infrastructure that belongs in `resource` blocks.
- You need action execution on destroy events; `after_destroy` is not supported.
- You are on Terraform versions older than 1.14 and cannot raise the version constraint.

## Overview

Terraform Actions (Terraform >= 1.14) add a first-class `action` block for non-CRUD, side-effect operations that do not modify Terraform-managed resource state. This is intended for day-2 workflows such as running Lambdas, Ansible playbooks, cache flushes, webhooks, and restarts.

Use `action` when all of the following are true:

- You are triggering a side effect.
- You do not need resulting data values.
- The operation should not appear as resource state.

If you do need result data, model it as an ephemeral resource instead.

> Requires Terraform >= 1.14. If you see red squiggly lines in your editor, set `required_version = ">= 1.14"` in your `terraform {}` block.

## Action Block Syntax

```hcl
action "<TYPE>" "<LABEL>" {
  config {
    <provider-specific arguments>
  }

  # Meta-arguments (optional):
  count    = <number>         # mutually exclusive with for_each
  for_each = { KEY = VALUE }  # or a set of strings
  provider = <provider>.<alias>
}
```

Reference declared actions with `action.<TYPE>.<LABEL>`.

## action_trigger Syntax in lifecycle

```hcl
resource "aws_instance" "example" {
  # ...
  lifecycle {
    action_trigger {
      events    = [after_create, after_update]
      actions   = [action.aws_lambda_invoke.db_init]
      condition = var.auto_update # optional boolean HCL expression
    }
  }
}
```

- Valid events: `after_create`, `after_update`
- `condition` accepts any HCL boolean expression and gates execution.

## CLI Invocation Without Full Apply

```bash
terraform plan  -invoke=action.aws_lambda_invoke.example
terraform apply -invoke=action.aws_lambda_invoke.example
```

## Worked Example: DB Init + Ansible Provisioning

```hcl
action "aws_lambda_invoke" "db_init" {
  config {
    lambda_arn = aws_lambda_function.db_migration.arn
    db_address = aws_db_instance.db.address
  }
}

action "ansible_playbook" "application" {
  config {
    playbook_path  = "${path.module}/playbook.yml"
    host           = aws_instance.application.public_ip
    ssh_public_key = aws_key_pair.application.public_key
  }
}

resource "aws_instance" "application" {
  ami           = var.ami
  instance_type = "t2.micro"
  key_name      = aws_key_pair.application.key_name

  lifecycle {
    action_trigger {
      events = [after_create]
      actions = [
        action.aws_lambda_invoke.db_init,
        action.ansible_playbook.application,
      ]
    }
  }
}

# Re-run Ansible when playbook file changes
resource "terraform_data" "playbook_changed" {
  input = filesha256("${path.module}/playbook.yml")

  lifecycle {
    action_trigger {
      events    = [after_update]
      condition = var.auto_update_application
      actions   = [action.ansible_playbook.application]
    }
  }
}
```

## count and for_each Patterns

```hcl
action "aws_lambda_invoke" "example" {
  count = 3

  config {
    function_name = "my_function"
  }
}

action "aws_lambda_invoke" "multi_region" {
  for_each = tomap({
    us_east = "arn:aws:lambda:us-east-1:123:function:fn"
    us_west = "arn:aws:lambda:us-west-2:123:function:fn"
  })

  config {
    function_name = each.value
  }
}
```

## Common Mistakes

- Using `action` when you need result data for later expressions; use an ephemeral resource.
- Trying to trigger on `after_destroy`; only `after_create` and `after_update` are supported.
- Confusing declaration syntax `action "TYPE" "LABEL"` with reference syntax `action.TYPE.LABEL`.
- Keeping `local-exec` provisioners for day-2 operations where `action` blocks are now a better fit.
- Forgetting `required_version = ">= 1.14"`, causing editor/linters to flag `action` blocks as invalid.

## External References

- [Terraform: Invoke an action](https://developer.hashicorp.com/terraform/language/invoke-actions)
- [Terraform: action block reference](https://developer.hashicorp.com/terraform/language/block/action)
- [Introduction to Terraform Actions (Daniel M. Schmidt)](https://danielmschmidt.de/posts/2025-09-26-terraform-actions-introduction/)
