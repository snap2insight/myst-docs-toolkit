---
title: MyST Docs Toolkit
site:
  hide_outline: true
  hide_toc: true
  hide_title_block: true
---

+++ { "kind": "split-image" }

Composable docs infrastructure for MyST.

# MyST Docs Toolkit

Templates, opinionated CSS, and plugins that fill the small gaps between
MyST and a polished published site — wired together so each docs repo
stays small and self-contained.

```{image} site-assets/images/hero-placeholder.svg
```

{button}`Get Started </intro/getting-started>`

+++ { "kind": "justified" }

## Why it exists

MyST gives you most of what you need to publish a serious docs site:
authoring in markdown, cross-references, deep-link previews, structured
output. But the last 10% — a hero-style landing, dark-mode-aware
mermaid diagrams, a place to share a footer across many sites — usually
gets reinvented per project.

This toolkit packages those bits so a new docs site is one workflow file
and one config away from looking finished.

## What's inside

- A pinned, vendored `book-theme` template — no surprises from upstream
  changes between builds.
- A small CSS overlay for landing-page block kinds (`.split-image`,
  `.justified`), the `{button}` role, and mermaid dual-theme toggling.
- A default footer; consumers can layer their own on top.
- A `myst-mermaid` plugin that pre-processes mermaid blocks for clean
  light/dark rendering.

## Who it's for

Teams running more than one MyST docs site and tired of copy-pasting
CSS, footers, and helper plugins. Also a useful reference if you're
adopting MyST and want a worked example of the moving pieces.
