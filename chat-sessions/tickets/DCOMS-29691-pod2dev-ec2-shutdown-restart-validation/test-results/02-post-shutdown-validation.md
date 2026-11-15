# Post-shutdown validation

**Date:** 2026-09-04  
**Method:** ASG scale-to-0 (terminate) + restore + pipeline recovery  
**Full runbook:** `runbook/post-termination-recovery.md`

## Recovery performed

1. `restore-asg-capacity.ps1` — new EC2 instances launched
2. **OMS-App-Deploy** (Build 306) — `pod2`, `webserver_setup_require=true`, `pre-gamma`
3. **OMS-DFS-Namespace** (Build 96) — `pod2` / `dev` / `create_and_validate`
4. Toronado — kept latest service set `-50092` only

## Validation results

| Check | Result | Notes |
|-------|--------|-------|
| SM login | **PASS** | Commerce tab loads |
| Order flow | Pending | Not fully re-tested in session |
| ALB SM `/hashcheck.asp` | **FAIL** | File missing; login works anyway |
| Toronado Job Manager/Processor | **PASS** | `OMS-*-pod2dev-50092` Running |
| API / Services ALB | Not re-validated | |

## Conclusion

Environment **recovered after terminate** via App-Deploy + DFS.  
**Not** a viable off-hours shutdown method — use suspend + stop only (see runbook).
