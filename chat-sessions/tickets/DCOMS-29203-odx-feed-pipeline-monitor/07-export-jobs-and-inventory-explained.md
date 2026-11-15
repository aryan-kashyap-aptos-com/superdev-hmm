# Export jobs, inventory feeds, and what the monitor sees

Plain-language guide to every feed/export path in OMS and how it relates to `odxtasklogging`, `omsfeedexport`, and the ODX monitor UI.

---

## The one sentence version

**Order feeds** export order/payment JSON to Sales Audit (POS). **Inventory feeds** export stock levels per supplier to XML on S3. They share `odxtasklogging` for pipeline tracking but use **different RabbitMQ queues**, **different reference IDs**, and **different output destinations**. Inventory does **not** use `omsfeedexport`.

---

## Three families of "exports" (do not confuse them)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ FAMILY A: OMS Order Feeds (Toronado jobs, FileType = transaction name)   │
│   OMSFeedsScheduled → RabbitMQ export_requested → ODX → JSON to SA/POS   │
│   Logs: odxtasklogging (taskname = OMSFeeds:Fulfillment, etc.)             │
│   Lock: omsfeedsqueuedorder (by order ID)                                │
│   Staging: omsfeedexport (sometimes, depending on consumer path)         │
├─────────────────────────────────────────────────────────────────────────┤
│ FAMILY B: Inventory Feed (Toronado job InventoryFeedScheduler)          │
│   InventoryFeedScheduledProcessing → RabbitMQ inventory_requested      │
│   Logs: odxtasklogging (taskname = "Inventory feed")                     │
│   Reference: supplier ID (not order ID)                                  │
│   Output: S3 XML file (via ODX inventoryfeedsupervisor) — NOT omsfeedexport│
├─────────────────────────────────────────────────────────────────────────┤
│ FAMILY C: Service Manager "Generate Notifications" (ExportOrderItems)    │
│   User-configured scheduled task → task processor → export_requested   │
│   Logs: odxtasklogging (taskname often OMSFeeds:ExportOrderItems)        │
│   Staging: omsfeedexport → OMSFeedsFileOutput job → notification JSON files│
└─────────────────────────────────────────────────────────────────────────┘

LEGACY (many sites still have these Toronado jobs):
│ OMSFeeds (sync) — writes JSON files directly, old ExportedRecord table     │
│   Does NOT use odxtasklogging in OMS code                                │
```

---

## Inventory feed — what it actually is

### Business purpose

Pushes **inventory availability** from OMS to external systems (store feeds, commerce platforms, etc.). One message per **supplier** (warehouse/location), not per order.

### How it runs

1. **Toronado job** `InventoryFeedScheduler` runs on a schedule (like other export jobs in Toronado admin).
2. `InventoryFeedScheduledProcessing` finds supplier IDs that need inventory published.
3. For each supplier, creates `InventoryFeedMessageDto` with a new `MessageId`.
4. Writes **`Queued`** to `odxtasklogging`:
   - `taskname` = `"Inventory feed"`
   - `referenceid` = **supplier ID** (not order ID)
5. Publishes to RabbitMQ routing key **`inventory_requested`** (not `export_requested`).
6. ODX consumer (`inventoryfeedsupervisor`) processes message, writes **`Started`** / **`Done`**, builds XML, uploads to **S3**.

### Does inventory use `omsfeedexport`?

**No.** That table is for **order export JSON** staging (Sales Audit / notifications). Inventory output goes to **S3 XML files** configured in job metadata (`ExportPath`, `FileName` pattern in `InventoryFeedDtoMetaData`).

### Does inventory use `omsfeedsqueuedorder`?

**No** in the OMS producer code — that lock table is for **order IDs** in the order feed path only.

### What you'd search in the monitor

- Task tile: **Inventory feed**
- Search by **supplier ID** in `referenceid`, not order ID
- Timeline ends with **S3 stage** (Story 10) when ODX metadata has the file path

---

## OMS order feed transaction types (Family A)

Each is a separate **Toronado export job** where `Export.FileType` = transaction type.  
`taskname` in `odxtasklogging` = `OMSFeeds:{FileType}`.

| Transaction type | When it fires (plain English) | What JSON represents |
|------------------|------------------------------|----------------------|
| **OrderCreated** | New order placed in OMS | Initial order snapshot to downstream |
| **Fulfillment** | Items shipped / fulfilled | Fulfillment transaction to Sales Audit |
| **PaymentReceived** | Payment captured/received | Payment auth data to SA |
| **Return** | Return processed | Return transaction |
| **Refund** / **SimpleCredit** / **DetailCredit** | Credits/refunds issued | Credit transactions |
| **RefundOnReturn** | Refund tied to a return | Combined return/refund credit |
| **CapturePostFulfillment** | Post-fulfillment capture | Payment capture after ship |
| **ItemCancelled** | Line item cancelled | Cancellation export |
| **ReadyForPickup** | BOPIS/ROPIS ready | Pickup-ready notification export |
| **PaymentsForMissedOrderAuths** | Catch-up payment auths | Missed auth repair export |
| **ServicesCredit** / **ServicesCharge** | Service line fees | Additional service charges/credits |

### Shared pipeline steps (all order types)

```
Eligible order selected
    → Queued logged (odxtasklogging)
    → RabbitMQ export_requested
    → omsfeedsqueuedorder lock
    → [ODX consumer]
    → Started / Done logged
    → Export JSON built
    → OMSFeedsExported*Record marked (item/auth/credit)
    → omsfeedsqueuedorder cleared
    → (optional) row in omsfeedexport
```

### POS suppression (why you see no log for some orders)

Before queueing, OMS may **skip** orders (ROPIS POS, offline POS payments, store returns, etc.). Those never get a `Queued` row — the monitor cannot show them.

---

## Service Manager — NOT the same as Toronado OMS feeds

Service Manager (`ServiceManager.aspx`) is a **user-facing scheduler** for bulk operations. Only **one** action is part of the ODX monitor epic:

| Service Manager action | ODX monitor? | Notes |
|------------------------|--------------|-------|
| **Generate Notifications** (`ExportOrderItems`) | **Yes** (Story 8) | Publishes per-order messages → `omsfeedexport` → file output job |
| Cancel items | No | Internal OMS operation, not SA export |
| Reset items for reroute | No | Internal routing |
| Auto-credit items | No | Internal credit |
| Update item status | No | Internal status change |
| Update inventory availability | No | Different from Inventory **Feed** Toronado job |

**Generate Notifications** 3-stage path:

1. Service Manager task runs → task processor queues orders to RabbitMQ
2. ODX consumer writes JSON into **`omsfeedexport`**
3. **`OMSFeedsFileOutput`** Toronado job reads `omsfeedexport` via `omsfeedexportreader` cursor → writes `.json` notification files to disk

---

## `omsfeedexport` — what it is

**Staging table** for serialized export JSON **before** a file is written to disk.

| Used by | Not used by |
|---------|-------------|
| ODX order export consumer (some paths) | Inventory feed (S3 XML) |
| ExportOrderItems / Generate Notifications | Legacy sync `OMSFeeds` (writes files directly) |
| `OMSFeedsFileOutput` job (reads from it) | Most Service Manager actions |

Columns: `exporttype`, `exportdata` (JSON blob), `createdateutc`, `fileoutputsubfolder`.

---

## `odxtasklogging` — shared audit log

| Field | Order feeds | Inventory feed |
|-------|-------------|----------------|
| `taskname` | `OMSFeeds:Fulfillment`, etc. | `Inventory feed` |
| `referenceid` | Order ID | Supplier ID |
| `messageid` | Rabbit message GUID | Rabbit message GUID |
| `taskstate` | Queued / Started / Done | Same |
| Rabbit routing key | `export_requested` | `inventory_requested` |

**Same table, different semantics for `referenceid`.**

---

## Legacy `OMSFeeds` (sync) — monitor blind spot

Older Toronado job class `OMSFeeds` (not `OMSFeedsScheduled`):

- Finds orders synchronously
- Writes JSON files **directly to disk**
- Uses old `ExportedRecord` / export tracking tables
- **Does not call `OdxTaskLoggingService`** in OMS code

Sites still on legacy jobs won't appear in `odxtasklogging` unless migrated to `OMSFeedsScheduled`.

---

## What the monitor UI tiles represent

Each tile = distinct `taskname` values seen in `odxtasklogging` in the time window:

| UI tile | Source |
|---------|--------|
| OMSFeeds:OrderCreated | Toronado OMS feed job |
| OMSFeeds:Fulfillment | Toronado OMS feed job |
| OMSFeeds:PaymentReceived | Toronado OMS feed job |
| Inventory feed | Toronado InventoryFeedScheduler |
| OMSFeeds:ExportOrderItems | Service Manager Generate Notifications |

Counts are **event rows** grouped by state, not unique orders (unless API pivots per messageid for drill-down).

---

## Are we missing anything in the epic?

### Covered

- All `odxtasklogging` tasknames (order + inventory)
- Backlog, errors, stuck queue
- ExportOrderItems 3-stage
- Inventory S3 indicator (where metadata exists)

### Gaps / not in monitor

| Gap | Why |
|-----|-----|
| Legacy sync `OMSFeeds` jobs | No `odxtasklogging` |
| Service Manager actions (Cancel, Reroute, etc.) | Not ODX export pipeline |
| Orders suppressed before queue | Never logged |
| Live RabbitMQ queue depth | Out of scope |
| Toronado job config / scheduling | Existing WebForms admin |
| `MerchTransferSent`, `OrderRouter` exports | Different export family, no ODX logging |
| Full JSON body preview | Security — out of scope |
| Whether SA actually consumed the file | Downstream of OMS |

### Worth confirming with team

- Are any production sites still on legacy `OMSFeeds` vs `OMSFeedsScheduled`?
- Does order feed consumer always write `omsfeedexport`, or only ExportOrderItems path?
- Exact `taskname` string for ExportOrderItems from ODX handler (may vary)
