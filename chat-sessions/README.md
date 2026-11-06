# Chat sessions

Memory between chats. While the AI works, it keeps a short note of the chat up to date: the goal, where things stand,
decisions and why, what failed, and the exact next steps. When the chat ends (or gets too long), a new chat with any AI
reads the note and carries on.

## Files

| File | What it is | Pushed to git? |
|------|------------|----------------|
| `TEMPLATE.md` | The shape of a session note | Yes |
| `save-session.py` | The command that writes and updates the notes (below) | Yes |
| `LATEST.md` | Names the session file to continue from | No (private) |
| `INDEX.md` | One line per saved session: date, topic, goal, next step | No (private) |
| `YYYY-MM-DD-topic.md` | One note per piece of work | No (private: they can hold client details) |

## Why `save-session.py` exists

Saving must be quick enough to do after every step, by any AI. Editing a markdown file by hand is slow and easy to get wrong.
The script makes it one command, keeps the format right, numbers the next steps, updates `LATEST.md`, and rebuilds `INDEX.md`.

```
python chat-sessions/save-session.py start "Fix refund bug" --goal "Partial refunds double count tax"
python chat-sessions/save-session.py note --section "Decisions" --text "Round per line, because the spec says so"
python chat-sessions/save-session.py note --section "Next steps" --replace --text "Run the tests" --text "Open the PR"
python chat-sessions/save-session.py index
```

- `start`: creates today's note (or adds "Session 2" to it) and points `LATEST.md` at it.
- `note`: adds a line to a section, or replaces the section with `--replace`.
  Sections: Goal, Where we are, Decisions, Tried and failed, Files and systems touched, Evidence, Open questions, Next steps, Watch out.
- `index`: rebuilds `INDEX.md`.

The method (when to save, what to write) is in `skills/save-session.md`. Continuing is in `skills/continue-session.md`.
Never write passwords, tokens, or connection strings in a note.
