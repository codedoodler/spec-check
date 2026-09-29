# Contributing

Thanks for considering it. `spec-check` is deliberately small and deliberately open —
the goal is for people to take the idea further, so there is plenty of room in every
direction. This file tells you how to get involved.

## The one rule

**Never commit project-specific knowledge.** No real colleague/customer names, no
internal codenames, no private paths, no real constants or credentials. A project's own
checks live in that project — this repo ships only the generic framework and toy
examples. Read [PROVENANCE.md](PROVENANCE.md).

A pre-push **leak guard** enforces this locally. After cloning, run once:

```bash
./scripts/install-hooks.sh
```

It refuses a push if the tree carries internal markers or secret-shaped strings. If you
extend it, add your own forbidden terms to `MARKERS` in `scripts/leak_guard.py`.

## Ways to contribute

You do not need deep familiarity with the code. Pick the smallest thing that interests
you:

**1. Write a check.** The easiest on-ramp. A check is a tiny function; see
[docs/WRITING-CHECKS.md](docs/WRITING-CHECKS.md). Ideas: no stray `TODO`s in shipped
code, every public module has a docstring, no direct network calls outside a client
layer, dependencies pinned, no logging of sensitive fields.

**2. Improve the judge.** Better prompts, fewer hallucinations, support for more
models/providers, cost controls, caching.

**3. Support another spec format.** Today: Markdown specs, `AGENTS.md`,
`.cursorrules`, `[REQ]` notes. Add Confluence exports, Jira, ADRs, `docs/` conventions.

**4. Build a verifier for another stack.** The evidence verifier currently browses a
codebase. A language-aware or AST-based one would be stronger.

**5. Integrations.** GitHub Action, GitLab CI, IDE plugin, editor gutter showing each
requirement's last verdict, a Slack/Linear alert already sketched in `alert.py`.

**6. A benchmark.** A corpus of "design decision + code that violates it" pairs to
measure how well judges actually perform. This would be genuinely valuable.

**7. Make it embeddable.** A clean library API so other tools can consume requirements
and verdicts without shelling out.

Full menu, with difficulty tags: [docs/IDEAS.md](docs/IDEAS.md).

## Development

No dependencies — Python 3.8+ standard library only.

```bash
git clone https://github.com/codedoodler/spec-check
cd spec-check

# run the tests (pytest in CI; the suite is stdlib-friendly)
python3 -m pytest tests/            # if you have pytest
python3 tests/test_spec_check.py    # or run the checks directly

# try it against the bundled example
python3 sweep.py  --root examples/target
python3 server.py --root examples/target
```

Keep changes small and focused. If you add a check, add a test for it. If you touch the
judge or the report format, update the docs in `docs/`.

## Pull requests

1. Fork, branch, make the change.
2. Make sure the guard passes: `python3 scripts/leak_guard.py`.
3. Keep the diff tight; explain the *why* in the description.
4. If it changes behaviour, say what you verified and how.

There is no formal code of conduct beyond: be direct, be kind, keep it honest. If in
doubt, open an issue and ask — the whole point is that others move this forward.
