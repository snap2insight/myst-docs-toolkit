---
title: What it is
---

# What it is

`myst-docs-toolkit` is a small, opinionated repository of shared
infrastructure for [MyST](https://mystmd.org) documentation sites:

- A **template** (vendored `book-theme` pinned to a known commit).
- A **CSS overlay** that adds a few hero-style block kinds and the
  `{button}` role, and that makes mermaid diagrams look right in both
  light and dark mode.
- **Parts** (just a default footer for now) that consumers can override.
- **Plugins** (currently one: `myst-mermaid`) that fill specific gaps
  upstream MyST doesn't cover.

It is *not* a fork of MyST. It is *not* a theme. It is *not* a
framework. It sits next to your MyST projects and lets them share a
small set of files instead of copy-pasting them around.

## Who it's for

- Teams running **two or more MyST docs sites** in the same
  organization, who don't want to duplicate footer/CSS/plugin choices
  across N repos.
- Adopters of MyST who want a **worked reference layout** — a real
  example of how multi-repo MyST setups can be wired together.
- People who want **reproducible** MyST builds: with the toolkit
  pinning the `book-theme` commit, your site renders the same way today
  and three months from now.

## What it deliberately is not

- **Not a wiki tool.** MyST is the tool; this just configures it.
- **Not a multi-tenant SaaS** or hosted service. It's a vendored
  dependency in your repos.
- **Not org-coupled.** The toolkit itself contains no organization
  names, logos, or copy. Branding belongs in a separate org-private
  repo that layers on top.

## How it compares to alternatives

| Approach | Trade-off |
|---|---|
| Copy-paste CSS / footer into each docs repo | No shared improvements; drift |
| Submodule a shared repo | Same idea as the toolkit, but submodules trip up cloners and CI |
| npm-publish shared CSS / plugins | Workable; adds a JS-publish pipeline. The toolkit can become this later. |
| `extends:` chain across MyST projects | Doesn't span repos; only works within one project |
| **This toolkit** | Single source of truth checked out at build time, no committed copies in consumers |

## Pieces, briefly

The three layers a typical setup uses:

1. **myst-docs-toolkit** (this repo) — generic, public.
2. **Org-branding repo** (private) — your CSS, logos, footer.
3. **Per-site docs repos** — the actual content.

Sites pull (1) and optionally (2) at build time; (3) is what gets
edited day-to-day. See [the three-layer model](three-layer-model.md)
for details.
