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
├── README.md                            — this file
├── LICENSE                              — MIT
├── .toolkit-version                     — pins the upstream book-theme commit
├── templates/
│   └── book-theme/                      — submodule of myst-templates/book-theme
├── css/
│   ├── README.md                        — explains the build flow
│   ├── site.css                         — GENERATED composed stylesheet
│   └── sources/
│       ├── _imports.css                 — @import statements (Google Fonts)
│       └── _layout.css                  — block kinds, button, footer rules
├── parts/
│   └── footer.md                        — generic default footer
├── plugins/
│   └── myst-mermaid/                    — dual-theme mermaid plugin
│       ├── plugin.py
│       ├── css/mermaid.css              — canonical mermaid CSS (also composed)
│       └── ...
├── bin/
│   ├── build-css.sh                     — compose css/site.css from sources
│   └── sync.sh                          — vendor toolkit into a docs site
└── docs/                                — toolkit's own docs site (Pages)
```

## Local development

This repo uses [`just`](https://github.com/casey/just) as the task
runner and [`uv`](https://docs.astral.sh/uv/) for Python deps. Same
recipes run locally and in CI — no drift between "works on my
machine" and "works in GH Actions".

```bash
# One-time setup (after `git clone` + submodule init)
just setup                # creates .venv via uv; installs mystmd globally

# Build the dogfood docs site
just docs                 # → docs/_build/html/

# Live dev server with hot reload
just docs-dev             # → http://localhost:3000

# Static preview matching what GH Pages serves (NOT the same as docs-dev)
just docs-preview         # → http://localhost:8000

# Run the plugin test suite
just test                 # Python unit + mermaid-cli SVG render

# Update last-updated dates in docs frontmatter from git history
just update-dates

# Recompose css/site.css from sources
just build-css

# Vendor toolkit assets into a downstream docs site
just sync ../enterprise-knowledge-architecture
```

Run `just` (no args) to list every recipe. The CI workflows are thin
wrappers that call `just` recipes — the actual build logic lives in
the [`Justfile`](Justfile):

| Workflow | Recipe | Triggers |
|----------|--------|----------|
| [`ci.yml`](.github/workflows/ci.yml) | `just test-python` + `just test-mmdc` | push / PR touching `plugins/**` |
| [`docs.yml`](.github/workflows/docs.yml) | `just ci-docs` | push to `main` touching `docs/`, `css/`, `plugins/`, etc. |
| [`release.yml`](.github/workflows/release.yml) | `gh release create --generate-notes` | tag `v*` pushed, or manual dispatch |

## CSS composition

`css/site.css` is a **generated** file. Edit one of the sources, then
re-run the composer:

```bash
just build-css
# equivalent to: ./bin/build-css.sh
```

The script reads:
- `css/sources/_imports.css` — @import statements (bubbled to the top of
  the output; CSS spec requires this).
- `css/sources/_layout.css` — block-kind, button, footer rules.
- `plugins/myst-mermaid/css/mermaid.css` — mermaid plugin CSS.

…dedupes the @imports, and writes a banner + concatenated rules into
`css/site.css`. Sources and generated output are both committed; CI can
verify they're in sync with `git diff --exit-code css/site.css`
after re-running the composer.

This roundabout dance exists because MyST's `site.options.style` only
accepts a single CSS path and doesn't serve CSS files referenced via
runtime `@import`. Build-time composition gives us modular sources +
a single deployable artifact.

## What's covered today

- **Template** — vendored `book-theme` upstream, pinned via
  `.toolkit-version`.
- **CSS** — styling for the landing-page block kinds
  (`.split-image`, `.justified`), the `{button}` role, the footer grid,
  and the mermaid dual-theme toggling classes. No brand colors, fonts,
  or logos.
- **Footer** — a minimal "Built with MyST" default. Sites that want
  branded footers reference their own (provided by the consuming
  organization, layered on top of the toolkit).
- **Plugins** — see [`plugins/`](plugins/). Currently ships
  [`myst-mermaid`](plugins/myst-mermaid/), a Python executable plugin
  that pre-processes mermaid blocks for dual light/dark rendering.

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
