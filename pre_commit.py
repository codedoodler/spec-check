#!/usr/bin/env python3
"""Pre-commit hook for the Design Compliance Checker.

Runs design-compliance checks against staged files before allowing a commit.
If any critical (tier A/B) requirement fails, the commit is blocked.

Install in a project:
  cp install-hook.sh /path/to/project/
  cd /path/to/project && ./install-hook.sh

Or manually add to .git/hooks/pre-commit:
  python3 /path/to/spec-check/pre_commit.py --root .
"""
import sys, subprocess, argparse, os
from pathlib import Path


def get_staged_files():
    """Return the list of files staged in the current git commit."""
    r = subprocess.run(["git", "diff", "--cached", "--name-only"],
                       capture_output=True, text=True)
    return [f for f in r.stdout.split("\n") if f.strip()]


def run_checks(root, staged_files):
    """Run the audit; return (results, critical_failures)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from server import run_audit_checks

    results = run_audit_checks(str(root))
    critical_failures = [
        r for r in results
        if r.get("status") == "fail" and r.get("tier") in ("A", "B")
    ]
    return results, critical_failures


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Project root")
    ap.add_argument("--allow-fail", action="store_true",
                    help="Warn instead of blocking (dry-run mode)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    staged = get_staged_files()

    if not staged:
        print("No staged files — nothing to check.")
        return 0

    print(f"Design compliance check — {len(staged)} staged file(s)")
    results, critical = run_checks(root, staged)

    for r in results:
        icon = {"pass":"✅","fail":"❌","warn":"⚠️"}.get(r.get("status"),"?")
        print(f"  {icon} [{r.get('tier')}] {r.get('id')}: {r.get('label')}")
        if r.get("detail"):
            print(f"     {r['detail']}")

    if critical and not args.allow_fail:
        print("\n❌ BLOCKED — critical design requirements failing:")
        for c in critical:
            print(f"  {c['id']}: {c['detail']}")
        print("\nFix the violations or use --allow-fail to commit anyway (not recommended).")
        return 1

    print("\n✅ OK — no critical violations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())