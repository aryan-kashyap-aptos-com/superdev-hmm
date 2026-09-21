## 2026-09-21 — Order facade tax rate from SNOWPA ecom

**Status when closed:** done

- Traced GET order path: OMS XML `TaxAuthRate` → facade `taxes[].rate` via `GetItemTaxes`.
- Traced import path: missing `ItemTaxAuthority` → `GetDefaultTaxAuthority` uses `ItemTax` + lookup "Item Tax Authority Defaults".
- Documented all OMS writers of `TaxAuthRate` (lookup, channel XML, taxation service, Avalara, fees, copy/reship).
- Files touched: `tickets/RANDOM/ecom-order-facade-tax-rate/README.md`, `CHAT-LOG.md`
