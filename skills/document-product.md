# Skill: Document a product

Use when the user wants to understand a product or module end to end, or wants every scenario listed (for business analysis, QA, onboarding, or test planning).
Output: files in `product-knowledge/<product>/` and a list of gaps.

## Before you start

1. Read `product-knowledge/README.md` for the layout and rules.
2. Ask the user (only what you do not already know):
   - Product name, and which modules are in scope.
   - Where the sources are: code folders, wiki spaces, ticket projects, existing test cases.
3. If `product-knowledge/<product>/` already exists, read its `overview.md` first and extend it. Do not start over.
   Before you create a file, search for an existing one: `python product-knowledge/search.py "<feature words>" --product <product>`.

## Step 1: Overview

Read the sources at a high level: folder structure, entry points (routes, screens, APIs, jobs), main docs.
Do not read every file. To scan a large codebase, write a small script that lists routes, endpoints, or screens.
Write `product-knowledge/<product>/overview.md` from `templates/overview.md`: purpose, users, modules, main flows, integrations.

## Step 2: Features

List the features in each module. For each feature, write `features/<feature>.md` from `templates/feature.md`:
what it does, who uses it, the business rules, and links to its scenarios.

## Step 3: Scenarios

For each feature, find scenarios in these categories. Not every category applies to every feature.

| Category    | Question to ask                                                 |
|-------------|-----------------------------------------------------------------|
| Happy path  | What happens when everything is correct?                        |
| Alternate   | What other valid ways lead to the result?                       |
| Edge        | What happens at limits: zero, maximum, empty, duplicate, time boundaries? |
| Error       | What happens with bad input, missing data, or a failing dependency? |
| Permission  | What can each role do or not do?                                |
| State       | What happens in each status of the main object?                 |
| Integration | What happens when another system is slow, down, or returns something unexpected? |

Write one file per scenario: `scenarios/<feature>-<short-name>.md` from `templates/scenario.md`.

## Step 4: Evidence

Every scenario needs evidence: a code path (file and function), a ticket, a wiki page, a test, or "user confirmed".
- Evidence found: set `Status: verified`.
- No evidence yet: set `Status: draft`. Never present a draft as fact.

## Step 5: Gaps

Write `product-knowledge/<product>/gaps.md` with three lists:
1. Scenarios with no evidence.
2. Scenarios with no test.
3. Code paths or rules that no scenario covers.

## Working in batches

A product can be big. Work one module at a time. After each module:
- Tell the user what you wrote and how many scenarios are verified vs draft.
- Update the session file (`skills/save-session.md`). If the chat is long, suggest continuing in a new chat.
- To share the result, the user can publish a feature file to Confluence: `connectors/confluence` `create` or `update` with `--file`.

## Rules

- Describe behavior from the user's point of view. Add technical detail only under "Evidence" or "Notes".
- Use the product's own terms. Add new terms to `glossary.md`.
- Never invent behavior to fill a gap. A gap is a useful finding.
