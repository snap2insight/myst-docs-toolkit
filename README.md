# myst-docs-toolkit

A generic, org-agnostic MyST documentation toolkit: vendored book-theme,
default styling for landing-page block kinds and roles, and a minimal
default footer. Designed for any project building a MyST docs site —
no company branding inside.

Planned future home: a separate public repo `myst-docs-toolkit`,
intended for contribution back to the MyST community.

In the current monorepo this lives under `docs/public/` (sibling to
the EKA spec) and is consumed by sites elsewhere in the tree via
relative paths in their `shared-theme.yml`.

See [`/docs/CONVENTION.md`](../../CONVENTION.md) for the full
three-layer architecture (toolkit / branding / individual sites) and
the bootstrap convention.

## Layout

```
myst-docs-toolkit/
├── README.md                       — this file
├── .toolkit-version                — pins the upstream book-theme commit
├── templates/
│   └── book-theme/                 — vendored clone of myst-templates/book-theme
├── css/
│   └── site.css                    — generic site styling (block kinds, button, footer)
└── parts/
    └── footer.md                   — generic default footer ("Built with MyST")
```

## What's covered today

- **Template** — vendored `book-theme` upstream, pinned via
  `.toolkit-version`.
- **CSS** — styling for the landing-page block kinds
  (`.split-image`, `.justified`), the `{button}` role, and the footer
  grid. No brand colors, fonts, or logos.
- **Footer** — a minimal "Built with MyST" default. Sites that want
  branded footers reference their own (provided by the consuming
  organization, layered on top of the toolkit).

## What will be added at split time

When this becomes a real repo:

- `plugins/` — MyST plugins (mermaid transforms, frontmatter validators).
- `starter/` — scaffolding template files (`myst.yml.template`,
  `toc.yml.template`, etc.) for new docs sites.
- `bin/init-site.sh` — scaffolds a new docs site from `starter/`.
- `bin/sync-toolkit.sh` — pulls a toolkit release into an existing site.
- `LICENSE` — MIT or Apache 2.0 (TBD before publication).

## Updating the vendored book-theme

```bash
cd templates/book-theme
git fetch origin
git checkout <tag>          # e.g. v1.4.0
cd ../..
git rev-parse --short=40 HEAD:templates/book-theme > .toolkit-version
```

Sites pick up the new template on the next `myst build`.

## Why not just point at the upstream template name?

MyST's template field accepts either a name (which fetches from
`https://api.mystmd.org/templates/site/myst/<name>` at build time) or
a local path. We use the local path so:

1. Builds are reproducible (no network dependency).
2. We can add our own modifications (CSS classes for new block kinds,
   etc.) without forking the upstream template.
3. Air-gapped or restricted-network environments can still build.
