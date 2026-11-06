# Skills

Step-by-step methods for one kind of task. The AI opens **only the skill the task needs** (the table in `START-HERE.md`, section 3),
so it reads little and stays focused.

| File | Open it when... |
|------|-----------------|
| `write-for-humans.md` | Writing for people: messages, emails, docs, PR descriptions |
| `write-for-ai.md` | Writing for an AI or a program: prompts, tool docs, error messages, session notes |
| `fix-bugs.md` | Something fails: find the root cause before changing anything |
| `document-product.md` | Explaining or documenting a product; plans the split with the user first |
| `save-session.md` | Saving the chat so a new one can continue (uses `chat-sessions/save-session.py`) |
| `continue-session.md` | The user says "continue", or a saved session exists |
| `save-to-knowledge.md` | Moving lasting facts from a chat into `product-knowledge/` |

Testing software is bigger than one skill, so it has its own folder: `qa-tester/` (start with `qa-tester/method.md`).

## Writing a skill

Use this shape, so every skill reads the same way:

1. `# Skill: <name>`
2. One line: **Use when** ... and, if useful, **Not for** ... (with the skill to use instead).
3. `## Steps`: numbered, each one an action the AI can do without asking.
4. `## Checks`: what to confirm before calling it done.

Then add a row to `START-HERE.md` section 3 and to the table above.
