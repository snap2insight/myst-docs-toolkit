---
title: Overview
---

# Capabilities

The toolkit ships four kinds of artifact. Each is independently
opt-in — your site can use the template only, or the CSS only, or
just the mermaid plugin.

| Capability | Provides | Page |
|---|---|---|
| **Template** | The `book-theme` MyST template, vendored and pinned. | [Templates](templates.md) |
| **Styling** | CSS rules for `.split-image`, `.justified`, `{button}`, the footer grid, and mermaid dual-theme toggling. | [Styling](styling.md) |
| **Parts** | A default footer that consumers can override. | [Parts](parts.md) |
| **Plugins** | Currently `myst-mermaid` (dual-theme rendering). More planned. | [Plugins](plugins.md) |

## How a site picks and chooses

A site uses each capability by referencing the corresponding file in
its `shared-theme.yml` and `myst.yml`. There's nothing all-or-nothing
about it.

Use the template + CSS only:

```yaml
site:
  template: _toolkit/templates/book-theme
  options:
    style: _toolkit/css/site.css
```

Add the default footer:

```yaml
site:
  parts:
    footer: _toolkit/parts/footer.md
```

Enable the mermaid plugin:

```yaml
project:
  plugins:
    - type: executable
      path: _toolkit/plugins/myst-mermaid/plugin.py
```

## What's *not* a capability

- The toolkit doesn't ship logos, brand colors, fonts, or copy. That
  belongs in a separate branding repo (layer 2 in the
  [three-layer model](../intro/three-layer-model.md)).
- The toolkit doesn't ship CI workflows for consumers. There's a
  reference deploy workflow in the docs of consuming sites, but each
  site owns its own.
- The toolkit doesn't ship docs content (other than its own). It is
  infrastructure, not boilerplate.
