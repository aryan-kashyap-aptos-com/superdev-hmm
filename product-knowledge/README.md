# Product knowledge

This folder holds lasting facts about the products: what each one is, how its parts work and connect, and every scenario that matters.
Newcomers, business analysts, QA, developers, and AI assistants read it. Every page is written for a first-time reader (see `writing-guide.md`).

## Large products: plan first

A big product cannot be documented in one pass. `skills/document-product.md` starts by asking the user how to split the product
(by system, by journey, or both) and how deep to go for each part. The answer is saved in `<product>/MAP.md`, so the work can continue part by part, across many chats.

## Layout

```
product-knowledge/
├── writing-guide.md        how to write so a newcomer understands
├── search.py               ranked search over the pages
├── check-pages.py               checks a product's pages (links, sections, evidence, coverage)
├── templates/              copy these, do not edit them for a product
└── <product>/              one folder per product, lowercase-with-dashes
    ├── MAP.md              the plan and the progress: which areas, which depth, what is done
    ├── overview.md         Level 0: what the product is, the big picture, how to read the rest
    ├── glossary.md         every product term and its meaning
    ├── integrations.md     how the parts connect: who talks to whom, how, and what if it fails
    ├── gaps.md             what is missing: no evidence, no test, no page
    ├── systems/            Level 1: one page per system or service
    ├── journeys/           end-to-end flows across systems, followed with one real example
    ├── features/           Level 2: one page per feature
    └── scenarios/          Level 3: one file per scenario
```

## Levels

| Level | Page | What the reader gets |
|-------|------|----------------------|
| 0 | `overview.md` | What the product is, the big picture, where to start |
| 1 | `systems/<name>.md`, `journeys/<name>.md` | What one system does and owns, or how one flow crosses systems |
| 2 | `features/<name>.md` | How one feature works, with its rules |
| 3 | `scenarios/<name>.md` | Every case: happy, edge, error, permission, state, integration |

Each area is documented only as deep as the plan says. A reader can stop at any level and still have understood something complete.

## Rules

1. **One topic per file.**
2. **File names:** lowercase, dashes, no spaces. Example: `scenarios/order-cancel-partial-refund.md`.
3. **Link with relative paths.** Example: `[Order cancel](../features/order-cancel.md)`.
4. **Every fact needs evidence:** a code path, ticket ID, wiki page, test name, or "user confirmed (YYYY-MM-DD)".
5. **Status** at the top of each page: `draft` (not confirmed), `verified` (confirmed by evidence), `outdated` (no longer true; keep the file and link to what replaced it).
6. **Never delete history.** When a rule changes, mark the old line `(until YYYY-MM-DD)` and add the new line under it.
7. **Search before you add.** Edit an existing page rather than creating a duplicate.
8. **No secrets and no personal data.**
9. **Check before you finish:** `python product-knowledge/check-pages.py <product>`.

## How to find things fast

- Search: `python product-knowledge/search.py "<words>" [--product <name>] [--sessions]`.
  It ranks files by match (titles count more) and shows a snippet, the path, and the status. Open only the files you need.
- Related pages: `python product-knowledge/search.py --related <path-or-words>` follows the relative
  links every page already has (Rule 3) one hop out and one hop in — no extra syntax to maintain, the
  existing `[Link](../path.md)` links are the graph.
- Start with `<product>/overview.md`. It says what to read next.
- `<product>/MAP.md` shows what is documented and what is not.
- `<product>/gaps.md` shows what is still unknown.

## Real facts vs. example facts

This folder is public and stays generic/example-only (see `templates/`). When a page would have to
name a real host, a real customer, or an internal system, it goes instead in the sibling
`product-knowledge-local/` folder — same layout, same rules, gitignored, same reason as
`qa-tester/environments.local.md`. `search.py` reads both folders together; you never point it at
one or the other by hand.

## How knowledge gets here

- `skills/document-product.md` plans with the user, then builds the pages part by part.
- `skills/save-to-knowledge.md` moves lasting facts from sessions into these pages.
- Any AI that learns a confirmed fact during work can add it, following the rules above.
