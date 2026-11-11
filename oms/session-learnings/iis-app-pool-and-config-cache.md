# IIS app pool recycle and config cache

**Status:** verified  
**Evidence:** DCOMS-29931 apply summary, product-knowledge § proxy cache, CRM / SM tickets in [transcript-index.json](./transcript-index.json)

## When to recycle

Recycle IIS app pools (or the whole SM site) after:

- SSM or **web.config** changes for CRM, scheduler URL, or other settings read at startup or from cached repos
- **Robocopy deploy** that updates binaries but UI still shows old behavior
- DCOMS-29931-style **CRMSearchResultUrl** / endpoint updates on content servers

Documented rollback copies: `web.config.bak-dcoms29931` beside changed files on content server.

## Site Manager scheduler URL cache

| Symptom | Cause |
|---------|--------|
| Updated `APIGatewayBatchSchedulerURL` in DB/SSM, UI still wrong | **`InfrastructureSettingRepository` ~15 minute cache** |
| API works on raw `execute-api` URL | Custom domain / Route53 mapping wrong (separate issue) |

**Fix:** Recycle affected app pool **or wait ~15 minutes** (product-knowledge [16-operations-runbooks.md](../product-knowledge/16-operations-runbooks.md)).

## CRM connectivity check (REST vs SOAP)

Three layers often disagree until recycle:

1. **SSM** `/oms/{space}/{env}/crm/endpoint`
2. **Postgres** `website_settings` / tenant `CRMRestURL` (REST v3 path)
3. **web.config** `CRMSearchResultUrl` on content SMB tree

SOAP WCF `<endpoint>` lines may still point at legacy `appsvr3` even when REST SSM is updated (out of scope for REST cutover).

**Verify REST:** Hit `.../CRMAPI/v3/` health or search from SM after recycle; compare to Confluence CRM lookup docs (DCOMS-29931 chat).

## Quick IIS introspection (pod2)

`oms_harness_connector/scripts/pod2-Find-ShopLogic.ps1` - list IIS sites and physical paths when debugging wrong deploy target.
