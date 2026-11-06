# Task: Log in

Date: 2026-01-15
Cases covered: C1, C2

## What we did
1. Opened the Shop Admin sign-in page in a visible browser window.
2. Typed a wrong password for a made-up account and pressed Sign in.
3. Typed the real test account and pressed Sign in.
4. Recorded the network calls the sign-in made.

## What we saw
- The wrong password was refused with the message "Login Credentials are Invalid." and the sign-in form stayed on screen (02-wrong-password-refused.txt).
- The real account signed in and landed on the Releases and Maintenance page (01-after-login.txt).
- The sign-in form is shown inside a frame served from a separate web address, not from the Shop Admin address itself.
- Signing in makes four calls to an external sign-in service, then two calls to the site, then a redirect (01-login-calls.txt).

## Evidence
- screenshots/01-after-login.txt: the page the user lands on after signing in.
- screenshots/02-wrong-password-refused.txt: the error shown for a wrong password.
- network/01-login-calls.txt: the calls made while signing in (names only, no values).

## Result
Verified - both the valid sign-in and the refused wrong password behave as expected.
