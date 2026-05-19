---
title: Design Decisions
---

# Design Decisions

A short record of the non-obvious choices baked into the toolkit and
why each was made. Useful as context if you're forking or extending.

## Vendor book-theme rather than use the registry

**Decision:** ship `templates/book-theme/` as a git submodule pinned via
`.toolkit-version`, and have consumer sites reference it by local path
(`_toolkit/templates/book-theme`) rather than by name (`book-theme`).

**Why:** MyST's by-name template fetch hits `api.mystmd.org` and
downloads the latest matching template at build time. Convenient but:
non-reproducible across time, and broken on air-gapped builds. Vendoring
solves both. See [Templates](../capabilities/templates.md).

## Gitignore `_toolkit/` in consumer repos

**Decision:** consumers' `.gitignore` always excludes `_toolkit/`
(symlink or directory). The toolkit is fetched at build time, not
committed.

**Why:** committed vendoring works but introduces drift between sites
and bloats the docs repos. Workflow-time fetch keeps each docs repo
small and ensures every build sees the same toolkit at the pinned ref.
See [Vendoring Modes](vendoring-modes.md).

## Two pin levels — toolkit ref + book-theme submodule SHA

**Decision:** consumers pin a toolkit ref; the toolkit independently
pins a book-theme commit. Bumping book-theme is a deliberate toolkit
commit.

**Why:** decouples the consumer's experience from upstream surprises.
A consumer pinned to `v1.0` keeps rendering the same way even if
book-theme ships a breaking change tomorrow.

## Three-layer split (toolkit / branding / sites)

**Decision:** generic toolkit stays separate from org-specific branding,
which stays separate from per-site content. See
[Three-layer model](../intro/three-layer-model.md).

**Why:** the toolkit can be open source while branding stays private.
Sites stay focused on writing. Adding a new site is one branding +
toolkit reference, not copy-pasting infrastructure.

## Plugins are inspectable Python files, not opaque packages

**Decision:** the `myst-mermaid` plugin is a single Python file in
`plugins/myst-mermaid/plugin.py`, not a `pip`-installed package.

**Why:** anyone consuming the toolkit can `cat plugins/myst-mermaid/plugin.py`
and see exactly what's running. No supply-chain surprises from a
third-party package. The trade-off is that contributors edit it
inline; if the plugin grows substantially we can split it into modules,
but at ~250 lines today, one file is the right size.

## Block-kind hero (split-image / justified) over a custom directive

**Decision:** the landing-page hero uses MyST's built-in `+++ {"kind":...}`
block-break marker, with CSS styled to it. Not a custom `{hero}`
directive.

**Why:** keeps the toolkit's surface area smaller. Block-kind metadata
is a stable MyST primitive; a custom directive would need a JS plugin
to register it. CSS is enough.

## Mermaid plugin emits two AST nodes, not one styled node

**Decision:** `myst-mermaid` rewrites each mermaid block into a
container with two children — one for the light variant, one for the
dark variant. CSS hides whichever doesn't match the active theme.

**Why:** Mermaid renders client-side from the config embedded in each
block. To get a *different* render in dark mode we need a *different*
config, hence two blocks. The CSS-only alternative (one block, restyled
via CSS variables) doesn't work because mermaid bakes colors into the
generated SVG at render time. See the
[plugin internals](../plugins/myst-mermaid.md#how-it-works-inside).

## MIT license

**Decision:** MIT for the toolkit (CSS, plugin, sync scripts). CC BY 4.0
is suggested for downstream docs *content*; that's a per-docs-repo
choice.

**Why:** lowest-friction permissive license. Allows commercial use,
modification, and redistribution; only requires attribution. Compatible
with both the MyST community's licensing patterns and most enterprise
adoption requirements.

## Things considered and *not* adopted

- **Submodules in consumer repos.** Forgotten `--recurse-submodules`
  is a real-world papercut. Workflow-time fetch is cleaner.
- **NPM-publish the toolkit.** Possible later, especially if we add JS
  plugins. The Python plugin and the bare CSS file don't currently
  benefit from a JS distribution channel.
- **A "starter template" GitHub repo.** Would be nice; on the roadmap.
  For now, the [Getting Started](../intro/getting-started.md) page is
  the closest thing.

## Open questions

These aren't decided yet — feedback welcome.

- Should the toolkit publish to MyST's template registry under a
  different name (e.g., `book-theme-extras`)? That gives consumers a
  by-name option for the CSS overlay, at the cost of running another
  distribution channel.
- Should the `myst-mermaid` plugin ship its own minimal CSS rather than
  rely on the toolkit's `site.css`? Would let it be used outside the
  toolkit, at the cost of duplication when used together.
- A JS port of `myst-mermaid` (so the plugin doesn't require Python)?
  Worthwhile if a contributor wants to take it on.
