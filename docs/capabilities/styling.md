---
title: Styling
---

# Styling

The toolkit's [`css/site.css`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/css/site.css)
is a small overlay that adds visual support for a handful of patterns
the upstream `book-theme` doesn't style on its own. It's brand-neutral
on purpose — colors and type belong in a branding layer.

## How to load it

In `shared-theme.yml`:

```yaml
site:
  options:
    style: _toolkit/css/site.css
```

If your site also has a branding stylesheet, MyST currently accepts a
single `style:` entry — point at your branding CSS and `@import`
`_toolkit/css/site.css` from there, or merge them at build time.

## What it styles

### `.split-image` and `.justified`

Hero block kinds for landing pages, used by `+++ {"kind": "split-image"}`
and `+++ {"kind": "justified"}` markers in a `landing-page.md`. See the
[landing page](../) of this site for an example.

```css
.split-image {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 3rem;
    align-items: center;
    ...
}
.justified { max-width: 720px; margin: 1rem auto 0; ... }
```

Mobile (≤768px) collapses `.split-image` to a single column.

### `{button}` role

MyST ships a `{button}` role. The toolkit styles its output as a dark
pill with a hover state:

```{button}`Example button </intro/getting-started>`
```

### Footer grid

A simple `.footer-grid` class for the rendered footer part — minimal
padding, light separator, dimmed text.

### Mermaid dual-theme toggling

When the [`myst-mermaid`](../plugins/myst-mermaid.md) plugin is enabled,
each mermaid diagram is emitted twice (once per theme). The CSS hides
the variant that doesn't match the active color scheme:

```css
.mermaid-light { display: block; }
.mermaid-dark  { display: none;  }

html.dark .mermaid-light { display: none; }
html.dark .mermaid-dark  { display: block; }

/* Plus a prefers-color-scheme fallback for sites that don't set html.dark */
```

If you don't use the plugin, these rules are no-ops (no `.mermaid-light`
/ `.mermaid-dark` elements are emitted).

## What it does *not* style

- No brand colors or typography. Set those in your own CSS layered on
  top.
- No layout overrides for the book-theme's core chrome (sidebar, nav,
  TOC). The upstream theme owns those.
- No print styles. PDF builds use `myst build --pdf` which handles
  that path separately.

## Extending it

Override or extend by loading your own stylesheet *after* this one. Your
site's `shared-theme.yml` can point at a branding CSS that `@import`s
the toolkit's site.css and adds rules below it.
