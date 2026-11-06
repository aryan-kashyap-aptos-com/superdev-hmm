# Environments the tester may use

Only the sites listed here, or in `environments.local.md`, may be opened. No passwords or tokens in either file: only the names of the settings that hold them.

- `environments.md` (this file) is pushed to the repository. Keep it to examples. Never put real addresses here.
- `environments.local.md` is private and gitignored. Put the real sites there, in the same table format.
- Add a row when the user names a new environment. Never add a production site unless the user says to.

| Name | Address | Kind | Login setting (in the .env, not here) | Notes |
|------|---------|------|----------------------------------------|-------|
| example-site | (add an address that starts with https://) | dev / qa / uat | `QA_EXAMPLE_USER`, `QA_EXAMPLE_PASSWORD` | Example row. Not a real site |
