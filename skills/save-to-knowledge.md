# Skill: Save to knowledge

Use when the user says "save what we learned", or after saving a session that found lasting facts.
Goal: move facts that stay true from `chat-sessions/` into `product-knowledge/`, so they are not buried in old chats.

## What is a lasting fact

Save:
- How a feature behaves, a business rule, a limit, an error and its meaning.
- A scenario that was confirmed (by code, a test, a ticket, or the user).
- A known issue and its cause.
- A term and its meaning.

Do not save:
- Task progress, plans, or to-dos. Those belong in the session file.
- Guesses that nobody confirmed. If useful, save them with `Status: draft`.
- Secrets or personal data.

## Steps

1. Read the session file (or the current chat).
2. List the lasting facts. For each one, note its evidence (file path, ticket, test, or "user confirmed").
3. Show the list to the user and ask which to save. Skip this step if the user said "save all".
4. For each fact, find where it belongs. Read `product-knowledge/README.md` for the layout.
   - If a matching file exists, edit it. Do not create a duplicate.
   - If not, create a new file from `product-knowledge/templates/`.
5. If a new fact replaces an old one, do not delete the old line. Mark it `(until YYYY-MM-DD)` and add the new line below it.
6. At the end of the session file, add: `Saved to knowledge: <list of files>` and the date.
7. Tell the user which files you changed.
