# API Client

A local, Postman-shaped request runner. Import collections and environments
you've already exported from Postman, pick a request from the sidebar, send
it, and read the response - no Postman install, no Postman account, no data
leaving this machine except the request you chose to send.

## What it does (v1)

- Imports `.postman_collection(.json)` and `.postman_environment.json` files as-is.
- Resolves `{{variables}}` from the active environment (and collection-level variables) before sending.
- Supports no-auth, bearer, basic, and API-key auth from the collection.
- Sends the request for real and shows status, timing, headers, and body.
- **Save evidence**: turns the request/response into a screenshot (PNG), the
  same way qa-tester turns a UI step into a screenshot - and can drop that PNG
  straight into an existing qa-tester run's `tasks/<task>/screenshots/`
  folder, so an API step gets the same visual proof a UI step gets.

## What it deliberately doesn't do yet

Postman collections can carry pre-request/test **scripts** (JS, using
`pm.environment.set`, `pm.test`, etc.) - the OMS collection has over a hundred
of these, often used to chain an auth token from one request into the next.
v1 does not execute them: import + variable substitution + send/view first,
script execution as a fast-follow once this core is solid. Until then,
anything a script would have computed (like a fetched token) needs to be
pasted into the environment's variables by hand.

## Data and secrets

Imported collections/environments (which can contain real tokens/passwords)
are stored under `data/` - gitignored, never committed. Evidence screenshots
land in `evidence/` - also gitignored by default; only what you explicitly
save into a qa-tester run leaves this folder.

## Run

```
pip install -r requirements.txt
python -m playwright install chromium   # once, for evidence screenshots
python app.py
```

Then open http://127.0.0.1:5152
