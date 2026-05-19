---
title: Plugins
---

# Plugins

The toolkit ships MyST plugins under
[`plugins/`](https://github.com/snap2insight/myst-docs-toolkit/tree/main/plugins).
Each is a standalone subdirectory with its own README and (when
relevant) configuration schema.

## Current plugins

| Plugin | What it does | Type |
|---|---|---|
| [`myst-mermaid`](../plugins/myst-mermaid.md) | Pre-processes mermaid blocks into light + dark variants so diagrams render correctly in both themes. | Executable (Python) |

## How a site enables a plugin

In `myst.yml`:

```yaml
project:
  plugins:
    - type: executable
      path: _toolkit/plugins/myst-mermaid/plugin.py
```

The plugin file lives inside the vendored `_toolkit/` directory, so
contributors don't have to install anything extra to use it — beyond
the plugin's own runtime dependencies, documented on its page.

## Plugin types

MyST supports two kinds of plugin:

- **JavaScript plugins** — for transforms, directives, and roles. Load
  via `type: javascript, path: ...`.
- **Executable plugins** — for plugins written in any language that can
  read JSON from stdin and write JSON to stdout. Load via
  `type: executable, path: ...`. This is what the toolkit's current
  plugin uses (Python).

See the [MyST plugin docs](https://mystmd.org/guide/external-plugins) for
the protocol details.

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
