"""Generic check: no debug statements left in source.

Flags interactive-debugger entry points that should never be committed
(`breakpoint()`, `pdb.set_trace()`, `ipdb`). Deterministic, no LLM.
"""
import re
from pathlib import Path

PATTERNS = [
    (re.compile(r"^\s*breakpoint\(\)"), "breakpoint()"),
    (re.compile(r"\b(?:pdb|ipdb|pudb)\.set_trace\(\)"), "debugger set_trace()"),
]

SKIP_DIRS = {"venv", ".venv", ".git", "node_modules", "__pycache__", "dist", "build", ".tox"}
SKIP_FILES = {"check_no_debug_statements.py"}


def run(root):
    root = Path(root)
    hits = []
    for f in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in f.parts) or f.name in SKIP_FILES:
            continue
        try:
            text = f.read_text(errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for pat, name in PATTERNS:
                if pat.search(line):
                    hits.append(f"{f.relative_to(root)}:{i} — {name}")
    return [{
        "id": "DBG-1", "label": "No debugger statements left in source", "tier": "C",
        "status": "fail" if hits else "pass",
        "detail": (f"{len(hits)} debugger statement(s): " + "; ".join(hits[:5])) if hits
                  else "no debugger statements found",
    }]
