# Ideas: ways to take this further

A menu. Pick anything — the smaller it is, the better as a first step. Difficulty:
🟢 a sitting · 🟡 a weekend · 🔴 a project.

## Checks (the easiest way in)

| Idea | Difficulty |
|------|:----------:|
| No `TODO`/`FIXME` in shipped code | 🟢 |
| Every public module has a docstring | 🟢 |
| No direct network calls outside a client layer | 🟡 |
| Dependencies are pinned to exact versions | 🟢 |
| No secrets, tokens, or keys in source *(ships as `check_no_secrets.py`)* | 🟢 |
| No debug statements in production paths *(ships as `check_no_debug_statements.py`)* | 🟢 |
| No file over N lines / no function over N statements | 🟢 |
| Every route/endpoint appears in the docs | 🟡 |
| No cyclic imports between packages | 🟡 |
| Migrations are reversible | 🔴 |
| Every public function has a type annotation | 🟡 |

## The judge

- Prompt improvements that reduce hallucinations
- Provider support beyond the current ones (base-URL config)
- Verdict caching so repeat audits are nearly free
- Cost/token budgeting per run
- Confidence calibration: does "warn" actually mean what it says?

## Spec sources

Today: Markdown specs, `AGENTS.md`, `.cursorrules`, `[REQ]` notes.
Add: ADRs, Confluence/Jira exports, `docs/` conventions, OpenAPI/JSON-Schema
descriptions, issue trackers.

## Verifiers

- AST-aware verifier (Python first) instead of file browsing
- Language-agnostic "grep the symbol, then confirm with the parser"
- A verifier that reads the *diff* and asks "does this change any requirement?"

## Integrations

- **GitHub Action** — annotate PRs with per-requirement verdicts
- **GitLab CI** job
- **IDE plugin** — gutter icon per requirement with its last verdict
- **Alerts** — Linear/issue-tracker and generic webhook (sketched in `alert.py`)
- **Agent loop** — a tool an AI agent calls before saying "done"

## Research-y (the good stuff)

- **A benchmark.** Real "design decision + violating code" pairs to measure judge
  accuracy. Nobody has this; it would make the whole idea credible.
- **A portable spec format.** One convention editors, agents, and CI can all read and
  write. If this project becomes anything, it is probably this.
- **Drift prediction.** Requirements most at risk, ranked, before they break.
- **Multi-model voting** to cut LLM false positives to near zero.

## Make it a standard

The long game: `spec-check` as the thing you add to any repo so your design decisions
come with a check attached — the way tests came with a runner. That needs people
adopting the *format*, not just running the tool. If that is a problem you want to work
on, you are the right person.

---

Have an idea not listed? Open an issue. Not sure where to start? Pick any 🟢 above and
open a PR — small contributions are genuinely welcome here.