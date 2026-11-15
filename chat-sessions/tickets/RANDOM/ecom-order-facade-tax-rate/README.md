# Ecom order facade tax `rate` field

**Intent:** Document how Order Facade `GET` order maps OMS `TaxAuthRate` to JSON `taxes[].rate` for channel-imported (SNOWPA) ecom orders.

**Status:** Reference doc from code trace (2026-09-21).

**Key code**

- `c:\OMS Other\eom-service-order-facade\src\EOM.OrderFacade\Services\OrderService.cs` — `GetItemTaxes`, `ConvertToCustomerOrder`
- `c:\oms\ShopVisible.Core.DataObjects.V2\OrderDO.cs` — `GetDefaultTaxAuthority` on import when no `ItemTaxAuthority` in payload

**Decision:** For API orders with only `ItemTax` (no tax authority XML), OMS stores dollar tax from the channel and default authority metadata (often `TaxAuthRate` = 0 from lookup); facade passes that through — it does not derive rate from amount ÷ taxable base.
