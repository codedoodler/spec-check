#!/usr/bin/env bash
# Install the Design Compliance pre-commit hook into a project.
# Usage: ./install-hook.sh /path/to/project
set -e

CHECKER_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="${1:-.}"

if [ ! -d "$PROJECT/.git" ]; then
  echo "ERROR: $PROJECT is not a git repository"
  exit 1
fi

HOOK="$PROJECT/.git/hooks/pre-commit"

cat > "$HOOK" << EOF
#!/usr/bin/env bash
# Design Compliance pre-commit hook (installed by spec-check)
python3 "$CHECKER_DIR/pre_commit.py" --root "$PROJECT"
EOF

chmod +x "$HOOK"
echo "✓ Installed pre-commit hook at $HOOK"
echo "  It runs: python3 $CHECKER_DIR/pre_commit.py --root $PROJECT"
echo "  To skip a commit: git commit --no-verify"