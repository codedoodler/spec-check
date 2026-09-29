# Vision: the living design contract

*What `spec-check` is meant to become. Read this if you're deciding whether the idea
is worth your time — and if you might build part of it.*

## The problem, stated fully

Every project has a design: the decisions people made about how the thing should work,
why it works that way, and what must never happen. Today that design lives in fragments
— a spec here, a meeting transcript there, a ticket comment, an `AGENTS.md`, someone's
memory. It is written once and then **rots**, because nothing checks it.

The cost is silent. The system passes review on Monday; by Wednesday a change has
violated a decision nobody remembers making, and the diff looks ordinary. Type checkers
catch syntax drift, linters catch style drift, tests catch behaviour you thought to
encode. **Nothing reads the design and asks: are we still what we said we were?**

When code can be rewritten by an AI in seconds, this stops being a nuisance. Design
fidelity becomes *the* maintenance problem, and there is almost no tooling for it.

## The bet

**Design intent can be made checkable — and once it is, it can be maintained
automatically, from every source, forever.**

The bet has three parts:

1. **Every design decision can carry a `Check`** — the concrete thing you would look at
   to decide "are we conforming?". A requirement you cannot answer yes/no to is not a
   requirement yet; it is a wish.
2. **Layers of trust.** Deterministic checks where the rule is mechanical, an LLM only
   where judgment is genuinely required, and a verifier that refuses to let the LLM lie
   confidently.
3. **"Unverifiable" is a first-class answer.** A tool for trust must never guess.

`spec-check` today is a small, honest implementation of those three ideas over a single
spec file. The vision is the whole loop: **ingest everything, model the requirements,
resolve the design against itself, check the code against it, act on every change, and
keep the history.**

## The whole system

```
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  1 · INGEST — continuously, from everywhere                             │
   │  meetings · transcripts · tickets · email · chat · docs · PRDs · ADRs   │
   │  each statement → [REQ] (a must) or [INTENT] (a motivation), source-linked
   └───────────────────────────────┬─────────────────────────────────────────┘
                                   ▼
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  2 · MODEL — the living requirements list                               │
   │  tiers A/B/C/D · importance · status · What / Why / Check · source      │
   │  precedence: recent-wins · supersede, never silently delete             │
   └───────────────────────────────┬─────────────────────────────────────────┘
                                   ▼
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  3 · RESOLVE — the spec checks itself                                   │
   │  conflicts (contradiction · supersession · duplicate · ambiguity ·      │
   │  orphan · staleness) · priority ranking · open-question triage          │
   └───────────────────────────────┬─────────────────────────────────────────┘
                                   ▼
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  4 · CONFORM — is the code still the design?                            │
   │  deterministic checks ▸ LLM judge ▸ evidence verifier ▸ verdict         │
   │  pass · warn · fail · unverifiable                                      │
   └───────────────────────────────┬─────────────────────────────────────────┘
                                   ▼
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  5 · ENFORCE — act on every change                                      │
   │  block (critical) · warn · always update the running violation tally    │
   └───────────────────────────────┬─────────────────────────────────────────┘
                                   ▼
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  6 · PRESENT — for humans and machines                                  │
   │  charted HTML · JSON · an agent-readable entry point                    │
   └───────────────────────────────┬─────────────────────────────────────────┘
                                   ▼
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  7 · REMEMBER — the history of evolution                                │
   │  every requirement's lifecycle: introduced → amended → superseded →     │
   │  retired, with source, date, and a time-travel view                     │
   └─────────────────────────────────────────────────────────────────────────┘
```

Each stage is useful on its own. Together they turn a pile of decisions into a
**living contract** that the codebase is continuously held to.

### 1 · Ingest everything, continuously

The design is already written down — scattered across the places work happens:
meeting recordings and transcripts, issue trackers, email threads, team chat,
forum/discussion boards, specs and PRDs, ADRs, spreadsheets, slide decks, and files
committed to the repo itself.

The ingestion stage reads all of it and pulls out two kinds of statement, source-linked:

- **`[REQ]`** — an explicit must / should / need / decided.
- **`[INTENT]`** — a motivation, concern, or complaint that *implies* a requirement
  even though it was never phrased as one. (This is where the valuable, unwritten
  requirements hide.)

It runs continuously: a new document, a new meeting, a new ticket comment → re-extract,
merge, and **flag what changed** — including when a new statement contradicts an old one.

### 2 · Model: the living requirements list

Everything extracted is deduplicated and organised into a hierarchy with four tiers:

| Tier | What it holds | Testable? |
|------|---------------|:---------:|
| **A · Aspirational** | the guiding light — the goal, not a rule | no |
| **B · Principles** | invariants; violating one is a defect | conceptually |
| **C · Component** | what each part of the system must do | yes |
| **D · Testable** | each becomes a test | yes, mechanically |

Every requirement carries:

- an **id** and a **title**
- **importance** — critical / high / medium
- **status** — addressed / partial / open / superseded / deferred
- **What** — the requirement itself
- **Why** — the intent it protects (so future readers know what they'd break)
- **Check** — the concrete thing to look at to judge conformance
- **source** — which meeting, document, or ticket it came from

The **`Check` field is the whole point**: walk the list and any `Check` you cannot
answer yes/no to is a red flag that the requirement is still too vague to enforce.

### 3 · Resolve: the spec checks itself

A growing requirements list will contradict itself — two decisions made weeks apart, a
principle that a newer ruling overrode, a "requirement" that two people read
differently. So the spec must be checked against itself, for at least:

- **Contradiction** — two active requirements that cannot both hold.
- **Supersession** — a newer decision overrides an older one (the older is *flagged*,
  never silently deleted).
- **Duplicate** — the same requirement stated twice in different words.
- **Ambiguity** — a `Check` with two defensible readings.
- **Orphan** — a requirement with no owner, no check, or nothing that implements it.
- **Staleness** — a requirement the system no longer honours and nobody re-affirmed.

Resolution follows an explicit **precedence rule**: the most recent ruling from a named
authority wins, and the loser is marked superseded rather than removed. Anything the
rule cannot settle is escalated as an open question — not guessed at.

The same pass produces a **priority ranking**, so effort goes where it matters:
importance × tier × how much else depends on the requirement × the risk of it being
violated.

### 4 · Conform: is the code still the design?

For each active requirement, walk the `Check` against the real codebase:

1. **Deterministic checks** settle the mechanical rules exactly, offline.
2. **An LLM judge** reads the semantic requirements against the code and returns a
   verdict plus evidence.
3. **An evidence verifier** flags any verdict the source contradicts — the guard
   against confident hallucination.

Each requirement ends with a verdict: **pass · warn · fail · unverifiable**.

### 5 · Enforce: act on every change

This is where it stops being a report and becomes a gate. When code is submitted —
a pull request, a push, a CI run, whatever the resolution happens to be — the checks
run against **the change**, and the system does one of two things:

- **Block** — a failing *critical* requirement stops the change (a required status
  check), or
- **Warn + tally** — a lesser violation is recorded.

Either way, the system keeps a **running tally of violations**: which requirement,
how often, trending how. That tally is the real asset — it turns "the design is
drifting" into a number you can watch, per requirement and over time.

A special case deserves its own signal: **passing on Monday, failing on Wednesday**.
A requirement that *was* conformant and no longer is, is a regression against the
design — and should alert like one.

### 6 · Present: for humans and for machines

- **For people** — a charted HTML view: the hierarchy, the verdict distribution, the
  drift trend, the conflict map, the open questions.
- **For machines** — structured JSON, and a concise entry point an agent can read to
  understand the project and the current design state.

### 7 · Remember: the history of evolution

The design is not a snapshot; it evolves, and the evolution is the audit trail:

- every requirement's lifecycle — *introduced → amended → superseded → retired* —
  with the source and the date of each transition
- **time-travel**: what did the design say on a given date? what changed since?
- the *why* behind every change, traced to the meeting or document that caused it

Without this, the list becomes a mystery: nobody knows why a rule exists or whether it
still applies. With it, the design is a record you can trust and audit.

## The principles (non-negotiable)

Any contribution should protect these:

- **Measured, not typed.** Prefer observing the real system over trusting a declaration.
- **Never guess.** If it can't be confirmed, say *unverifiable* and hand it back.
- **Deterministic first.** Cheapest, most certain method that works; LLM only for
  genuine judgment.
- **Supersede, don't delete.** History is the point; a silent removal destroys the audit.
- **Honest about limits.** A tool for trust must not overstate what it knows.

## What it could become

Less "a tool", more a **missing standard** — the way a lockfile or a Dockerfile is a
standard: a conventional way to state design that anything can read and verify.

- **A shared library of checks** — contributed by everyone, applicable anywhere.
- **A portable spec format** — editors, agents, and CI all consuming the same
  requirements.
- **CI that enforces design** the way CI enforces tests.
- **Agents that check their own work** — before declaring a task done, verify the change
  against the project's own requirements and report honestly.
- **A conflict-aware spec** — a requirements list that tells you when it contradicts
  itself, instead of waiting for someone to notice.

## The invitation

If the premise is right — that checking design intent is about to matter as much as
checking behaviour — then almost none of this is built, and the interesting work is
wide open. You do not need permission to build on it. Fork it, rename it, take it
further than we did.

Keep it honest, and keep it generic. See [CONTRIBUTING.md](../CONTRIBUTING.md) and
[docs/IDEAS.md](IDEAS.md) for where to start, and
[docs/REQUIREMENTS-MODEL.md](REQUIREMENTS-MODEL.md) for the requirements/conflict model
in detail.