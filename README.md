# spec-check

**Check a codebase against its own written design requirements — before the two drift apart.**

In the age of AI-written code, anything can change at any moment. A system can pass
its design review on Monday and quietly violate it by Wednesday — and the diff looks
ordinary. `spec-check` is the missing linter for **design intent**: it reads what you
said the system should be, and checks the code still honours it.

> **This is the public, generalized tool** — it carries no project-specific or
> internal knowledge, and it has no dependency beyond the Python standard library.
> See [PROVENANCE.md](PROVENANCE.md).

---

## The problem: silent design drift

Type checkers catch **syntax** drift. Linters catch **style** drift. Tests catch
**behaviour**, in the cases you thought to write down. **None of them read your
design decisions and check they still hold.**

So when an LLM rewrites a module at 2am, or a "quick fix" quietly embeds 2,000 records
into a layer that was supposed to stay thin, nothing tells you. The design is violated,
the build is green, and you find out weeks later.

## The idea

**Treat every design decision as a checkable claim.**

A requirement is not prose in a wiki that rots. It is a small object with an ID, an
importance, and — crucially — a *check*: the thing you would look at to confirm it.
Once requirements are checkable, you can walk the whole list on every change and get a
verdict per requirement: pass, warn, fail, or *unverifiable*.

That last one matters. The tool is designed to **never guess**: when it cannot confirm
something, it says so and hands you the decision. A confident audit you can trust beats
a clever one you can't.

## How it works

```
   spec docs ──►  EXTRACT  ──►  CHECK  ──►  JUDGE  ──►  VERIFY  ──►  REPORT
   (specs,         requirements   deterministic  LLM tier   browser-    terminal ·
   AGENTS.md,      + provenance   checks/        (optional) based        JSON · UI ·
   .cursorrules)                                             evidence     hook · alert
   [REQ] notes
```

1. **Extract** — parse requirements from specs, `AGENTS.md`, `.cursorrules`, or `[REQ]`
   notes into *what / why / check / source*.
2. **Check** — deterministic checks (tiny functions in `checks/`) settle the mechanical
   rules exactly, offline, in milliseconds.
3. **Judge** — an LLM reads each *semantic* requirement against the code and returns a
   verdict plus evidence. Optional: no API key and this tier degrades gracefully.
4. **Verify** — a browser-based verifier flags any verdict the source contradicts
   (e.g. "X is missing" when X is right there).
5. **Report** — terminal, JSON, a browsable UI, a pre-commit gate, and a regression
   alert for the *"passing Monday, failing Wednesday"* case.

## Why not just linters and tests?

| Tool | Catches | Reads your design? |
|------|---------|:------------------:|
| type checker | type errors | ✗ |
| linter | style / smell | ✗ |
| test suite | behaviour you encoded | ✗ |
| **spec-check** | **drift from stated design** | **✓** |

It is not a replacement for any of them. It covers the gap they all leave open.

## Quickstart

Stdlib only — Python 3.8+, nothing to install.

```bash
git clone https://github.com/codedoodler/spec-check
cd spec-check

# 1. Browse requirements in a UI (filters, provenance, run an audit in place)
python3 server.py --root examples/target          # http://localhost:8090

# 2. Audit and get a verdict per requirement
python3 sweep.py  --root examples/target          # add --json for machine output
python3 judge.py  --root examples/target          # semantic tier (needs an API key)

# 3. Gate commits on critical requirements
./scripts/install-hooks.sh && ./install-hook.sh   # see AUTOMATION.md for details
```

## Try the bundled example

`examples/target/` is a tiny notes service with deliberate violations. Run the audit
against it and watch the tool catch them:

```bash
python3 sweep.py --root examples/target
```

## Help build it

This is early and the surface is wide open — **the whole point is for others to take
it further.** The idea (requirements as checkable claims) is small; the ways to
generalize it are not. If that sounds interesting, you are exactly who this is for.

- Read the [vision](VISION.md) — why this exists and where it could go.
- See [CONTRIBUTING.md](CONTRIBUTING.md) — concrete ways to add.
- Browse [docs/IDEAS.md](docs/IDEAS.md) — a menu of extension directions, from
  "write one more check" to "make this the standard".

## Documentation

- [`docs/index.html`](docs/index.html) — visual overview with charts (open in a browser)
- [`VISION.md`](VISION.md) — the purpose and the invitation
- [`docs/VISION.md`](docs/VISION.md) — the full system vision (ingest → model → resolve → conform → enforce → history)
- [`docs/REQUIREMENTS-MODEL.md`](docs/REQUIREMENTS-MODEL.md) — the requirements, conflict, and priority model
- [`docs/OVERVIEW.md`](docs/OVERVIEW.md) — the problem and the idea, in depth
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — pipeline, modules, JSON contracts
- [`docs/SPEC-FORMAT.md`](docs/SPEC-FORMAT.md) — how to write requirements
- [`docs/WRITING-CHECKS.md`](docs/WRITING-CHECKS.md) — how to add a deterministic check
- [`docs/LLM-GUIDE.md`](docs/LLM-GUIDE.md) — guide for agents/LLMs
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — status and roadmap
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to help
- [`llms.txt`](llms.txt) — machine-readable entry point for LLMs

## License

MIT — see `LICENSE`. Use it, fork it, rename it, ship it.
