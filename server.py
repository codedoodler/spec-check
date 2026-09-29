#!/usr/bin/env python3
"""Design Compliance Checker — portable HTTP server.

Usage:
  python3 server.py --root /path/to/project
  python3 server.py --root /path/to/project --port 8091

Then open http://localhost:8090 to browse requirements and run audits.

How it works:
- Scans the project root for design documents (requirements-hierarchy.md,
  AGENTS.md, .cursorrules, meeting notes with [REQ] tags).
- Extracts requirements with What/Why/Check/Source + provenance.
- Runs audits from check files in the project's checks/ directory.
- Serves a self-contained checker UI at /.
"""
import http.server, json, subprocess, os, sys, urllib.parse, re, argparse
from pathlib import Path
from collections import OrderedDict

PORT = 8090


# ── Generic requirement extraction ──

TOPIC_KEYWORDS = OrderedDict([
    ("api",           ["api", "endpoint", "route", "handler", "controller", "request", "response"]),
    ("data",          ["data", "database", "schema", "store", "persistence", "migration", "table"]),
    ("logic",         ["business", "algorithm", "calculation", "compute", "formula", "rule"]),
    ("integration",   ["integration", "external", "client", "third-party", "webhook", "service"]),
    ("validation",    ["validator", "validation", "guardrail", "constraint", "invariant", "gate"]),
    ("observability", ["observability", "trace", "tracer", "logging", "span", "metric", "monitor"]),
    ("security",      ["security", "auth", "secret", "credential", "permission", "token", "encrypt"]),
    ("testing",       ["test", "eval", "claim", "golden", "regression", "pytest", "fixture", "assert"]),
    ("process",       ["process", "review", "ticket", "cadence", "workflow", "documentation", "convention"]),
])

def classify_topic(text, label):
    combined = (label + " " + text).lower()
    scores = {t: sum(1 for kw in kws if kw in combined) for t, kws in TOPIC_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "process"


def extract_requirements_from_md(text):
    """Parse a markdown file for requirements in the standard hierarchy format."""
    items = []
    pattern = re.compile(
        r'^(#{3,4})\s+([A-Z][-A-Za-z0-9]+)\s+·\s+(\S+)\s+·\s+(\S+)\s+—\s+(.+?)$',
        re.MULTILINE
    )
    for m in pattern.finditer(text):
        hashes, rid, importance, status, label = m.groups()
        tier = (rid.split("-", 1)[0][:1].upper() or "M")
        if tier not in "ABCDOM": tier = "M"

        start = m.end()
        end_block = len(text)
        for sep in ["\n---", "\n### ", "\n#### "]:
            idx = text.find(sep, start)
            if idx != -1 and idx < end_block:
                end_block = idx
        block = text[start:end_block]

        what = re.search(r'-\s+\*\*What:\*\*\s*(.+?)$', block, re.MULTILINE)
        why  = re.search(r'-\s+\*\*Why:\*\*\s*(.+?)$', block, re.MULTILINE)
        check = re.search(r'-\s+\*\*Check:\*\*\s*(.+?)$', block, re.MULTILINE)
        source_raw = re.search(r'-\s+\*\*Source:\*\*\s*(.+?)$', block, re.MULTILINE)
        source = source_raw.group(1).strip() if source_raw else ""

        who = ""; when = ""
        if source:
            parts = source.split(",", 1)
            who_match = re.match(r'^[\w\s]+(?:\s*\([^)]+\))?', parts[0].strip())
            if who_match: who = who_match.group(0).strip()
            if len(parts) > 1:
                dm = re.search(r'(Sep|Aug|Jul|Jun|Oct|Nov|Dec)\s+\d{1,2}', parts[1])
                when = dm.group(0) if dm else parts[1][:40]

        topic = classify_topic(block, label)

        items.append({
            "id": rid, "tier": tier, "topic": topic,
            "label": label.strip(),
            "importance": {"🔴":"critical","🟠":"high","🟡":"medium","⚪":"low"}.get(importance, importance),
            "status_flag": {"✅":"addressed","◐":"partial","○":"open","🗑":"superseded","⏳":"deferred"}.get(status, status),
            "what": what.group(1).strip() if what else "",
            "why": why.group(1).strip() if why else "",
            "check": check.group(1).strip() if check else "",
            "source": source, "who": who, "when": when,
        })
    return items


def extract_requirements_from_agents(text, filename):
    """Extract requirements from AGENTS.md / CLAUDE.md / .cursorrules files."""
    items = []
    # Every paragraph that starts with a capital and contains "must"/"should"/"always"/"never"
    lines = text.split("\n")
    buf = ""; rid_counter = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            if buf and any(w in buf.lower() for w in ["must","should","always","never","do not"]):
                rid_counter += 1
                items.append({
                    "id": f"AG-{rid_counter:02d}", "tier": "B", "topic": "process",
                    "label": buf[:120], "importance": "high", "status_flag": "addressed",
                    "what": buf, "why": f"From {filename}", "check": "Manual review",
                    "source": filename, "who": "", "when": "",
                })
            buf = ""
            continue
        if buf: buf += " " + stripped
        else: buf = stripped
    return items


def scan_requirements(root):
    """Scan a project root for all requirement sources and return consolidated list."""
    all_items = []
    root = Path(root)

    # 1+2. Requirement documents — any file named like a spec/requirements doc,
    #      discovered anywhere the project keeps them.
    candidates = set()
    for base in (root, root / "docs", root / "spec"):
        if base.is_dir():
            candidates.update(base.glob("*.md"))
            candidates.update(base.rglob("*requirement*.md"))
    for f in sorted(candidates):
        low = f.name.lower()
        if "requirement" in low or low in ("spec.md", "specification.md"):
            all_items.extend(extract_requirements_from_md(f.read_text()))

    # 3. AGENTS.md / CLAUDE.md / .cursorrules (conventions as requirements)
    for name in ["AGENTS.md", "CLAUDE.md", ".cursorrules"]:
        f = root / name
        if f.exists():
            all_items.extend(extract_requirements_from_agents(f.read_text(), name))

    # 4. Meeting notes with [REQ] tags
    meetings_dir = root / "docs" / "meetings"
    if meetings_dir.exists():
        for f in sorted(meetings_dir.glob("*.md"))[-20:]:  # most recent 20
            text = f.read_text()
            reqs = re.findall(r'\[REQ\]\s*(.+?)(?:\n|$)', text)
            for i, r in enumerate(reqs):
                all_items.append({
                    "id": f"M-{f.stem[:8]}-{i+1:02d}",
                    "tier": "D", "topic": "process",
                    "label": r[:120], "importance": "medium",
                    "status_flag": "open",
                    "what": r, "why": f"From meeting: {f.name}",
                    "check": "Manual review",
                    "source": f"docs/meetings/{f.name}", "who": "", "when": "",
                })

    return all_items


# ── Audit runner ──

def run_audit_checks(root, tier=None, ids=None):
    """Run check files from BOTH the tool's checks/ and the project's checks/ (if any)."""
    tool_checks = Path(__file__).resolve().parent / "checks"
    project_checks = Path(root) / "checks"
    check_dirs = [tool_checks]
    if project_checks.exists():
        check_dirs.append(project_checks)

    if not tool_checks.exists() and not project_checks.exists():
        return [{"id":"system","label":"no checks directory","tier":"-",
                 "status":"warn","detail":f"No checks/ directory found. Create one with check scripts."}]

    results = []
    for checks_dir in check_dirs:
        if not checks_dir.exists():
            continue
        for check_file in sorted(checks_dir.glob("check_*.py")):
            try:
                ns = {}
                exec(check_file.read_text(), ns)
                if "run" in ns:
                    for result in ns["run"](str(root)):
                        if tier and result.get("tier") != tier: continue
                        if ids and result.get("id") not in ids: continue
                        results.append(result)
            except Exception as e:
                results.append({
                    "id": check_file.stem, "label": f"check error: {check_file.name}",
                    "tier": "-", "status": "fail", "detail": str(e)[:100]
                })
    return results


# ── HTTP server ──

def make_handler(root, static_dir):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            params = urllib.parse.parse_qs(parsed.query)

            if path == "/api/requirements":
                reqs = scan_requirements(root)
                self._json(reqs)

            elif path == "/api/audit":
                tier = params.get("tier", [None])[0]
                ids_param = params.get("ids", [None])[0]
                ids_list = None
                if ids_param:
                    ids_list = [x.strip() for x in ids_param.split(",")]
                results = run_audit_checks(root, tier=tier, ids=ids_list)
                self._json(results)

            elif path == "/" or path == "/index.html":
                html = (Path(static_dir) / "index.html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html)

            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not found")

        def _json(self, data):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        def log_message(self, format, *args):
            pass

    return Handler


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Design Compliance Checker server")
    ap.add_argument("--root", required=True, help="Project root directory to audit")
    ap.add_argument("--port", type=int, default=PORT, help=f"Port (default: {PORT})")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"ERROR: root path does not exist: {root}")
        sys.exit(1)

    static_dir = Path(__file__).resolve().parent / "static"
    reqs = scan_requirements(str(root))

    print(f"Design Compliance Checker — http://localhost:{args.port}")
    print(f"  Root: {root}")
    print(f"  Requirements found: {len(reqs)}")
    print(f"  Static: {static_dir}")
    print(f"Press Ctrl+C to stop")

    Handler = make_handler(str(root), str(static_dir))
    server = http.server.HTTPServer(("0.0.0.0", args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")