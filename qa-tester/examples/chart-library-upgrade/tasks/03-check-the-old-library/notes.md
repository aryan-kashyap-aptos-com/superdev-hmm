# Task: Check the old library and cookies

Date: 2026-01-15
Cases covered: C6, C7, C10

## What we did
1. Asked the server directly for the old file chartlib-legacy.js and for the new chartlib.js, and recorded the answer codes.
2. Checked the library version reported by each page (from task 02).
3. Listed the cookies the site stores, with their protection flags, without showing any value.

## What we saw
- The old file chartlib-legacy.js answers "not found" (404). The new chartlib.js answers "found" (200).
- No page reports a OldChart version.
- The main sign-in cookies (.AUTHCOOKIE and SessionId) are protected: HttpOnly and Secure.
- Three cookies named like session or login cookies are not marked Secure: AdminCookie, session_id and customertoken. AdminCookie and session_id can also be read by scripts on the page, and session_id lasts about 29 days.
- The browser stores no tokens in its local storage.

## Evidence
- old-library-check.txt: the answer codes for the two files.
- cookies.txt: the cookie table (names, flags, lifetime, size; no values) and the notes from the check.

## Result
Issue found - the old library is gone (verified), but some cookies are less protected than the main sign-in cookies.
