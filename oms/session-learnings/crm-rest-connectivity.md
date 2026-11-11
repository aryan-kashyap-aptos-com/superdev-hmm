# OMS CRM connectivity (REST cutover)

**Status:** verified  
**Evidence:** DCOMS-29931 `apply-20261013/APPLY-SUMMARY.md`, `tickets/DCOMS-29931-oms-dev-crm-rest-api-endpoints/`, transcript-index `crm`

## Three configuration surfaces

| Layer | What changes |
|-------|----------------|
| **SSM** | `/oms/{space}/{env}/crm/endpoint` → `https://dev-crm.aptos.com:4497/CRMAPI` (or `:4447` for integration QA) |
| **Postgres** | Per-tenant `CRMRestURL` → `.../CRMAPI/v3/` |
| **Content server** | `web.config` `CRMSearchResultUrl` on each tenant SMB tree |

Apply backups live in `backup-20261013/` (SSM JSON, postgres listings).

## SOAP vs REST

- **REST** lookup uses `CRMRestURL` / v3 API paths.
- Legacy **SOAP WCF** `<endpoint>` in web.config may still reference `appsvr3` even after REST SSM update - treat as separate verification.

## How to verify integration works

1. Confirm SSM + DB + web.config **same port** (`4497` vs `4447`) for that tenant.
2. **Recycle IIS** for that SM site (config cache).
3. SM CRM customer search - network tab or logs should hit `dev-crm.aptos.com` REST path, not legacy host.
4. Compare to Confluence "Site Manager CRM lookup" (pulled during DCOMS-29931 transcript).

## Rollback

- SSM: `backup-20261013/ssm-crm-endpoint.json`
- DB: `postgres-crm-listings.json`
- web.config: `*.bak-dcoms29931` on server

## Gap

Pod2 SM file tree on `oms-pod2-dev-content` was not fully file-scanned in apply pass even though SSM `/oms/pod2/dev/crm/endpoint` was updated.
