# Roadmap & status

Honest assessment. See `README.html` for the visual status table.

## Works today

| Area | State |
|------|-------|
| Requirement extraction (spec docs, `AGENTS.md`, `.cursorrules`, `[REQ]` tags) | working |
| Deterministic check registry (`checks/`) | working |
| LLM judge (diff + full-source modes) | working |
| Evidence verifier (contradiction detection) | working |
| Browsable UI (`server.py`) | working |
| Pre-commit hook | working |
| Regression detector (`regress.py`) | working |
| Alerts (Linear / webhook) | code complete, needs a live key/webhook |

## Known limits

- Topic auto-classification is keyword-based and rough.
- The judge batches requirements; very large requirement sets may need scoping
  (`--ids`, `--tier`, `sweep --source`).
- No incremental cache — each audit re-reads the source.
- Provenance is read from the doc text; there is no git-blame integration yet.

## Roadmap

- **git-blame provenance** — attribute a requirement to the commit/review that set it.
- **Auto-rescan on file change** — the UI currently scans once at startup.
- **Deeper model routing** — cheap model for easy requirements, strong model for
  semantic ones.
- **More shipped checks** — a small generic library (licence headers, file-size
  guards, docstring coverage, dependency pinning).
- **Native agent integration** — expose the audit as an MCP tool so an agent can
  call it mid-task.

## Non-goals

- Running your tests or building your code.
- Replacing type checkers or linters — it checks *your* design intent, not language rules.
- A hosted service — this is a local, dependency-free tool.
