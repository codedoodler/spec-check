#!/usr/bin/env bash
# Install the leak-guard pre-push hook into this clone.
#
#   ./scripts/install-hooks.sh
#
# The hook refuses a push if the tree carries internal markers or secret-shaped
# strings (see scripts/leak_guard.py). Hooks are not versioned by git, so run
# this once per clone.
set -e
ROOT="$(git rev-parse --show-toplevel)"
mkdir -p "$ROOT/.git/hooks"
cat > "$ROOT/.git/hooks/pre-push" <<'EOF'
#!/usr/bin/env bash
exec python3 "$(git rev-parse --show-toplevel)/scripts/leak_guard.py"
EOF
chmod +x "$ROOT/.git/hooks/pre-push"
echo "✓ installed pre-push leak guard at $ROOT/.git/hooks/pre-push"
