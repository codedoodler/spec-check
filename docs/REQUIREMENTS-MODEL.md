# The requirements model

This is the data model behind the vision: what a requirement *is*, how requirements
relate, how conflicts are found and settled, and how priority is decided. It is
deliberately plain so that other tools can read and write it.

## A requirement

A requirement is a small, checkable object — not a paragraph in a wiki.

```json
{
  "id": "API-2",
  "title": "All request bodies are validated",
  "tier": "B",
  "importance": "critical",
  "status": "active",
  "what": "Every mutating endpoint validates its request body against a schema before use.",
  "why": "Unvalidated input is the most common source of defects and security issues.",
  "check": "For each mutating route, confirm a schema validation call precedes any use of the body.",
  "source": ["docs/specs/api.md#validation", "meeting 2026-03-04"],
  "supersedes": [],
  "superseded_by": null,
  "introduced": "2026-03-04",
  "amended": ["2026-05-11"]
}
```

Field notes:

- **`what`** — the requirement, in one sentence, imperative.
- **`why`** — the intent it protects. Without this, nobody knows what they'd break by
  changing it, and the rule becomes cargo cult.
- **`check`** — the concrete thing to look at to judge conformance. **If you cannot
  answer the `check` yes/no, the requirement is too vague to enforce** — that is itself
  a finding.
- **`source`** — where it came from. Every requirement is sourced; an unsourced
  requirement is a rumour.

## Tiers

| Tier | Holds | Example shape | Testable |
|------|-------|---------------|:--------:|
| **A · Aspirational** | the guiding light; a goal, not a rule | "the reasoning is auditable" | no |
| **B · Principles** | invariants; violating one is a defect | "state lives in components, not the model" | conceptually |
| **C · Component** | what each part must do | "the store returns full records" | yes |
| **D · Testable** | each becomes a test | "the pricing anchor matches the golden set" | mechanically |

The tiers matter because they are held to *different bars*: an aspirational goal can be
partially met and still be on track, while a violated Tier-B principle is a defect by
definition, and a Tier-D item either passes its test or does not.

## Importance and status

**Importance** — critical · high · medium. Drives enforcement (see below).

**Status** — active · partial · open · superseded · deferred · retired.

Superseded and retired requirements stay in the list. Nothing is ever silently deleted;
that is what makes the history auditable.

## Precedence: how conflicts are settled

Requirements accumulate over months from many people. When two of them disagree, the
resolution rule must be explicit, or stale rules get resurrected:

> **The most recent ruling from a named authority wins.** The loser is marked
> *superseded* and kept, with a pointer to what replaced it.

Two properties make this work:

- **Recency** — later decisions override earlier ones.
- **Authority** — a ruling attributed to a specific, named source outranks an
  inference or an undocumented memory.

Anything the rule cannot settle (two equally recent, equally authoritative, mutually
exclusive requirements) is **escalated as an open question**, never guessed.

## Conflict classes

The spec checks itself for at least these:

| Class | Meaning | How it's found | How it's handled |
|-------|---------|----------------|------------------|
| **Contradiction** | two active requirements cannot both hold | pairwise `check` comparison | precedence; escalate if tied |
| **Supersession** | a newer decision overrides an older one | same subject, different date/authority | mark older *superseded*, keep it |
| **Duplicate** | the same requirement stated twice | text/semantic similarity | merge, union the sources |
| **Ambiguity** | a `check` with two defensible readings | LLM judge + human confirmation | rewrite the `check` to be binary |
| **Orphan** | no owner, no check, or nothing implements it | cross-reference to code/tickets | flag; assign or retire |
| **Staleness** | code no longer honours it and nobody re-affirmed | conformance history | flag for re-affirmation or retirement |

## Priority

When everything cannot be done at once, rank by what actually matters:

```
priority ≈ importance × tier_weight × dependency_count × violation_risk
```

- **importance** — critical > high > medium
- **tier_weight** — principles outrank component details
- **dependency_count** — how much else breaks if this requirement is violated
- **violation_risk** — how likely it is to drift (from the running tally)

The output is a ranked backlog: the design tells you what to fix first.

## Lifecycle and history

Every requirement moves through states, and each transition is recorded:

```
introduced ──► amended ──► superseded ──► retired
     │              │
     └──────────────┴── each transition: {date, source, reason}
```

This yields two things nobody has today:

- an **audit trail** — who decided what, when, and based on which meeting or document
- **time-travel** — "what did the design say on this date, and what changed since?"

## Extraction conventions

Ingestion reads every source and tags each statement:

- **`[REQ]`** — an explicit must / should / need / decided / will-do.
- **`[INTENT]`** — a motivation, concern, or complaint that *implies* a requirement
  without stating one. Often the most valuable, and the easiest to lose.

Every extracted statement keeps a link back to its source, so a requirement can always
be traced to the words that created it.

## Practical quality bar

A requirements list is healthy when:

- every active requirement has a `check` that can be answered yes/no
- every requirement has a source
- conflicts are surfaced, not quietly resolved
- superseded items are retained with a pointer to their replacement
- the priority ranking is derived, not hand-waved

Run the list against those five and you will find the holes fast.