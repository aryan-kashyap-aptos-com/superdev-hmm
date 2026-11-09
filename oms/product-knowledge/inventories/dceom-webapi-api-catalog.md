# DCEOM.WebApi — HTTP catalog

Host: Site Manager **same origin** (`https://…/backadmin/…` → `https://…/api/…`).

**Auth:** Most controllers use `[ClientSideAuthorization]` → valid Site Manager session cookie (`InvalidCredentialException` → **401**).

## `AddressConfigurationController`

- **Prefix:** `api/AddressConfig`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `AffiliateGroupViewController`

- **Prefix:** `api/AffiliateGroupView`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `AffiliateServiceController`

- **Prefix:** `api/AffiliateServiceView`
- **Session auth:** False

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `AggregateOrderController`

- **Prefix:** `api/AggregateOrder`
- **Session auth:** False

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `AurusAuthController`

- **Prefix:** `api/payment/aurus`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `AurusPaymentController`

- **Prefix:** `api/payment/aurus`
- **Session auth:** False

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `AurusPaymentViewController`

- **Prefix:** `api/payment/aurus/view`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `BatchSchedulerProxyController`

- **Prefix:** `api/v1`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `ConfigController`

- **Prefix:** `api/config`
- **Session auth:** False

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `ConfigRuleController`

- **Prefix:** `api/ConfigRule`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `CustomEmailController`

- **Prefix:** `api/CustomEmail`
- **Session auth:** False

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `CustomerProfileAnswersController`

- **Prefix:** `api/CustomerProfileAnswers`
- **Session auth:** False

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `CybersourcePaymentViewController`

- **Prefix:** `api/payment/Cybersource`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `ExtensiblePaymentController`

- **Prefix:** `api/payment/extensible`
- **Session auth:** False

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `GetParamController`

- **Prefix:** `api/GetParam`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `InfrastructureSettingController`

- **Prefix:** `api/infrastructure/setting`
- **Session auth:** False

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `ItemFulfillmentController`

- **Prefix:** `api/ItemFulfillment`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `ManualAuthController`

- **Prefix:** `api/ManualAuth`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `OdxFeedMonitorController`

- **Prefix:** `api/OdxFeedMonitor`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `OrderAuthController`

- **Prefix:** `api/OrderAuth`
- **Session auth:** False

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `OrderCurrencyController`

- **Prefix:** `api/OrderCurrency`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `OrdersController`

- **Prefix:** `api/orders`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `PaymentAggregateController`

- **Prefix:** `api/PaymentAggregate`
- **Session auth:** False

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `PaymentTemplatesController`

- **Prefix:** `api/PaymentTemplates`
- **Session auth:** False

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `PaymentTypeController`

- **Prefix:** `api/ExtensiblePaymentTypes`
- **Session auth:** False

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `ProductSupplierOptionViewController`

- **Prefix:** `api/ProductSupplierOptions`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `ProductSupplierViewController`

- **Prefix:** `api/ProductSupplier`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `RefundOrderController`

- **Prefix:** `api/RefundOrder`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `RequestRmaController`

- **Prefix:** `api/RequestRma`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `SanitizeHtmlController`

- **Prefix:** `api/sanitizeHtml`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `ShippingController`

- **Prefix:** `api/Shipping`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `ShippingRestrictionController`

- **Prefix:** `api/shippingRestriction`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `SupplierController`

- **Prefix:** `api/Suppliers`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `TaskSchedulerViewController`

- **Prefix:** `api/TaskSchedulerView`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `TaxationServiceController`

- **Prefix:** `api/TaxationService`
- **Session auth:** False

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `WebsiteSettingsController`

- **Prefix:** `api/WebsiteSettings`
- **Session auth:** False

| HTTP | Route suffix | Action |
|------|--------------|--------|

## `WhitelistedImageUrlController`

- **Prefix:** `api/whitelistedImageUrls`
- **Session auth:** True

| HTTP | Route suffix | Action |
|------|--------------|--------|
