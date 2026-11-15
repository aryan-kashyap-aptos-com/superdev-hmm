# MD Reader

A local, private Markdown viewer. Add one or many `.md` files, reorder them,
read them rendered instead of raw, and export the current file or the whole
stack to Word or PDF.

- Runs only on `127.0.0.1` - nothing is uploaded anywhere, nothing calls out.
- Added files are copied into `library/` (gitignored) so the originals are untouched.
- Reorder by dragging a row in the sidebar.
- "export all, in order" exports every file in the current sidebar order as
  one document; unchecked, it exports only the file you're reading.

## Run

```
pip install -r requirements.txt
python -m playwright install chromium   # once, for PDF export
python app.py
```

Then open http://127.0.0.1:5151
