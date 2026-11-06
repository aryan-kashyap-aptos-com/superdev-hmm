# super-dev

A plain-text toolkit that any AI assistant can pick up. Drop the folder into a project, point the AI at one file, and it knows how to work: which rules to follow, which method to use for a task, how to reach your systems, where product knowledge lives, and how to continue a long chat in a new one.

There are no plugins, servers, or tool-specific settings. If the AI can read files, it works. If it cannot, you paste the files in.

## Use it

1. Copy `super-dev/` into your project (or keep it anywhere and give the AI its path).
2. Start a chat and say:

   > Read super-dev/START-HERE.md

3. Optional: if your AI tool always reads a fixed instructions file, put that one line in it.

## What is inside

```
super-dev/
├── START-HERE.md                  the AI reads this first
├── rules/                         always followed
│   ├── keep-it-simple.md
│   ├── only-do-what-was-asked.md
│   └── safety-and-secrets.md
├── skills/                        opened only when the task needs one
│   ├── write-for-humans.md
│   ├── write-for-ai.md
│   ├── fix-bugs.md
│   ├── document-product.md
│   ├── save-session.md
│   ├── continue-session.md
│   └── save-to-knowledge.md
├── connectors/                    scripts for outside systems, read-only by default
│   ├── jira/  confluence/  harness/  sumologic/  msteams/
│   ├── ec2-ssm/  db-ssh/  aws-rds/
│   ├── common.py                  code shared by all connectors
│   └── selftest.py                checks every connector without network or credentials
├── product-knowledge/             how each product works + all its scenarios
│   ├── search.py                  ranked search over the knowledge files
│   └── templates/
└── chat-sessions/                 kept up to date during each chat, so a new chat can continue
    ├── LATEST.md
    └── TEMPLATE.md
```

## Connectors

| Connector | What it does |
|-----------|--------------|
| `jira` | Read, search, comment, create issues |
| `confluence` | Search, read, create, update, comment on pages |
| `harness` | Pipelines, failed runs and stages, start a run |
| `sumologic` | Log search |
| `msteams` | Read teams, channels, messages, chats; post messages |
| `ec2-ssm` | List EC2 servers, run commands through SSM |
| `db-ssh` | PostgreSQL, MySQL/MariaDB, SQL Server, directly or through SSH (OpenSSH or PuTTY keys) |
| `aws-rds` | Aurora PostgreSQL or MySQL through the RDS Data API |

Everything that changes data needs `--write`, and the AI must ask you first.

## Set up

Only for the connectors you need:

```
pip install -r connectors/requirements.txt          # only db-ssh, aws-rds and ec2-ssm need packages
cp connectors/<name>/.env.example connectors/<name>/.env
# fill in .env (each GUIDE.md lists every setting), then:
python connectors/<name>/run.py test
```

After any change to the connectors, run `python connectors/selftest.py`.
`.env`, `.token.json`, and `connectors/results/` are ignored by git.

## Daily flow

| You say                          | What happens                                                   |
|----------------------------------|----------------------------------------------------------------|
| "Read super-dev/START-HERE.md"   | The AI loads the rules. If a chat was saved, it offers to continue it. |
| (nothing)                        | The AI keeps `chat-sessions/` up to date as it works.          |
| "save session"                   | The AI brings the session file fully up to date. Start a new chat any time. |
| "continue"                       | The AI picks up from the last saved session.                   |
| "save what we learned"           | Lasting facts go into `product-knowledge/`.                    |
| "document the product <name>"    | The AI builds features, scenarios, and a gaps list.            |
