# Vision

*Why `spec-check` exists, and what it could become. Read this if you're deciding
whether the idea is worth your time.*

## The shift nobody has tools for yet

For decades, software moved slowly enough that design lived in people's heads and
review meetings. The cost of change was high, so drift was slow and visible.

That is over. When an AI can rewrite a module in seconds, the bottleneck is no longer
writing code — it is **trusting** it. And the thing we trust least is not correctness in
the test cases we imagined; it is *fidelity to the design we agreed on*. The design
decisions are the part that rots silently, because nothing checks them.

We think this is the defining maintenance problem of AI-built software, and that it has
been almost completely unaddressed.

## The bet

**Design intent can be made checkable.**

If every requirement carries the thing you would look at to confirm it, then "does the
code still match the design?" stops being a vibe and becomes an audit you can run in
CI, on every commit, forever. Not a proof — a systematic, honest check that surfaces
drift while it is still cheap to fix.

The pieces:

1. **A format** for requirements that is light enough to actually write and rich enough
   to check (what / why / check / source).
2. **Layers of trust**: exact deterministic checks where the rule is mechanical, an LLM
   only where judgment is genuinely required, and a verifier that refuses to let the LLM
   lie confidently.
3. **One first-class answer for "I don't know"**: *unverifiable*. A tool that guesses is
   worse than no tool.

That is all `spec-check` is today: a small, honest implementation of those three ideas.

## What it could become

Think of it less as "a tool" and more as a **missing standard**, the way
`package.json` or `Dockerfile` are standards — a conventional way to state and verify
design that every project could adopt:

- **A shared library of checks** — secrets, structure, observability, layering,
  licensing — contributed by everyone, applicable anywhere.
- **A portable spec format** — one convention that other tools can read and write;
  editors, agents, and CI all able to consume the same requirements.
- **CI that enforces design**, the way CI enforces tests: a red build when the system
  stops being what it claims.
- **Agents that check their own work** — an AI that, before declaring a task done,
  verifies the change against the project's own requirements and reports honestly.

None of that exists yet. The core here is small enough to read in an afternoon and
open enough to extend in any of a dozen directions.

## Principles

These are the non-negotiables, and they are what any contribution should protect:

- **Measured, not typed.** Prefer observing the real system over trusting a declaration.
- **Never guess.** If it can't be confirmed, say *unverifiable* and hand it back.
- **Deterministic first.** Use the cheapest, most certain method that works; reach for
  an LLM only for genuine judgment.
- **Honest about limits.** A tool for trust must not overstate what it knows.

## The invitation

If the premise is right — that checking design intent is about to matter as much as
checking behaviour — then the interesting work is wide open and barely started.

You do not need permission to build on this. Fork it, rename it, take the idea further
than we did. If you want a place to start, see [CONTRIBUTING.md](CONTRIBUTING.md) and
[docs/IDEAS.md](docs/IDEAS.md).

The only thing we ask: keep it honest, and keep it generic.
