# myst-docs-toolkit

Composable docs infrastructure for [MyST](https://mystmd.org): a pinned
book-theme template, opinionated CSS, parts, and plugins that several
docs sites in the same org can share.

## What it is

| Piece | Role |
|---|---|
| [`templates/book-theme/`](https://github.com/snap2insight/myst-docs-toolkit/tree/main/templates) | Vendored `myst-templates/book-theme`, pinned via `.toolkit-version`. Sites reference this instead of fetching from the MyST registry, so builds are reproducible. |
| [`css/site.css`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/css/site.css) | CSS overlay for landing-page block kinds (`.split-image`, `.justified`), the `{button}` role, footer grid, and mermaid dual-theme toggling. |
| [`parts/footer.md`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/parts/footer.md) | Minimal default footer. Consumers override by pointing at their own. |
| [`plugins/myst-mermaid/`](https://github.com/snap2insight/myst-docs-toolkit/tree/main/plugins/myst-mermaid) | Python MyST plugin: pre-renders mermaid blocks in light + dark variants. |
| [`bin/sync.sh`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/bin/sync.sh) | Optional vendor-by-copy helper for environments that can't use symlinks or fresh clones. |

## How a docs site consumes it

A consuming docs site sets up a `_toolkit/` directory at its repo root
that points at a checkout of this repo (either via symlink to a local
clone, or via `actions/checkout` in CI). The site's `shared-theme.yml`
then references theme assets through stable paths:

```yaml
site:
  template: _toolkit/templates/book-theme
  options:
    style:  _toolkit/css/site.css
  parts:
    footer: _toolkit/parts/footer.md
```

This means `_toolkit/` itself is **never committed** into a docs repo
— it's populated at build time. Bumping the toolkit version is a one-
line change in the consuming repo's workflow.

See [Getting Started](intro/getting-started.md) for the full bootstrap
flow, or jump to [the three-layer model](intro/three-layer-model.md)
for the architecture.

## Status

Active. Latest release: `main`. License: MIT.

Upstream source:
[github.com/snap2insight/myst-docs-toolkit](https://github.com/snap2insight/myst-docs-toolkit).
