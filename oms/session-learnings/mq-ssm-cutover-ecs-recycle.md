# MQ SSM cutover and ECS recycle

**Status:** verified  
**Evidence:** `tickets/RANDOM/g2-mq-ssm-backup/G2-CUTOVER-SUMMARY.md`, `tickets/RANDOM/oms-consolidated-mq-pre-destroy-audit/CHAT-LOG.md`, `shared-mq-pilot-pod-omnipod/`

## Rule

**Changing SSM MQ host/vhost/password is not enough.** ECS services (and sometimes Toronado consumers) hold **long-lived AMQP connections**. After SSM cutover:

```bash
aws ecs update-service --cluster <cluster> --service <service> --force-new-deployment --region us-east-1
```

Typical services: `taskscheduler`, `taskprocessor`, `omsfeed`, `omsinventoryfeed`, `servicemanagerscheduler` (env-dependent).

## G1 / G2 cutover pattern

1. Backup SSM to dated JSON (`mq-backup-g1-*`, `mq-backup-g2-*`).
2. Apply cutover script (`apply_g1_ssm_cutover.py`, `apply_g2_ssm_cutover.py`) - watch for **quiet** progress; interrupted script may still have applied all puts.
3. **AMQPS proof** from **content server in VPC** (not bastion alone) with same creds ECS task definitions use (`pika` to `:5671`, correct vhost).
4. `force_deploy_*_mq_services.py` across catalog envs.
5. Verify taskscheduler `/health` → RabbitMQ **Healthy**; CloudWatch no `Cannot establish RMQ channel`.

## Password drift (pod-qa / DCOMS-29982)

Symptom: SM task history **0 rows**; taskscheduler `/health` RabbitMQ **Unhealthy**; AMQPS **403 ACCESS_REFUSED** for one env only.

Fix: Re-align `/oms/pod/qa/aws-mq-broker/adminpassword` (and `applicationpassword`) with known-good G1 broker user, then recycle taskscheduler + taskprocessor.

**UI detail:** History grid skips runs with `StartTimestamp == null` (pending/failed dispatch looks like "no history").

## omsfeed-specific

After MQ change, `omsfeedsqueuedorder` can backlog while `omsfeedexport` stops advancing.

- Force-new-deployment on `oms-pod-*-omsfeed-service`
- If task fails to start: check ECR tag exists (example: missing `1.4.0-beta-012bbed` → register working image revision)

## Rollback / pilot scripts

| Script | Use |
|--------|-----|
| `shared-mq-pilot-pod-omnipod/scripts/Export-MqSsmBaseline.ps1` | Pre-change export |
| `Restore-MqSsmBaseline.ps1` | Rollback SSM from baseline JSON |
| `Open-TempMqConsole.ps1` | SSM port-forward MQ console via bastion |

**Never commit** `ssm-mq-baseline-*.json` with decrypted secrets (gitignored).

## Harness trap

Avoid **`UPDATE_SSM=true`** Harness runs for a **single** G2 prefix without full broker alignment - caused pod-qa drift on G1 (see G2-CUTOVER-SUMMARY).
