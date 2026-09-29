# Notes service — design requirements

This is the bundled example spec. It lives inside `examples/target/` so that
`python3 server.py --root examples/target` discovers it automatically.

### API-1 · 🔴 · ◐ — Public functions are documented
- **What:** every public function in `notes/` carries a docstring.
- **Why:** callers should not have to read the body to use it.
- **Check:** inspect `notes/*.py` — does every public `def` have a docstring?
- **Source:** style guide, 2026-01-10

### API-2 · 🟠 · ✅ — Entry points validate their input
- **What:** every public entry point validates its payload before use.
- **Why:** prevents malformed state.
- **Check:** does each public entry point validate before it mutates state?
- **Source:** design review, 2026-02-20

### SEC-1 · 🔴 · ○ — No hard-coded secrets
- **What:** credentials come from the environment, never from source.
- **Why:** source is shared widely.
- **Check:** grep `notes/` for literal tokens or keys.
- **Source:** security review, 2026-02-02
