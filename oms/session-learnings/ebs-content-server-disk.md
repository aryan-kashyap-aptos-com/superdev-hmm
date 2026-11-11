# EBS and content-server disk (picklists, exports)

**Status:** verified  
**Evidence:** `tickets/RANDOM/order-worklist-picklist-disk-space-qa-sm/README.md`, transcript-index topic `ebs-disk`

## Symptom

Site Manager Order Worklist: **"Could not generate picklist at this time. There is not enough space on the disk."**

## Architecture trap

| Component | Storage |
|-----------|---------|
| ECS minisoft | **EFS** (`/minisoft`) |
| SM picklist / `productExports` | **Windows SMB share on content server** backed by **EBS** (not EFS) |

Pod QA example: SSM `contentpath` `//dev.aptos.com/sh-dev/dev`, sitename `podqa` → files on **sh-cnt** (`i-0364472ad7dcb1458`), share `dev` → `D:\content\dev\podqa\sm\...`.

## Root cause (2026-10-28)

- **D: on sh-cnt full** (400 GB total, **0 GB free**)
- Largest: `D:\content\task` ~323 GB; `D:\content\dev` ~59 GB (podqa ~13 GB)
- Code writes under `{rootDir}\productExports` (`Reporting.vb` / `order-worklist.aspx.cs`)

## Remediation

1. **Expand D: EBS** on content instance (note volume IDs from ticket CHAT-LOG: data vs OS volumes).
2. Archive or purge `D:\content\task` per ops policy.
3. Hygiene: stale `*\sm\productExports` under dev tenants (podqa had hundreds of PDFs).
4. On IIS host, also check **C:** and **%TEMP%** during ActiveReports/GDI+ generation.

## Orphan EBS after terminate

DCOMS-29691 captured **`ebs-volumes-orphaned.json`** - terminated EC2 leaves **available** volumes; review for cost cleanup (no automated snapshot policy on that pod account at time of ticket).
