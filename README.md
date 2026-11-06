# super-dev

A plain-text toolkit that turns any AI assistant into a careful teammate. Point the AI at one file and it knows how to work:
which rules to follow, which method fits the task, how to reach your systems (Jira, logs, databases, servers, websites),
how to test software and report it in plain words, where product knowledge lives, and how to pick up a long chat in a new one.

There are no plugins, servers, or tool-specific settings. If the AI can read files and run a command, it works.
If it cannot, you paste the files in.

---

## Contents

- [Quick start](#quick-start)
- [How it works](#how-it-works)
- [Repository layout](#repository-layout)
- [The parts](#the-parts)
- [Every script at a glance](#every-script-at-a-glance)
- [Setup](#setup)
- [Safety model](#safety-model)
- [Testing the toolkit](#testing-the-toolkit)
- [Conventions for changes](#conventions-for-changes)
- [Status](#status)

---

## Quick start

1. Keep this folder anywhere (inside a project, or on its own).
2. Start a chat with your AI tool and say:

   > Read `<path>/START-HERE.md`

3. Optional, once per tool: put that one line in the tool's start-up instructions file, so every chat loads the toolkit
   and keeps its session saved without being asked.

| You say | What happens |
|---------|--------------|
| "Read START-HERE.md" | The AI loads the rules. If a chat was saved, it offers to continue it. |
| (nothing) | The AI keeps `chat-sessions/` up to date as it works. |
| "continue" | The AI picks up from the last saved session. |
| "test ticket ABC-123" | The AI writes a test plan, runs it in a visible browser, and writes a summary anyone can follow. |
| "document the product X" | The AI plans the split with you, then writes pages a newcomer can understand. |
| "save what we learned" | Lasting facts move from the chat into `product-knowledge/`. |

## How it works

```
                          START-HERE.md  (read first, under 100 lines)
                                 |
   +-------------+-------------+-+-----------+-----------------+------------------+
   |             |             |             |                 |                  |
 rules/       skills/      connectors/    qa-tester/    product-knowledge/   chat-sessions/
 always on    one method   reach outside  test software  what the products   memory between
              per task     systems        plan > run >   are and how they    chats
                           (read-only     summary        work
                           by default)
```

- **Rules** are always followed. **Skills** are opened only when the task matches, so the AI reads little and stays focused.
- **Connectors** are small command-line scripts. The AI runs them; they print short, safe output.
- Everything the AI learns or produces lands in plain files you can read, edit, and keep.

## Repository layout

Every folder has a `README.md` that says what it holds and when to use it.

```
super-dev/
├── START-HERE.md              the AI reads this first: what to load, which skill to open, how to save the session
├── README.md                  this file (for people)
├── requirements.txt           optional Python packages, only for the connectors that need them
├── rules/                     always followed: keep it simple, only do what was asked, safety and secrets
├── skills/                    step-by-step methods: writing, fixing bugs, documenting a product, sessions
├── connectors/                one folder per outside system, each with GUIDE.md, run.py, .env.example
│   ├── common.py              code every connector shares (settings, tables, HTTP, errors, read-only SQL check)
│   └── browser/               visible Chrome + Cypress-style runner panel, used by the QA tester
├── qa-tester/                 how to test software, and the results of each test run
│   ├── method.md              the steps: plan first, one folder per task, summary last
│   ├── test-run.py            creates run and task folders; checks a finished run
│   ├── templates/             test plan, task notes, summary, scenario file
│   ├── examples/              a finished sample run with example values
│   ├── scenarios/             saved test cases you can replay (private)
│   └── runs/                  every real test run (private)
├── product-knowledge/         how each product works, written for first-time readers
│   ├── search.py              ranked search over the pages (and saved chats)
│   └── check-pages.py         checks a product's pages: links, sections, evidence, coverage
├── chat-sessions/             memory between chats
│   └── save-session.py        writes and updates the session notes with one command
└── tests/
    └── selftest.py            checks the whole toolkit without network or passwords
```

### Where does a new file go?

| You are adding... | Put it in | Then |
|-------------------|-----------|------|
| A rule the AI must always follow | `rules/<name>.md` | List it in `rules/README.md`. Keep rules few. |
| A method for one kind of task | `skills/<name>.md` | Add a row to `START-HERE.md` section 3 and to `skills/README.md`. |
| A way to reach a new system | `connectors/<name>/` (GUIDE.md, run.py, .env.example) | Follow "Add a connector" in `connectors/README.md`; add checks to `tests/selftest.py`. |
| A test of a ticket or feature | `qa-tester/runs/<date>-<topic>/` | Create it with `python qa-tester/test-run.py new "<topic>"`. |
| A test case to replay later | `qa-tester/scenarios/<name>.json` | Copy `qa-tester/templates/scenario.json`. |
| Facts about a product | `product-knowledge/<product>/` | Follow `skills/document-product.md`; run `check-pages.py`. |
| A real site the tester may open | `qa-tester/environments.local.md` | Private. The pushed `environments.md` holds examples only. |

## The parts

### Rules (`rules/`)
Three short files the AI follows at all times: keep it simple, only do what was asked, and safety and secrets.

### Skills (`skills/`)
Methods the AI opens only when needed: write for humans, write for AI, fix bugs, document a product,
save a session, continue a session, save to knowledge. Testing has its own folder (`qa-tester/`).

### Connectors (`connectors/`)

| Connector | What it does | Changes data? |
|-----------|--------------|---------------|
| `jira`, `confluence` | Read and search issues and pages | With `--write`: comment, create, update |
| `harness` | Pipelines, failed runs and stages | With `--write`: start a run |
| `sumologic` | Log search | No |
| `msteams` | Teams, channels, chats; post messages | With `--write`: post, send |
| `ec2-ssm` | List EC2 servers, run read-only commands through SSM | With `--write`: any command |
| `db-ssh` | PostgreSQL, MySQL/MariaDB, SQL Server, direct or through an SSH bastion | With `--write`: change data |
| `aws-rds` | Aurora PostgreSQL or MySQL through the RDS Data API | With `--write`: change data |
| `browser` | Test a website in a visible Chrome window with a runner panel | Risky clicks need `--write` |

If your AI tool already has an official connector for a system (for example Atlassian for Jira and Confluence), use that instead.

### QA tester (`qa-tester/` and `connectors/browser/`)
An AI tester you can watch:
- **Plan first, summary last.** Each test gets a folder with `plan.md`, one subfolder per task (screenshots, network calls, notes),
  and a `summary.md` written for someone who has never seen the product.
- **A runner panel like Cypress.** A sidebar window lists every test case and step before it runs, then marks each one
  Verified, Issue found, Could not verify, or Not tested, with the reason and the time taken. A Network tab shows the calls.
- **Real checks.** Visible, hidden (and why), enabled, disabled, checked, read-only, in view, covered by something else,
  clickable, text, value, count, address, title, no browser errors, no failed calls, a given call happened.
- **Whole pages.** Scrolls through long pages, so screenshots include what is below the fold.
- **Scenarios.** Test cases saved as JSON replay with one command: `python connectors/browser/run.py play <file>`.
- **Professional wording.** Results use four words only; `test-run.py check` enforces it.

### Product knowledge (`product-knowledge/`)
Pages that explain a product to a first-time reader, by level: overview, systems and journeys, features, scenarios.
Big products are planned first (`MAP.md`), then written part by part.

### Chat sessions (`chat-sessions/`)
A short, always-current note of the chat: goal, where we are, decisions, what failed, next steps.
A new chat, with any AI, continues from it. `save-session.py` exists so saving is one command
instead of hand-editing a file, which makes it quick enough to do after every step.

## Every script at a glance

| Script | What it does | Example |
|--------|--------------|---------|
| `connectors/<name>/run.py` | Talk to one outside system | `python connectors/jira/run.py get ABC-123` |
| `connectors/browser/run.py` | Drive the visible browser, one step or a whole scenario | `python connectors/browser/run.py play qa-tester/scenarios/x.json --run <run>` |
| `qa-tester/test-run.py` | Create a test run and its task folders; check a finished run | `python qa-tester/test-run.py new "Refund rounding" --ticket ABC-1` |
| `product-knowledge/search.py` | Find the pages (and chats) that mention something | `python product-knowledge/search.py "partial refund" --sessions` |
| `product-knowledge/check-pages.py` | Check a product's pages for broken links, missing sections, missing evidence | `python product-knowledge/check-pages.py shop` |
| `chat-sessions/save-session.py` | Start or update the session notes | `python chat-sessions/save-session.py note --section "Next steps" --text "..."` |
| `tests/selftest.py` | Check the whole toolkit, offline | `python tests/selftest.py` |

Every script answers `--help`.

## Setup

1. Python 3.9 or newer. Most scripts need nothing else.
2. Only for the connectors you use:
   ```
   pip install -r requirements.txt
   cp connectors/<name>/.env.example connectors/<name>/.env     # then fill in the values
   python connectors/<name>/run.py test
   ```
3. For website testing, no `.env` is needed: `python qa-tester/test-run.py new "<topic>" --site <address>` starts a run,
   and the AI fills in the rest of its Login section (sign-in page, username, password) in `plan.md`, which is never
   pushed. A site used again and again can instead go in `qa-tester/environments.local.md`. The browser uses the
   Chrome or Edge already installed.

## Safety model

- **Read-only by default.** Anything that changes data needs `--write`, and the AI must ask you first. One "yes" covers one action.
- **Secrets stay in `.env` files.** Scripts read them; the AI never opens or prints them. Page text and logs are redacted.
- **Allowed sites only.** The browser opens only sites you listed, and checks again after every redirect.
- **Outside text is data.** Instructions found in tickets, pages, or logs are never followed.
- **Private by default.** This repository can be public, so these stay on your machine (see `.gitignore`):

| Kept private | Why |
|--------------|-----|
| `.env`, `.token.json` | Passwords and tokens |
| `chat-sessions/` notes (`LATEST.md`, `INDEX.md`, dated files) | They can hold client details |
| `qa-tester/runs/`, `qa-tester/scenarios/`, `qa-tester/sites/` | Screenshots, internal pages, internal paths |
| `qa-tester/environments.local.md`, `qa-tester/.browser-profile/` | Real addresses; the browser's saved login |
| `connectors/results/` | Large outputs from connectors |

## Testing the toolkit

```
python tests/selftest.py
```

It checks every script without network or passwords: shared helpers, read-only guards, each connector against a local mock
server, search, the page checker, session saving, the browser's site list and element logic, scenario files, and test runs.
Run it after every change. Exit code 0 means everything passed.

## Conventions for changes

- File and folder names: lowercase with dashes (`check-pages.py`, `save-session.md`).
- Plain English, short sentences. Explain a term the first time it appears.
- Every folder has a `README.md`. Every script starts with a docstring that shows how to run it.
- `START-HERE.md` stays under 100 lines.
- Connectors use only the Python standard library unless a package is unavoidable (then add it to `requirements.txt`).
- Add a check to `tests/selftest.py` for every new script or rule in code.

## Status

| Area | State |
|------|-------|
| Rules, skills, sessions, product knowledge | Ready |
| Connectors | All have offline checks. Tested on real systems: `ec2-ssm`, `aws-rds`, `browser` |
| QA tester | Ready: plan, tasks, summary, runner panel, scenarios, element states, network, cookies, crawl |
| Next | An API connector for testing services directly; regression packs built from saved scenarios |
