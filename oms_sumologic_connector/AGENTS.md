# OMS Sumo Logic Connector — Agent Guide

Query Sumo Logic logs and export results to Excel.

## When to use

- Search OMS application logs (API, payment, services)
- Client health checks (ERROR/WARN counts)
- API path analysis, distinct endpoints, top paths
- Export log query results to `.xlsx`

## Setup

```powershell
cd C:\PROD\ConnectorSuite\oms_sumologic_connector
copy .env.example .env
pip install -r requirements.txt
```

Fill in `.env` with Sumo access keys. **Never read or print `.env` contents.**

## Environment variables

| Variable | Purpose |
|----------|---------|
| `SUMO_DEPLOYMENT` | Deployment region: `us1`, `us2`, `eu`, `au`, `de`, `jp`, `ca`, `in`, `fed` |
| `SUMO_ACCESS_ID` | Access key ID |
| `SUMO_ACCESS_KEY` | Access key secret |
| `SUMO_TIMEZONE` | Search job timezone (default `UTC`) |

## CLI commands

```powershell
python sumologic.py test
python sumologic.py query "<query>" --from -24h --to now --limit 50
python sumologic.py export "<query>" -o exports/report.xlsx --from -7d
python sumologic.py export-file queries/health.txt -o exports/health.xlsx --from -24h
```

### Time range flags

- `--from` — start time: `-15m`, `-1h`, `-24h`, `-7d`, ISO timestamp, or `now`
- `--to` — end time (default `now`)
- `--timezone` — override job timezone
- `--result-type` — `auto`, `messages`, or `records` (use `records` for aggregates)
- `--page-size` — API page size (max 1000)
- `--max-rows` — stop after N rows

## Agent rules

1. **Max 3 queries per request** unless the user asks for more detail.
2. **Never read or print** `.env` or access keys.
3. **Never search `*CLIENT*` text alone** — hits CloudTrail noise.
4. **Confirm scope before querying** — client code, env, time range, question type.
5. **Use saved queries** in `queries/` when they match the task.
6. **Use `--result-type records`** for aggregate queries (`count`, `count_distinct`).
7. **Default time ranges** — `-24h` for health, `-7d` for API stats.

## Client query context

Before querying, confirm (or infer):

| Field | Example |
|-------|---------|
| Client code | 3-letter lowercase: `jmc`, `tly`, `tbh`, `hft` |
| Env | `PROD`, `UAT`, `DEV` |
| Time range | `-24h` health, `-7d` API stats |
| Question type | health / distinct APIs / top paths / export |

## Log locations (pick one scope)

```
API (cloud):    _sourceCategory=DCOMS/API/PROD/{client}
API (legacy):   _collector=OMS-{client}-* AND _sourceCategory=OMS/api
Payment:        _collector=OMS-{client}-* AND _sourceCategory=OMS/payment
Services:       _collector=OMS-{client}-* AND _sourceCategory=OMS/service
Toro/on-prem:   _sourceCategory=DCOM/Prod/Toro/{CLIENT}
Collector:      _collector=OMS-{client}-*
```

If `DCOMS/API/PROD/{client}` returns 0 rows, fall back to legacy `OMS/api` scope.

## Standard queries (replace `{client}`)

**Health (24h)**
```
(_sourceCategory=DCOMS/API/PROD/{client} OR _collector=OMS-{client}-*)
| where _loglevel in ("ERROR","WARN")
| count by _loglevel
```

**Distinct API paths (7d)**
```
_sourceCategory=DCOMS/API/PROD/{client}
| parse regex field=_raw "\"(?<method>GET|POST|PUT|DELETE|PATCH)[^\"]* (?<path>/[^\"\\s?]+)" nodrop
| count_distinct(path)
```

**Top API paths (7d)**
```
_sourceCategory=DCOMS/API/PROD/{client}
| parse regex field=_raw "\"(?<method>GET|POST|PUT|DELETE|PATCH)[^\"]* (?<path>/[^\"\\s?]+)" nodrop
| count by path, method | sort by _count desc | limit 20
```

## Response format

When answering the user:

1. Scope used (client, env, time)
2. Health: ERROR/WARN counts or "none"
3. Metrics: distinct paths, total volume if relevant
4. One-line recommendation

Only drill deeper if the user asks.

## File map

| File | Role |
|------|------|
| `sumologic.py` | CLI entry point |
| `client.py` | Env loading, credentials, API base URL |
| `search.py` | Search job creation and result fetching |
| `export.py` | Excel export |
| `queries/` | Saved query templates |
| `exports/` | Default output directory for Excel files |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Auth error | Check `SUMO_ACCESS_ID` / `SUMO_ACCESS_KEY` and deployment |
| 0 rows | Try legacy scope or wider time range |
| Aggregate query empty | Use `--result-type records` |
| Query timeout | Narrow time range or add filters |
