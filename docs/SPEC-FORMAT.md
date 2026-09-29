# Spec format

A spec is a plain Markdown file. Each requirement is a level-3 (or level-4)
heading plus a short body.

## The heading

```
### <ID> · <importance> · <status> — <label>
```

- **ID** — a stable identifier. The prefix before the first `-` is the *tier*
  (`API-1` → tier `A`, `SEC-3` → tier `S`... by first letter). Use A/B for
  requirements that must block a commit.
- **importance** — a symbol or word. The default legend is emoji:
  `🔴 critical · 🟠 high · 🟡 medium · ⚪ low`. Any symbol/word works — unknown
  values pass through as-is, so you can use `high` / `medium` / `low` directly.
- **status** — a symbol or word. Default legend: `✅ addressed · ◐ partial ·
  ○ open · 🗑 superseded · ⏳ deferred`.
- **label** — a one-line title.

`·` is the field separator and `—` separates status from the label.

## The body

```
### API-1 · 🔴 · ✅ — All request bodies are validated
- **What:** every public entry point validates its payload before use.
- **Why:** unvalidated input corrupts state downstream.
- **Check:** does each public entry point validate before it mutates state?
- **Source:** design review, 2026-02-20
```

| Field | Meaning |
|-------|---------|
| **What** | The requirement, tightened until it is unambiguous. |
| **Why** | The intent it protects — this is what lets an LLM judge edge cases. |
| **Check** | The concrete thing to look at. Becomes the judge's instruction. |
| **Source** | Provenance: who/where/when. Lets you trace and supersede. |

Fields are matched by name, so order is flexible and extra fields are ignored.

## Where specs live

`spec-check` discovers requirement documents automatically. For a project rooted
at `R`, it reads:

- `R/docs/**/*requirement*.md`, `R/**/*requirement*.md`, `R/spec/**/*requirement*.md`
- `R/docs/spec.md`, `R/spec.md`, `R/specification.md`
- `R/AGENTS.md`, `R/CLAUDE.md`, `R/.cursorrules` (conventions as requirements)
- meeting notes with `[REQ]` tags

So a project does not need the full hierarchy format to get value — plain
conventions files count.

## Provenance and supersession

- A requirement never disappears silently. Marking one `🗑 superseded` (or tier
  `S`) keeps it as history and excludes it from judging.
- `Source` ties a requirement to the review it came from, so when a newer ruling
  contradicts an older one, the most recent wins. `sweep.py` reports conflicts.

## Tips

- One claim per requirement. If you write "and", split it.
- Make **Check** answerable by looking. "Is the graph thin?" is weak; "does any
  node embed more than a key?" is checkable.
- Keep IDs stable — they are the join key across runs, history, and alerts.
