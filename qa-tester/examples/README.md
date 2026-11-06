# Examples

`chart-library-upgrade/` is a finished test run, to copy the shape from. It came from a real run, with every real name, address, ticket, version and cookie name replaced by an example value. Screenshots and logs are left out: each evidence file holds one line saying so.

Open in this order:
1. `plan.md`: written before testing. The goal, the background in plain words, and the table of checks.
2. `tasks/`: one folder per task, each with `notes.md` (what we did, what we saw, the result).
3. `summary.md`: written last, for someone who has never seen the product.

Check it the way a real run is checked: `python qa-tester/testrun.py check qa-tester/examples/chart-library-upgrade`.
Real runs go in `qa-tester/runs/`, which is private and never pushed.
