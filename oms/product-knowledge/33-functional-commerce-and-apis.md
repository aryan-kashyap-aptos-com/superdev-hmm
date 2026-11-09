# Commerce UI + Site Manager APIs — scenarios & expectations

**Audience:** QA, commerce/CSR developers, Batch migration testers.  
**Scope:** `roleGroup` **Commerce** UI (`ShopVisible.Core.ShopLogic/backadmin`) + **`DCEOM.WebApi`** (same site origin).  
**Inventories:** [commerce-backadmin-pages.md](./inventories/commerce-backadmin-pages.md) (68 pages), [dceom-webapi-api-catalog.md](./inventories/dceom-webapi-api-catalog.md).

**Not in this repo:** Partner **order/inventory facades** (`orderfacade`, `inventoryfacade` ECS) — see [09-facades-core-edge.md](./09-facades-core-edge.md).

---

## 1. Architecture

```text
Operator browser
  → backadmin/*.aspx (WebForms) ──► DCEOM.BackAdmin.Application.Controllers
  → React bundles ──► fetch("/api/…") ──► DCEOM.WebApi (Web API 2)
  → Batch Job Manager React ──► /api/v1/* ──► BatchSchedulerProxyController ──► scheduler ECS
```

| Layer | Auth expectation |
|-------|------------------|
| `.aspx` | `BaseCommonPage` / `validateSiteMgrUser()` — session + role/resource |
| `/api/*` with `[ClientSideAuthorization]` | Site Manager **ASP.NET session cookie** |
| `/api/v1/*` proxy | Session + **`ServiceManagerModernizationGuard`** + scheduler URL in DB |
| Facade HTTP | Bearer JWT (Keycloak) — **not** ShopLogic cookie |

---

## 2. Cross-cutting scenarios (all Commerce + APIs)

| # | Scenario | What happens | Expected |
|---|----------|--------------|----------|
| C1 | Valid CSR session, resource allowed | Page loads; API returns 200 | Normal UI/API behavior |
| C2 | No session / timeout | Redirect login or API **401** | `ClientSideAuthorization` message |
| C3 | Session OK, **no resource** permission | SM may show error/blank; API may 401/403 depending on page | Fix `rolesvsresources` for role |
| C4 | **`?store=1`** store mode | `manage-orders`, ShowOrders hide customer links | Store-scoped UX |
| C5 | **Supplier** user (`Session["isSupplier"]`) | Master nav hides Commerce/Content/…; order pages use `roleGroupId=10` breadcrumbs | Supplier order view only |
| C6 | **`rid` / `roleID` query** mismatch | Wrong submenu/highlights | Match link from `resources.xml` for that role |
| C7 | Sales tax suppressed cookie | `SalesTax=1` → tax APIs return suppressed path | See `OrdersController` |
| C8 | DB replica lag (rare) | Stale order list | Refresh; ops checks RDS |

---

## 3. Commerce UI — functional groups (all 68 pages)

Each row: **pages** → **purpose** → **happy path** → **what can go wrong** → **expectation**.

### G1 — Hub & navigation

| Pages | Purpose | Happy path | Failures | Expect |
|-------|---------|------------|----------|--------|
| `commerce.aspx` | Commerce landing (tabs/stats) | Open from nav → `TabContent` loads stats | No permission | Hub only; links need resources |
| `manage-orders.aspx` | Manage entry; `store` panel | Links to worklist/list tools | `store=1` layout | Correct store panel visibility |

### G2 — Order search, list, AJAX

| Pages | Purpose | Happy path | Failures | Expect |
|-------|---------|------------|----------|--------|
| `ShowOrders.aspx` | Primary **Manage Existing** grid | Filter/sort → rows; drill to ViewOrder | Timeout on huge filters | Grid binds; export paths under `productExports/Orders` |
| `ordersAjax.aspx` | AJAX order grid fragments | Partial updates | Script/JSON errors | No full postback |
| `europeanorders.aspx`, `giftcardOrders.aspx` | Variant list scopes | Same as ShowOrders pattern | Wrong affiliate filter | Correct dataset |
| `orderstatusreport.aspx`, `itemStatusReport.aspx`, `orderSummaryReportDetails.aspx`, `ordernotesreport.aspx`, `BackOrderProductReport.aspx` | Operational reports | Run report → export/print | Empty data | Report still renders |

**ShowOrders specifics:** Uses `ViewOrderViewController`; honors `roleID`; customer link to `editcustomer.aspx` unless `store` mode; Amazon-like orders may lack billing contact (falls back to shipping).

### G3 — Order detail & CSR actions

| Pages | Purpose | Happy path | Failures | Expect |
|-------|---------|------------|----------|--------|
| `ViewOrder.aspx` | Single order workspace | Load order id → tabs/actions | Invalid id | Error or empty per `OrderViewController` |
| `orderAction.aspx` | Bulk/single actions on orders | Select action → confirm → DB update | EOM validation | Action-specific message; partial success possible |
| `CustomerOrders.aspx`, `CustomerOrdersFrame.aspx` | Orders for one customer | Customer context | Missing `custid` | Scoped list |
| `OrderNotes.aspx`, `OrderItemAdditionalInfo.aspx` | Notes / line metadata | Save note/fields | Concurrency | Persisted to OMS DB |
| `viewOrderPrint.aspx` | Printable order | Print layout | — | Read-only |

### G4 — Worklist & fulfillment pipeline

| Pages | Purpose | Happy path | Failures | Expect |
|-------|---------|------------|----------|--------|
| `order-worklist.aspx` | Pick/pack/ship queues | Tabs: pickup vs ship; counts | `validateSiteMgrUser` fail | `OrderWorklistViewController` DTOs; PDF labels via iText when configured |
| `FulfillOrder.aspx` | Fulfillment wizard | Lines fulfilled → status change | Inventory lock | Status transitions in DB |
| `ShipOrder.aspx`, `ShipOrderLabel.aspx` | Ship + label | Carrier selection → label | Carrier API down | Error surfaced in UI |
| `GetShipmentTracking.aspx`, `trackingList.aspx`, `sentTrackingList.aspx` | Tracking admin | List/send tracking | Bad tracking # | Logged; no silent success |
| `OrderShippingUpdate.aspx`, `OrderShippingRecalculate.aspx` | Shipping corrections | Recalc totals | Invalid address | Tax/shipping services invoked |
| `sendPO.aspx`, `sendPO_reset.aspx` | Supplier PO send | PO transmitted | Supplier config missing | User-visible failure |
| `fulfillment-rules.aspx`, `fulfillmentSettlement.aspx` | Rules/settlement config | Save rules | Validation | Config in DB |

### G5 — Returns, credits, RMA

| Pages | Purpose | Happy path | Failures | Expect |
|-------|---------|------------|----------|--------|
| `returnList.aspx`, `ProcessReturn.aspx` | Return processing | Return authorized → inventory/credit | Item not returnable | `ProcessReturnController` errors shown |
| `RequestRma.aspx`, `RefundOrder.aspx` | RMA/refund UI (also APIs below) | Wizard complete | Payment already captured | Use `/api/RequestRma`, `/api/RefundOrder` from React where migrated |
| `applyReturnCredit.aspx`, `CreditOrder.aspx` | Credits | Credit applied to order | Over-credit | `CreditOrderViewController` exceptions |
| `report-returns.aspx`, `CreditReturnsReport.aspx` | Reporting | Export | — | Read-only |

### G6 — Payments, gift cards, AVS

| Pages | Purpose | Happy path | Failures | Expect |
|-------|---------|------------|----------|--------|
| `PaymentTypes.aspx`, `managePaymentTypes.aspx`, `addPaymentType.aspx` | Payment type admin | CRUD payment types | Duplicate code | DB constraint message |
| `GiftCards.aspx`, `addGiftCard.aspx`, `editGiftCard.aspx`, `deptGiftCard.aspx` | Gift card admin | Issue/edit card | Invalid amount | Validation |
| `avsInformation*.aspx` (9) | AVS tier configuration | Save tier rules | — | Config tables updated |
| `addTierGroupPayment.aspx` | Tier/payment linkage | Save | — | Affiliate tier DB |

### G7 — Call tracking & misc commerce

| Pages | Purpose | Happy path | Failures | Expect |
|-------|---------|------------|----------|--------|
| `callTracking*.aspx` (5) | Call center logs | Log lifecycle | — | CRUD on tracking tables |
| `HistoricalAffiliateTracking.aspx` | Affiliate tracking history | View | — | Read-only |
| `InternationalAddressFormat.aspx` | Intl address admin | Save formats | — | Pairs with `/api/AddressConfig` |
| `ItemCancellationStatuses.aspx` | Cancellation reason admin | Configure statuses | — | Used by cancel flows + Batch tasks |
| `eBillMeOrderStatus.aspx` | eBillMe integration status | Status view | Gateway down | Error panel |

---

## 4. `DCEOM.WebApi` — scenarios by controller family

Unless noted, failures: **401** (no session), **404** (missing entity), **400** (validation), **500** (logged).

### 4.1 Orders & tax — `api/orders` (`OrdersController`)

| Endpoint | Scenario | Expect |
|----------|----------|--------|
| `GET {id}/item-status-summary` | CSR opens order status widget | **200** + counts; **404** if order missing |
| `PUT {id}/salesperson` | Change CSR on order | **200**; **401** if no `salesId` in session; **404** order; **400** bad name |
| `POST {id}/summary-tax` | Edit lines → refresh summary tax | **200** DTO; respects `SalesTax` cookie suppression |
| `POST {id}/tax-calculation` | Line-level tax calc | **200**; same suppression rules |

### 4.2 Order auth — `api/OrderAuth`

| Pattern | Scenario | Expect |
|---------|----------|--------|
| `GET GetByOrder/{orderId}` etc. | Payment UI needs auth rows | **200** list; empty if no auths |
| `POST New/` | Create auth record | **200**/DTO; validation on bad payload |

### 4.3 Aggregate order — `api/AggregateOrder`

| Endpoint | Scenario | Expect |
|----------|----------|--------|
| `GET GetById/{orderId}` | Load header aggregate | Order DTO or **404** |

### 4.4 Refund & RMA — `api/RefundOrder`, `api/RequestRma`

| Step | Scenario | Expect |
|------|----------|--------|
| `GET context/{orderId}` | Open refund/RMA wizard | Context DTO; **404** bad order |
| `GET preview` / `fees` | User previews financial impact | Calculated fees |
| `POST submit` / `commit` | Commit refund/RMA | **200**; processor errors → **400** with message |
| `GET emailtemplate/{orderId}` | Email preview | Template HTML/body |

### 4.5 Manual payment auth — `api/ManualAuth`

| Endpoint | Scenario | Expect |
|----------|----------|--------|
| `GET context/{orderId}` | Manual auth UI | Context |
| `POST commit` | Submit manual auth | Processor result; declines → **400** |

### 4.6 Fulfillment — `api/ItemFulfillment`

| Endpoint | Scenario | Expect |
|----------|----------|--------|
| `POST Update` | Update fulfillment from SPA | Line updates persist; validation errors **400** |

### 4.7 Shipping — `api/Shipping`, `api/shippingRestriction`, `api/Suppliers`

| Endpoint | Scenario | Expect |
|----------|----------|--------|
| `GET Carriers` / `ActiveCarriers` | Populate ship UI | Carrier list |
| `GET services/{carrierId}` | Services for carrier | Service codes |
| Shipping restriction endpoints | Validate restricted ship | Allowed/blocked |
| `GET SuppliersAndAddresses/{name}` | Supplier picker | Addresses |

### 4.8 Taxation — `api/TaxationService` (no ClientSideAuthorization on class — verify deployment rules)

| Endpoint | Scenario | Expect |
|----------|----------|--------|
| `CalculateTax` / `UpdateOrderTax` | Cart/order tax | Tax lines returned |
| `GetMultiShipTax` | Multi-shipment orders | Per-ship tax |
| `CalculateFeeTax` | Fee tax | Fee tax DTO |

### 4.9 Payments — Aurus / Cybersource / extensible

| Prefix | Scenario | Expect |
|--------|----------|--------|
| `api/payment/aurus` | Auth/capture/void | Processor codes; declines logged |
| `api/payment/aurus/view` | iframe session | iframe URL |
| `api/payment/Cybersource` | Token + authorize | Transient token flow |
| `api/payment/extensible` | Plugin capture/void | Extensibility payment types |
| `api/PaymentAggregate` | Resolve processor URL/guid | Config-driven routing |
| `api/ExtensiblePaymentTypes` | CRUD payment types | Standard REST |

### 4.10 Product/supplier inventory (commerce-adjacent)

| Prefix | Scenario | Expect |
|--------|----------|--------|
| `api/ProductSupplier` | Reserve/update supplier SKU qty | Optimistic failures → **400** |
| `api/ProductSupplierOptions` | Option-level inventory | Same |

### 4.11 Task scheduler UI API — `api/TaskSchedulerView`

Supports **legacy scheduled task** UI (feeds into paths that **Batch** is replacing).

| Endpoint | Scenario | Expect |
|----------|----------|--------|
| `GET ""` | List scheduled tasks | All tasks for site |
| `GET Get*Filters` | Build filter dropdowns | Filter metadata |
| `POST CreateService` | Create scheduled task | **200**; invalid filter → **400** |
| `GET/DELETE GetService/{taskId}` | View/delete task | **404** unknown id |
| `GET GetOrderPreviewByFilter` | Preview orders matching task filter | Count/sample orders |
| `GET GetInventoryServicePreviewByFilter` | Preview inventory scope | Preview DTO |

**Batch migration note:** Bulk cancel/update/export/reroute/inventory should move to **BJM + Batch**; this API remains for legacy TASK definitions until cutover ([29-functional-batch-jobs.md](./29-functional-batch-jobs.md)).

### 4.12 ODX feed monitor — `api/OdxFeedMonitor`

| Endpoint | Scenario | Expect |
|----------|----------|--------|
| `GET summary` | Dashboard tiles | Paged summary + task message counts |
| `GET backlog` | Queue depth | Counts + message ids |
| `GET stuckorders` | Stuck detection | Order ids list |
| `GET errors` | Error stream | Paged errors |
| `GET timeline/{messageId}` | Trace one message | Timeline DTO |
| `GET messages` / `search` | Search/export feed messages | Paginated |
| `GET orderqueue/{orderId}` | Per-order queue state | Queue snapshot |

Invalid date window → **400**; service failure → **500**.

### 4.13 Batch scheduler proxy — `api/v1/{*path}`

| Scenario | Expect |
|----------|--------|
| Modernization **disabled** | **403** JSON title/detail (before forward) |
| Modernization enabled, scheduler URL missing | **503** “not configured” |
| Enabled + valid URL | Transparent pass-through of scheduler status/body |
| Scheduler down | **502**/5xx from HttpClient |

BJM React uses same paths as [30-functional-scheduler-platform.md](./30-functional-scheduler-platform.md).

### 4.14 Configuration & platform

| Prefix | Scenario | Expect |
|--------|----------|--------|
| `api/infrastructure/setting` | Read/write infra settings (e.g. scheduler URL) | CRUD; `health/check` for probes |
| `api/WebsiteSettings` | Site settings read | Settings DTO |
| `api/config` | Misc config (`GetEstShipTimeOut`) | Single values |
| `api/ConfigRule` | Fee rules | Fee config by group |
| `api/GetParam` | Legacy param read | Value string |
| `api/sanitizeHtml` | Sanitize user HTML | Clean HTML |

### 4.15 Affiliate group admin — `api/AffiliateGroupView`

Large surface (fulfillment rules, PayPal settings, returns, suppliers, products). **Scenario pattern:** CRUD per sub-resource; **404** on bad id; validation on **400**; all require session auth.

### 4.16 Address — `api/AddressConfig`

Country/state/city cascades for intl checkout/commerce. **Expect:** lists for valid ids; **404**/empty for unknown ids.

### 4.17 Order currency — `api/OrderCurrency`

Multi-currency orders: get/set currency symbols and affiliate currency. Session auth on controller.

### 4.18 Custom email — `api/CustomEmail`

`GET generateCustomEmail/{orderId}` — template generation for CSR comms.

### 4.19 Whitelisted image URLs — `api/whitelistedImageUrls`

CDN/security allowlist CRUD for content/commerce images.

---

## 5. BackAdmin controllers (server-side for `.aspx`)

Commerce pages delegate to `DCEOM.BackAdmin.Application.Controllers` (not HTTP). Same scenarios as UI groups:

| Controller | Tied UI |
|------------|---------|
| `OrderWorklistViewController` | `order-worklist.aspx` |
| `ViewOrderViewController` / `OrderViewController` | `ShowOrders`, `ViewOrder` |
| `FulfillOrderViewController`, `ShipOrderViewController` | Fulfill/ship pages |
| `ProcessReturnController`, `ReturnListViewController` | Returns |
| `CreditOrderViewController` | Credits |
| `OrderActionController` | `orderAction.aspx` |
| `TrackingListViewController` | Tracking lists |

**Expectation:** Exceptions in controllers bubble to `.aspx` as error labels or redirects; API counterparts return HTTP codes above.

---

## 6. External APIs (outside monorepo)

| API | Use | Auth |
|-----|-----|------|
| `orderfacade` ECS | Partner order CRUD | JWT |
| `inventoryfacade` ECS | Partner inventory | JWT |
| `coreapi` / `corepaymentapi` | Core commerce services | JWT |
| `oms-aws-job-scheduler` | Batch catalog | JWT (direct) or proxy |

Site Manager **cookie does not** authorize facade calls.

---

## 7. QA scenario packs (recommended)

| Pack | Covers |
|------|--------|
| **P1 Order CSR** | Login → `ShowOrders` → `ViewOrder` → change salesperson API → tax refresh API |
| **P2 Fulfillment** | `order-worklist` → `FulfillOrder` → `ShipOrder` → tracking list |
| **P3 Returns** | `returnList` → `ProcessReturn` → refund API context/submit |
| **P4 Payments** | Manual auth API; Aurus/Cybersource sandbox decline/approve |
| **P5 Migration** | BJM → proxy → scheduler → one Batch job; ODX monitor `summary` with empty backlog |
| **P6 Supplier** | Supplier login → supplier ShowOrders breadcrumb (`roleGroup 10`) |

Pod dev login: [03-qa-environments.md](./03-qa-environments.md).

---

## Related

- [06-site-manager-shoplogic.md](./06-site-manager-shoplogic.md)  
- [28-functional-oms-monorepo.md](./28-functional-oms-monorepo.md)  
- [27-functional-cross-repo-flows.md](./27-functional-cross-repo-flows.md)  
- [FUNCTIONAL-COVERAGE.md](./FUNCTIONAL-COVERAGE.md)
