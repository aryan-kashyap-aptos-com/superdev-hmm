# Startup log - oms-pod2-dev

**Ticket:** DCOMS-29691  
**Action:** Restore after ASG scale-to-0 shutdown  
**Initiated:** 2026-09-04  

## Restore command

```powershell
.\scripts\restore-asg-capacity.ps1
```

## New instance IDs (post-restore)

| Tier | Instance ID | ASG health |
|---|---|---|
| oms-pod2-dev-content | i-00000000000000037 | Healthy |
| oms-pod2-dev-services | i-00000000000000039 | Healthy |
| oms-pod2-dev-sitemanager | i-00000000000000032 | Healthy |
| oms-pod2-dev-api | i-00000000000000035 | Healthy |
| oms-pod2-dev-toronado | i-0000000000000003b | Healthy |
| oms-pod2-dev-BastionHost | i-00000000000000042 | running (same instance, was stopped) |
| oms-pod2-dev-rds-migration-host | i-00000000000000043 | running (same instance, was stopped) |

All 5 ASGs restored to saved capacity (min/max/desired from `asg-settings-before-shutdown.json`).

## Post-restart validation (pending)

- [ ] Site Manager
- [ ] Order flow
- [ ] Compare to `01-pre-shutdown-validation.md`
