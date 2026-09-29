#!/usr/bin/env python3
"""Design-compliance sweep: extract -> check -> judge -> verify -> report.

One command that runs the whole pipeline and produces a "how broken is this
system" report, for human review.

Layers:
  1. Deterministic checks (checks/) - current-state greps; can't hallucinate.
  2. LLM-judge (--full) - walks every requirement against the FULL current code.
  3. Evidence verifier (NEW) - greps each FAIL verdict's evidence back against
     source and flags negative claims ("no X", "X removed") that the code
     contradicts, so the judge's hallucinations are surfaced, not trusted.
  4. Stale/conflict detection (NEW) - flags FAILs that are really "functionality
     was deliberately removed" (stale requirement), and anchor requirements that
     conflict with the derive-don't-hardcode principle.

The report now surfaces each verdict's SOURCE (the doc/meeting it came from),
so you can trace every finding back to its origin.

Usage:
  python3 sweep.py --root /path/to/project [--out report.md] [--json] [--skip-judge]
"""
import argparse, json, re, subprocess, sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from server import scan_requirements, run_audit_checks
from judge import judge_all

# --- verification / conflict patterns ---
# "no X", "never X", "without X", "missing X", "lacks X" -> capture X
NEGATION_RE = re.compile(r"\b(?:no|never|without|missing|lacks)\s+[`\"']?([^\s,;]+)", re.I)
# evidence that says the functionality was deliberately removed / superseded
STALE_RE = re.compile(r"\b(?:removed|obsolete|no longer|deprecated)\b", re.I)
# a requirement that pins a specific formula/value (an "anchor")
ANCHOR_RE = re.compile(r"byte-for-byte|anchor|==\s*\$|\$\d+(?:\.\d+)?", re.I)
# a requirement that mandates derive-don't-hardcode
NO_HARDCODE_RE = re.compile(r"hardcod|deriv(?:e|ed)|no hardcod", re.I)


def build_full_diff(root, source=None):
    """git diff empty-tree -> HEAD for the project source, minus generated/vendored files.

    `source` is an optional path (file or dir) relative to the repo root that scopes the
    diff; default is the whole repo. Generated data and vendored dirs are excluded so the
    judge reasons about code and the diff stays within its context window.
    """
    root = Path(root)
    empty = subprocess.run(
        ["git", "hash-object", "-t", "tree", "/dev/null"],
        cwd=root, capture_output=True, text=True).stdout.strip()
    cmd = ["git", "diff", empty, "HEAD"]
    if source:
        cmd += ["--", source]
    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    chunks = re.split(r"(?=^diff --git )", r.stdout, flags=re.M)
    kept = []
    for c in chunks:
        m = re.match(r"diff --git a/(\S+) b/", c)
        if not m:
            continue
        p = m.group(1)
        # Exclude generated/data + vendored files — the judge reasons about CODE,
        # not data. Keeps the diff within the judge model's context window.
        if p.endswith(".cypher") or any(seg in p for seg in ("venv", "node_modules", "/tests/")):
            continue
        kept.append(c)
    return "".join(kept)


def _grep_symbol(root, symbol, source=None):
    """Return real source files under the project (or `source`) containing `symbol`."""
    symbol = symbol.strip().strip('`"\'').rstrip(".,;:")
    if len(symbol) < 3 or symbol.lower() in {"the", "and", "for", "not", "that"}:
        return []
    # Only "code-like" symbols matter — generic prose words ("test", "JSON",
    # "flush", "skill") are the judge's wording, not a claim about a real identifier.
    if not (re.search(r"[._@]", symbol) or (symbol.isupper() and len(symbol) >= 3)):
        return []
    base = (Path(root) / source) if source else Path(root)
    if not base.is_dir():
        return []
    r = subprocess.run(
        ["grep", "-rlF", "--include=*.py", "--include=*.md", "--include=*.json",
         "--", symbol, str(base)],
        capture_output=True, text=True)
    out = []
    for p in r.stdout.splitlines():
        if not p:
            continue
        if "venv" in p or "__pycache__" in p or p.endswith(".pyc"):
            continue
        out.append(p)
    return out


def verify_evidence(judge_results, root, source=None):
    """Layer 3: flag FAIL verdicts whose evidence claims something is absent
    that the source actually contains (the 'X is missing' hallucination)."""
    for r in judge_results:
        flags = []
        if r.get("status") == "fail":
            for m in NEGATION_RE.finditer(r.get("evidence", "")):
                sym = m.group(1)
                hits = _grep_symbol(root, sym, source)
                if hits:
                    flags.append(f'claims "{sym}" absent, but found in {Path(hits[0]).name}')
        r["contradictions"] = flags
    return judge_results


def detect_stale(judge_results):
    """Flag FAILs whose evidence says the functionality was deliberately removed
    — stale-requirement candidates, not active violations."""
    for r in judge_results:
        r["stale"] = bool(r.get("status") == "fail" and STALE_RE.search(r.get("evidence", "")))
    return judge_results


def detect_conflicts(reqs):
    """Heuristic: requirements that pin a specific formula/value conflict with
    the derive-don't-hardcode requirements. Needs human confirmation."""
    no_hardcode_ids = [r["id"] for r in reqs
                       if NO_HARDCODE_RE.search((r.get("check", "") + " " + r.get("what", "")))]
    conflicts = []
    for r in reqs:
        text = (r.get("check", "") + " " + r.get("what", "") + " " + r.get("label", ""))
        if ANCHOR_RE.search(text):
            conflicts.append({
                "id": r["id"], "label": r["label"],
                "conflicts_with": no_hardcode_ids[:5],
                "why": "pins a specific formula/value while other requirements mandate derive-don't-hardcode",
            })
    return conflicts


def _attach_sources(results, reqs_by_id):
    for r in results:
        rid = r.get("id")
        r["source"] = (reqs_by_id.get(rid) or {}).get("source", "")
    return results


def _tally(results):
    return Counter(r["status"] for r in results)


def sweep(root, skip_judge=False, source=None):
    reqs = scan_requirements(root)
    det = run_audit_checks(root)
    diff = build_full_diff(root, source)
    judge = [] if skip_judge else judge_all(reqs, diff, full=True)

    reqs_by_id = {r["id"]: r for r in reqs}
    det = _attach_sources(det, reqs_by_id)
    judge = _attach_sources(judge, reqs_by_id)
    judge = verify_evidence(judge, root, source)
    judge = detect_stale(judge)
    conflicts = detect_conflicts(reqs)
    superseded = [r["id"] for r in reqs
                  if r.get("status_flag") == "superseded" or r.get("tier") == "S"]

    return {"reqs": reqs, "deterministic": det, "judge": judge,
            "diff_bytes": len(diff), "root": root, "source": source,
            "conflicts": conflicts, "superseded": superseded}


def _rows(results, status):
    return [r for r in results if r["status"] == status]


def format_markdown(s):
    tiers = Counter(r["tier"] for r in s["reqs"])
    dt = _tally(s["deterministic"])
    jt = _tally(s["judge"])
    contradictions = [r for r in s["judge"] if r.get("contradictions")]
    stale = [r for r in s["judge"] if r.get("stale")]

    L = []
    L.append("# Design-Compliance Sweep")
    L.append("")
    L.append(f"**Project:** `{s['root']}`")
    L.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    L.append("")
    L.append("## 1 · Requirement inventory")
    L.append(f"- **{len(s['reqs'])}** requirements extracted (hierarchy + meeting [REQ] tags + conventions)")
    L.append(f"- by tier: " + ", ".join(f"{k}={v}" for k, v in sorted(tiers.items())))
    L.append(f"- **{len(s['superseded'])}** already marked superseded (excluded from judging): {', '.join(s['superseded']) or '—'}")
    L.append("")
    L.append("## 2 · Deterministic checks (current-state)")
    L.append(f"- result: **{dt.get('pass',0)} pass · {dt.get('fail',0)} fail · {dt.get('warn',0)} warn**")
    L.append("")
    L.append("| Status | ID | Check | Source | Detail |")
    L.append("|---|---|---|---|---|")
    for r in s["deterministic"]:
        L.append(f"| {r['status'].upper()} | {r['id']} | {r['label']} | {r.get('source','') or '—'} | {r.get('detail','')} |")
    L.append("")
    L.append("## 3 · LLM-judge (full current-state audit)")
    L.append(f"- judged against the full project source ({s['diff_bytes']:,} bytes), not just a change diff")
    L.append(f"- result: **{jt.get('pass',0)} pass · {jt.get('fail',0)} fail · {jt.get('warn',0)} warn**")
    L.append("")

    for status, title in [("fail", "### ❌ FAIL — the code violates the requirement"),
                          ("warn", "### ⚠️ WARN — risky / can't confirm"),
                          ("pass", "### ✅ PASS — consistent")]:
        rows = _rows(s["judge"], status)
        if not rows:
            continue
        L.append(title)
        L.append("")
        L.append("| ID | Tier | Requirement | Source | Evidence |")
        L.append("|---|---|---|---|---|")
        for r in rows:
            L.append(f"| {r['id']} | {r['tier']} | {r['label']} | {r.get('source','') or '—'} | {r['evidence']} |")
        L.append("")

    L.append("## 4 · Evidence verification (sanity check on the judge)")
    if contradictions:
        L.append(f"**{len(contradictions)} verdict(s) flagged — the judge claims something is absent that the code contains.** Review these; they are likely false positives.")
        L.append("")
        for r in contradictions:
            L.append(f"- **{r['id']}** {r['label']} — {'; '.join(r['contradictions'])}")
    else:
        L.append("No verdict's evidence was contradicted by the source.")
    L.append("")
    if stale:
        L.append(f"**{len(stale)} FAIL(s) look like stale requirements** (evidence says the functionality was deliberately removed/superseded), not active violations:")
        L.append("")
        for r in stale:
            L.append(f"- **{r['id']}** {r['label']}")
    L.append("")

    if s["conflicts"]:
        L.append("## 5 · Requirement conflicts (heuristic — confirm by hand)")
        L.append("")
        L.append("| ID | Requirement | Conflicts with | Why |")
        L.append("|---|---|---|---|")
        for c in s["conflicts"]:
            L.append(f"| {c['id']} | {c['label']} | {', '.join(c['conflicts_with']) or '—'} | {c['why']} |")
        L.append("")

    L.append("## 6 · Verdict")
    total_fail = dt.get("fail", 0) + jt.get("fail", 0)
    total_warn = dt.get("warn", 0) + jt.get("warn", 0)
    total_pass = dt.get("pass", 0) + jt.get("pass", 0)

    def n(word, count):
        return f"{count} {word if count == 1 else word + 's'}"
    L.append(f"- **{n('hard failure', total_fail)}**, **{n('warning', total_warn)}**, **{n('passing', total_pass)}**")
    L.append("")
    if contradictions:
        L.append(f"⚠️ {len(contradictions)} of the FAILs are flagged as likely false positives — subtract them before acting.")
    if stale:
        L.append(f"⚠️ {len(stale)} of the FAILs are likely stale requirements — mark them superseded, don't fix the code.")
    if not contradictions and not stale and total_fail == 0:
        L.append("The system is **conforming** — no requirement is demonstrably violated.")
    elif total_fail <= 3:
        L.append(f"The system has **{total_fail} confirmed violations** (see FAIL rows). Fix those first; warnings are the next tranche.")
    else:
        L.append(f"The system has **{total_fail} confirmed violations** — materially out of spec. The FAIL rows are the fix queue, ranked by tier (A/B first), minus any flagged false-positive/stale.")
    L.append("")
    L.append("---")
    L.append("_Generated by `spec-check/sweep.py`. Review §4 flags and §5 conflicts before acting on §3 FAILs. Treat any requirement whose Check you can now make machine-checkable as a candidate for a new `checks/*.py`._")
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="Design-compliance sweep (extract -> check -> judge -> verify -> report)")
    ap.add_argument("--root", required=True, help="Project root")
    ap.add_argument("--source", help="Scope the code diff to this path (default: the whole repo)")
    ap.add_argument("--out", help="Write the report to this file")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    ap.add_argument("--skip-judge", action="store_true", help="Deterministic checks + verification only (no LLM judge)")
    args = ap.parse_args()

    s = sweep(args.root, skip_judge=args.skip_judge, source=args.source)

    if args.json:
        print(json.dumps({
            "root": s["root"],
            "inventory": {"total": len(s["reqs"]),
                          "tiers": dict(Counter(r["tier"] for r in s["reqs"]))},
            "superseded": s["superseded"],
            "deterministic": s["deterministic"],
            "judge": s["judge"],
            "conflicts": s["conflicts"],
        }, indent=2))
        return

    md = format_markdown(s)
    print(md)
    if args.out:
        Path(args.out).write_text(md)
        print(f"\n[saved report to {args.out}]", file=sys.stderr)


if __name__ == "__main__":
    main()
