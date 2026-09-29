# Automated design-compliance checking

spec-check runs three ways.

## 1. Interactive (human review)

```bash
python3 server.py --root /path/to/project
# open http://localhost:8090
```

## 2. Pre-commit (blocks bad commits)

```bash
./install-hook.sh /path/to/project
```

Runs `pre_commit.py` on every commit. Blocks when critical (tier A/B)
requirements fail.

## 3. Scheduled regression detection (the smart alert)

The most valuable automation: run `regress.py` + `alert.py` on a schedule,
and it tells you when a requirement that was passing starts failing.

### cron (daily at 9am)

```cron
0 9 * * * cd /path/to/spec-check && python3 regress.py --root /path/to/project --history /path/to/project/.audit-history.json >> /tmp/spec-check.log 2>&1
```

### cron + Linear auto-ticket (daily, silent unless regression)

```cron
0 9 * * * cd /path/to/spec-check && python3 alert.py --root /path/to/project --linear-key $LINEAR_API_KEY --team ENG --history /path/to/project/.audit-history.json >> /tmp/spec-check.log 2>&1
```

`alert.py` stays silent (exit 0) when nothing regressed. It only creates a
Linear ticket when a pass→fail transition is detected.

### cron + Slack webhook (summary post)

```cron
0 9 * * * cd /path/to/spec-check && python3 alert.py --root /path/to/project --webhook https://hooks.slack.com/services/XXX --history /path/to/project/.audit-history.json
```

### CI (GitHub Actions)

```yaml
name: spec-check
on: [pull_request, push]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # the project under audit (this repo)
      - run: python3 "$SPEC_CHECK/pre_commit.py" --root .
        env:
          SPEC_CHECK: ${{ github.workspace }}/.spec-check
      # fetch spec-check itself (or vendor it as a submodule / pip package)
      - uses: actions/checkout@v4
        with:
          repository: codedoodler/spec-check
          path: .spec-check
```

The tool is stdlib-only — no `pip install` step is needed.

## The LLM judge (optional)

The deterministic checks run anywhere. The semantic layer (`judge.py`,
`sweep.py --full`) calls an OpenAI-compatible chat endpoint and needs a key:

```bash
export OPENROUTER_API_KEY=...        # or DEEPSEEK_API_KEY
export SPEC_CHECK_MODEL=deepseek/deepseek-chat   # optional override
python3 sweep.py --root /path/to/project
```

Without a key, the judge degrades to `warn` and the deterministic layers still
run.
