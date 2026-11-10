# How to test

Follow these steps in order. Keep `chat-sessions/` updated as you go (`START-HERE.md`, section 6).
Every piece of testing gets its own folder under `runs/`, with a plan first and a plain-language summary last.

```
runs/2026-11-07-<topic>/
├── plan.md              written FIRST: goal, background, what we will check, tasks
├── tasks/
│   ├── 01-<task>/       one folder per task
│   │   ├── notes.md     what we did, what we saw, result
│   │   ├── screenshots/ as many as needed, numbered in order
│   │   └── network/     the calls each step made (names only)
│   └── 02-<task>/ ...
└── summary.md           written LAST, for someone who has never seen the product
```

## Hard rules for reports and file names (never skip)

1. **Every report is a new file, never an overwrite.** `report` writes `report-<TICKET>-<YYYYMMDD-HHMMSS>-<session>.html`
   and the matching `.pdf` in the run folder. The same naming (`results-<TICKET>-<date-time>-<session>.md/.json`) is used for
   each task's results. A fixed name like `report.html` lets an open tab or the browser cache show an older build.
2. **Always open the file the `report` command prints** (`report --open` does this). Do not reopen a tab you already had.
   After building, say the file name, its date-time, and the session id to the user, so they can see it is the new one.
3. **A report shows one session** (the latest by default). Several scenarios that belong together are played with
   `play --same-session`. `report --list` shows every session; `report --session all` shows everything.
4. **The ticket id is in every name.** Any ticket counts (ABC-123, XYZ-45), not only one project. `test-run.py new --ticket <ID>`
   puts it in the run folder name, and reports, results files and the report's title and footer carry it. When you write a
   summary, note or scenario file for a ticket, put the ticket id in its file name too (for example
   `ABC-123-login-page-summary.md`).
5. **The PDF is a 3-page stakeholder summary** (verdict, KPI tiles, what we checked / test cases and page performance / evidence and run
   details). A longer step-by-step PDF is written next to it, named `... Detail.pdf`. The numbers in the summary are computed from the
   recorded events. The wording comes from `runs/<run>/stakeholder.json`, which the tester writes after the run (format: top of
   `browser/stakeholder_pdf.py`; use `[[calls]]`, `[[ready_min]]` and the other placeholders instead of typing numbers). Without it a plain
   factual summary is generated. After `report`, read the "Check before presenting" lines it prints (headline versus step counts,
   duplicate case IDs, cases not in the plan, anything not Verified) and pass them on to the user. Render the PDF pages and look at them
   before handing it over.
4a. If the runner panel's **Report** button was opened before the tool was changed, it still runs the old code (it lives in a
   background process). After changing the browser tool, run `run.py stop` and `run.py start` so it picks up the change.

## 1. Understand

- Read `qa-tester/learnings.md` first. It lists what earlier runs taught.
- Ticket given: read it with the official Jira/Atlassian connector if you have one, else `connectors/jira`. Read its attachments (reproduction steps, specs).
- Code given: read only what the ticket or area points to. Search `product-knowledge/` first (`python product-knowledge/search.py "<words>"`).
- Testing a product you have tested before: search product knowledge for it (`python product-knowledge/search.py "<product> sign in"`).
  A system page's "Where it lives and how to sign in" section (see `product-knowledge/templates/system.md`) may already
  give the address and sign-in page, so you only need to ask the user for the account. It never holds a password.
- Write down: what changed, what could break, who uses it, and where "expected" comes from.

## 2. Write the plan first (before opening the website)

No `.env` file is needed: every test can target a different website with a different account, so the site and
login live in that run's own `plan.md`, which is never pushed to git.

1. Create the run: `python qa-tester/test-run.py new "<topic>" --ticket <ID> --environment dev`. Add `--site <address>`
   (take it from product knowledge if step 1 found it, otherwise ask the user) and, once you have them,
   `--login <sign-in page>` `--user <name>` `--password "..."`; this fills in the run's Login section for you.
   This makes the folder and `plan.md`, and makes it the **active run**, so the browser knows which site to open
   without being told again.
2. Fill in the rest of `plan.md`: the goal, the background in plain words, what the ticket says, the table of checks
   (what, how it should work, where "expected" comes from), the tasks, what is not planned, open questions.
   If the Login section still has placeholders, fill them in now: the site's address, its sign-in page, and the
   test account. If the user pastes a login into the chat, write it straight into this file and nowhere else.
   A test that needs no sign-in: write "none" for Username and Password instead.
3. Tell the user where the plan is and give a two-line summary. Carry on with read-only work. Stop and ask before anything that saves, sends, deletes, or downloads.

## 3. Prepare

- Check the Login section of `plan.md` has no placeholders left (`<...>`), and that the site is one you are allowed
  to test. Working on a different run already? `python qa-tester/test-run.py use <run>` switches the active one.
- A site you come back to often can instead live in `environments.md` or `environments.local.md`, so it stays
  allowed without a run.
- Note the version of the system under test (for example the page footer).

## 4. Run, one task at a time

Start the browser once: `python connectors/browser/run.py start` (Chrome on the right, the runner panel on the left), then `login`.
The browser's full manual is `connectors/browser/GUIDE.md`.

For each task in the plan:
1. `python qa-tester/test-run.py task <run> "<task name>"` makes the task folder. It prints the `--run` and `--task` values to use.
2. Explore first, if the page is new to you: `snapshot` (the page as text), `elements` (every button, link and field with
   visible, hidden, disabled), `state "<target>"` (one element in detail).
3. Then test, in one of two ways. Both put screenshots, network records and results into the task's folder:
   - **A scenario (preferred when there are several checks).** Write the task's cases as a JSON file from
     `templates/scenario.json` (save it in `scenarios/`), then
     `python connectors/browser/run.py play scenarios/<file>.json --run <run> --task <task>`.
     The user watches each step in the runner panel; `results.md` lands in the task folder.
   - **Single steps.** `goto`, `click`, `fill`, `select`, `scroll`, `expect <check> "<target>"`, each with `--run <run> --task <task>`.
4. Check states, not just looks: visible or hidden, enabled or disabled, checked, in view, covered, clickable (`expect`).
5. Scroll: long pages are captured whole by default; use `scroll` and `expect in-view` when position matters.
6. Watch the network: each step prints its calls, the panel's Network tab shows them, scenarios can `expect request` and
   `no-failed-requests`. `watch` records what happens while the user clicks by hand. `cookies` shows what the site stores.
7. Look at every screenshot you cite. Compare charts with the tables beside them.
8. Write `notes.md` for the task at once: what you did, what you saw, the evidence files, and one result word.
9. A case that goes wrong twice is a finding. Do not retry endlessly (and never a sign-in: accounts lock). Do not change test data to make it pass.

## 5. Write the summary last

Copy the shape of `templates/test-summary.md` into `summary.md`. It is for someone seeing the product for the first time, so:
- Explain every product term the first time it appears, and say how the feature should work, before you report results.
- One table of cases with a result word and an evidence file for each. Use only: Verified, Issue found, Could not verify, Not tested. No ticks, crosses, or pass/fail.
- For each issue: where, what happens, what should happen, steps to see it, how serious (your estimate), evidence.
- A list of what you could not verify, and what is needed to do it.
- A conclusion with next steps.
- Then run `python qa-tester/test-run.py check <run>` and fix every error. It checks the plan, the task notes, the sections, the result words, and that every evidence file exists.
- Post to the ticket only if the user asks (needs `--write`).

## 6. Learn

- Add what you learned to `qa-tester/learnings.md` (keep it general: no customer names, no passwords).
- Stable passing cases: save them as a scenario in `qa-tester/scenarios/` (copy `templates/scenario.json`), so they replay with `play` any time, with no AI needed to work out the steps again.
- New lasting facts about the product: `skills/save-to-knowledge.md`. If you learned the product's address, its
  sign-in page, or something about how signing in behaves, and it is not already on the product's system page, add it
  to "Where it lives and how to sign in" there — never the username, password, or token — so the next test does not
  have to rediscover it.
- Gaps (cases you could not run): list them in the summary, and add to the product's `gaps.md`.
