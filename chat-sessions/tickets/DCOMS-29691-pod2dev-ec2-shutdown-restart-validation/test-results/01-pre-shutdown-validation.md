# Pre-shutdown validation - oms-pod2-dev

**Ticket:** [DCOMS-29691](https://aptos.atlassian.net/browse/DCOMS-29691)  
**Phase:** Before EC2 shutdown/restart test  
**Status:** Pass  
**Recorded:** 2026-09-04  

## Summary

Environment verified healthy **before** the planned off-hours EC2 shutdown. Site Manager and order flow both working with no issues observed.

## Tests performed

| Test | Result | Notes |
|---|---|---|
| Site Manager | **Pass** | Loads and functions normally |
| Order flow (end-to-end) | **Pass** | No issues observed |

## Infrastructure state at time of test

- All 7 EC2 instances: **running** (see `baseline/ec2-instances-summary.json`)
- AWS baseline captured: **2026-09-04** (see `baseline/`)
- RDS Aurora: **available** (`oms-pod2-dev-aurora`)

## EC2 instances in scope for shutdown test

| Instance | Instance ID |
|---|---|
| oms-pod2-dev-content | `i-00000000000000046` |
| oms-pod2-dev-services | `i-00000000000000047` |
| oms-pod2-dev-sitemanager | `i-00000000000000044` |
| oms-pod2-dev-api | `i-00000000000000045` |
| oms-pod2-dev-toronado | `i-00000000000000048` |
| oms-pod2-dev-BastionHost | `i-00000000000000042` |
| oms-pod2-dev-rds-migration-host | `i-00000000000000043` |

## Next steps

1. Optional: create pre-shutdown EBS snapshots (see `baseline/backup-summary.md`)
2. Stop all 7 EC2 instances during off-hours
3. Start all instances next working day
4. Re-run same validation (SM + order flow) and record in `02-post-shutdown-validation.md`
5. Document any failures or recovery steps in `runbook/`

## Post-shutdown checklist (to complete after restart)

- [ ] All 7 instances reach `running`
- [ ] ALB target groups healthy (SM, API, Services, Content)
- [ ] Site Manager - same test as above
- [ ] Order flow - same test as above
- [ ] Compare results to this pre-shutdown record
