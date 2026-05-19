---
title: Getting Started
---

# Getting Started

Below is the fastest path from "I have a MyST docs repo" to "it's
using this toolkit's template, CSS, and footer." About five minutes.

## Prerequisites

- A MyST project (anything with a `myst.yml`).
- `git` and a way to install MyST locally (`npm install -g mystmd` or
  equivalent).
- For local symlink mode: a sibling clone of this toolkit repo. Optional.

## 1. Set up `shared-theme.yml`

In your docs repo's root, create a `shared-theme.yml`:

```yaml
version: 1
site:
  template: _toolkit/templates/book-theme
  options:
    logo: site-assets/images/logo.svg          # your site's own logo
    favicon: site-assets/images/favicon.svg
    style: _toolkit/css/site.css
    hide_authors: true
  parts:
    footer: _toolkit/parts/footer.md
```

## 2. Wire it into `myst.yml`

```yaml
version: 1
extends:
  - toc.yml
  - shared-theme.yml

project:
  id: my-site
  title: "My Site"
  authors:
    - name: My Org

site:
  options:
    hover_xref: true
```

## 3. Ignore the vendored directory

Add to `.gitignore`:

```
_toolkit
_build/
```

## 4. Drop in `bin/setup-dev.sh`

A small script that creates `_toolkit/` on demand. Two modes — pick
whichever fits:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Symlink mode (preferred if you have a local clone as a sibling)
if [ -n "${TOOLKIT_LOCAL:-}" ]; then
  rm -rf _toolkit
  ln -s "$(cd "$TOOLKIT_LOCAL" && pwd)" _toolkit
  echo "✅ Linked _toolkit → $TOOLKIT_LOCAL"
  exit 0
fi

# Clone mode
TOOLKIT_URL="${TOOLKIT_URL:-https://github.com/snap2insight/myst-docs-toolkit.git}"
TOOLKIT_REF="${TOOLKIT_REF:-main}"
rm -rf _toolkit
git clone --depth 1 --branch "$TOOLKIT_REF" --recurse-submodules \
  "$TOOLKIT_URL" _toolkit
echo "✅ Cloned _toolkit"
```

Make it executable: `chmod +x bin/setup-dev.sh`.

Run it once: `./bin/setup-dev.sh` (or
`TOOLKIT_LOCAL=../myst-docs-toolkit ./bin/setup-dev.sh` if you have a
sibling clone).

## 5. Build

```bash
myst build --html
```

That's it. Your site now uses the toolkit's template, the shared CSS
overlay, and the default footer.

## 6. Deploy to GitHub Pages

Use [this workflow](https://github.com/snap2insight/myst-docs-toolkit/blob/main/.github/workflows/docs-deploy.yml)
as a starting template, adjusted to fetch the toolkit at build time:

```yaml
- uses: actions/checkout@v5
  with:
    repository: snap2insight/myst-docs-toolkit
    ref: main
    path: _toolkit
    submodules: true
```

The `submodules: true` is important — it pulls the book-theme submodule
into `_toolkit/templates/book-theme/`. Skip it and your build will fail
to find the template.

## Next steps

- [Three-layer model](three-layer-model.md) — how the toolkit, branding,
  and per-site docs fit together.
- [Capabilities](../capabilities/overview.md) — what the toolkit
  actually provides.
- [myst-mermaid plugin](../plugins/myst-mermaid.md) — opt in for
  dual-theme mermaid rendering.
