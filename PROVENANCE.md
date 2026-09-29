# Provenance & boundaries

## What this repository is

`spec-check` is the **public, generalized** version of a design-compliance tool.
It was extracted from an internal project and rewritten so it carries **no
project-specific or internal knowledge**. Everything here — the requirements
format, the checks, the examples — is generic and safe to read.

## The rule

**Project-specific knowledge never belongs in this repository.**

That means, never commit here:

- names of real colleagues, customers, or reviews
- internal codenames, component names, or dataset names
- internal file paths (a private source tree outside this repo)
- real constants, metrics, or schemas from a private system
- credentials of any kind

A project's *own* checks and requirements live **in that project** — in its own
`checks/` and its own spec docs — not here. This repo ships only the generic
framework plus two example checks and a toy demo project.

## Guards

`git` does not version hooks, so each clone should run once:

```bash
./scripts/install-hooks.sh
```

That installs a **pre-push leak guard** (`scripts/leak_guard.py`) which refuses
to push if the tree contains internal markers or secret-shaped strings. It is a
backstop, not a substitute for care — review `MARKERS` and extend it for any
term your project must never publish.

## Publishing

The public home is **https://github.com/codedoodler/spec-check**. The history is
intentionally a small, clean set of commits — an extraction like this should not
carry the internal changelog, whose commit messages describe the private project.

## If you maintain the internal source

Keep this repo and the internal copy deliberately separate:

- internal copy: the real, project-specific checks and requirements
- this repo: the generic framework, examples only

When back-porting improvements here, re-read them for leaked specifics before
committing. The pre-push guard is the last line of defence for exactly that.
