# Rules

Rules the AI follows **all the time**, in every chat. `START-HERE.md` tells the AI to read all three at the start of a session.

| File | In one line |
|------|-------------|
| `keep-it-simple.md` | Understand first, then do the simplest thing that works. The best code is code you do not write. |
| `only-do-what-was-asked.md` | Do what was asked, nothing more. Check the plan with the user before big or risky work. |
| `safety-and-secrets.md` | Never open or print secrets. Read-only by default. Ask before anything that changes data. |

## Adding a rule

Keep rules few: every rule is read in every chat. If it only matters for one kind of task, it is a skill (`skills/`), not a rule.
To add one: create `rules/<name>.md` (a title, then short bullet points), and add a row to the table above.
