# DCOMS-29625 — Review ISL shipping connector to fix shipFrom phone number

**Jira:** [DCOMS-29625](https://aptos.atlassian.net/browse/DCOMS-29625)  
**Status:** In Progress  
**Assignee:** Aryan Kashyap  
**Type:** Bug - Internal | **Priority:** Level 3 | **Points:** 5  
**Sprint:** 2026.7 Warriors 252 | **Candidate:** 2026.7.0

## Intent

Align OMS → ISL label payload with domain canonical for **BusinessUnit** (`shipFrom`, `sourceBusinessUnit`, customer-order `businessUnit`) phone: use `telephoneNumbers[]` with `primaryFlag`, not the `shipTo`-style `phone.phoneNumber` object.

## Related

- [INTSER-579](https://aptos.atlassian.net/browse/INTSER-579) — Shippo adapter shipFrom telephone (Closed)
- [DCOMS-29498](https://aptos.atlassian.net/browse/DCOMS-29498) — OMS → EasyPost via ISL (Closed)
- Canonical types: [scp-types-canonical-shipping](https://bitbucket.org/aptosretail/scp-types-canonical-shipping/src/master/)

## Primary fix location

**`oms-isl-client` (`Aptos.OMS.Isl`)** — not OMS UI or `IslShipmentLabelService` data sourcing.

| Area | Action |
|------|--------|
| `BusinessUnit.cs` | `telephoneNumbers` list instead of `phone` |
| `LabelService.BuildBusinessUnit()` | Emit canonical array shape |
| `ShippingLabelRequestShipmentContextMapper.cs` | Read from `telephoneNumbers` (legacy `phone` optional) |
| Tests | `shipFrom` → `telephoneNumbers`; `shipTo` unchanged |

**OMS:** Bump `Aptos.OMS.Isl` NuGet after publish (was 1.6.0).

## Rollout notes

- Coordinate with IS/Shippo adapter for dual-shape read during transition.
- Scope may include all `BuildBusinessUnit()` consumers, not only `shipFrom`.
- Team expanded scope: fix other domain-canonical gaps in same ticket (per Sabyasachi).

## Artifacts

- ISL infra: [isl-infra-config PR 81](https://bitbucket.org/aptosretail/isl-infra-config/pull-requests/81/overview) (Scratchpad Shippo adapter, us-east-1)
- Jira Development: 1 merged Bitbucket PR (stale cache)

## Open questions

- Additional canonical mismatches from Natalya’s EasyPost vs Shippo sample comparison (pending as of 2026-09-15).
