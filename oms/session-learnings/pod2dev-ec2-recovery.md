# pod2-dev EC2 recovery (terminate ≠ stop)

**Status:** verified  
**Evidence:** `C:\PROD\ConnectorSuite\tickets\DCOMS-29691-pod2dev-ec2-shutdown-restart-validation\runbook\post-termination-recovery.md`, agent transcripts tagged `pod2dev-ec2` in [transcript-index.json](./transcript-index.json)

## Mental model

- **Stop** preserves EBS, IIS sites, DFS targets, and Toronado Windows services.
- **ASG scale to 0** often **terminates** instances. New instances boot from AMI with **empty content paths** and **stale DFS** until pipelines run.
- **RDS** on pod2 was not stopped during DCOMS-29691 - app data in Postgres survived; **Windows/IIS/UNC** layer did not.

## Recovery order (after accidental terminate)

1. **Restore ASG capacity** from saved settings (`restore-asg-capacity.ps1`, `test-results/asg-settings-before-shutdown.json`).
2. **Harness OMS-App-Deploy** with:
   - `environment_name` = **`pod2`** (registry key - not `pod2-dev`)
   - `webserver_setup_require` = **`true`** (mandatory after terminate)
   - `dm_config_ref` = e.g. `pre-gamma`
3. **Harness OMS-DFS-Namespace** with `dfs_action` = **`create_and_validate`** (typo `creata_and_validate` fails). Fixes SM UNC `\\omspod.aptos.com\pod2-dev\dev\sm` after content host replacement.
4. **Toronado:** App-Deploy registers `OMS-JobManager-pod2dev-<sequenceId>` services - keep **latest sequence only**, remove older `-50026` style sets.
5. **Refresh SSM inventory:** `python oms_ec2.py --env .env.pod2dev refresh` after instance ID changes.

## Validation

| Check | Pass signal |
|-------|-------------|
| SM login | `/backadmin/login.aspx` HTTP 200 |
| Health probe | `/hashcheck.asp` not 404 on ALB |
| Toronado | `Get-Service OMS-*` - one running JobManager/Processor/PostOffice set |

## Tools

- `C:\PROD\ConnectorSuite\oms_ec2_connector\` - SSM exec, remote scripts, `.env.pod2dev`
- `scripts/Check-Pod2Dev-SM-Health.ps1` in DCOMS-29691 ticket folder

## Common mistakes

| Mistake | Effect |
|---------|--------|
| App-Deploy only, skip DFS | SM site exists but **500** - UNC unreachable |
| Wrong Harness env name `pod2-dev` | Deploy targets wrong registry |
| Expect stop-like behavior after terminate | Full redeploy + DFS + webserver setup required |
