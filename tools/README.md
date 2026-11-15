# Local tools

Two small local web apps, both private (bind to `127.0.0.1` only) and themed
to match the qa-tester reports (dark/light, same palette).

- **`md-reader/`** - add, reorder, and read Markdown files without opening
  VS Code each time; export the current file or the whole stack to Word or PDF.
- **`api-client/`** - a Postman-shaped request runner: import collections and
  environments you've already exported from Postman, send requests with
  `{{variable}}` substitution, and capture a screenshot of the call as
  evidence - the same kind of visual proof qa-tester gets for UI steps, now
  available for API steps too.

Each has its own `README.md` and `requirements.txt`. Neither talks to the
network except the requests you explicitly send from the API client; nothing
you add to either tool is committed to git (see root `.gitignore`).
