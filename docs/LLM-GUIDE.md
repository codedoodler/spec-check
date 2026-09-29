# LLM / agent guide

This file is for an AI agent (or a person driving one) that needs to understand,
run, or extend `spec-check` without reading every source file.

## One-line description

`spec-check` extracts design requirements from a project's docs and checks the
code against them — deterministic checks, an optional LLM judge, and an evidence
verifier — then reports pass/fail/warn + evidence.

## Repository map (read in this order)

1. `docs/OVERVIEW.md` — the problem and the idea.
2. `docs/ARCHITECTURE.md` — pipeline, modules, JSON contracts.
3. `docs/SPEC-FORMAT.md` — how to write requirements.
4. `docs/WRITING-CHECKS.md` — how to add a deterministic check.

Key source files: `server.py` (extract + check runner), `judge.py` (LLM tier),
`sweep.py` (end-to-end audit), `checks/` (deterministic registry).

## Run it

```bash
# browse + audit interactively
python3 server.py --root /path/to/project          # http://localhost:8090

# end-to-end audit (deterministic + judge + verifier), machine-readable
python3 sweep.py --root /path/to/project --json
python3 sweep.py --root /path/to/project --skip-judge     # no LLM, offline

# just the deterministic checks
python3 pre_commit.py --root /path/to/project

# regression vs the last run
python3 regress.py  --root /path/to/project --json
python3 alert.py    --root /path/to/project --webhook <url> --dry-run
```

## Environment

- The judge is optional. It needs `OPENROUTER_API_KEY` or `DEEPSEEK_API_KEY`.
- Without a key, the judge degrades to `warn`; the deterministic layers still run.
- `SPEC_CHECK_MODEL` overrides the model (default `deepseek/deepseek-chat`).
- No pip dependencies — standard library only. Python 3.8+.

## Machine-readable outputs

- `sweep.py --json` → `{reqs, deterministic, judge, diff_bytes, conflicts, superseded}`
- `judge.py --json` → `[{id, label, tier, status, evidence}]`
- `regress.py --json` → `{regressions, improvements, new_checks, total}`
- `pre_commit.py` → exit code 1 on a critical failure (use as a gate).

## If you are asked to add a requirement

1. Append a heading block to a `*requirement*.md` (or `spec.md`) in the project,
   following `docs/SPEC-FORMAT.md`.
2. If it is machine-checkable, add a `checks/check_*.py` returning a result with
   that ID.
3. Otherwise leave it to the judge — it will be judged from its What/Why/Check.

## If you are asked to add a check

Follow `docs/WRITING-CHECKS.md`. Keep it deterministic, put evidence in `detail`,
pick the tier by severity. Copy `checks/check_no_secrets.py` as a template.

## Conventions

- Requirement IDs are the join key across runs/history/alerts — keep them stable.
- Never fabricate a verdict: `warn`/"unverifiable" is a valid, expected answer.
- Evidence must cite a file/line or the specific change.
- Prefer a deterministic check over a prompt whenever the rule is mechanical.

## Honest status

Early project. Extraction and the deterministic check registry are stable; the
judge and verifier are usable but young. See `docs/ROADMAP.md`.
