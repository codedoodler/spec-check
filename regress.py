#!/usr/bin/env python3
"""Design regression detector — flags when a passing requirement starts failing.

Usage:
  python3 regress.py --root /path/to/project [--history .audit-history.json]

Behavior:
- Runs the audit (same as the server/pre-commit hook).
- Loads the previous audit results from --history (a JSON file).
- Compares: any requirement that was "pass" last time and is "fail"/"warn"
  now is a REGRESSION.
- Any requirement that was "fail" and is now "pass" is an IMPROVEMENT.
- Any new requirement that appears is a NEW CHECK.
- Prints a summary and saves the new history.

This is the "passing Monday, failing Wednesday" signal — the most valuable
alert the tool produces.
"""
import json, sys, argparse
from pathlib import Path
from datetime import datetime


def load_history(path):
    if Path(path).exists():
        try:
            return json.loads(Path(path).read_text())
        except Exception:
            return {}
    return {}


def save_history(path, results):
    history = {
        "updated": datetime.now().isoformat(),
        "checks": {r["id"]: {"status": r["status"], "detail": r["detail"],
                             "label": r.get("label","")} for r in results}
    }
    Path(path).write_text(json.dumps(history, indent=2))
    return history


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Project root")
    ap.add_argument("--history", default=".audit-history.json",
                    help="History file (default: .audit-history.json)")
    ap.add_argument("--json", action="store_true", help="Output JSON for integration")
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from server import run_audit_checks

    prev = load_history(args.history)
    results = run_audit_checks(args.root)

    prev_checks = prev.get("checks", {})
    now = {r["id"]: r["status"] for r in results}

    regressions = []
    improvements = []
    new_checks = []

    for r in results:
        rid = r["id"]
        if rid not in prev_checks:
            new_checks.append(rid)
            continue
        before = prev_checks[rid]["status"]
        after = r["status"]
        if before == "pass" and after in ("fail", "warn"):
            regressions.append((rid, before, after, r.get("detail","")))
        elif before in ("fail", "warn") and after == "pass":
            improvements.append((rid, before, after))

    # Save new history
    save_history(args.history, results)

    if args.json:
        print(json.dumps({
            "updated": datetime.now().isoformat(),
            "regressions": [{"id":x[0],"from":x[1],"to":x[2],"detail":x[3]} for x in regressions],
            "improvements": [{"id":x[0],"from":x[1],"to":x[2]} for x in improvements],
            "new_checks": new_checks,
            "total": len(results),
        }, indent=2))
        return 0

    print(f"DESIGN REGRESSION SCAN — {len(results)} checks")
    print("-" * 60)

    if regressions:
        print(f"🔴 {len(regressions)} REGRESSION(S) — were passing, now failing:")
        for rid, before, after, detail in regressions:
            print(f"  ❌ {rid}: {before} → {after} — {detail}")
    else:
        print("✅ No regressions — nothing that was passing is now failing.")

    if improvements:
        print(f"\n🟢 {len(improvements)} IMPROVEMENT(S) — were failing, now passing:")
        for rid, before, after in improvements:
            print(f"  ✅ {rid}: {before} → {after}")

    if new_checks:
        print(f"\n🆕 {len(new_checks)} NEW CHECK(S) — first time seen:")
        for rid in new_checks:
            print(f"  → {rid}")

    print("-" * 60)
    print(f"History saved to {args.history}")

    return 1 if regressions else 0


if __name__ == "__main__":
    sys.exit(main())