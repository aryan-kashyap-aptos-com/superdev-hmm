# Skill: Answer a data question through an ontology

Use when the user asks a business question over structured/relational data (a metric, a count, a
trend) and getting the definitions right matters more than getting an answer fast — the number has
to be traceable to real columns and a real join, not a guessed query.
Not for: a one-off query against a database you already understand well (just write the SQL) or a
database connector that already has its own GUIDE (check `connectors/README.md` first).

Tool: [NVIDIA Auto Ontology](https://github.com/NVIDIA/auto-ontology), cloned for reference at
`../SPIDERS/auto-ontology` next to this project. It is a deployed stack (Postgres + pgvector, a
FastAPI backend, an MCP server), not a script you run — it needs the user's explicit setup and an
NVIDIA API key, and it is not wired into this harness yet.

## What it gives you

Auto-Ontology sits between an agent and a database. It turns raw schemas into an ontology of
business **terms** (e.g. "Customer", mapped to the columns that hold it), certified **SQL
attributes** (reviewed expressions like a margin calc, reused so every answer computes it the same
way), and **relationships** (how tables actually join). An agent asks it a question; it resolves the
terms, writes the SQL, validates the filter values and the query against the live database, and
returns the answer with the SQL and the steps that produced it — or says the data can't answer it.

## Steps

1. **Check it's set up and certified**, with `check_readiness` (or the UI) — not just running, but
   with an ontology that has been reviewed by a person. An uncertified draft ontology answers
   questions too, but treat its terms as unverified until someone has certified them.
2. **Check answerability before trusting an answer.** Call `check_answerable` for the question first.
   If coverage is low or a key term (e.g. "ad spend") has nothing mapped to it, say that to the user
   instead of accepting a best-effort guess — Auto-Ontology is built to refuse rather than fabricate,
   so don't override that by asking it to answer anyway.
3. **Ask the question** with `ask_question` (MCP) or the chat/REST API. Get back the answer, the SQL,
   and the steps (terms resolved, tables joined, validation done).
4. **Verify before repeating the answer.** Read the returned SQL yourself — does it join what the
   question actually asked about? Spot-check a row if the stakes are high. Report the SQL alongside
   the answer so the user can check it too, the same way `fix-bugs.md` asks for evidence, not just a
   conclusion.
5. **If the ontology is wrong or stale** (a term maps to the wrong column, a join is missing), tell
   the user — fixing it is a certify/edit step in the UI or API, not something to patch around in the
   question.
6. **For predictive questions** ("what will X be"), note these route to KumoRFM only if configured,
   and that it is a hosted service the connected tables get uploaded to — flag that data-sharing
   implication before assuming it's available.

## Checks

- You ran `check_answerable` (or equivalent) before presenting an answer as reliable.
- The answer you report to the user includes the SQL and the resolution steps, not just the number.
- You distinguished a certified term/attribute from an uncertified draft one.
- You did not enable or rely on KumoRFM without flagging that it uploads table data externally.
