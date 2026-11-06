# System: <Name>

> <One sentence: what this system is and what it is for.>

Status: draft | verified · Updated: YYYY-MM-DD · Level 1 · Part of: [<product>](../overview.md)

## In plain words
<3-6 sentences, no jargon. If the reader stops here, they still understand what this system does.>

## Where it fits
<Who or what uses it, and which systems it works with. A small diagram.>

```
<diagram>
```

**What it is not:** <The most common wrong guess, and what is true.>

## Where it lives and how to sign in
For testing (`qa-tester/`): the facts a test's plan.md needs to fill in its Login section automatically, so nobody
has to rediscover them each time. **Never put a username, password, or token here** — this page is pushed to git.
If the address itself must stay private, write "see environments.local.md" instead of the real one.

- Address (or environment name): <e.g. https://example.com, or "see environments.local.md">
- Sign-in page: <path, e.g. login.aspx, or "same as the address above">
- How signing in behaves: <anything a tester should expect — a delay, a message after a wrong password, a sign-in
  form served from another domain, multi-factor, and so on>

## What it owns
The data and decisions that belong to this system and nobody else.
- <Thing it owns, for example "the status of every shipment">
- <Decision it makes, for example "which carrier is used">

## How it works
The normal path, in plain steps, with one example.

1. <Step>
2. <Step>

**Example:** <A concrete case with real-looking data, followed through the steps.>

## What it receives and sends
| Direction | With | How (API, queue, file, screen) | What | When |
|-----------|------|--------------------------------|------|------|
| in        |      |                                |      |      |
| out       |      |                                |      |      |

## What can go wrong
| Situation | What happens | What the user or other systems see |
|-----------|--------------|-------------------------------------|
|           |              |                                     |

## Features
| Feature | In one line | Page | Status |
|---------|-------------|------|--------|
|         |             |      |        |

## Terms
| Term | Meaning |
|------|---------|
|      |         |

## Where the code is
- Repository / folder: `<path>`
- Entry points: `<routes, jobs, handlers>`
- Configuration: `<where settings live; never write secrets here>`

## Evidence
- <Statement> — <code path / ticket / wiki page / test / user confirmed (date)>

## Not confirmed yet
- <Open question>

## Read next
- <link> — <why>
