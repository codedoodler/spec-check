#!/usr/bin/env python3
"""Pre-push leak guard.

Refuses to push this repo if the working tree carries internal markers or
secret-shaped strings. Installed by scripts/install-hooks.sh as
.git/hooks/pre-push.

The marker list here is intentionally project-agnostic: edit MARKERS for your
own forbidden terms. This file itself is skipped during the scan (it embeds the
patterns).
"""
import re
import subprocess
import sys
from pathlib import Path

try:
    ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"],
                               capture_output=True, text=True, check=True).stdout.strip())
except Exception:
    ROOT = Path(".").resolve()

# Forbidden internal/domain markers — generalize or extend for your project.
# Case-insensitive: names/tokens that must not appear in any casing.
MARKERS = re.compile(
    r"issac|weave|aravind|delman|felicia|memgraph|commodit|cotton|bangladesh|"
    r"opik|danny|datacube|pandora|ralph|47\.130|benchmark_store|cube-mcp|"
    r"calc-mcp|graph-mcp|deploy/|hermes|aisle8", re.I)

# Case-sensitive: tokens whose lowercase spelling is ordinary English, so they
# must only match in their exact form (e.g. the internal team key "ASK").
TOKENS = re.compile(r"\bASK\b")

# Real key shapes (not obvious placeholders).
SECRETS = re.compile(
    r"sk-or-v1-[A-Za-z0-9]{16,}|sk-[A-Za-z0-9]{32,}|AKIA[0-9A-Z]{16}|"
    r"ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY|xox[baprs]-[0-9A-Za-z-]{10,}")

SKIP_PARTS = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}
EXTS = {".py", ".md", ".html", ".sh", ".txt", ".yml", ".yaml", ".json", ".toml", ".cfg", ".ini"}
SELF = Path(__file__).resolve()


def scan():
    hits = []
    for f in ROOT.rglob("*"):
        if f.is_dir() or any(p in SKIP_PARTS for p in f.parts) or f.suffix not in EXTS:
            continue
        try:
            if f.resolve() == SELF:
                continue
        except OSError:
            pass
        try:
            text = f.read_text(errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if MARKERS.search(line):
                hits.append((f, i, "internal-marker", line.strip()[:100]))
            if TOKENS.search(line):
                hits.append((f, i, "internal-token", line.strip()[:100]))
            if SECRETS.search(line):
                hits.append((f, i, "secret-shaped", line.strip()[:100]))
    return hits


def main():
    hits = scan()
    if hits:
        print("\u270b pre-push blocked \u2014 the tree carries material that must not be published:\n")
        for f, i, kind, line in hits[:40]:
            try:
                rel = f.relative_to(ROOT)
            except ValueError:
                rel = f
            print(f"  {rel}:{i} [{kind}] {line}")
        print(f"\n{len(hits)} finding(s). Remove or generalize them, or push with "
              f"--no-verify if you are certain this is intended.")
        return 1
    print("\u2713 pre-push leak guard: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
