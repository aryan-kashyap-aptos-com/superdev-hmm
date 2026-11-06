# Skill: Save session

Use when the first real task of a chat starts, after every finished step or decision, and when the user says "save session" (or "handoff").
Goal: a short file, always current, that lets a new chat with any AI continue the work without the old chat.

## Use the save command

`chat-sessions/save.py` creates and edits the file for you. Run it from the toolkit folder.

```
python chat-sessions/save.py start "Fix refund bug" --goal "Partial refunds double count tax" --product shop
python chat-sessions/save.py note --section "Where we are" --replace --text "Cause found" --text "Fix in progress"
python chat-sessions/save.py note --section "Decisions" --text "Round per line, because the spec says so"
python chat-sessions/save.py note --section "Next steps" --replace --text "Run the tests" --text "Open the PR"
```

- `start` makes `chat-sessions/YYYY-MM-DD-topic.md`, points `LATEST.md` at it, and rebuilds `INDEX.md` (one line per session).
  If `LATEST.md` already names a file for this same work, do not run `start` again; use `note`.
- `note` edits the newest session block. `--replace` swaps the section; without it the line is added.
  Sections: Goal, Where we are, Decisions, Tried and failed, Files and systems touched, Evidence, Open questions, Next steps, Watch out.
- If you cannot run commands, copy `chat-sessions/TEMPLATE.md` by hand and set `File:` in `LATEST.md`.

## When to save

- Right after the first real task starts: run `start`.
- After each finished step, decision, or failed attempt: run `note`. It is routine; do not tell the user each time.
- Rewrite "Where we are" and "Next steps" so they are true now. Do not let them grow.

## When the user says "save session"

1. Bring every section up to date. Follow the writing rules below.
2. Tell the user: "Saved to `chat-sessions/<file>`. To continue, start a new chat and say: read super-dev/START-HERE.md."

## Writing rules

- Keep it under one page (about 60 lines). It must be faster to read than the old chat.
- Point to things, do not paste them. Write the file path, function name, ticket ID, or command, not its contents.
- Use absolute dates ("2026-11-01"), never "yesterday" or "last week".
- Only write what happened in the chat. Never invent facts. If something is unclear, put it under "Open questions".
- When a decision changed, write both: "Was X, now Y, because Z."
- Write "Next steps" as exact actions a new AI can do without asking: which file, which command, which check.
- Never write secrets, passwords, tokens, or connection strings.
- Use the rules in `skills/write-for-ai.md`. The reader is another AI.

## What matters most

If space is short, keep these sections and cut the others:
1. Goal
2. Next steps
3. Decisions (with the reason)
4. Tried and failed

## After saving

If the session found lasting facts about a product, ask the user: "Do you want me to save the lasting facts to knowledge?" If yes, follow `skills/save-to-knowledge.md`.
