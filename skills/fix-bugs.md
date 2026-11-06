# Skill: Fix bugs

Use when something fails: a bug, an error, a failed test, a failed pipeline, an incident.
Rule: find the root cause before you change anything.

## Steps

1. **Get the facts.** Collect the exact error message, the time, the environment, and the steps that cause it. If you need logs or data, use a connector (see `connectors/README.md`).
2. **Reproduce it.** Find the smallest set of steps that shows the failure. If you cannot reproduce it, say so and list what you tried.
3. **Read the error fully.** Read the whole stack trace. Find the first line in the project's own code.
4. **Trace backward.** Start where the wrong value appears. Follow it back to where it was created. The cause is usually earlier than the symptom.
5. **Check what changed.** Look at recent commits, deploys, configuration, and data around the time the failure started.
6. **Form one hypothesis.** Write it as: "X fails because Y, which happens when Z."
7. **Test the hypothesis** with the smallest check: a log line, a query, a one-line script. Do not fix yet.
8. **If the check disproves it,** go back to step 4. After 3 wrong hypotheses, stop and tell the user what you know and what you ruled out.
9. **Fix the cause.** Find every caller of the code you change. Fix the shared code once.
10. **Prove the fix.** Run the reproduction again. Add one small check that would catch the bug if it came back.

## Report

Tell the user, in this order:

- **Cause:** one or two sentences.
- **Evidence:** the log line, query result, or test that proves it.
- **Fix:** what you changed.
- **Check:** how you verified it.
- **Risk:** other places that might have the same problem.

## Do not

- Do not change code just to see if the error goes away.
- Do not wrap an error in try/except to hide it.
- Do not claim a fix without running the reproduction again.

If the root cause is a lasting fact about the product (a rule, a known issue), add it to `product-knowledge/`.
