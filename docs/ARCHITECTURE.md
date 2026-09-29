# Architecture

## Pipeline

```
            ┌─────────────┐
  spec docs │  EXTRACT    │  requirements + provenance (what / why / check / source)
  ─────────► │  server.py  │
            └──────┬──────┘
                   │  list of requirements
        ┌──────────┼───────────────────────────┐
        ▼          ▼                           ▼
 ┌────────────┐ ┌──────────────┐      ┌────────────────┐
 │ 1 DETERM.  │ │ 2 LLM JUDGE  │      │ 3 EVIDENCE     │
 │ checks/*.py│ │ judge.py     │      │  VERIFIER      │
 │ exact,fast │ │ semantic     │      │ sweep.py       │
 └─────┬──────┘ └──────┬───────┘      └───────┬────────┘
       │               │                      │
       └───────────────┴──────────┬───────────┘
                                  ▼
                          ┌───────────────┐
                          │   REPORT      │  terminal · JSON · HTML UI
                          │  + HOOK/ALERT │  pre_commit.py · regress.py · alert.py
                          └───────────────┘
```

## Modules

| File | Role |
|------|------|
| `server.py` | Requirement extraction (the parser + discovery) and the local browse/audit UI on `:8090`. `scan_requirements()`, `run_audit_checks()`. |
| `judge.py` | The LLM-judge tier. Batches requirements and asks a model for a verdict + evidence. `--full` judges the whole current source; default judges a diff. |
| `sweep.py` | The end-to-end audit: extract → deterministic → judge → verify → report. Adds evidence verification, stale/conflict detection, source traceability. |
| `checks/` | The deterministic check registry. One file per check; `run(root) -> [results]`. |
| `pre_commit.py` | Blocks a commit when a tier A/B requirement fails. |
| `regress.py` | Compares the current audit to the last saved one; flags pass→fail transitions. |
| `alert.py` | Turns regressions into Linear tickets or a Slack/webhook summary. |
| `install-hook.sh` | Installs the pre-commit hook into a target project. |
| `static/index.html` | The browse UI (served by `server.py`). |

## The requirement model

Every requirement carries the same shape, so every layer can reason about it:

```
id  tier  topic  importance  status_flag
    what   — the claim, tightened so it is unambiguous
    why    — the intent it protects
    check  — the concrete thing to look at to judge "are we conforming?"
    source — provenance (who / when / which review)
```

`tier` drives severity: A/B failures block commits and trigger alerts; C/D notify
only. `topic` powers filtering and scoping. `status_flag` (addressed / partial /
open / superseded / deferred) records design state independently of whether the
code currently conforms.

## Data flow (JSON contracts)

- `scan_requirements(root) -> [ {id, tier, topic, importance, status_flag, label, what, why, check, source} ]`
- `run_audit_checks(root) -> [ {id, label, tier, status, detail} ]`
- `judge_all(reqs, diff, full=) -> [ {id, label, tier, status, evidence} ]`
- `sweep(root) -> { reqs, deterministic, judge, diff_bytes, conflicts, superseded }`

Everything is plain dicts / JSON so the layers stay decoupled and any of them can
be replaced.

## Extension points

1. **Add a check** — drop a file in `checks/`. See [`WRITING-CHECKS.md`](WRITING-CHECKS.md).
2. **Add requirements** — write them in your spec doc; see [`SPEC-FORMAT.md`](SPEC-FORMAT.md).
3. **Swap the model** — `SPEC_CHECK_MODEL` env var; any OpenAI-compatible endpoint.
4. **Change the source root** — `sweep.py --source <path>` scopes the audit.

## Design principles

- **Deterministic first.** Anything machine-checkable should not cost a token.
- **Evidence or silence.** A verdict must cite a file/line or the specific change.
- **Never guess.** When a requirement can't be confirmed, the answer is `warn` /
  "unverifiable", not a confident fabrication.
- **No hidden coupling.** Requirements, checks, and the judge are independent;
  each can be run alone.
