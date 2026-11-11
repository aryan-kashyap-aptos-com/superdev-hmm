# Miscellaneous ops gotchas

**Status:** verified (mixed sources)  
**Evidence:** Various `tickets/RANDOM/*` CHAT-LOGs and agent transcripts

## Timezones and scheduling

- Toronado **JobManager** `dailystarttime` / `dailyendtime` use **server local** (CST/CDT)
- RDS `now()` is **UTC**
- `website.ServerTimeOffset` is **ShopLogic UI display only** - not JobManager schedule (DCOMS-29903)

## CloudTrail and MQ

`omnipod-qa-rmq-cloudtrail-delete` - traced **who deleted** omnipod-qa MQ via CloudTrail when broker vanished unexpectedly.

## OMS Engine GUI (ConnectorSuite)

Built for faster Parameter Store / logs / files work:

- Parameter Store full load needed **MaxResults** pagination fix
- AWS **resource name search** for SSM paths
- SFTP removed per feedback; logs sidebar + files cache improvements (multiple chat sessions)

## Omni facade versioning

Multiple OMNI-matched facade deployments **can** target one OMS if configured - limits are **compatibility and ops**, not a single hard blocker (`omni-facade-multi-version-single-oms`).

## AWS cost investigation

`aws-cost-investigation-sep-2026` - CLI scripts for NAT, snapshots, EBS, EIPs (`nat_snapshots_use1.py`).

## Security / hygiene tickets

- DCOMS-30081 - remove CodeMirror `mode/php`
- DCOMS-30069 - eMudhra cert compromise impact map
- TinyMCE `auth_example.php` deployment risk - remove on feature branch

## Name tag ECS runs

`name-tag-runs` - backup JSONL before fixing wrong ECS **Name** tag values; scan-then-apply wizard pattern.

## Harness connector / ODX CI

`oms-harness-connector-and-odx-ci` - green CI can still ship **stale ODX UI** if `alpha_common` skipped.

## Where ConnectorSuite ticket docs live

Flat `tickets/<KEY-or-RANDOM>/` with `README.md` + `CHAT-LOG.md` - session narrative stays there; this folder holds **cross-ticket distillate**.
