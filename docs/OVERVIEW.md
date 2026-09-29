# Overview

**spec-check** checks a codebase against its own written design requirements —
before the two drift apart.

## The problem

LLM-built systems can change anything, at any time. A system that passed its
design review on Monday can silently violate it on Wednesday: a guard gets
removed, a boundary gets crossed, a value that was supposed to be derived gets
hard-coded. The diff looks ordinary. Nobody notices until something breaks.

Conventional tools catch *syntax* drift:

| Tool | Catches |
|------|---------|
| type checker | the code is ill-typed |
| linter | the code is unidiomatic |
| tests | the code does the wrong thing in a case you thought of |

None of them catch **design drift** — "we agreed the data layer stays thin, but a
run just embedded 2,000 records in it." Design intent lives in prose: architecture
docs, review notes, `AGENTS.md`, conventions files. It is written down and then
never checked again.

## The idea

If a design decision is worth writing down, it is worth checking mechanically.

spec-check treats each design requirement as a *checkable claim* and walks the
whole list against your code — the thing a careful reviewer does by hand, and
that nobody actually does on every commit.

```
requirements  ──►  check each against the code  ──►  pass / fail / warn + evidence
```

## How it checks

Three layers, from cheap-and-certain to expensive-and-semantic:

1. **Deterministic checks** — ~10-line Python functions in `checks/`. Fast, exact,
   no LLM. Run everywhere, block commits.
2. **LLM judge** — for requirements that need semantic judgment, a model reads the
   requirement's What/Why/Check plus the code and returns a verdict + evidence.
   Covers every requirement the deterministic checks can't.
3. **Evidence verifier** — cross-checks the judge. If a verdict claims "X is
   missing" but X is in the source, it flags the contradiction. Catches the
   hallucination that matters most: a false "it's fine / it's gone".

## Where it fits

- **Interactive** — browse requirements and run audits in a local UI.
- **Pre-commit** — block a commit when a critical requirement fails.
- **Scheduled** — the "passing Monday, failing Wednesday" alert: any requirement
  that was passing and now fails, to your terminal, a Linear ticket, or a webhook.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for how the pieces fit,
[`SPEC-FORMAT.md`](SPEC-FORMAT.md) for the requirement format, and
[`WRITING-CHECKS.md`](WRITING-CHECKS.md) to add a check.

## What it is not

- Not a linter or a type checker — it checks *your* design intent, not language rules.
- Not a test suite — it does not run your code.
- Not a proof — it is a systematic audit that surfaces drift early, with evidence
  you can read. "Unverifiable" is a first-class answer; the tool does not guess.
