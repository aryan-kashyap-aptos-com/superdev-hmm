# Task: Open the 11 report pages

Date: 2026-01-15
Cases covered: C3, C4, C5, C8, C9

## What we did
1. Opened each of the 11 report addresses from the ticket on the dev site, one after another.
2. Waited for each page to finish loading (no request still running, nothing changing on screen).
3. Took a screenshot, then noted the browser's error messages, the files that failed to load, and which chart library each page uses.
4. Looked at every screenshot, and compared chart numbers with the numbers beside them.

## What we saw
- All 11 pages opened and finished loading in about 1.6 seconds.
- Every page loads ChartLib 4.2.3. None exposes OldChart.
- Nine pages show a chart with data.
- No Stock Report shows no data for the date range, so there is no chart to look at.
- Top Sub-Categories Report: the Traffic chart says "No data to display" and its table has one stray row with only a pair of angle brackets. The Revenue chart is below the part of the page we captured.
- Numbers agree where we compared them: Items by Status (723 of 1,369 items = 52.81%), Sales by State (11 orders, $346.20 = $176.33 + $169.87), and Hourly Trends show the same 11 orders and $346.20 for the same day. Top Products: the bar 11.07K matches the table's $11,074.04.
- Three pages ask for a script named with a doubled ".js" and get "not found": Shipping Latency, Item Status Report, No Stock Report.
- All 11 pages write an "unload is not allowed" warning in the browser's error log, two or three times each.
- Shipping Latency shows negative durations in its legend: -3143, -2778, -25 and -3 days.
- Productivity by Credit Card Type lists "visa", "Visa" and "VISA" as three separate card types.
- The charts carry a "ChartLib Trial" label.

## Evidence
- crawl-report.md: the table for all 11 pages (load time, library, errors, failed files) and the list of problems.
- screenshots/00-top-products-full-size.txt: Top Products, with the bar and table that agree.
- screenshots/005-shippinglatency.txt: the negative day counts.
- screenshots/006-itemstatusreport.txt and screenshots/007-productbystate.txt: charts that agree with their tables.
- screenshots/009-nostockreport.txt and screenshots/011-categoryviews.txt: the two pages with no chart data.
- network/00-top-products-calls.txt: what loading one report page asks for.

## Result
Issue found - the pages work and the library is upgraded, but a missing script, a browser warning and some odd data need an owner's answer.
