"""Generic check: no hard-coded secrets in source.

Flags obvious credential literals — cloud keys, private-key blocks, and
hard-coded password/token strings. Deterministic, no LLM.

Every check file in checks/ defines run(root) -> list of result dicts:
    {"id": "...", "label": "...", "tier": "A|B|C|D",
     "status": "pass|fail|warn", "detail": "explanation"}
Tier A/B failures block commits (pre-commit hook) and trigger alerts.
"""
import re
from pathlib import Path

PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key id"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"), "private-key block"),
    (re.compile(r"(?i)(?:password|passwd|secret|api[_-]?key|access[_-]?token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
     "hard-coded credential literal"),
]

SKIP_DIRS = {"venv", ".venv", ".git", "node_modules", "__pycache__", "dist", "build", ".tox"}
SKIP_FILES = {"check_no_secrets.py"}  # don't match the pattern strings in this file


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
        "id": "SEC-1", "label": "No hard-coded secrets in source", "tier": "B",
        "status": "fail" if hits else "pass",
        "detail": (f"{len(hits)} potential secret(s): " + "; ".join(hits[:5])) if hits
                  else "no hard-coded secret patterns found",
    }]
