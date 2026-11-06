# Skill: Document a product

Use when the user wants a product, a system, or a module explained, mapped, or documented for people who do not know it yet
(business analysis, QA, onboarding, support, test planning).
Output: pages in `product-knowledge/<product>/` that a first-time reader can understand, plus a coverage map and a gaps list.

A product can be very large. Never start writing pages right away. First plan with the user (Step 0), then work one part at a time.

## Step 0: Plan with the user (always)

### 0.1 Look before you ask
1. Read `product-knowledge/README.md` and `product-knowledge/writing-guide.md`.
2. If `product-knowledge/<product>/MAP.md` exists, read it, tell the user what is done and what is next, and go to Step 2. Do not start over.
3. Otherwise, take a quick look at the sources, only to learn the shape: top-level folders, services, entry points, API routes, wiki page tree, ticket projects.
   Write a small script when the list is long. Do not read details yet.

### 0.2 Ask the user (one message, short questions, your recommendation first)
Ask all of these in a single message. Offer options and mark your recommendation. If the user already answered something, skip it.

1. **Reader:** Who will read this, and what must they be able to do after reading? (new developer, QA, BA, support, a mix)
2. **How to split it.** Propose a split based on what you saw:
   - **By system or service** (for example: shipping service, public APIs, integration services, UI). Best when the teams or codebases are separate.
   - **By business journey** (for example: place an order, ship it, return it). Best for understanding how pieces work together.
   - **Both** (recommended for large products): one page per system, plus journey pages that cross systems.
   - **By layer or by customer type**, if that fits the product better.
   List the actual areas you found, so the user can add, remove, merge, or rename them.
3. **Depth for each area** (the user can say "all deep" or pick per area):

   | Level | Name | What the reader gets | Typical size |
   |-------|------|----------------------|--------------|
   | 0 | Overview | What the product is, the big picture, how to read the rest | 1 page for the whole product |
   | 1 | System | What one system does, what it owns, what it talks to | 1-2 pages per system |
   | 2 | Feature | How one feature works, its rules, its flow | 1 page per feature |
   | 3 | Scenario | Every case: happy, edge, error, permission, state, integration | 1 file per scenario |

   Recommend: Level 0 for the product, Level 1 for every system, journeys for the 3-5 main flows, Levels 2-3 only for the areas the user names first.
4. **Order:** Which area first? (Recommend the one the reader needs first, or the one that changes most.)
5. **Sources and access:** Which code folders, wiki spaces, ticket projects, test suites, and environments may you read? Which connector should you use (`connectors/README.md`)?
6. **Language and terms:** Does the product have names the reader must learn (internal names, abbreviations)? Who can confirm what they mean?

### 0.3 Save the plan
Write `product-knowledge/<product>/MAP.md` from `templates/map.md`: reader, chosen split, one row per area with its target level, and status `todo`.
Show the user the table and ask for a quick OK. Update the session file (`skills/save-session.md`).

## Step 1: Level 0, the overview
Write `overview.md` from `templates/overview.md`. It must work as a stand-alone first read:
what the product is in plain words, who uses it, a picture of how the systems fit together, the main journeys in one line each, and a reading path ("read these pages in this order").
Write the glossary entries for every term you use (`glossary.md`).

## Step 2: One area at a time
Take the next `todo` area from `MAP.md` and write pages up to its target level. Mark it `in-progress`, then `done` in `MAP.md`.

- **Level 1 system page:** `systems/<system>.md` from `templates/system.md`. Purpose, what it owns, how it works in plain steps, what it receives and sends, what depends on it, key terms, where the code is.
- **Journey page:** `journeys/<journey>.md` from `templates/journey.md`. One real example followed from start to finish across all systems, step by step.
- **Level 2 feature page:** `features/<feature>.md` from `templates/feature.md`.
- **Level 3 scenarios:** `scenarios/<feature>-<short-name>.md` from `templates/scenario.md`. For each feature, look for these categories (not every one applies):

  | Category    | Question to ask |
  |-------------|-----------------|
  | Happy path  | What happens when everything is correct? |
  | Alternate   | What other valid ways lead to the result? |
  | Edge        | What happens at limits: zero, maximum, empty, duplicate, time boundaries? |
  | Error       | What happens with bad input, missing data, or a failing dependency? |
  | Permission  | What can each role do or not do? |
  | State       | What happens in each status of the main object? |
  | Integration | What happens when another system is slow, down, or returns something unexpected? |

- **Connections:** record every link between systems in `integrations.md` (from `templates/integrations.md`): who talks to whom, how, what data, what happens on failure.
- **Evidence:** every statement of behavior needs evidence (code path, ticket, wiki page, test, or "user confirmed"). Evidence found: `Status: verified`. No evidence: `Status: draft`. Never present a draft as fact.
- Search before you create a file: `python product-knowledge/search.py "<words>" --product <product>`.

## Step 3: Check, then show the user
After each area:
1. Run `python product-knowledge/check-pages.py <product>`. Fix every error.
2. Apply the newcomer test from `product-knowledge/writing-guide.md`: could someone who has never seen the product understand this page without asking you anything?
3. Update `gaps.md` (from `templates/gaps.md`): scenarios with no evidence, scenarios with no test, code or rules that no page covers.
4. Tell the user, in at most 6 lines: what you wrote, how many pages are verified vs draft, what you could not confirm, and which area is next.
5. Update the session file. If the chat is long, suggest continuing in a new chat. The next chat resumes from `MAP.md`.

## Step 4: Share (optional)
The user can publish pages to Confluence with `connectors/confluence` (`create` or `update` with `--file`). Ask first.

## Rules
- Plan first. Do not write pages before the user has confirmed the split and the depth.
- Write for a reader who knows nothing. Follow `product-knowledge/writing-guide.md`.
- Use the product's own terms, and explain each one the first time it appears.
- Never invent behavior to fill a gap. A gap is a useful finding.
- If the plan turns out wrong (areas overlap, an area is too big), stop, tell the user, and update `MAP.md` before you continue.
