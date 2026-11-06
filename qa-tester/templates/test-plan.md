# Test plan: <topic>

Status: draft
Date: YYYY-MM-DD
Source: <ticket ID or request>
Environment: <name from environments.md>
Login setting: <setting name, never the value>

Write this plan BEFORE opening the website. Fill every part. Delete these two lines when done.

## Goal
<What we want to find out, in two or three plain sentences.>

## Background in plain words
<What this part of the product is and what it is for, so someone seeing it for the first time can follow. Three to six lines.>

## What the ticket or request says
<The issue in three to five lines. Use the ticket's own words where they help.>

## What we will check

| ID | What we will check | How it should work | Where this comes from | Task |
|----|--------------------|--------------------|-----------------------|------|
| C1 | <what to check> | <expected result> | <ticket line, code path, doc page, or "assumption"> | 01-<task name> |

## Tasks

One folder per task under `tasks/`. Create each with `python qa-tester/testrun.py task <run> "<name>"`.

| Task | What we do | Screenshots we plan to take |
|------|------------|-----------------------------|
| 01-<task name> | <steps in one or two lines> | <which pages or moments> |

## Safety
- Read-only: we only look. Anything that saves, sends, deletes, or downloads needs the user's OK first.
- Only sites listed in `environments.md` are opened. Passwords are never written down.

## Not planned
- <What we will not test, and why.>

## Open questions
- <Question> (who can answer)
