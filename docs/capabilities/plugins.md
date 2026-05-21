---
title: Plugins
---

# Plugins

The toolkit ships MyST plugins under
[`plugins/`](https://github.com/snap2insight/myst-docs-toolkit/tree/main/plugins).
Each is a standalone subdirectory with its own README and (when
relevant) configuration schema.

## Current plugins

| Plugin | What it does | Delivery |
|---|---|---|
| [`myst-mermaid`](../plugins/myst-mermaid.md) | Pre-processes mermaid blocks into light + dark variants so diagrams render correctly in both themes. | Executable plugin (Python) via `project.plugins` |
| [`myst-figure-viewer`](../plugins/myst-figure-viewer.md) | Adds an interactive zoom / pan / fullscreen overlay to mermaid diagrams, `<figure>` blocks, and standalone images. | Runtime JS via `{anywidget}` directive in `parts/footer.md` |

## How a site enables a plugin

There are two enablement paths depending on the plugin's delivery model.

**Executable / JavaScript plugins** — listed in `project.plugins` of `myst.yml`:

```yaml
project:
  plugins:
    - type: executable
      path: _toolkit/plugins/myst-mermaid/plugin.py
```

The plugin runs at *build time* and transforms the AST. `myst-mermaid`
uses this path.

**Runtime widget plugins** — embedded via the `{anywidget}` directive
in a parts file (typically `parts/footer.md` for site-wide effect):

````markdown
```{anywidget} _toolkit/plugins/myst-figure-viewer/viewer.esm.js
```
````

The plugin runs at *page-load time* as a JS module the browser executes.
`myst-figure-viewer` uses this path because the features it adds
(modal, drag-to-pan, zoom) need to react to user input — they can't be
baked into a static AST transform.

Both styles live alongside each other in `_toolkit/plugins/` and are
inspectable as plain source.

## Plugin types

MyST supports several plugin shapes:

- **Executable plugins** — written in any language that can read JSON
  from stdin and write JSON to stdout. Load via
  `type: executable, path: ...`. `myst-mermaid` uses this.
- **JavaScript plugins** — TypeScript / JS modules registered for
  build-time transforms, directives, and roles. Load via
  `type: javascript, path: ...`.
- **Runtime widgets via `{anywidget}`** — ESM JS modules that execute
  in the browser. Loaded by MyST's anywidget integration; book-theme
  mounts each widget instance inside a shadow-DOM container.
  `myst-figure-viewer` uses this.

See the [MyST plugin docs](https://mystmd.org/guide/external-plugins) for
the build-time protocol details, and
[`myst-figure-viewer`](../plugins/myst-figure-viewer.md) for the runtime
pattern.

## Why ship plugins separately rather than baking into the template

- **Opt-in.** Not every site wants dual-theme mermaid; not every site
  uses mermaid at all. Plugins shouldn't be implicit.
- **Inspectable.** A consuming docs repo can read the plugin source in
  `_toolkit/plugins/<name>/` — no NPM black box.
- **Pinned with the toolkit.** When you bump the toolkit, you bump
  plugins too. No drift between template and plugin versions.

## Planned

Possible future plugins:

- A frontmatter validator for shared schemas (e.g., classification labels).
- A pre-built abbreviation list importer.
- A "last reviewed" date stamper.

If you have a concrete need, see [Adding a plugin](../contributing/adding-plugins.md).
