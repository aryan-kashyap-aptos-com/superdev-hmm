# pod2-dev recovery runbook — after accidental terminate

**Ticket:** DCOMS-29691  
**Date:** 2026-09-04  
**Account:** 123456789012 | **Region:** us-east-1

This documents what happened after **ASG scale-to-0 terminated** all app EC2 instances, and the **correct recovery path** used to bring pod2-dev back.

---

## What went wrong (shutdown mistake)

| Step | What we did | Effect |
|------|-------------|--------|
| 1 | `stop-instances` on all 7 EC2 | Correct intent (off-hours save) |
| 2 | Toronado ASG replaced stopped instance immediately | ASG had no suspended processes |
| 3 | Scaled all 5 ASGs to **0/0/0** | **Terminated** app instances (not stop) |
| 4 | `restore-asg-capacity.ps1` | Launched **new** EC2 from AMI + bootstrap |

**Terminate ≠ stop.** New instances = fresh disks, lost IIS config, empty content volume, DFS targets pointing at old hostnames.

---

## Timeline after termination

### Phase 1 — ASG restore (new instances)

**Script:** `scripts/restore-asg-capacity.ps1`  
**Saved settings:** `test-results/asg-settings-before-shutdown.json`

| Tier | Old instance (terminated) | New instance |
|------|---------------------------|--------------|
| content | i-00000000000000046 | i-00000000000000037 |
| services | i-00000000000000047 | i-00000000000000039 |
| sitemanager | i-00000000000000044 | i-00000000000000032 |
| api | i-00000000000000045 | i-00000000000000035 |
| toronado | i-00000000000000048 | i-0000000000000003b |
| bastion | i-00000000000000042 | same (was only stopped) |
| rds-migration | i-00000000000000043 | same (was only stopped) |

**Symptoms:** ALB **502** → then **500** on SM. Health checks **404** on `/hashcheck.asp`.

**RDS:** Never stopped — database data intact.

---

### Phase 2 — OMS-App-Deploy (application + IIS)

**Pipeline:** Harness → **OMS-App-Deploy** (Build 306)

| Input | Value | Notes |
|-------|-------|-------|
| `environment_name` | **`pod2`** | NOT `pod2-dev` (registry key) |
| `dm_config_type` | `branch` | |
| `dm_config_ref` | `pre-gamma` | |
| `action` | `apply` | Run `plan` first on future recoveries |
| `webserver_setup_require` | **`true`** | Required after terminate |
| Codebase branch | `main` | oms-infrastructure-v2 |

**What this fixed:**

- Terraform app layer (ECS, Lambda, ALB rules, etc.)
- **Sitemanager CoreServices Deploy** (WinRM):
  - `content_directory_setup`
  - `sitemanager_server_setup` → creates `pod2-dev-sm` IIS site
  - `sitemanager_deploy` → robocopy shoplogic to `D:\content\dev\sm` on content server
  - `services_deploy`, `api_deploy`, `jobmanager_deploy`, `jobprocessor_deploy`, etc.

**Still broken after App-Deploy alone:** SM **500** — IIS site existed but UNC path unreachable.

---

### Phase 3 — OMS-DFS-Namespace (content path)

**Pipeline:** Harness → **OMS-DFS-Namespace** (Build 96)

| Input | Value | Notes |
|-------|-------|-------|
| `dfs_action` | **`create_and_validate`** | Typo `creata_and_validate` is invalid |
| `space_name` | `pod2` | |
| `environment_type` | `dev` | |

**Why needed:** SM IIS points at `\\omspod.aptos.com\pod2-dev\dev\sm`. After new content server (`pod-cnt-d-2966`), DFS on DCs still targeted the **old** hostname.

**Auto-resolved targets:**

```text
DFS folder:  \\omspod.aptos.com\pod2-dev\dev
Target:      \\pod-cnt-d-2966\dev
Task:        \\pod-cnt-d-2966\task
```

**Result:** SM login **HTTP 200** — Commerce tab loads in browser.

---

### Phase 4 — Toronado cleanup (optional)

Each App-Deploy run registers services named `OMS-JobManager-pod2dev-<sequenceId>`.

**Keep latest only** (Build 306 → `-50092`):

```powershell
cd C:\PROD\ConnectorSuite\oms_ec2_connector
python oms_ec2.py --env .env.pod2dev exec toronado "Get-Service OMS-* | Format-Table Name,Status -AutoSize"
```

Old `-26` / `-50026` sets were removed; only **`-50092`** running:

- `OMS-JobManager-pod2dev-50092`
- `OMS-JobProcessor-pod2dev-50092`
- `OMS-PostOffice-pod2dev-50092`

---

## Final validation status

| Check | Result |
|-------|--------|
| SM login (`/backadmin/login.aspx`) | **PASS** |
| Commerce UI | **PASS** |
| ALB SM health (`/hashcheck.asp`) | **Still unhealthy** — file missing from deploy |
| Order flow | Pending full test |
| Toronado services | **PASS** (latest set running) |

---

## Recovery checklist (use after terminate)

Run in this order:

```text
[ ] 1. Restore ASG capacity (or re-run infra if destroyed)
        scripts/restore-asg-capacity.ps1

[ ] 2. Wait ~20 min for Windows bootstrap (AD join, sysprep)

[ ] 3. OMS-App-Deploy
        environment_name = pod2
        webserver_setup_require = true
        action = plan → then apply

[ ] 4. OMS-DFS-Namespace
        space_name = pod2
        environment_type = dev
        dfs_action = create_and_validate

[ ] 5. Verify SM login in browser

[ ] 6. Verify toronado: Get-Service OMS-* (stop old duplicates if needed)

[ ] 7. Order flow test → log in 02-post-shutdown-validation.md
```

---

## Verification commands (`oms_ec2_connector`)

```powershell
cd C:\PROD\ConnectorSuite\oms_ec2_connector
pip install -r requirements.txt

# Instance inventory + SSM status
python oms_ec2.py --env .env.pod2dev list

# SM health script
python oms_ec2.py --env .env.pod2dev script sitemanager `
  "C:\PROD\ConnectorSuite\tickets\DCOMS-29691-pod2dev-ec2-shutdown-restart-validation\scripts\Check-Pod2Dev-SM-Health.ps1"

# Toronado services
python oms_ec2.py --env .env.pod2dev exec toronado "Get-Service OMS-* | Format-Table Name,Status -AutoSize"

# ALB SM target
aws elbv2 describe-target-health `
  --target-group-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/oms-pod2-dev-sm-tg/000000000000003e `
  --region us-east-1
```

**Update instance IDs** in `.env.pod2dev` after any redeploy:

```powershell
python oms_ec2.py --env .env.pod2dev refresh
```

---

## What NOT to do next time (off-hours shutdown)

| Wrong | Right |
|-------|-------|
| ASG scale to **0** | Suspend `Launch` + `ReplaceUnhealthy`, then **stop** instances |
| `environment_name = pod2-dev` in Harness | Use registry key **`pod2`** |
| Expect stop to preserve state after terminate | Terminate = full redeploy + DFS + webserver pipeline |
| Skip DFS after new content instance | Always run **OMS-DFS-Namespace** when content hostname changes |

**Safe stop-only procedure (not yet scripted):**

```powershell
# On each ASG — before stopping EC2
# Preferred: use safe scripts (suspend ASG + stop, no terminate)
.\scripts\stop-pod2-dev-safe.ps1
.\scripts\start-pod2-dev-safe.ps1

# See runbook/safe-stop-start.md for full procedure
```

---

## Key lessons for DCOMS-29691

1. **Terminate + ASG restore is a full environment rebuild**, not an overnight pause.
2. **App-Deploy alone is not enough** for Windows pods — need `webserver_setup_require=true` **and** DFS.
3. **Content data** on terminate: 300 GB volume was recreated empty; app code came back via pipeline, not disk.
4. **Multiple Toronado service sets** accumulate per App-Deploy run — keep latest sequence suffix only.
5. **`hashcheck.asp`** may still be missing — ALB can be unhealthy while SM login works.

---

## Related files

| File | Purpose |
|------|---------|
| `test-results/shutdown-log.md` | What was stopped/scaled |
| `test-results/startup-log.md` | ASG restore |
| `test-results/asg-settings-before-shutdown.json` | ASG min/max/desired to restore |
| `scripts/stop-pod2-dev-safe.ps1` | Safe off-hours shutdown (stop, not terminate) |
| `scripts/start-pod2-dev-safe.ps1` | Safe startup after stop-only shutdown |
| `runbook/safe-stop-start.md` | Safe stop/start procedure |
| `scripts/restore-asg-capacity.ps1` | Restore ASG after scale-to-0 only |
| `scripts/Check-Pod2Dev-SM-Health.ps1` | SM diagnostic |
| `oms_ec2_connector/.env.pod2dev` | Current instance IDs for SSM |
