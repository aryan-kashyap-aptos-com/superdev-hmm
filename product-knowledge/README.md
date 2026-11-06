# Knowledge

This folder holds lasting facts about the products: how they work and every scenario that matters.
Business analysts, QA, developers, and AI assistants read it. Write it so all of them understand it.

## Layout

```
product-knowledge/
├── templates/             copy these, do not edit them for a product
└── <product>/              one folder per product, lowercase-with-dashes
    ├── overview.md         purpose, users, modules, main flows, integrations
    ├── glossary.md         product terms and their meaning
    ├── gaps.md             what is missing: no evidence, no test, no scenario
    ├── features/
    │   └── <feature>.md
    └── scenarios/
        └── <feature>-<short-name>.md
```

## Rules

1. **One topic per file.** One feature per feature file, one scenario per scenario file.
2. **File names:** lowercase, dashes, no spaces. Example: `scenarios/order-cancel-partial-refund.md`.
3. **Link with relative paths.** Example: `[Order cancel](../features/order-cancel.md)`.
4. **Every fact needs evidence:** a code path, ticket ID, wiki page, test name, or "user confirmed (YYYY-MM-DD)".
5. **Status** at the top of each feature and scenario file:
   - `draft`: not confirmed yet.
   - `verified`: confirmed by evidence.
   - `outdated`: no longer true. Keep the file and link to what replaced it.
6. **Never delete history.** When a rule changes, mark the old line `(until YYYY-MM-DD)` and add the new line under it.
7. **Search before you add.** Edit an existing file rather than creating a duplicate.
8. **No secrets and no personal data.**

## How to find things fast

- Search: `python product-knowledge/search.py "<words>" [--product <name>] [--sessions]`.
  It ranks files by match (titles count more) and shows a snippet, the path, and the status. Open only the files you need.
- Start with `<product>/overview.md`. It links to every feature.
- `gaps.md` shows what is still unknown.

## How knowledge gets here

- `skills/document-product.md` builds a product map from code, docs, and tickets.
- `skills/save-to-knowledge.md` moves lasting facts from sessions into this folder.
- Any AI that learns a confirmed fact during work can add it, following the rules above.
