# OMS logs - integration analysis

Three log families you use today, how they relate to infrastructure, and how the Shared Ops GUI can expose them.

## Architecture (where logs actually live)

```text
  Site Manager EC2 (IIS)                Toronado EC2                    API EC2 (scale-out)
  physicalPath per IIS site             D:\torojobs\OMS-*\*.log         stdout / file -> CW agent
        |                                      |                              |
        v                                      v                              v
  ShopLogic.debug / ShopLogic-Debug.log   job processor logs          CloudWatch Log Group
        |                                      |                         (e.g. *SHOPLOGICAPI*)
        |                                      |
        +------------ SFTP mirror (optional) ---+
                     Content / deploy pipeline copies some paths to
                     oms-shared-dev-sftp.dev.eom.aptos.io
```

**SFTP is usually a copy/sync target**, not the live write path. Toro and SM write on the **Windows server** first; SFTP paths like `/dev/poddev/sm/ShopLogic-Debug.log` or `/task/podqa/` are convenient for humans with FileZilla but lag behind real-time debugging on the box.

| Source | Live location | SFTP | Best for GUI "tail" |
|--------|---------------|------|-------------------|
| Site Manager | IIS site `physicalPath` + `ShopLogic.debug` (or `ShopLogic-Debug.log`) | `.../dev/{env}/sm/...` | **SSM on SM instance** (same as Explore in IIS) |
| Toronado | `D:\torojobs\{OMS-ServiceFolder}\*.log` | `/task/{env}/` style paths | **SSM on Toro host** |
| API | CloudWatch Logs | N/A | **boto3 `filter_log_events`** (needs `logs:*` IAM) |

---

## 1. Site Manager - ShopLogic debug

**What you do manually:** IIS -> site -> app pool -> Explore -> folder contains `ShopLogic.debug` (archives rotate in same tree).

**Data path:**

1. `Get-Website` -> `physicalPath` (now returned in the GUI IIS tab).
2. Resolve file: `ShopLogic.debug`, `ShopLogic.Debug.log`, or `ShopLogic-Debug.log` (environment-dependent naming).
3. Tail with `Get-Content -Tail N`.

**GUI (implemented):** Logs tab -> **Site Manager** -> pick site -> **Tail ShopLogic log**. IIS `physicalPath` is usually UNC (`\\omspod.aptos.com\shareddev\dev\poddev\sm`). Files on **content** are at **`D:\content\dev\poddev\sm\ShopLogic-Debug.log`** (not under `D:\shareddev\...`). The GUI tails on **content first** (`eom-core-shared-dev-cont`), then SM as fallback.

**SFTP vs SSM:**

| Approach | Pros | Cons |
|----------|------|------|
| SSM tail on SM EC2 | Live, no extra creds if AWS works; matches IIS Explore | Needs SSM Online; large files still OK with `-Tail` |
| SFTP download | Familiar; good for big archives | Second auth (AD user); not live; path mapping per env |
| S3 sync (if any) | Central | Not confirmed for all envs |

**Recommendation:** Primary = SSM tail. Optional phase 2 = "Open SFTP URL" clipboard copy using stack-specific base URL from `inventory.json`.

---

## 2. Toronado logs

**What you do manually:** RDP to `eom-core-shared-dev-toronado`, browse `D:\torojobs\OMS-JobProcessor-{env}-{build}\`, read `.log` files. SFTP `sftp://omspod\user@oms-shared-dev-sftp.dev.eom.aptos.io/task/...` mirrors task output for some jobs.

**Naming:** Service name `OMS-JobProcessor-regression202510qa-26` maps to folder `D:\torojobs\OMS-JobProcessor-regression202510qa-26\`.

**GUI (implemented):** Logs tab -> **Toronado** -> uses selected OMS service from Toronado tab -> **Tail latest .log** via SSM.

**SFTP vs SSM:**

| Approach | Pros | Cons |
|----------|------|------|
| SSM on Toro | Direct, per-service folder | Many envs on one host - must pick correct service |
| SFTP `/task/` | Good for exported job artifacts | May not include all processor logs; not always real-time |
| Sumo / other | Central search | Extra tooling |

**Recommendation:** SSM for processor troubleshooting; link SFTP base URL in UI for artifacts. Content server role: often **publishes** static/content and **syncs** logs to SFTP - confirm with your deploy docs per env; do not assume SFTP is the only source.

---

## 3. API - CloudWatch

**What you do manually:** CloudWatch -> Log groups -> names containing **SHOPLOGICAPI**.

**GUI (implemented):** Logs tab -> **API (CloudWatch)** -> refresh groups -> pick group -> **Tail recent events** (last stream, last N messages).

**Requirements:** AWS credentials with `logs:DescribeLogGroups`, `logs:DescribeLogStreams`, `logs:GetLogEvents` (and optionally `logs:FilterLogEvents` for search in phase 2).

**Phase 2 ideas:**

- Filter by `{env}` or pod name in log group list using `inventory.json` `log_group_hints`.
- Time range picker + `filter_log_events` with pattern.
- Link to AWS Console URL for the selected group.

---

## S/N (serial number) on hosts

The GUI loads **BIOS serial** via SSM (`Win32_BIOS`). On EC2 this is often the **instance identity string**, not a physical rack S/N. We also show **instance ID** and **private IP** for change control.

---

## Security notes

- SSM actions use your existing AWS role; mutating service/IIS still requires confirm in GUI.
- SFTP credentials (`omspod\...`) should **not** be stored in the repo; use Windows credential manager or prompt in a future SFTP tab.
- CloudWatch tails may contain PII - treat log pane as sensitive.

---

## Suggested roadmap

| Phase | Deliverable |
|-------|-------------|
| **Now** | Readable Running/Stopped; host S/N; SSM retry; Logs tab (SM + Toro SSM tail, CW tail) |
| **Now (OMS Engine)** | **SFTP** tab per stack (`inventory.json`); browse/download with progress; SSM chunked download for large files |
| **Next** | SFTP upload; open archiver list for SM folder |
| **Later** | Unified search; Sumo MCP; bookmark log paths in `inventory.json` |
