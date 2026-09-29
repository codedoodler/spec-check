# Example target: a tiny notes service

A deliberately imperfect project for demonstrating `spec-check`.

- `notes/api.py` — one conforming function, one undocumented function, one
  hard-coded secret.
- `notes/store.py` — clean, documented.
- `docs/requirements.md` — the spec this project is checked against.
- `docs/status.md` — an uncited "LIVE" claim.

Try it from the repo root:

```bash
python3 server.py --root examples/target          # browse requirements + run checks
python3 pre_commit.py --root examples/target      # deterministic checks (blocks tier A/B)
```
