# myst-figure-viewer

A zero-dependency ESM widget that adds interactive zoom, pan, and
fullscreen capabilities to figures and Mermaid diagrams on any MyST
site. Delivered via MyST's `{anywidget}` directive.

## How it works

The widget's `render()` function runs at page load and:

1. Injects a single `<style>` element into `<head>` with toolbar +
   dialog CSS (supports light and dark mode).
2. Scans the page for target elements (`.mermaid-light`,
   `.mermaid-dark`, `<figure>`) using `querySelectorAll`.
3. Attaches a hover toolbar with a fullscreen button (`⛶`) to each
   target that contains renderable content (`<svg>`, `<img>`,
   `<canvas>`).
4. Starts a `MutationObserver` to catch diagrams that render
   asynchronously after page load (mermaid does this).

When the user clicks `⛶`, the widget:

1. Clones the source element into a native `<dialog>` overlay.
2. Fixes SVG ID collisions (mermaid generates unique IDs with internal
   `<style>` blocks — cloning duplicates IDs and breaks CSS scoping).
3. Strips theme-visibility classes so the clone is always visible.
4. Sizes SVGs and images for the fullscreen viewport.
5. Wires up zoom (buttons, keyboard, mouse wheel), pan (drag), and
   close (button, ESC, backdrop click).

## Usage

Add to any page or to your site's footer for site-wide coverage:

````markdown
```{anywidget} _toolkit/plugins/myst-figure-viewer/viewer.esm.js
```
````

The toolkit's default `parts/footer.md` already includes this directive.

## Configuration

Pass a JSON body to the `{anywidget}` directive to override defaults:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `targets` | string | `.mermaid-light, .mermaid-dark, .mermaid-dual-container, figure` | CSS selector for elements to enhance |
| `show_toolbar` | bool | `true` | Set `false` to disable the toolbar entirely |

## Files

```
myst-figure-viewer/
├── README.md           — this file
├── viewer.esm.js       — the ESM widget module
└── examples/           — (planned) example pages
```

## Keyboard shortcuts (inside fullscreen)

| Key | Action |
|-----|--------|
| `+` / `=` | Zoom in |
| `-` / `_` | Zoom out |
| `0` | Reset zoom + position |
| `Esc` | Close |

## Browser support

Uses `<dialog>`, `MutationObserver`, CSS `min()`, and ES module syntax.
All are supported in Chrome 37+, Firefox 98+, Safari 15.4+, Edge 79+.

## License

MIT (matches the parent myst-docs-toolkit repo).
