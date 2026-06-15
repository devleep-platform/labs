# Devloop Labs

Community lab definitions for the [Devloop platform](https://devleep.com) â€” hands-on DevOps incident labs that run on real infrastructure inside your own AWS account.

This repo is **public**. Every engineer is welcome to contribute a lab.

---

## How it works

1. You write a YAML file describing a broken environment and how to fix it.
2. Open a pull request â€” automated validation runs immediately.
3. The Devloop team reviews, approves, and merges.
4. The lab goes live on [devleep.com/catalog](https://devleep.com/catalog) within minutes.

You do not need access to the platform codebase, Terraform, or the database. Write the YAML, open the PR.

---

## File layout

```
labs/
  linux/          â† Linux incident labs
  docker/
    beginner/
    intermediate/
    advanced/
  kubernetes/     â† planned
scripts/          â† CI validation and sync scripts (do not modify)
.github/
  workflows/
    validate-pr.yml   â† runs on every PR
    publish.yml       â† runs on merge to main
```

Place your lab YAML at `labs/<track>/<lab-id>.yaml`. The filename must match the `id` field inside the file.

---

## Lab YAML schema

Every lab is a single YAML file. All fields marked **required** must be present.

### Identity & Classification

| Field | Type | Required | Notes |
|---|---|---|---|
| `schema_version` | integer | âœ… | Always `1` |
| `id` | string | âœ… | Unique kebab-case slug. Must match the filename. |
| `title` | string | âœ… | Under 100 characters. |
| `description` | string | âœ… | 1â€“2 sentences. Shown on the catalog card. |
| `track` | enum | âœ… | `linux` Â· `docker` Â· `kubernetes` Â· `ansible` Â· `git` Â· `jenkins` |
| `module` | string | âœ… | Sub-group within the track. e.g. `linux-fundamentals` |
| `sort_order` | integer | âœ… | Position in curriculum. Use multiples of 10. |
| `difficulty` | enum | âœ… | `beginner` Â· `intermediate` Â· `advanced` Â· `expert` |
| `engineer_level` | enum | âœ… | `L1` Â· `L2` Â· `L3` Â· `L4` |
| `mode` | enum | âœ… | `guided` Â· `incident` Â· `challenge` |
| `tags` | string[] | âœ… | 4â€“6 search keywords. |

### Timing & Infrastructure

| Field | Type | Required | Notes |
|---|---|---|---|
| `estimated_minutes` | integer | âœ… | Shown on catalog. 5â€“480. |
| `timeout_minutes` | integer | âœ… | Hard session timeout. Infrastructure is destroyed after this. |
| `terraform_module` | enum | âœ… | See [Terraform Modules](#terraform-modules) below. |
| `scenario_id` | string | âœ… | Which setup script runs on the instance. e.g. `disk-full` |
| `prerequisites` | string[] | âœ… | Lab IDs that should be completed first. `[]` if none. |

### Learning Content

| Field | Type | Required | Notes |
|---|---|---|---|
| `objectives` | string[] | âœ… | 3â€“5 concrete learning objectives. |
| `success_criteria` | string[] | âœ… | Plain-English version of what passing looks like. |
| `hint_policy` | enum | âœ… | `show_level_1_automatically` Â· `manual_only` |
| `hints` | Hint[] | âœ… | All three levels (1, 2, 3) required. See [Hint System](#hint-system). |
| `validation` | Validation | âœ… | Automated checks. See [Validation Checks](#validation-checks). |
| `completion_message` | string | | 2â€“3 sentences shown after all checks pass. |
| `deliverables` | Deliverable[] | | Explicit files the student must produce. |

### Optional blocks

```yaml
metadata:
  version: 1.0.0
  author: your-name
  reviewed_by: []
  last_updated: 2026-06-14

environment:
  instance_type: t3.micro
  estimated_cost: "$0.01"
  aws_services:
    - ec2

briefing:
  severity: sev-1   # sev-1 Â· sev-2 Â· sev-3 Â· sev-4
  impact: One-line blast radius
  title: Short alert title
  narrative: |
    3â€“5 sentences of operational context.

evidence:
  - type: pagerduty   # pagerduty Â· slack Â· email Â· note
    title: "P1: Alert title"
    content: |
      Alert body text
```

---

## Terraform Modules

| `terraform_module` | Status | What it provisions |
|---|---|---|
| `labs/linux-ec2` | **stable** | Single Ubuntu 22.04 t3.micro. Connects via Cloudflare Tunnel. Used for all Linux labs. |
| `labs/docker-ec2` | **planned** | EC2 with Docker + Compose pre-installed. For Docker track labs. |
| `labs/kubernetes-eks` | **planned** | EKS cluster with a broken workload. Note: 8â€“12 min provision time. |

Template variables available in `http_get` URLs: `{{EC2_IP}}`, `{{INSTANCE_ID}}`

---

## Validation Checks

Checks run against the live instance when the student clicks Submit. All checks must pass (or at least one with `strategy: any`).

```yaml
validation:
  strategy: all         # all (default) or any
  default_timeout_seconds: 5
  checks:
    - id: nginx-running
      name: Nginx Running
      type: output_matches
      cmd: systemctl is-active nginx
      contains: active
      failure_hint: Run 'sudo systemctl restart nginx' and check 'journalctl -xe'
```

### Check types

**`output_matches`** â€” runs `cmd` via SSH, checks output against `contains` / `pattern` / `value`.
```yaml
- id: disk-below-90
  type: output_matches
  cmd: df / | awk 'NR==2 {gsub("%",""); print ($5 < 90) ? "ok" : "full"}'
  value: ok
  failure_hint: Run 'du -sh /* 2>/dev/null | sort -h' to find what is using space
```

**`ssh`** â€” runs `cmd` via SSH, passes if exit code is 0. Output is not checked.
```yaml
- id: config-exists
  type: ssh
  cmd: test -f /etc/myapp/config.yaml
  failure_hint: Create the config file at /etc/myapp/config.yaml
```

**`http_get`** â€” makes an HTTP GET, passes if response is 2xx (or matches `expect_status`).
```yaml
- id: app-responding
  type: http_get
  url: "http://{{EC2_IP}}:8080/health"
  failure_hint: Check the app with 'systemctl status myapp'

- id: auth-enforced
  type: http_get
  url: "http://{{EC2_IP}}:8080/admin"
  expect_status: 401
```

**`multi_check`** â€” runs sub-checks with `operator: all` or `operator: any`.
```yaml
- id: stack-healthy
  type: multi_check
  operator: all
  checks:
    - { id: nginx, type: output_matches, cmd: systemctl is-active nginx, contains: active }
    - { id: app,   type: output_matches, cmd: systemctl is-active myapp,  contains: active }
```

### Writing good checks

- âœ… Test the outcome, not the method. `systemctl is-active nginx` is better than checking if a config file exists.
- âœ… Reduce output to something predictable â€” pipe through `awk` to produce `ok`/`fail`.
- âœ… Write `failure_hint` as a command to run, not a description of what is wrong.
- âŒ Do not use `ps aux | grep myapp` â€” grep matches itself. Use `pgrep -f` or `systemctl is-active`.
- âŒ Do not hardcode IPs. Use `{{EC2_IP}}` in `http_get` URLs.

---

## Hint System

Every lab requires all three hint levels. They are progressive â€” each reveals more.

| Level | Type | What it contains |
|---|---|---|
| 1 | Directional | Points the student at the right area. No commands. Shown automatically on lab load by default. |
| 2 | Specific | Names relevant commands and flags. Student still pieces together the fix. |
| 3 | Full walkthrough | Every command in order with a one-line explanation. A student who is completely stuck can follow this to completion. |

```yaml
hint_policy: show_level_1_automatically
hints:
  - level: 1
    text: |
      Something swept ownership across a directory it should not have touched.
      Find out which directory nginx needs to read.

  - level: 2
    text: |
      Check what nginx is trying to read:
        sudo journalctl -u nginx --since "5 min ago"
        ls -la /var/www/html

      nginx runs as www-data. Fix ownership:
        sudo chown -R www-data:www-data /var/www/html

  - level: 3
    text: |
      # Confirm the problem
      sudo journalctl -u nginx --since "5 min ago" | grep "Permission denied"
      ls -la /var/www/html   # should show root:root â€” that is wrong

      # Fix
      sudo chown -R www-data:www-data /var/www/html
      sudo chmod 755 /var/www/html
      sudo find /var/www/html -type f -exec chmod 644 {} \;

      # Verify
      sudo nginx -t
      curl -s -o /dev/null -w "%{http_code}" http://localhost
```

A lab without a complete Level 3 will be sent back.

---

## Full example

```yaml
schema_version: 1

metadata:
  version: 1.0.0
  author: your-name
  reviewed_by: []
  last_updated: 2026-06-14

id: linux-disk-full
title: "Disk Full: Production Filesystem Saturated"
description: >
  The root filesystem is at 100%. Every write is failing.
  Find what consumed the disk, clear space, and restore the service.

track: linux
module: linux-storage
sort_order: 80
difficulty: intermediate
engineer_level: L2
mode: incident

tags:
  - linux
  - disk
  - storage
  - troubleshooting
  - incident

estimated_minutes: 45
timeout_minutes: 90
terraform_module: labs/linux-ec2
scenario_id: disk-full

environment:
  instance_type: t3.micro
  estimated_cost: "$0.01"
  aws_services:
    - ec2

prerequisites:
  - linux-filesystem-anatomy

briefing:
  severity: sev-1
  impact: Service down â€” production impact
  title: Filesystem 100% â€” write errors
  narrative: |
    The production web server is returning 500 errors on every request.
    The app cannot write logs or temp files. The root filesystem hit 100%.
    Identify what consumed the disk, clear space, and restore the service.

evidence:
  - type: pagerduty
    title: "P1: Filesystem 100% â€” write errors"
    content: |
      CRITICAL: / at 100% on prod-web-01
      App is throwing ENOSPC on every write
  - type: slack
    title: "#ops-alerts"
    content: |
      [automated] ALERT: prod-web-01 disk usage 100%
      First seen: 14:23 UTC â€” still firing

objectives:
  - Identify what is consuming disk space
  - Remove the bloat without deleting production data
  - Restore service without a restart

success_criteria:
  - df / shows less than 90% used
  - nginx is active and responding

deliverables:
  - path: /tmp/disk-cleanup.log
    description: What you found and what you removed

hint_policy: show_level_1_automatically
hints:
  - level: 1
    text: |
      Something wrote a lot of data somewhere.
      Find out what is large and what is growing.

  - level: 2
    text: |
      df -h â€” which filesystem is full?
      sudo du -sh /* 2>/dev/null | sort -h â€” what is largest?
      sudo journalctl --disk-usage â€” are logs the culprit?

  - level: 3
    text: |
      df -h
      sudo du -sh /* 2>/dev/null | sort -h
      sudo journalctl --vacuum-size=200M
      sudo find /var/log -name "*.gz" -delete
      sudo apt-get clean
      df -h
      sudo systemctl restart nginx

validation:
  strategy: all
  default_timeout_seconds: 5
  checks:
    - id: disk-below-90
      name: Disk Below 90%
      type: output_matches
      cmd: df / | awk 'NR==2 {gsub("%",""); print ($5 < 90) ? "ok" : "full"}'
      value: ok
      failure_hint: Run 'du -sh /* 2>/dev/null | sort -h' to find what is using space

    - id: nginx-running
      name: Nginx Running
      type: output_matches
      cmd: systemctl is-active nginx
      contains: active
      failure_hint: Start nginx with 'sudo systemctl start nginx'

completion_message: |
  A full disk silently kills services that try to write.
  You can now isolate the cause, clean safely, and verify the fix.
  Set up disk monitoring so you see this at 80% â€” not 100%.
```

---

## Submitting a lab

1. **Fork this repo** â€” [github.com/devleep-platform/labs](https://github.com/devleep-platform/labs)
2. **Write your YAML** at `labs/<track>/<your-lab-id>.yaml`
3. **Open a pull request** â€” automated validation runs immediately and posts a comment
4. **Fix any errors** reported by the validator, push a new commit, validation re-runs
5. **Team reviews** â€” we test the scenario, verify hints, and check validation checks are tight
6. **Merged â†’ live** â€” within 5 minutes of merge, your lab is live on [devleep.com/catalog](https://devleep.com/catalog)

### PR checklist

Before opening your PR, verify:

- [ ] `schema_version: 1` is the first field
- [ ] `id` matches the filename (without `.yaml`)
- [ ] All three hint levels are present (1, 2, 3)
- [ ] Level 3 hint is a complete, step-by-step walkthrough
- [ ] Every `validation.check` has `id`, `name`, and `type`
- [ ] `failure_hint` is written as a command to run, not a description of the error
- [ ] `estimated_minutes` reflects how long a typical student at this level will take
- [ ] No secrets, credentials, or personal data in the YAML

### Review SLA

We aim to review PRs within **5 business days**. Labs that fail validation are not reviewed until the checks pass. Labs without a complete Level 3 hint are sent back immediately.

---

## Good lab ideas

Good labs come from real incidents. If you have been through an outage and want to turn it into a lab:

- The scenario should be reproducible on a fresh EC2 instance via a setup script
- The fix should be learnable â€” not "redeploy from backup"
- The validation checks should test the outcome (service responding), not just that a file exists
- The Level 3 hint should be usable as a runbook for a junior engineer

If you are unsure whether your idea is a good fit, open a GitHub Discussion before writing the full YAML.

---

## License

Labs in this repository are released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). You retain authorship credit. The platform is free to use.

