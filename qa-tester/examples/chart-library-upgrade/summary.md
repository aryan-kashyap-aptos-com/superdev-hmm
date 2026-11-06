> Example only. This is a sanitized sample of a real run. Names, addresses, versions and findings are illustrative.
> Screenshots and logs are left out of the public example, so each evidence file below holds a one-line note.

# TICKET-123, chart library upgrade: test summary

Date: 2026-01-15
Source: TICKET-123 (security finding from the yearly penetration test)
Environment and version: example-site (the dev copy of Shop Admin), version 1.0.0
Tested by: an AI assistant using the QA tester toolkit. Reviewed by: not yet reviewed.

Written for someone who has never seen this product. Use plain words. Explain every product term the first time it appears.
Result words (use only these): **Verified** = works as it should, with proof. **Issue found** = does not work as it should. **Could not verify** = we tried or needed to, but could not (say why). **Not tested** = out of scope or not reached.

## In plain words
The ticket said the report pages of Shop Admin used an old, unsafe version of the software that draws their charts. We opened all 11 report pages listed in the ticket on the dev site and confirmed that the old software is gone: every page now uses a newer version (ChartLib 4.2.3) and the old file is no longer served. The reports still open quickly and show correct-looking numbers. So the fix described in the ticket is in place on dev. Along the way we found a few smaller problems that are not part of the ticket: a script file that three pages cannot find, a browser warning on every page, odd negative day counts in one chart, and a "Trial" label on the charts. We could not check the chart on two pages because they had no data to show, and we did not test the export buttons.

## The issue
A penetration test (a planned security attack by testers, to find weaknesses) found that Shop Admin's report pages loaded an old charting engine, OldChart 2.1.6, hidden inside a file called chartlib-legacy.js. That version has known security weaknesses, listed by number in the ticket. In the worst case such a weakness lets an attacker run their own code in a staff member's browser while that person is on a report page. The ticket gives it a severity score (CVSS) of 7.9 out of 10, which is high. The ticket asked for an upgrade to a supported version, and it is marked closed with fix version 1.0.0.

## How it should work
Shop Admin is the back-office website of the order management system (OMS), where staff manage users, content, orders and customers. After signing in, the top menu has an Analytics area with report pages. Each report page has a filter bar at the top (dates, customer group, order status) and a search button. Below it, the page shows a chart and usually a table with the same numbers. The chart is drawn in the browser by a charting library, which is a ready-made piece of code the page loads. After the fix, the pages should look and behave as before, the old library should not be loaded anywhere, and the old file should be gone from the server.

```
Browser --> Shop Admin report page --> loads chartlib.js (new, version 4.2.3) --> draws chart
                                     x-- chartlib-legacy.js (old, OldChart 2.1.6) must be gone
```

## What we tested

| ID | What we checked | Result | Evidence |
|----|-----------------|--------|----------|
| C1 | A valid user can sign in | Verified | tasks/01-log-in/screenshots/01-after-login.txt, tasks/01-log-in/network/01-login-calls.txt |
| C2 | A wrong password is refused with a clear message | Verified | tasks/01-log-in/screenshots/02-wrong-password-refused.txt |
| C3 | The 11 pages in the ticket open without an error | Verified | tasks/02-open-the-11-report/crawl-report.md |
| C4 | Charts show on the pages that have data (9 of 11 pages) | Verified | tasks/02-open-the-11-report/screenshots/001-averagesalesreport.txt, tasks/02-open-the-11-report/screenshots/002-hourlytrends.txt, tasks/02-open-the-11-report/screenshots/003-monthlycomparisonreport.txt, tasks/02-open-the-11-report/screenshots/004-productproductivity.txt, tasks/02-open-the-11-report/screenshots/005-shippinglatency.txt, tasks/02-open-the-11-report/screenshots/006-itemstatusreport.txt, tasks/02-open-the-11-report/screenshots/007-productbystate.txt, tasks/02-open-the-11-report/screenshots/008-salesforecast.txt, tasks/02-open-the-11-report/screenshots/00-top-products-full-size.txt |
| C4b | Charts show on the other 2 pages (No Stock, Top Sub-Categories) | Could not verify | tasks/02-open-the-11-report/screenshots/009-nostockreport.txt, tasks/02-open-the-11-report/screenshots/011-categoryviews.txt |
| C5 | Chart numbers agree with the numbers beside them (checked on 3 pages) | Verified | tasks/02-open-the-11-report/screenshots/006-itemstatusreport.txt, tasks/02-open-the-11-report/screenshots/007-productbystate.txt, tasks/02-open-the-11-report/screenshots/002-hourlytrends.txt |
| C6 | No page loads the old OldChart 2.1.6 | Verified | tasks/02-open-the-11-report/crawl-report.md |
| C7 | The old file chartlib-legacy.js is no longer served | Verified | tasks/03-check-the-old-library/old-library-check.txt |
| C8 | Pages load without messages in the browser's error log | Issue found | tasks/02-open-the-11-report/crawl-report.md |
| C9 | Every file a page asks for can be found | Issue found | tasks/02-open-the-11-report/crawl-report.md |
| C10 | Sign-in cookies are protected | Issue found | tasks/03-check-the-old-library/cookies.txt |
| C11 | The export buttons work | Not tested | none |

## What we found

### Three pages ask for a script that does not exist
- Where: Shipping Latency, Item Status Report, and No Stock Report.
- What happens: each page asks for `jquery.scrollTo.min.js.js` (the ending ".js" is doubled) and gets "not found". The Sales by State page asks for the correctly spelled file and works.
- What should happen: every file a page asks for loads.
- Steps to see it: sign in, open Shipping Latency, and look at the browser's network list; the request for the doubled name shows "not found".
- How serious (our estimate): low to medium. We did not check whether anything on those pages depends on that script (it is a scrolling helper).
- Evidence: tasks/02-open-the-11-report/crawl-report.md

### A browser warning on every page
- Where: all 11 report pages.
- What happens: the browser's error log shows "Permissions policy violation: unload is not allowed in this document" two or three times per page. Some script on the pages uses a browser feature that current Chrome blocks.
- What should happen: the log should be empty. The feature may stop working altogether in future browser versions.
- Steps to see it: open any report page and look at the browser's console.
- How serious (our estimate): low. We did not find which script causes it.
- Evidence: tasks/02-open-the-11-report/crawl-report.md

### Some cookies are less protected than the main sign-in cookies
- Where: the whole site.
- What happens: the two main sign-in cookies are protected (HttpOnly and Secure). Three cookies with session-like names are not marked Secure: AdminCookie, session_id and customertoken. AdminCookie and session_id can also be read by scripts on the page, and session_id lasts about 29 days.
- What should happen: any cookie that identifies a user's session should be protected the same way as the main ones. If these three hold nothing sensitive, this is fine.
- Steps to see it: sign in, then list the browser's cookies for the site.
- How serious (our estimate): low to medium until the owners say what these cookies hold.
- Evidence: tasks/03-check-the-old-library/cookies.txt

### Things that look odd and need an owner's answer (not confirmed as bugs)
- Shipping Latency shows negative durations in its legend ("-3143 Day(s)", "-2778 Day(s)", "-25 Day(s)", "-3 Day(s)"). Either the dev data is wrong or the report calculates the delay wrongly. See tasks/02-open-the-11-report/screenshots/005-shippinglatency.txt
- Every chart carries a "ChartLib Trial" label. A trial licence on a release may be unintended. See tasks/02-open-the-11-report/screenshots/00-top-products-full-size.txt
- The Top Products page (the one that shows "Products by Revenue") has the browser title "Example - Order Payments", which belongs to the credit-card page next to it. Probably a copy-and-paste slip.
- Productivity by Credit Card Type lists "visa", "Visa" and "VISA" as three separate card types, so one card brand is split into three bars. See tasks/02-open-the-11-report/screenshots/004-productproductivity.txt
- On the Top Sub-Categories Report, the Traffic table has a stray row holding only a pair of angle brackets. See tasks/02-open-the-11-report/screenshots/011-categoryviews.txt

## What we could not verify
- Charts on the No Stock Report and the Top Sub-Categories Report: the first had no data for the date range (no chart is drawn) and on the second the Traffic chart said "No data to display" while the Revenue chart was below the part of the page we captured. To verify, use a date range that has data, or capture the full page.
- The export buttons on the report pages: they download files, so we need the user's OK first.
- The QA copy of the site named in the ticket (its address is not in the list of allowed sites). The fix was checked on dev only.
- Whether chart numbers agree with the database: we only compared a chart with the table next to it, on 3 pages.

## Conclusion
The fix asked for in TICKET-123 is confirmed on dev: the old charting library is gone from all 11 pages and the old file is no longer served, with the reports still working. Not confirmed: the QA site, the export buttons, and two pages with no data to chart. Next steps: ask the ticket owners about the missing script, the negative day counts, the Trial label and the page title; ask the cookie owners what the three cookies hold; and repeat the check on the QA site once it is added to the allowed list.
