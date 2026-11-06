# Skill: Save session

Use when the first real task of a chat starts, after every finished step or decision, and when the user says "save session" (or "handoff").
Goal: a short file, always current, that lets a new chat with any AI continue the work without the old chat.

## Create the file (once per piece of work)

1. Pick the file name: `chat-sessions/YYYY-MM-DD-short-topic.md` (today's date, 2-4 words, lowercase, dashes).
   - If `chat-sessions/LATEST.md` already names a file for this same work, add a new `## Session N` section to that file instead of making a new file.
2. Copy the structure from `chat-sessions/TEMPLATE.md`. Fill what you know now.
3. Update `chat-sessions/LATEST.md` so its `File:` line names the session file.

## Update the file (as you go)

After each finished step, decision, or failed attempt, edit the file. Do not tell the user each time; it is routine.
- Rewrite "Where we are" and "Next steps" so they are true now. Do not let them grow.
- Add one line to "Decisions", "Tried and failed", or "Files and systems touched" when something new happened.

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
