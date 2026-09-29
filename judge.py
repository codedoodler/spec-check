#!/usr/bin/env python3
"""LLM-judge tier: walk every design requirement against a diff.

The deterministic checks (checks/ directory) cover ~5 machine-checkable
requirements. This module covers the REST — every requirement that needs
semantic judgment. For each requirement, an LLM reads the requirement's
What/Why/Check plus the code diff, and answers: "does this diff violate this
requirement?" — returning pass/fail/warn + evidence.

This is the "go through the list one by one" the tool exists to automate.

Usage:
  python3 judge.py --root /path/to/project --diff < diff.txt
  python3 judge.py --root /path/to/project --diff-file /tmp/pr.diff

Requires OPENROUTER_API_KEY or DEEPSEEK_API_KEY in the environment.
"""
import json, sys, os, argparse, re
from pathlib import Path

# Use the same LLM provider logic as the project. Prefer OpenRouter (shared key),
# fall back to direct DeepSeek.
def _llm_call(system, user):
    key = os.getenv("OPENROUTER_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if not key:
        return None

    if os.getenv("OPENROUTER_API_KEY"):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {key}", "HTTP-Referer": "https://spec-check.local"}
        model = os.getenv("SPEC_CHECK_MODEL", "deepseek/deepseek-chat")
    else:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {key}"}
        model = "deepseek-chat"

    import urllib.request
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.0,
    })
    req = urllib.request.Request(url, data=body.encode(), headers={**headers, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return None


JUDGE_SYSTEM = """You are a design-compliance judge. You are given a LIST of design requirements and a code diff.
For EACH requirement, decide whether the diff VIOLATES it. Return ONLY a JSON object mapping
requirement ID → {"status": "pass"|"fail"|"warn", "evidence": "<one sentence citing the specific change>"}.

Rules:
- "fail" = the diff clearly violates the requirement.
- "warn" = the diff is risky or the requirement's Check can't be confirmed from the diff alone.
- "pass" = the diff is consistent with the requirement (or doesn't touch it).
- Be specific. Cite the actual change. If the diff doesn't touch the requirement's concern,
  that's "pass" — but say why. Never "pass" a diff that silently removes a guard, gate, or
  provenance field the requirement demands.
"""

JUDGE_SYSTEM_FULL = """You are a design-compliance judge. You are given a LIST of design requirements and the FULL CURRENT SOURCE CODE of a system (not a change diff).
For EACH requirement, decide whether the CURRENT code VIOLATES it. Return ONLY a JSON object mapping
requirement ID → {"status": "pass"|"fail"|"warn", "evidence": "<one sentence citing the specific file/line>"}.

Rules:
- "fail" = the current code clearly violates the requirement.
- "warn" = the code is risky or the requirement's Check can't be confirmed from the code alone.
- "pass" = the code is consistent with the requirement.
- Be specific. Cite the actual file/line. Never "pass" code that lacks a guard, gate, or provenance field the requirement demands.
"""

BATCH_SIZE = 10


def _judge_batch(batch, diff, full=False):
    """Judge a batch of requirements in ONE LLM call. Returns dict id → result."""
    lines = []
    for req in batch:
        lines.append(
            f"[{req['id']}] {req['label']} (tier {req['tier']})\n"
            f"  WHAT: {req['what'] or req['label']}\n"
            f"  WHY: {req['why']}\n"
            f"  CHECK: {req['check']}\n"
        )
    user = "REQUIREMENTS:\n" + "\n".join(lines) + f"\nCODE DIFF:\n{diff}\n"
    out = _llm_call(JUDGE_SYSTEM_FULL if full else JUDGE_SYSTEM, user)
    if not out:
        return {req["id"]: {"status": "warn", "evidence": "LLM unavailable"} for req in batch}

    m = re.search(r'\{.*\}', out, re.DOTALL)
    if not m:
        return {req["id"]: {"status": "warn", "evidence": f"unparseable: {out[:80]}"} for req in batch}
    try:
        parsed = json.loads(m.group(0))
    except Exception:
        return {req["id"]: {"status": "warn", "evidence": f"bad JSON: {out[:80]}"} for req in batch}

    # Fill in any requirements the LLM missed
    result = {}
    for req in batch:
        if req["id"] in parsed and isinstance(parsed[req["id"]], dict):
            result[req["id"]] = {
                "status": parsed[req["id"]].get("status", "warn"),
                "evidence": parsed[req["id"]].get("evidence", "")
            }
        else:
            result[req["id"]] = {"status": "warn", "evidence": f"no verdict returned for {req['id']}"}
    return result


def judge_all(requirements, diff, ids=None, tier=None, full=False):
    """Judge all requirements in batches. Returns list of results."""
    eligible = []
    for req in requirements:
        if ids and req["id"] not in ids:
            continue
        if tier and req["tier"] != tier:
            continue
        if req["tier"] == "O" or req["status_flag"] == "superseded":
            continue
        if not req.get("check"):
            continue
        eligible.append(req)

    results = []
    for i in range(0, len(eligible), BATCH_SIZE):
        batch = eligible[i:i + BATCH_SIZE]
        verdicts = _judge_batch(batch, diff, full)
        for req in batch:
            v = verdicts[req["id"]]
            results.append({
                "id": req["id"], "label": req["label"], "tier": req["tier"],
                "status": v["status"], "evidence": v["evidence"],
            })
    return results


def main():
    ap = argparse.ArgumentParser(description="LLM-judge design compliance against a diff")
    ap.add_argument("--root", required=True, help="Project root (for requirement extraction)")
    ap.add_argument("--diff-file", help="Path to a .diff/.patch file")
    ap.add_argument("--diff", help="Inline diff text")
    ap.add_argument("--ids", help="Comma-separated requirement IDs to judge (default: all)")
    ap.add_argument("--tier", help="Only judge this tier")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    ap.add_argument("--full", action="store_true", help="Judge the FULL current code (current-state audit), not a change diff")
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from server import scan_requirements

    diff = ""
    if args.diff_file:
        diff = Path(args.diff_file).read_text()
    elif args.diff:
        diff = args.diff
    elif not sys.stdin.isatty():
        diff = sys.stdin.read()

    if not diff.strip():
        print("No diff provided. Use --diff-file, --diff, or pipe stdin.", file=sys.stderr)
        sys.exit(1)

    reqs = scan_requirements(args.root)
    ids = [x.strip() for x in args.ids.split(",")] if args.ids else None

    print(f"Judging {len(reqs)} requirements against a {len(diff)}-char diff…", file=sys.stderr)
    results = judge_all(reqs, diff, ids=ids, tier=args.tier, full=args.full)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        passed = sum(1 for r in results if r["status"] == "pass")
        warned = sum(1 for r in results if r["status"] == "warn")
        failed = sum(1 for r in results if r["status"] == "fail")
        print(f"DESIGN COMPLIANCE JUDGEMENT — {len(results)} requirements")
        print(f"PASS: {passed}  WARN: {warned}  FAIL: {failed}")
        print("-" * 60)
        for r in results:
            icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(r["status"], "?")
            print(f"{icon} [{r['tier']}] {r['id']}: {r['label']}")
            if r["evidence"]:
                print(f"   {r['evidence']}")
        print("-" * 60)
        print(f"PASS: {passed}  WARN: {warned}  FAIL: {failed}")


if __name__ == "__main__":
    main()