# Batch scheduler and Service Manager traps

**Status:** verified  
**Evidence:** DCOMS-29982 README, oms-consolidated-mq CHAT-LOG (job 68816), product-knowledge BJM section

## Stuck Toronado / scheduler job (pod-qa 68816)

**Symptom:** `Unreserve, Routing, Reserve` pipeline stale; step `processstate=2` for hours; peers healthy.

**Fix applied:** `force-new-deployment` on `oms-pod-qa-servicemanagerscheduler-service` - startup **`ResetZombies`** cleared stuck **Reserve** rows.

**Lesson:** Before deep SQL surgery, try scheduler ECS recycle when only one job family is wedged.

## SM history empty (pod-qa)

Not always "scheduler broken" - often **MQ auth** prevents dispatch:

- Runs created with `StartTimestamp == null` are **hidden** in SM grid
- Fix MQ passwords in SSM, recycle **taskscheduler** + **taskprocessor**

Secondary: `servicemanagerscheduler` failing queries to `oms_batch.scheduled_job` affects Batch/EventBridge SM jobs, not EOM history path.

## Batch Job Manager quick AWS checks

From [16-operations-runbooks.md](../product-knowledge/16-operations-runbooks.md):

```bash
aws ecs describe-task-definition --task-definition <prefix>-servicemanagerscheduler-td \
  --query "taskDefinition.containerDefinitions[0].environment[?starts_with(name,'EventBridgeScheduler')]" \
  --output table --no-cli-pager

aws batch describe-job-definitions --job-definition-name <prefix>-inventory-feed-jd \
  --status ACTIVE --query "reverse(sort_by(jobDefinitions,&revision))[0].[revision,containerProperties.image]" \
  --output text --no-cli-pager
```

## Proxy / custom domain

If UI fails but direct API Gateway URL works - check custom domain mapping; separate from 15-minute settings cache (see [iis-app-pool-and-config-cache.md](./iis-app-pool-and-config-cache.md)).
