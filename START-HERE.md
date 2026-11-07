# START HERE

You are an AI assistant working with the user. This folder (`super-dev/`) is your toolkit.
Everything in it is plain text. Read this whole file before you do anything else. It is short on purpose.

All paths below are relative to the `super-dev/` folder.

## 1. Every session, in this order

1. Read the three files in `rules/`. Follow them at all times.
2. Open `chat-sessions/LATEST.md`. If it names a session file, follow `skills/continue-session.md`.
   (If the file is missing, there is no earlier session. `chat-sessions/INDEX.md` lists all saved sessions.)
3. Then do what the user asks.

## 2. What is in this folder

| Folder               | What it holds                                   | When to open it                            |
|----------------------|-------------------------------------------------|--------------------------------------------|
| `rules/`             | Rules you always follow                         | Start of every session                     |
| `skills/`            | Step-by-step methods for specific tasks         | Only when the task matches (section 3)     |
| `connectors/`        | Scripts for Jira, Confluence, AWS, databases... | Only when you need data from such a system |
| `product-knowledge/` | How the products work, and all their scenarios  | Before you ask the user a product question |
| `qa-tester/`         | How to test software; every test run's files    | When the user wants something tested       |
| `chat-sessions/`     | Saved summaries of past chats                   | Session start, and when saving a session   |
| `tests/`             | `selftest.py`: checks this toolkit offline      | After you change any script here           |

Every folder has a `README.md` that says what it holds. Read it before you add a file there.

## 3. Skills

Open only the skill the task needs. Never load all of them.

| When...                                                        | Open                          |
|----------------------------------------------------------------|-------------------------------|
| You write for a person (message, email, doc, PR text)          | `skills/write-for-humans.md`  |
| You write for an AI or a tool (prompt, tool doc, error text)   | `skills/write-for-ai.md`      |
| Something is broken or failing                                 | `skills/fix-bugs.md`          |
| The user wants a product or system explained or documented (it asks how to split a big product first) | `skills/document-product.md` |
| The chat is long, or the user says "save session"              | `skills/save-session.md`      |
| The user says "continue", or `LATEST.md` names a file          | `skills/continue-session.md`  |
| The user says "save what we learned"                           | `skills/save-to-knowledge.md` |
| The user wants a ticket, feature, API, or website tested       | `qa-tester/method.md`         |
| Explain how a binary/app/website works, no source available   | `skills/reverse-engineer.md`  |
| Answer a data question where definitions must be traceable    | `skills/query-with-ontology.md` |

## 4. Connectors

To get data from Jira, Confluence, Harness, Sumo Logic, MS Teams, AWS, or a database, or to test a website (`browser`):

1. Read `connectors/README.md`. It says which connector to use.
2. Read only the `GUIDE.md` of that connector.
3. Run its script. Start with its `test` command.

Connectors are read-only by default. Never use `--write` without the user's clear permission.

## 5. Product knowledge

- Before you ask the user about a product, search: `python product-knowledge/search.py "<words>"`.
  This already reads the private `product-knowledge-local/` folder too (real sites/systems) -
  nothing extra to run. Add `--sessions` for saved chats, or `--related <path>` for linked pages.
- When you learn a lasting fact about a product, add it there (see `product-knowledge/README.md`).

## 6. Keep the session saved as you go

Do not wait for the user to say "save session". Keep the session file current, so the chat can end at any time:

- After the first real task starts, run `python chat-sessions/save-session.py start "<topic>" --goal "<goal>"`.
- After each finished step, decision, or failed attempt, run `python chat-sessions/save-session.py note ...`. One or two lines is enough.
  Details and examples: `skills/save-session.md`.
- Keep it short. Rewrite "Where we are" and "Next steps"; do not keep adding history there.

## 7. Save tokens

- Read an index or a list before you open files. Open only what you need.
- Never paste big outputs into the chat. Summarise them, or save them to a file and give the path.
- If you would read more than 5 files to answer a question, write a small script that finds the answer instead.
- Do not re-read a file you read earlier in this session unless it changed.
- When the chat gets long, tell the user the session is saved and suggest starting a new chat.

## 8. If you cannot read files

Ask the user to paste what you need: first `rules/`, then one skill.
For connectors, give the user the exact command to run and ask them to paste the output.

## 9. Make every chat load this toolkit (user, once)

Nothing forces an AI to read this file. In the start-up file of each AI tool you use (the one it reads on every chat), add one line:

> At the start of every chat, read `<full path to super-dev>/START-HERE.md` and follow it.

Do this once per tool, and every chat will load the rules and save its session.

## 10. Changing this toolkit

- New skill: add `skills/<name>.md`, then add one row to section 3.
- New connector: follow "Add a connector" in `connectors/README.md`.
- Where any other file goes: the table "Where does a new file go?" in `README.md`.
- After a change, run `python tests/selftest.py`. Keep this file under 100 lines.
