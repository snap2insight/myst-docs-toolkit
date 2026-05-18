#!/usr/bin/env bash
# sync.sh — vendor myst-docs-toolkit assets into a docs site.
#
# Copies the toolkit's CSS, parts, and version pin into <target>/_toolkit/
# so the site is standalone-buildable (no relative paths into another repo).
#
# The site template itself is pulled by name (`template: book-theme` in
# shared-theme.yml), so we don't vendor the heavy book-theme bundle.
#
# Usage:
#   ./bin/sync.sh <target-site-dir>
#
# Examples:
#   # From monorepo, vendor toolkit into the EKA spec:
#   public/myst-docs-toolkit/bin/sync.sh public/enterprise-knowledge-architecture
#
#   # After repo-split, vendor latest toolkit into a docs repo:
#   git clone https://github.com/{org}/myst-docs-toolkit /tmp/toolkit
#   /tmp/toolkit/bin/sync.sh .

set -euo pipefail

TOOLKIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:?usage: $0 <target-site-dir>}"

if [ ! -d "$TARGET" ]; then
  echo "❌ Target directory does not exist: $TARGET" >&2
  exit 1
fi

DEST="$TARGET/_toolkit"
mkdir -p "$DEST/css" "$DEST/parts"

cp -f "$TOOLKIT_ROOT/css/site.css"      "$DEST/css/site.css"
cp -f "$TOOLKIT_ROOT/parts/footer.md"   "$DEST/parts/footer.md"

# Pin the toolkit version so the consuming repo can tell what's installed.
if [ -f "$TOOLKIT_ROOT/.toolkit-version" ]; then
  cp -f "$TOOLKIT_ROOT/.toolkit-version" "$DEST/.toolkit-version"
fi

# Drop a marker README so anyone browsing the docs repo understands what
# this directory is and how to update it.
cat > "$DEST/README.md" <<'EOF'
# _toolkit (vendored)

This directory is **vendored** from the myst-docs-toolkit project. Do
not edit files here directly — edits will be overwritten the next time
the sync script runs.

To update to a newer toolkit release:

```bash
# Either reuse the vendored script from a clone of the toolkit repo:
git clone https://github.com/{org}/myst-docs-toolkit /tmp/toolkit
/tmp/toolkit/bin/sync.sh .

# Or pull a specific version:
git -C /tmp/toolkit checkout v1.4.0
/tmp/toolkit/bin/sync.sh .
```

The `.toolkit-version` file records the upstream commit currently
vendored. Commit changes to `_toolkit/` together with the version bump.
EOF

echo "✅ Synced toolkit into $DEST/"
echo "   - css/site.css"
echo "   - parts/footer.md"
[ -f "$DEST/.toolkit-version" ] && echo "   - .toolkit-version ($(cat "$DEST/.toolkit-version" | head -c 12))"
