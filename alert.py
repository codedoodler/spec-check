#!/usr/bin/env python3
"""Alert module — post design-compliance failures to Linear (or a webhook).

Usage:
  python3 alert.py --root /path/to/project --linear-key $LINEAR_API_KEY --team ENG
  python3 alert.py --root /path/to/project --webhook https://hooks.slack.com/...

Behavior:
- Runs the regression detector.
- If regressions found, creates ONE Linear ticket per regression (or posts
  a summary to a webhook).
- If no regressions, stays silent (exit 0, no output).

This is the "somehow alert the user" piece — wire it to cron or CI.
"""
import json, sys, argparse, subprocess, os
from pathlib import Path


def linear_gql(key, query, variables=None):
    body = {"query": query}
    if variables: body["variables"] = variables
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", "https://api.linear.app/graphql",
         "-H", f"Authorization: {key}", "-H", "Content-Type: application/json",
         "-d", json.dumps(body)],
        capture_output=True, text=True
    )
    return json.loads(r.stdout)


def create_linear_ticket(key, team_key, title, description):
    """Create a Linear issue. Returns (identifier, url) or (None, error)."""
    teams = linear_gql(key, f'{{ teams(filter:{{key:{{eq:"{team_key}"}}}}) {{ nodes {{ id }} }} }}')
    nodes = teams.get("data", {}).get("teams", {}).get("nodes", [])
    if not nodes:
        return None, f"team {team_key} not found"
    team_id = nodes[0]["id"]

    result = linear_gql(key,
        "mutation($input: IssueCreateInput!) { issueCreate(input: $input) { success issue { identifier url } } }",
        {"input": {"teamId": team_id, "title": title, "description": description, "priority": 2}}
    )
    if result.get("data", {}).get("issueCreate", {}).get("success"):
        issue = result["data"]["issueCreate"]["issue"]
        return issue["identifier"], issue["url"]
    return None, str(result)


def post_webhook(url, payload):
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", url,
         "-H", "Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True, text=True
    )
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Project root")
    ap.add_argument("--linear-key", help="Linear API key (auto-ticket)")
    ap.add_argument("--team", default="", help="Linear team key (required for Linear tickets)")
    ap.add_argument("--webhook", help="Slack/Teams webhook URL (summary post)")
    ap.add_argument("--history", default=".audit-history.json")
    ap.add_argument("--dry-run", action="store_true", help="Print actions, don't execute")
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from regress import load_history, save_history
    from server import run_audit_checks

    prev = load_history(args.history)
    results = run_audit_checks(args.root)
    prev_checks = prev.get("checks", {})

    regressions = []
    for r in results:
        rid = r["id"]
        if rid in prev_checks and prev_checks[rid]["status"] == "pass" and r["status"] in ("fail", "warn"):
            regressions.append(r)

    save_history(args.history, results)

    if not regressions:
        return 0  # silent — nothing to alert

    # Build summary
    lines = [f"Design compliance regression in {args.root}"]
    for r in regressions:
        lines.append(f"- {r['id']}: {r.get('label','')} — {r['detail']}")
    summary = "\n".join(lines)

    if args.dry_run:
        print(summary)
        return 1

    # Linear tickets
    if args.linear_key:
        for r in regressions:
            title = f"Design regression: {r['id']} — {r.get('label','')[:60]}"
            desc = f"Requirement was passing, now failing.\n\n{r['detail']}\n\nDetected by spec-check."
            ident, url = create_linear_ticket(args.linear_key, args.team, title, desc)
            if ident:
                print(f"Created {ident}: {url}")
            else:
                print(f"Linear error: {url}")

    # Webhook summary
    if args.webhook:
        post_webhook(args.webhook, {"text": summary})

    return 1


if __name__ == "__main__":
    sys.exit(main())