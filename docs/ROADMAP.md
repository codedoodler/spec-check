# Roadmap & status

Honest assessment of where the project is against the [vision](VISION.md). Phases are
roughly ordered; none is a prerequisite for using the stage before it.

## Where it is today (P0 — working)

| Area | State |
|------|-------|
| Requirement extraction from spec docs, `AGENTS.md`, `.cursorrules`, `[REQ]` notes | ✅ |
| Deterministic checks (`checks/`, tiny `run(root)` functions) | ✅ |
| LLM judge tier (optional; degrades gracefully without a key) | ✅ |
| Evidence verifier (flags judge verdicts the source contradicts) | ✅ |
| Browsable UI, JSON output | ✅ |
| Pre-commit gate + regression alert | ✅ |
| Bundled example + tests + CI workflow | ✅ |

This is a **single-repo, single-spec** conformance checker. The vision is the loop
around it.

## P1 — The requirements model

- [x] Four tiers (aspirational → principles → component → testable)
- [x] `what` / `why` / `check` / `source` on every requirement
- [x] importance + status legends
- [ ] A machine-readable schema for the model (so other tools can read/write it)
- [ ] Validation: flag any active requirement whose `check` can't be answered yes/no

## P2 — Ingest everything

- [x] Markdown specs · `AGENTS.md` · `.cursorrules` · `[REQ]` notes
- [ ] Meeting recordings / transcripts
- [ ] Issue trackers
- [ ] Email, team chat, discussion boards
- [ ] PRDs, ADRs, spreadsheets, slide decks in-repo
- [ ] Continuous mode: new source → re-extract, merge, **flag what changed**
- [ ] `[REQ]` vs `[INTENT]` tagging (intent = the requirement nobody wrote down)

## P3 — The spec checks itself

- [ ] Conflict detection: contradiction · supersession · duplicate · ambiguity ·
      orphan · staleness
- [ ] Precedence resolution (recent + authority wins; supersede, never delete)
- [ ] Escalation of what the rule can't settle (open questions)
- [ ] Derived priority ranking: importance × tier × dependencies × violation risk
- [ ] A conflict report a human can act on

## P4 — Enforcement on every change

- [x] Pre-commit gate (block on critical failure)
- [x] Regression alert (the "passing Monday, failing Wednesday" case)
- [ ] Run conformance on the **diff** of a pull request / push
- [ ] Block as a required status check (GitHub, or any CI/other resolution)
- [ ] **Running violation tally** — per requirement, over time, trending
- [ ] Alert routing (issue tracker, webhook, chat)

## P5 — History of evolution

- [ ] Record every transition: introduced → amended → superseded → retired
- [ ] Keep source + date + reason for each transition
- [ ] Time-travel view: "what did the design say on date X?"
- [ ] Diff two points in time: what changed, and why

## P6 — Presentation & standard

- [x] Charted HTML overview, JSON output, agent-readable entry point
- [ ] Charted views: hierarchy tree, verdict distribution, drift trend, conflict map
- [ ] A **portable spec format** others can consume
- [ ] A shared library of contributed checks
- [ ] A benchmark for judge accuracy (design decision + violating code pairs)

## Known rough edges

- Topic auto-classification is rough.
- git-blame provenance and auto-rescan on change are not built.
- The judge needs a live API key; without one, the semantic tier degrades to `warn`.
- Alerts (issue tracker / webhook) need a live key.

## Not in scope (deliberately)

- Not a type checker, linter, or test runner — it does not run your code.
- Not a proof system. It is a systematic, honest audit that surfaces drift early.
- Not project-specific: this repo stays generic, always. A project's own checks live in
  that project. See [PROVENANCE.md](../PROVENANCE.md).