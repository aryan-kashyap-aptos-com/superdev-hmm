## 2026-09-20 — Public mcp-connector-suite structure plan

**Status when closed:** done

- Copied five connectors + `docs/infra` into `mcp-connector-suite-main`; excluded secrets and live harness exports.
- Added root README, `index.html`, `connectors/README.md`, `scripts/setup.ps1`, `examples/cursor-mcp.json`, `.gitignore`; sanitized EC2/RDS/DB env examples.
- Updated AGENTS.md paths, infra doc links, Sumo Cursor rule globs; verified Python `py_compile` on all connector modules.
- Target: `C:\Users\akashyap\Downloads\mcp-connector-suite-main\mcp-connector-suite-main\`
