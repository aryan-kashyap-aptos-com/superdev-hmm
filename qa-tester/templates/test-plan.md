# Test plan: <topic>

Status: draft
Date: YYYY-MM-DD
Source: <ticket ID or request>
Environment: <dev / qa / uat / other, in plain words>

Write this plan BEFORE opening the website. Fill every part. Delete these two lines when done.

## Login

This file lives in `qa-tester/runs/`, which is never pushed to git, so the password can go here.
Tested this product before? Search `product-knowledge/` for its system page first (`python product-knowledge/search.py
"<product> sign in"`) — its "Where it lives and how to sign in" section may already give the address and sign-in
page, so only the account is left to fill in. If this test needs no sign-in, write "none" in Username and Password.

| | |
|---|---|
| Site address | <the full address, e.g. https://example.com, or just example.com> |
| Sign-in page | <path to the sign-in page, e.g. login.aspx, or "same as site" if the address above already shows it> |
| Username | <the test account's username, or "none"> |
| Password | <the test account's password, or "none"> |

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

One folder per task under `tasks/`. Create each with `python qa-tester/test-run.py task <run> "<name>"`.

| Task | What we do | Screenshots we plan to take |
|------|------------|-----------------------------|
| 01-<task name> | <steps in one or two lines> | <which pages or moments> |

## Safety
- Read-only: we only look. Anything that saves, sends, deletes, or downloads needs the user's OK first.
- Only the site named above (and any site listed in `environments.md`) may be opened.
- The password above is never printed: the browser connector hides it in every screenshot, log and report.

## Not planned
- <What we will not test, and why.>

## Open questions
- <Question> (who can answer)
