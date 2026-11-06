# Skill: Continue session

Use at the start of a chat when `chat-sessions/LATEST.md` names a file, or when the user says "resume" or "continue".

## Steps

1. Open `chat-sessions/LATEST.md`. Read the `File:` line.
   - If the file is missing or says `(none)`, there is nothing to resume. Tell the user and wait for a task.
2. Open that session file. If it has several `## Session N` sections, read the last one fully and the others only for decisions.
3. Do not open the files it mentions yet. Open them only when a next step needs them.
4. Tell the user, in at most 5 lines:
   - The goal.
   - Where the work stopped.
   - The next step you plan to do.
5. Ask: "Continue with this?" Then wait.
6. If the user agrees, start the next step.

## Checks

- If the session date is more than 7 days old, tell the user. Files or systems may have changed since then.
- If a file the session mentions no longer exists, or looks different from the description, tell the user before you act.
- If the user wants to work on something else, leave `LATEST.md` as it is. The next saved session will update it.
