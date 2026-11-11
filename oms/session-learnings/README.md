# OMS session learnings (from Cursor agent work)

**Status:** verified (distilled 2026-11-10)  
**Audience:** You and future Cursor sessions - ops traps we hit in real tickets, not generic product docs.

This folder captures **how we actually fixed things** after struggling in chat: pod2dev recovery, IIS recycles, EBS disk on content servers, MQ SSM cutover + ECS recycle, Harness traps, CRM endpoints, Simfa Lambda deploy, RDS SSO, batch scheduler zombies, ODX/omsfeed pipelines, and smaller gotchas.

**Sources:** 62 ConnectorSuite agent transcript JSONL files under  
`C:\Users\akashyap\.cursor\projects\c-PROD-ConnectorSuite\agent-transcripts\`  
plus durable artifacts in `C:\PROD\ConnectorSuite\tickets\` (README, CHAT-LOG, runbooks).  
Machine index: [transcript-index.json](./transcript-index.json). Rebuild: `python _build_index.py`.

**Related (canonical product knowledge):** [../product-knowledge/16-operations-runbooks.md](../product-knowledge/16-operations-runbooks.md), [HOME.md](../product-knowledge/HOME.md).

---

## Topic pages

| Page | What you will find there |
|------|--------------------------|
| [pod2dev-ec2-recovery.md](./pod2dev-ec2-recovery.md) | Terminate vs stop, OMS-App-Deploy + DFS, `webserver_setup_require`, Toronado service cleanup |
| [iis-app-pool-and-config-cache.md](./iis-app-pool-and-config-cache.md) | When to recycle SM app pools; 15-minute `InfrastructureSettingRepository` cache |
| [ebs-content-server-disk.md](./ebs-content-server-disk.md) | Picklist disk errors, `sh-cnt` D: full, `productExports`, EFS vs Windows share |
| [mq-ssm-cutover-ecs-recycle.md](./mq-ssm-cutover-ecs-recycle.md) | G1/G2 SSM apply, AMQPS proof, force-new-deployment, password drift, omsfeed image tags |
| [harness-pipeline-traps.md](./harness-pipeline-traps.md) | `environment_name=pod2`, DFS typo, ECR two-account, Git Tag publish |
| [crm-rest-connectivity.md](./crm-rest-connectivity.md) | SSM + Postgres `CRMRestURL` + web.config; SOAP vs REST verification |
| [rds-connector-sso.md](./rds-connector-sso.md) | `AWS_PROFILE` + `aws sso login` instead of pasting temp keys |
| [batch-scheduler-servicemanager-traps.md](./batch-scheduler-servicemanager-traps.md) | Zombie Reserve rows, SM history empty when MQ auth fails |
| [odx-feeds-omsfeed-pipeline.md](./odx-feeds-omsfeed-pipeline.md) | Job steps vs `omsfeedexport`; queue consumer recycle |
| [simfa-lambda-deploy-rollback.md](./simfa-lambda-deploy-rollback.md) | POD QA Lambda deploy, manual rollback, SNOWPA / digital delivery patterns |
| [misc-ops-gotchas.md](./misc-ops-gotchas.md) | DB connector `PGDATABASE`, timezone / JobManager, CloudTrail MQ delete, OMS Engine GUI |

---

## ConnectorSuite ticket map (artifacts)

| Ticket / folder | Tied learnings |
|-----------------|----------------|
| [DCOMS-29691](https://aptos.atlassian.net/browse/DCOMS-29691) pod2dev | `C:\PROD\ConnectorSuite\tickets\DCOMS-29691-pod2dev-ec2-shutdown-restart-validation\` |
| [DCOMS-29982](https://aptos.atlassian.net/browse/DCOMS-29982) | SM history / pod-qa MQ password |
| [DCOMS-29931](https://aptos.atlassian.net/browse/DCOMS-29931) | CRM REST endpoints |
| [DCOMS-29975](https://aptos.atlassian.net/browse/DCOMS-29975) | Simfa digital delivery |
| `tickets/RANDOM/g2-mq-ssm-backup` | G2 cutover summary |
| `tickets/RANDOM/oms-consolidated-mq-pre-destroy-audit` | G1 re-apply, omsfeed stuck orders |
| `tickets/RANDOM/order-worklist-picklist-disk-space-qa-sm` | EBS / picklist |
| `tickets/RANDOM/oms-aws-rds-sso-credentials` | RDS SSO |
| `shared-mq-pilot-pod-omnipod` | MQ SSM export/restore scripts |

Do not commit MQ baseline JSON with decrypted passwords (see that folder `.gitignore`).
