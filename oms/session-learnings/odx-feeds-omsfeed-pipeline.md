# ODX feeds and omsfeed pipeline

**Status:** verified  
**Evidence:** DCOMS-29203 ticket, oms-consolidated-mq CHAT-LOG, product-knowledge [08](../product-knowledge/08-task-engine-feeds.md)

## Pipeline (do not confuse steps)

1. **Toronado job step** (e.g. 72985 **ODX OrderCreated** on `OMSFeedsScheduled`) - marks work in SM scheduler; does **not** directly insert `omsfeedexport`.
2. SM / engine publishes **`export_requested`** to MQ + row in **`omsfeedsqueuedorder`**.
3. **`omsfeed` ECS consumer** processes queue → writes **`omsfeedexport`** → downstream file/output jobs.

Stuck symptom: queue rows growing, `omsfeedexport` max timestamp frozen, no new `OrderCreated` rows.

## Debug checklist

| Check | Meaning |
|-------|---------|
| MQ healthy for env? | Post-cutover without omsfeed recycle = common stall |
| `omsfeedsqueuedorder` count | Backlog |
| `odxfeederror` for `export_requested` | Consumer exceptions (e.g. null parse in `GetAffilateGroupId`) |
| Correct **database** | Order may exist only on podqa not poddev |

## ODX Feed Pipeline Monitor (SM UI)

**Content → Tasks → ODX Monitor** - read-only RabbitMQ/ODX visibility (`odxtasklogging`, `omsfeedsqueuedorder` stuck > 4h). Does **not** replay queues.

## Manual learning session

DCOMS-29203 chat included manual `oms_push` trigger to observe behavior - use monitor UI + CloudWatch, not production replay without approval.
