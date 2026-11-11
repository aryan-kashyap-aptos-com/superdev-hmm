# Simfa, Lambda deploy, and SNOWPA patterns

**Status:** verified  
**Evidence:** DCOMS-29975, DCOMS-29981 ticket folders and CHAT-LOGs, transcript-index `simfa-lambda`

## POD QA Lambda deploy (DCOMS-29975)

- Master deploy **v26** health checks documented in ticket CHAT-LOG
- **Manual rollback** path when deploy misbehaves - see `podqa_lambda_deploy_rollback.md`
- Digital delivery / **SNOWPA** XML fixtures under ticket folder (`podqa_SNWPA_*.xml`)

## Digital delivery / carrier alignment

- `express_shipping_carrier` id **8** aligned to Cole Haan prod pattern for podqa tests
- Orders **590135** vs **604060** used as good vs broken comparators
- DB reset scripts for retest (`podqa_reset_*_digital_delivery_retest.sql`)

## Reconciliation replay (DCOMS-29981)

- Feature branch for hash snapshot replay without MV
- Full pod QA order replay (**584692**) validated deploy + happy path
- Review concerns: multi-version safety, publish guards, MV coverage

## Simfa item discount split (DCOMS-29921)

- poddev SNWPA duplicate order cleanup + clean XML
- CloudWatch pulls when console access blocked - use connector + saved queries

## Cole Haan prod validation

- Lambda + DB checks for pending MV rows, `sim_fulfillment_orders` presence
- Keep prod investigation **read-only** unless change ticket approved
