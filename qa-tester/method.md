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

## 1. Understand

- Read `qa-tester/learnings.md` first. It lists what earlier runs taught.
- Ticket given: read it with the official Jira/Atlassian connector if you have one, else `connectors/jira`. Read its attachments (reproduction steps, specs).
- Code given: read only what the ticket or area points to. Search `product-knowledge/` first (`python product-knowledge/search.py "<words>"`).
- Write down: what changed, what could break, who uses it, and where "expected" comes from.

## 2. Write the plan first (before opening the website)

1. Create the run: `python qa-tester/testrun.py new "<topic>" --ticket <ID> --env <site name>`. This makes the folder and `plan.md`.
2. Fill `plan.md` completely: the goal, the background in plain words, what the ticket says, the table of checks (what, how it should work, where "expected" comes from), the tasks, what is not planned, open questions.
3. Tell the user where the plan is and give a two-line summary. Carry on with read-only work. Stop and ask before anything that saves, sends, deletes, or downloads.

## 3. Prepare

- Check the site is in `environments.md` or `environments.local.md`. If not, stop and ask.
- Check the login setting exists (the script says which one is missing). Do not open the `.env`.
- Note the version of the system under test (for example the page footer).

## 4. Run, one task at a time

For each task in the plan:
1. `python qa-tester/testrun.py task <run> "<task name>"` makes the task folder. It prints the `--run` and `--task` values to use.
2. Drive the browser with those values, so screenshots and network records land in that task's folder:
   `python connectors/browser/run.py goto <url> --run <run> --task <task>`
3. Read pages as text (`snapshot`), not as pixels. Wait until a page has really finished (`goto` and `click` do this). Take a screenshot at each decision point, then move on. Several screenshots per task is normal.
4. Watch the network: `goto`, `click` and `login` print the calls each step caused. `watch` records what happens while the user clicks by hand. `cookies` shows what the site stores (values hidden).
5. Look at every screenshot you cite. Compare charts with the tables beside them.
6. Write `notes.md` for the task at once: what you did, what you saw, the evidence files, and one result word.
7. A case that goes wrong twice is a finding. Do not retry endlessly. Do not change test data to make it pass.

## 5. Write the summary last

Copy the shape of `templates/test-summary.md` into `summary.md`. It is for someone seeing the product for the first time, so:
- Explain every product term the first time it appears, and say how the feature should work, before you report results.
- One table of cases with a result word and an evidence file for each. Use only: Verified, Issue found, Could not verify, Not tested. No ticks, crosses, or pass/fail.
- For each issue: where, what happens, what should happen, steps to see it, how serious (your estimate), evidence.
- A list of what you could not verify, and what is needed to do it.
- A conclusion with next steps.
- Then run `python qa-tester/testrun.py check <run>` and fix every error. It checks the plan, the task notes, the sections, the result words, and that every evidence file exists.
- Post to the ticket only if the user asks (needs `--write`).

## 6. Learn

- Add what you learned to `qa-tester/learnings.md` (keep it general: no customer names, no passwords).
- Stable passing cases: save as plain test files in `tests/` so they rerun without AI.
- New lasting facts about the product: `skills/save-to-knowledge.md`.
- Gaps (cases you could not run): list them in the summary, and add to the product's `gaps.md`.
