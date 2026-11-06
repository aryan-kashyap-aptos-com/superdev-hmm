# Learnings

What past test runs taught. Read this before you test (`method.md`, step 1). Add a line when something new bites you.
Keep it general: no customer names, accounts, or passwords here.

## Pages and waiting
- "Loaded" is not "ready". Report and dashboard pages keep filling in after the load event. The browser connector's `settle` waits for: no request in flight, no spinner, and the page text and chart count stop changing. Use it, and do not take a screenshot before it finishes.
- If a page is still changing at the wait limit, report "still loading", not "passed".
- Older server-rendered sites (ASP.NET WebForms) do not make background data calls. Their data is in the page itself, so "0 XHR calls" is normal there.

## Logins
- A login form can live inside a frame served from another host. Read and fill every frame, not only the main page.
- After pressing Sign in, the site may show "Processing request" for several seconds. Wait for the form to come back (refused) or to disappear (accepted). A fixed 1-2 second wait gives false "failed" results.
- If the browser is already logged in, the login page redirects. Say "already logged in" and carry on. Do not fail.
- Page text can contain what you typed, including the password. Always redact secrets before printing page text.

## What to check on every page
- Console errors and failed requests (status 400 or more). A page can look fine and still request a missing file.
- Which library versions are loaded (for security tickets, the version string is the evidence).
- A chart's numbers against the table or data beside it. Pictures alone prove nothing.
- Cookies: session and auth cookies should be HttpOnly and Secure, and should not live for weeks. The `cookies` command lists them without printing values.

## Evidence and honesty
- Look at every screenshot you cite. A script saying "not blank" is not the same as seeing the chart.
- A screenshot shows only the visible part of the page. If the content is long, use `screenshot --full`, or say the rest was not seen.
- A page with no data for the date range cannot prove its chart works. Mark it "Could not verify" and say what data is needed.
- Cross-check numbers across pages: the same day's totals should agree between reports. Agreement is good evidence; a mismatch is a finding.
- Odd values (negative durations, the same word in three spellings, a stray row of symbols) are worth listing as "needs an owner's answer", not as confirmed bugs.
- A small browser window can switch a page to a narrow layout and give misleading screenshots. Use the connector's large window, and quit and restart the browser after changing it.

## Typing and signing in
- A form can re-draw while you type and drop characters (a username ended up cut off and the sign-in was refused). Confirm each field
  holds the full value before pressing Sign in; the browser connector now does this and refuses to submit otherwise.
- A site's base address may answer 403 instead of showing the sign-in page. Name the sign-in page in the environments row (`login: <path>`).
- After one refused sign-in, stop and look (`elements`, `state "label=..."`) before trying again. Accounts lock.

## Checking states
- "Is it there" is not enough. Check visible or hidden (and why), enabled or disabled, in view, covered, clickable.
- Image buttons (`input type=image`, such as an "Export To Excel" icon) are buttons; find them by their alt text.
- Many menus keep their links in the page but hidden (for example a Sign Out link until the user menu opens). `hidden` is the right check.
- Screenshots must not contain the tester's own overlays. Use the connector's outline (it fades and is removed before capture).

## Folders and sharing
- One run folder per piece of testing, one task folder per task. Plan first, summary last, then run `test-run.py check`.
- The repository is public. Never push run folders, site maps, real addresses, screenshots of internal systems, or session notes. Real sites go in `environments.local.md`.

## Working with the user
- The user wants to watch. Use the visible browser, slow typing, and the red dot. Take a screenshot at each decision point, then move on.
- Do not write passwords to files. Pass them for one command through the environment, or use the connector's `.env`.
