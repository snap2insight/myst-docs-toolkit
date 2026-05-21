---
title: "myst-figure-viewer"
description: "Interactive zoom, pan, and fullscreen for figures and Mermaid diagrams."
---

# myst-figure-viewer

> Interactive zoom, pan, and fullscreen for every figure on your site —
> delivered as a zero-dependency ESM widget via MyST's `{anywidget}`
> directive.

## What it does

The figure viewer scans each page for renderable content (Mermaid
diagrams, standalone images, `{figure}` blocks) and attaches a small
hover toolbar with a **fullscreen** button. Clicking it opens a native
`<dialog>` overlay where the user can:

- **Zoom** — mouse wheel, `+` / `−` buttons, or keyboard shortcuts
- **Pan** — click-and-drag anywhere on the canvas
- **Reset** — `⊙` button or press `0`
- **Close** — `×` button, press `Esc`, or click the backdrop

The overlay adapts to light and dark mode automatically.

## Quick start

Add the widget to your site's footer so it loads on every page:

````markdown
```{anywidget} _toolkit/plugins/myst-figure-viewer/viewer.esm.js
```
````

Or place it in a specific page if you only want the viewer there.

### Recommended: site-wide via `parts/footer`

The toolkit's default [`parts/footer.md`](../../parts/footer.md)
already includes the directive. If your `shared-theme.yml` references
the toolkit footer, you get the viewer for free:

```yaml
# shared-theme.yml
site:
  parts:
    footer: _toolkit/parts/footer.md
```

## How it works

```{mermaid}
sequenceDiagram
    participant Page as Page load
    participant AW as anywidget runtime
    participant Viewer as viewer.esm.js
    participant DOM as Document DOM

    Page->>AW: render footer widget
    AW->>Viewer: call render({ model, el })
    Viewer->>DOM: injectStyles() — single <style> in <head>
    Viewer->>DOM: querySelectorAll(targets)
    loop MutationObserver
        DOM-->>Viewer: new figure/mermaid node appeared
        Viewer->>DOM: attachViewer(target) — add ⛶ toolbar
    end
    Note over Viewer,DOM: User clicks ⛶
    Viewer->>DOM: openFullscreen(source)
    DOM->>DOM: <dialog>.showModal()
```

### Target selection

The viewer enhances elements matching these selectors (configurable):

| Selector | What it matches |
|---|---|
| `.mermaid-light` | Light-theme mermaid diagram (from myst-mermaid plugin) |
| `.mermaid-dark` | Dark-theme mermaid diagram |
| `.mermaid-dual-container` | Skipped — inner variants get the toolbar instead |
| `figure` | Any `<figure>` element (book-theme wraps standalone images here) |

Override via the widget model:

````markdown
```{anywidget} _toolkit/plugins/myst-figure-viewer/viewer.esm.js
{
  "targets": ".mermaid-light, figure.custom-class"
}
```
````

### Fullscreen overlay

The overlay uses the native `<dialog>` element with `showModal()`, which
provides:

- **ESC to close** — built into the browser
- **Focus trapping** — keyboard focus stays inside the dialog
- **Inert background** — the page behind is non-interactive
- **Backdrop click** — clicking outside the content closes the dialog

Pan-zoom is implemented with CSS `transform: translate() scale()` — no
external libraries.

## Keyboard shortcuts (inside fullscreen)

| Key | Action |
|-----|--------|
| `+` or `=` | Zoom in |
| `-` or `_` | Zoom out |
| `0` | Reset zoom and position |
| `Esc` | Close fullscreen |

## Dark mode support

Toolbar buttons and the fullscreen dialog automatically adapt to the
page's color scheme. Supports `html.dark`, `html[data-theme="dark"]`,
and `prefers-color-scheme: dark`.

## Design decisions

1. **Zero dependencies.** Pan-zoom is ~30 lines of pointer math +
   CSS transforms. No need for a library.
2. **`<dialog>` over custom modals.** Native accessibility, focus
   management, and ESC handling for free.
3. **Runtime injection via anywidget.** No build-time AST transform
   needed — the viewer operates purely on the rendered DOM.
4. **MutationObserver for async content.** Mermaid diagrams render
   client-side after page load; the observer catches them.
5. **Styles in `<head>`, not Shadow DOM.** The widget's `el` lives
   inside Shadow DOM, but toolbar buttons are attached to the main
   document. Styles must be in the main document to apply.

## Limitations

- **Per-page delivery.** Each page needs the `{anywidget}` directive.
  Placing it in `parts/footer` is the recommended workaround.
- **No pinch-to-zoom.** Single-finger drag-to-pan works on mobile
  (touch events are wired up). Pinch-to-zoom isn't yet implemented;
  on touch devices you can still zoom via the toolbar's `+` / `−` /
  `⊙` buttons.
- **No export.** The viewer doesn't offer download/copy-to-clipboard
  for diagrams (planned).
