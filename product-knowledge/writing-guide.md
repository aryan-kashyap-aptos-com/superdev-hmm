# Writing guide: explain it to someone who knows nothing

Every page in `product-knowledge/` is written for a **first-time reader**: a person who has never seen the product, has no one to ask, and wants to understand it after one read.
Use `skills/write-for-humans.md` for tone. This guide adds the rules for explaining a product.

## The rules

1. **Start with what and why.** The first lines of every page say what the thing is and why it exists, in plain words. No history, no internals yet.
2. **Say who it is for and where it fits.** One sentence: who uses it, and which other parts it works with.
3. **Explain every term the first time it appears.** Add a short meaning in brackets or a sentence. Then add it to `glossary.md`. Never assume the reader knows an abbreviation.
4. **Follow one real example.** After the idea, walk through a concrete case with real-looking data: "Maria orders 3 items. Item 2 is out of stock. Here is what happens next." Examples teach faster than rules.
5. **Show the picture.** Put a small diagram in each Level 0, Level 1, and journey page (see below). Words alone are hard to hold in your head.
6. **One idea per section, short sections.** Headings are questions or plain labels: "What does it do?", "What does it talk to?", "What happens when it fails?".
7. **Say what it is not.** One line that stops the most common wrong guess: "This service does not store prices. Prices live in the pricing service."
8. **Order for the reader, not for the code.** Big picture first, then the normal flow, then the exceptions, then the details.
9. **Say where to go next.** End each page with "Read next" links (2-4 links, with a reason for each).
10. **Mark what you are not sure about.** Use `Status: draft` and a "Not confirmed" list. Never write a guess as a fact.
11. **Evidence for facts.** A code path, ticket, wiki page, test, or "user confirmed (date)". The reader can then check it.
12. **Keep pages small.** Over about 200 lines? Split the page.

## Diagrams

Use text diagrams that any viewer can show. Mermaid works in most tools; ASCII always works.

```
Customer ──places order──▶ Order service ──asks──▶ Inventory service
                               │
                               └──sends──▶ Shipping service ──label──▶ Carrier API
```

Name every box with the product's own name. Label every arrow with what travels on it.

## Page shape (all levels)

```
# <Name>
> One sentence: what it is and what it is for.

## In plain words        ← 3-6 sentences, no jargon. If the reader stops here, they still got it.
## Where it fits         ← who uses it, what it works with, a small diagram
## How it works          ← the normal path, step by step, with one example
## What can go wrong     ← the common failures and what happens
## Terms                 ← only the new words on this page
## Evidence              ← where each fact comes from
## Read next             ← 2-4 links, each with a reason
```

## Bad and good

Bad: "The OMS ingests orders via the OrderIntake API, validates against the SKU master, and publishes OrderCreated events to the integration bus for downstream consumers."

Good: "When a customer places an order, the order arrives at **Order Intake** (the part of the product that receives orders). Intake checks that every item exists and is for sale. If everything is fine, it tells the other systems, such as Shipping, that a new order is ready. Example: Maria orders 3 items. Intake confirms all 3 exist, then tells Shipping to prepare her parcel."

What changed: it says what each part is when first used, uses a person and an example, and uses plain verbs ("tells") instead of internal words ("publishes events").

## The newcomer test

Before you call a page done, check each line. If any answer is "no", fix the page.

- [ ] I can say what this is in one sentence, using only words the page explains.
- [ ] Every term, name, and abbreviation is explained where it first appears.
- [ ] There is at least one concrete example with real-looking data.
- [ ] There is a diagram (Level 0, Level 1, journeys).
- [ ] I know what this is not, and what it works with.
- [ ] I know what happens when something fails.
- [ ] Every fact has evidence, or is marked draft.
- [ ] I know which page to read next.
- [ ] A person with no product knowledge could read it in under 5 minutes and explain it back.
