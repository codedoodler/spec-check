"""Deterministic tests for spec-check (no network, no LLM).

Run:  pip install pytest && pytest -q
"""
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import server  # noqa: E402


def _mkproject(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "requirements.md").write_text(textwrap.dedent("""
        ### API-1 · 🔴 · ✅ — Handlers validate input
        - **What:** every request body is validated.
        - **Why:** prevents injection.
        - **Check:** inspect every handler.
        - **Source:** design review, 2026-08-12

        ### SEC-1 · 🟠 · ◐ — No secrets in source
        - **What:** no credentials hard-coded.
        - **Why:** secrecy.
        - **Check:** grep source for key literals.
        - **Source:** security review, 2026-08-13
    """).strip())
    (tmp_path / "api").mkdir()
    (tmp_path / "api" / "service.py").write_text("def handle(payload):\n    return payload\n")
    return tmp_path


def test_extract_requirements(tmp_path):
    reqs = server.scan_requirements(str(_mkproject(tmp_path)))
    ids = {r["id"] for r in reqs}
    assert {"API-1", "SEC-1"} <= ids
    api = next(r for r in reqs if r["id"] == "API-1")
    assert api["importance"] == "critical"
    assert api["tier"] == "A"
    assert api["topic"] == "api"


def test_heading_accepts_word_legend(tmp_path):
    (tmp_path / "requirements.md").write_text(
        "### R-1 · high · open — Plain text legend\n- **What:** x\n")
    reqs = server.scan_requirements(str(tmp_path))
    assert reqs and reqs[0]["importance"] == "high"
    assert reqs[0]["status_flag"] == "open"


def test_check_runner_detects_secret(tmp_path):
    (tmp_path / "a.py").write_text('API_KEY = "abcd1234efgh"\n')
    det = server.run_audit_checks(str(tmp_path))
    sec = [r for r in det if r["id"] == "SEC-1"]
    assert sec and sec[0]["status"] == "fail"


def test_check_runner_clean_project(tmp_path):
    (tmp_path / "a.py").write_text("def f():\n    return 1\n")
    det = server.run_audit_checks(str(tmp_path))
    assert det, "expected at least one check to run"
    assert all(r["status"] != "fail" for r in det)


def test_bundled_example_is_discovered():
    root = ROOT / "examples" / "target"
    if not root.is_dir():
        return
    ids = {r["id"] for r in server.scan_requirements(str(root))}
    assert {"API-1", "API-2", "SEC-1"} <= ids
