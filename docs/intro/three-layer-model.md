---
title: Three-layer Model
---

# Three-layer Model

The toolkit fits into a three-layer architecture for docs in an
organization that runs more than one MyST site.

| Layer | Scope | Typical visibility |
|---|---|---|
| 1. **Generic toolkit** | This repo. Template, CSS overlay, parts, plugins. No org content. | Public (contribute back) |
| 2. **Org branding** | Brand colors, logos, footer copy. | Private |
| 3. **Per-site docs** | The actual content of each docs site. | Per-site |

A site at layer 3 consumes layer 1 at build time, and *optionally* layer
2 if it's an internal/branded site. A purely community-facing site
(this docs site, for example) consumes only layer 1.

## What goes where

| Concern | Layer | Why |
|---|---|---|
| Template (book-theme) | 1 | Same theme for everyone in the org; pin upgrades centrally |
| Generic CSS (block kinds, button, mermaid toggling) | 1 | Same intent across sites; layer 2 only overrides what's specifically branded |
| Default footer (`Built with MyST`) | 1 | Fallback for unbranded sites |
| Brand colors, custom fonts | 2 | Org-specific; never leak into a public toolkit |
| Branded footer (`© My Org 2026`) | 2 | Per-org copy |
| Logos / favicon / hero artwork | 3 | Per-site (a strategy doc and an eng portal may differ) |
| Site content, TOC, landing page | 3 | The actual writing |

## Why the split

- **Layer 1 stays small and contributable.** No org-specific decisions
  live here, so the toolkit can be shared with the wider MyST community
  without a fork.
- **Layer 2 is the only thing that's private.** When the toolkit is
  open-sourced, your branding stays out of sight.
- **Layer 3 stays focused on writing.** Each docs site doesn't carry
  shared infrastructure as committed bytes — it pulls layers 1 and 2 at
  build time.

## At build time

Inside a layer-3 docs site:

```
my-docs-site/
├── _toolkit/        ← gitignored. Symlink or clone of layer 1.
├── _branding/       ← gitignored. Symlink or clone of layer 2 (private sites only).
├── shared-theme.yml ← references _toolkit/ and optionally _branding/
├── myst.yml
├── toc.yml
└── ...content
```

A public docs site uses only `_toolkit/`. A private/internal site uses
both `_toolkit/` and `_branding/`, with `_branding/` providing the
override styles and the company-specific footer.

## What this isn't

- It's not a hard requirement. A team running just one MyST site can
  fold layers 1 and 2 into the docs repo itself. The split pays off
  starting at two or three sites.
- It's not a layering of CSS cascade rules. Layer 2's CSS doesn't have
  to import layer 1 — sites typically include both files via separate
  `site.options.style` entries and let the browser handle order.

The CONVENTION at the docs-tree root in any consuming setup typically
spells out which directories play which roles.
