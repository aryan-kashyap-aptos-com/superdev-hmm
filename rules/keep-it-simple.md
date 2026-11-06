# Rule: Keep it simple

Simple means efficient, not careless. The best code is code you do not need to write.

## First, understand

Read the task. Trace the real flow end to end. A small change in the wrong place is a second bug.

## Then, climb this ladder. Stop at the first step that works.

1. Does this need to exist at all?
2. Does the codebase already have it? Reuse it.
3. Does the standard library do it?
4. Does the platform or framework do it?
5. Does an installed dependency do it?
6. Can it be one line?
7. Only then: write the minimum code that works.

## Defaults

- No new abstractions unless asked.
- No new dependency if you can avoid it.
- Prefer deleting code to adding code. Prefer boring code to clever code.
- Touch the fewest files possible.
- If a request looks bigger than the need, ask: "Do you need X, or does Y already cover it?"
- If you choose a simple approach with a known limit, write a short comment that names the limit.

## Bugs

A report names a symptom. Fix the cause.

1. Find every caller of the code you change.
2. Fix the shared code once, not each caller.

## Never cut corners on

- Understanding the problem.
- Input checks where outside data enters.
- Error handling that prevents data loss.
- Security.
- Anything the user asked for explicitly.

## Verify

- For non-trivial logic, leave one small runnable check that fails if the logic breaks.
- For a one-line change, no test is needed.
- Never say "done" without showing how you checked it.
