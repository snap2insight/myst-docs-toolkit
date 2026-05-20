# plugins/

MyST plugins bundled with the toolkit. Each subdirectory is one plugin
that consuming docs sites can opt into via their `myst.yml`.

## Current plugins

| Plugin | What it does |
|---|---|
| [`myst-mermaid/`](myst-mermaid/) | Dual-theme rendering for Mermaid diagrams — emits light + dark variants per block; companion CSS in `css/site.css` toggles visibility based on the page's color scheme. |
| [`myst-figure-viewer/`](myst-figure-viewer/) | Interactive zoom, pan, and fullscreen for figures and Mermaid diagrams — delivered as a zero-dependency ESM widget via MyST's `{anywidget}` directive. |

## How a docs site enables a plugin

In `myst.yml`:

```yaml
project:
  plugins:
    - type: executable
      path: _toolkit/plugins/myst-mermaid/plugin.py
```

`_toolkit/` is the symlink (or clone) of this toolkit repo that
the docs site sets up via `bin/setup-dev.sh` or its deploy workflow.
See [`/CONVENTION.md`](https://github.com/snap2insight/myst-docs-toolkit)
in a consuming repo for details.
