> Example only. This is a sanitized sample of a real run. Names, addresses, versions and findings are illustrative.
> Screenshots and logs are left out of the public example, so each evidence file below holds a one-line note.

# Test plan: TICKET-123 chart library upgrade

Status: done
Date: 2026-01-15
Source: TICKET-123 (security finding from the yearly penetration test)
Environment: example-site
Login setting: QA_EXAMPLE_USER and QA_EXAMPLE_PASSWORD

Note: this plan was written after a first exploratory pass, so it describes what was done. From now on the plan is written before the website is opened.

## Goal
Confirm that the outdated chart library named in the ticket is gone from the Shop Admin report pages, that the reports still work, and note anything else that looks wrong on the way.

## Background in plain words
Shop Admin is the back-office website of the order management system (OMS). Staff sign in to manage users, content, orders and customers. Its Analytics area has report pages that show charts and tables, for example sales per day or shipping delays. The charts are drawn by a charting library, which is a ready-made piece of code the site loads in the browser.

## What the ticket or request says
A penetration test (a planned security attack by testers, to find weaknesses) found that the report pages load an old copy of a charting engine called OldChart, version 2.1.6, bundled inside a file named chartlib-legacy.js. That version has known security problems (listed by number in the ticket). The ticket lists 11 report pages and asks to upgrade to a supported version. The ticket is marked closed with fix version 1.0.0.

## What we will check

| ID | What we will check | How it should work | Where this comes from | Task |
|----|--------------------|--------------------|-----------------------|------|
| C1 | A valid user can sign in | The user lands on the site after signing in | Basic expectation | 01-log-in |
| C2 | A wrong password is refused | A clear error shows and the user stays on the sign-in page | Basic expectation | 01-log-in |
| C3 | The 11 pages in the ticket open | Each page opens without an error | Ticket list of pages | 02-open-the-11-report |
| C4 | The charts show on pages that have data | Each report shows its chart and table | Basic expectation after an upgrade | 02-open-the-11-report |
| C5 | Chart numbers agree with the numbers beside them | Totals in the chart match the table | Basic expectation | 02-open-the-11-report |
| C6 | The old library is not on the pages | No page loads OldChart 2.1.6 | Ticket remediation | 03-check-the-old-library |
| C7 | The old file is no longer served | chartlib-legacy.js is gone | Ticket remediation | 03-check-the-old-library |
| C8 | Pages load without browser errors | The browser's error log is empty | Good practice | 02-open-the-11-report |
| C9 | No file the pages ask for is missing | Every file loads | Good practice | 02-open-the-11-report |
| C10 | Login cookies are protected | Login cookies are marked HttpOnly and Secure | Ticket theme: session safety | 03-check-the-old-library |
| C11 | The export buttons work | A file downloads | Basic expectation | none (needs permission) |

## Tasks

| Task | What we do | Screenshots we plan to take |
|------|------------|-----------------------------|
| 01-log-in | Sign in with a real test account, then try a wrong password | The page after sign-in, the error for the wrong password |
| 02-open-the-11-report | Open each of the 11 pages and wait until it finishes loading | One screenshot per page |
| 03-check-the-old-library | Ask the server for the old file, and list the cookies the site stores | None needed (text output) |

## Safety
- Read-only: we only look. Nothing was saved, sent, deleted or downloaded.
- Only the site listed in environments was opened. Passwords are not written anywhere.

## Not planned
- The QA copy of the site named in the ticket (it is not in the list of allowed sites).
- Export buttons: they download files, so they need the user's OK first.

## Open questions
- Is the "ChartLib Trial" label on the charts expected? (ticket owners)
