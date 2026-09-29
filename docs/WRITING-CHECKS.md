# Writing a check

Deterministic checks are the cheap, exact layer. Each is a small Python file in
`checks/` exposing one function.

## The contract

```python
# checks/check_no_secrets.py
def run(root):
    """Inspect the project at `root`; return a list of result dicts."""
    ...
    return [{
        "id":     "SEC-1",                 # requirement ID this check verifies
        "label":  "No hard-coded secrets", # human title
        "tier":   "B",                     # A/B block commits + alert; C/D notify
        "status": "pass",                  # "pass" | "fail" | "warn"
        "detail": "no secret patterns found",  # the evidence
    }]
```

- `root` is a `pathlib.Path` — the project being checked.
- Return one dict per result; a file may return several.
- No network, no LLM, no side effects. Deterministic: same input → same output.
- Put the *evidence* in `detail` — what you looked at and what you found.

## Tiers

| Tier | Meaning | Effect |
|------|---------|--------|
| `A` | must never be violated | blocks the commit, triggers alerts |
| `B` | serious | blocks the commit, triggers alerts |
| `C` | should be true | reported only |
| `D` | nice to have | reported only |

## How checks are loaded

`server.run_audit_checks(root)` imports every `checks/check_*.py` and calls
`run(root)` on each. A broken check is isolated — it reports a `fail` with the
traceback as `detail` rather than crashing the run.

## Two that ship with the tool

- `checks/check_no_secrets.py` — flags credential-shaped literals.
- `checks/check_no_debug_statements.py` — flags `breakpoint()` / `pdb.set_trace()`.

They are also a template: copy one, rename it, change the patterns.

## Good checks vs bad checks

**Good** — exact, cheap, and certain:

```python
def run(root):
    hits = [p for p in root.rglob("*.md") if "TODO" in p.read_text(errors="ignore")]
    return [{"id": "DOC-4", "label": "No TODOs in docs", "tier": "C",
             "status": "fail" if hits else "pass",
             "detail": f"{len(hits)} docs contain TODO"}]
```

**Bad** — anything needing judgment ("is this code clean?"), anything that calls
the network, anything non-deterministic. Those belong to the **LLM judge**
(`judge.py`), which reasons over the requirement's What/Why/Check instead.

## Rule of thumb

If you can write the check as a boolean over the filesystem, do it — it is free
and exact. If you find yourself approximating, stop and let the judge handle it.
