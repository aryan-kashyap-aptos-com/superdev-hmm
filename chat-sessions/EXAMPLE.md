# Worked example — fix a flaky checkout test

This file is a reference only. It is never read by `continue-session.md` and never listed in `INDEX.md`
(`save-session.py` skips `EXAMPLE.md` by name). Copy its shape, don't edit it in place.

It shows a session that IS tied to a ticket. A session with no ticket looks identical, just with
`Ticket: (none)` and no `tickets/<id>/` folder.

---

Date: 2026-11-15
Project / product: qa-tester
Ticket: EXAMPLE-000

## Session 1

### Goal
Checkout scenario fails about 1 in 5 runs; find out why and stop the flake.

### Where we are
- Reproduced locally: the "place order" button is clicked before the cart total finishes recalculating.
- Root cause confirmed: a missing wait after the discount code is applied.

### Decisions
- Wait on the total's text content, not a fixed sleep — because a fixed sleep would just move the flake to a different delay. See `tickets/EXAMPLE-000/` for the before/after timing evidence.

### Tried and failed
- A 2-second sleep before clicking "place order" — failed because the recalculation sometimes takes longer than that on a cold cache.

### Files and systems touched
- `qa-tester/scenarios/checkout.md` — added the explicit wait step
- `tickets/EXAMPLE-000/` — timing evidence and the scenario spec this came from

### Evidence
- 20 local runs after the fix, 0 failures → `tickets/EXAMPLE-000/test-results/`

### Open questions
- (none)

### Next steps
1. Run the full checkout suite 3 more times in CI to confirm before closing the ticket.

### Watch out
- The same recalculation delay likely affects the "apply gift card" scenario too — not fixed yet.
