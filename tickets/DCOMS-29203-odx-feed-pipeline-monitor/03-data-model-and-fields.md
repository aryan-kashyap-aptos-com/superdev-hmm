# ODX Data Model and Field Reference

Every ODX-related table, column, enum, and DTO field relevant to the feed pipeline monitor.

---

## `odxtasklogging` — primary monitor data source

**Purpose:** Append-only audit log of RabbitMQ message lifecycle.  
**Domain model:** `DCEOM.Models/Domain/OdxTaskLogging.cs`  
**Schema:** `SQLChangeScripts/2019.1/Shopvisible/DCOMS-7091_Create_Table_OdxTaskLogging_v2.sql`

| Column | C# property | Type | Meaning |
|--------|-------------|------|---------|
| `tasklogid` | `TaskLogId` | bigint PK | Auto-increment log ID |
| `siteid` | `SiteId` | int | ShopVisible site ID |
| `messageid` | `MessageId` | nvarchar(40) | RabbitMQ message GUID (no dashes) — **correlation key** |
| `taskname` | `TaskName` | nvarchar(60) | Feed identifier, e.g. `OMSFeeds:Fulfillment`, `Inventory feed` |
| `referenceid` | `ReferenceId` | bigint | Order ID or Supplier ID depending on feed |
| `taskstate` | `TaskState` | nvarchar(10) | `Queued`, `Started`, or `Done` |
| `result` | `Result` | nvarchar(20) | `Success` or `Error` (meaningful on `Done` rows) |
| `timestamputc` | `TimestampUtc` | datetime | UTC event timestamp |

### Indexes (existing on podqa)

- `IXN_OdxTaskLogging__MessageId` — detail/timeline lookups
- `IXN_OdxTaskLogging__SiteId`
- `IXN_OdxTaskLogging__TimestampUtc` — time-window scans

### Index added by Story 1 (DCOMS-29419)

- `(referenceid, timestamputc)` — order-ID search within time window

### Event pattern

One `messageid` produces **1–3 rows**:

```
Queued  →  Started  →  Done (Success|Error)
```

Monitor API collapses these into `MessagePipelineStatus`:

| DTO field | Source |
|-----------|--------|
| `messageid` | Group key |
| `taskname` | From any row |
| `referenceid` | From any row |
| `queued_at` | `TaskState=Queued` timestamp |
| `started_at` | `TaskState=Started` timestamp |
| `done_at` | `TaskState=Done` timestamp |
| `done_result` | `Result` on Done row |

### TaskState enum

`DCEOM.Models/Enum/OdxTaskLoggingAction.cs`

- `Queued` — written by OMS producer
- `Started` — written by ODX consumer
- `Done` — written by ODX consumer

### Result enum

`DCEOM.Models/Enum/OdxTaskLoggingResult.cs`

- `Success`
- `Error`

---

## `odxfeederror` — consumer exceptions

**Purpose:** Failed feed processing error storage.  
**Schema:** `SQLChangeScripts/2019.1/DCOMS-10835-Create_OdxFeedError_Table_v2.sql`  
**C# model:** None in OMS repo (raw SQL access in monitor)

| Column | Type | Meaning |
|--------|------|---------|
| `errorid` | bigint PK | Auto-increment |
| `error` | nvarchar(max) | Full error payload (often JSON with OrderId, TransactionType) |
| `createdateutc` | datetime | When error occurred |
| `feedtype` | nvarchar(50) | e.g. `export_requested` |

**Scale:** 4.1M rows on podqa  
**Index (Story 1):** `createdateutc` for recent error panel

**Monitor displays:** Error summary and timestamp only — no raw bodies, no PII.

---

## `omsfeedsqueuedorder` — in-flight dedup lock

**Purpose:** Prevents re-queueing orders before consumer finishes.  
**Domain model:** `DCEOM.Models/Domain/OmsFeedsQueuedOrder.cs`

| Column | C# property | Type | Meaning |
|--------|-------------|------|---------|
| `rowid` | `RowId` | bigint PK | Auto-increment |
| `orderid` | `OrderId` | bigint UNIQUE | Order currently being processed |
| `taskid` | `TaskId` | bigint | Task type (0 for OMS feeds) |
| `queueddateutc` | `QueuedDateUtc` | datetime | When order was queued |

**Stuck detection:** Orders present longer than threshold (relates to DCOMS-27496).  
**podqa snapshot:** 205 rows, 203 older than 1 day.

---

## `omsfeedexport` — export JSON staging

**Purpose:** Staging table for export payloads before file output.  
**Domain model:** `DCEOM.Models/Domain/OmsFeedExport.cs`

| Column | C# property | Type | Meaning |
|--------|-------------|------|---------|
| `omsfeedexportid` | `OmsFeedExportId` | bigint PK | Staging record ID |
| `exporttype` | `ExportType` | nvarchar | Transaction type |
| `exportdata` | `ExportData` | nvarchar(max) | Serialized JSON payload |
| `createdateutc` | `CreateDateUtc` | datetime | When record created |
| `fileoutputsubfolder` | `FileOutputSubFolder` | nvarchar | Subfolder for file output |

**Postgres-only columns (schema drift):** `orderid`, `suppresspublicationflag` — not in C# model.

**Index (Story 1):** `createdateutc` or `(orderid, createdateutc)`

---

## `omsfeedexportreader` — file output cursor

**Purpose:** Tracks read position for `OMSFeedsFileOutput` job.  
**Domain model:** `DCEOM.Models/Domain/OmsFeedExportReader.cs`

| Column | Type | Meaning |
|--------|------|---------|
| `omsfeedexportreaderid` | bigint PK | Reader ID |
| `readername` | nvarchar(100) | e.g. `OmsFeedFileoutput_{JobStepID}` |
| `exporttype` | nvarchar(100) | Filename prefix / export type |
| `lastreadindex` | bigint | Last `OmsFeedExportId` read |
| `lastreaddateutc` | datetime | Last read timestamp |

Used in Story 8 for ExportOrderItems stage 2 correlation.

---

## `OMSFeedsExported*Record` — export completion markers

### Item record

`OMSFeedsExportedItemRecord`

| Column | Meaning |
|--------|---------|
| `OMSFeedsExportedItemRecordId` | PK |
| `ItemId` | Order item ID |
| `ExportTypeId` | FK to LookupTable "Integration Export Type" |
| `ExportedDate` | When marked exported |
| `TaskID` | uuid — task correlation (DCOMS-12780) |

### Credit record

`OMSFeedsExportedCreditRecord` — keyed on `OrderCreditId`

### Auth record

`OMSFeedsExportedAuthRecord` — keyed on `OrderAuthId`

### Export type lookup

`DCEOM.Models/Enum/OMSFeedExportType.cs`

- `FulfillmentExportedtoSA`
- `SimpleCreditExported`
- `DetailCreditExported`
- `PaymentExportedtoSA`
- `ReturnExportedtoSA`
- `OrderCreatedExported`
- `CancelledItemExported`
- `ReadyForPickupExported`
- `ServiceChargeExported`

Stored in `LookupTable` where `LookupType = 'Integration Export Type'`.

---

## `odxqueue` — queue configuration metadata

**Domain model:** `DCEOM.Models/Domain/OdxQueue.cs`

| Column | Meaning |
|--------|---------|
| `OdxQueueId` | PK |
| `QueueName` | RabbitMQ queue name |
| `RoutingKey` | Exchange routing key |
| `MaxSize` | Max queue depth |
| `ConsumerDockerName` | Docker service for consumer scaling |
| `MinimumConsumers` / `MaximumConsumers` | Consumer instance bounds |

**Note:** `OdxCredential` table was dropped (DCOMS-24048); credentials now in Parameter Store.

---

## RabbitMQ message fields (`OmsFeedsOrderExportDto`)

| Field | Type | Monitor exposure |
|-------|------|------------------|
| `MessageId` | string | Yes — search key |
| `OrderId` | int | Yes — as `referenceid` |
| `TransactionType` | string | Yes — via `taskname` |
| `Metadata.Version` | string | No (internal) |
| `Metadata.ExportStartDate` | string | No |
| `Metadata.ExportEndDate` | string | No |
| `Metadata.LogExtraDetails` | bool | No |
| `Metadata.SuppressPaymentReceived` | bool | No |
| `Metadata.TaxInclusivePricing` | bool | No |

**Security rule:** API and UI must not expose full RabbitMQ message bodies.

---

## Inventory feed message fields

`InventoryFeedMessageDto` implements `IOdxMessage`:

| Field | Typical value |
|-------|---------------|
| `TaskName` | `Inventory feed` |
| `ReferenceId` | Supplier ID |
| Routing key | `inventory_requested` |

---

## API response shapes (Story 4 contract)

### Summary response

```json
{
  "windowStartUtc": "...",
  "windowEndUtc": "...",
  "tasks": [
    {
      "taskName": "OMSFeeds:Fulfillment",
      "queued": 1200,
      "started": 1180,
      "done": 1150,
      "error": 30
    }
  ]
}
```

### Backlog response

```json
{
  "count": 42,
  "messages": [
    {
      "messageId": "abc123...",
      "taskName": "OMSFeeds:OrderCreated",
      "referenceId": 4781085,
      "queuedAt": "2025-12-18T16:35:29Z"
    }
  ]
}
```

### Timeline response

```json
{
  "messageId": "abc123...",
  "taskName": "OMSFeeds:Fulfillment",
  "referenceId": 4781085,
  "queuedAt": "...",
  "startedAt": "...",
  "doneAt": "...",
  "doneResult": "Success",
  "stagedAt": "...",
  "fileWrittenAt": "...",
  "errors": [],
  "stuckInQueue": false,
  "queueDurationHours": null
}
```

(Exact shapes to match Story 4 implementation when available.)

---

## Query constraints (all monitor queries)

| Rule | Value |
|------|-------|
| Default time window | 24 hours |
| Maximum time window | 7 days |
| Unbounded queries | **Forbidden** |
| Pagination | Required on list endpoints |
| PII in responses | **Forbidden** |
