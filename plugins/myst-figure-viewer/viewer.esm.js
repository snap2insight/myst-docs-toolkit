/* myst-figure-viewer — runtime widget delivered via MyST's {anywidget} directive.
 *
 * Shipped as an ESM module that anywidget loads at page-load time. The widget
 * itself renders nothing visible; its job is to scan the page for figures
 * (mermaid diagrams, standalone images, {figure} blocks) and attach a
 * zoom / pan / reset / fullscreen toolbar to each.
 *
 * Fullscreen is implemented with the native <dialog> element so we get
 * ESC-to-close, focus trapping, and backdrop click for free. Pan-zoom is
 * a small custom implementation using CSS transforms — no external libs.
 *
 * Targets (default):
 *   .mermaid-light, .mermaid-dark, .mermaid-dual-container
 *   figure (book-theme wraps standalone images here)
 *
 * Override via the widget model (passed through the directive in markdown):
 *   :targets: ".mermaid-light, figure.my-class"
 *
 * Limitations:
 *   - Per-page: each page that should have the viewer needs the {anywidget}
 *     directive. We recommend adding it to parts.footer for site-wide.
 *   - Runs inside a Shadow DOM mount (book-theme's anywidget renderer) so
 *     the widget script itself is isolated; the toolbar buttons it attaches
 *     to figures DO live in the main document tree and inherit page CSS.
 *   - Mermaid renders asynchronously after page load. We use a
 *     MutationObserver to attach to diagrams that show up late.
 */

const VIEWER_MARKER = '__mystFigureViewerAttached';

const DEFAULT_TARGETS = [
  '.mermaid-light',
  '.mermaid-dark',
  '.mermaid-dual-container',
  'figure',
].join(', ');

function render({ model, el }) {
  // The widget element itself stays invisible — it's just a bootstrap.
  el.style.display = 'none';

  const targets = (model && model.get && model.get('targets')) || DEFAULT_TARGETS;
  const showToolbar = (model && model.get && model.get('show_toolbar')) ?? true;

  // Inject stylesheet once. Targets shadow DOM root for our buttons too.
  injectStyles();

  const enhance = () => {
    document.querySelectorAll(targets).forEach(target => {
      // Skip dual-container parent — only the inner .mermaid-light /
      // .mermaid-dark get a toolbar (CSS hides whichever doesn't match
      // the active color scheme).
      if (target.classList.contains('mermaid-dual-container')) return;
      // Skip clones living inside any open fullscreen dialog.
      if (target.closest('.mfv-fullscreen-dialog')) return;
      // Skip if already enhanced.
      if (target[VIEWER_MARKER]) return;
      // Prefer the innermost match: skip a target that contains another
      // target as a descendant. book-theme wraps mermaid in <figure>,
      // which contains our .mermaid-light figure — the inner one wins.
      if (target.querySelector(targets)) return;
      // Skip if no rendered SVG/image content yet — mermaid renders async;
      // the MutationObserver will catch it on the next pass.
      const hasRenderable = target.querySelector('svg, img, canvas');
      if (!hasRenderable) return;

      attachViewer(target, { showToolbar });
      target[VIEWER_MARKER] = true;
    });
  };

  // Initial pass: mermaid renders client-side, so wait a tick.
  setTimeout(enhance, 200);

  // Catch diagrams that finish rendering later (mermaid is async).
  const observer = new MutationObserver(() => enhance());
  observer.observe(document.body, { childList: true, subtree: true });

  // Re-run on book-theme client-side navigation (no full page reload).
  // The shadow DOM gets torn down between pages so this listener is per-page.
  window.addEventListener('popstate', () => setTimeout(enhance, 200));
}

function attachViewer(target, { showToolbar }) {
  if (!showToolbar) return;

  // Ensure the target can host an absolutely-positioned toolbar.
  const cs = getComputedStyle(target);
  if (cs.position === 'static') {
    target.style.position = 'relative';
  }

  const toolbar = document.createElement('div');
  toolbar.className = 'mfv-toolbar';
  toolbar.setAttribute('aria-hidden', 'true');

  const fsBtn = makeButton('⛶', 'Open fullscreen', () => openFullscreen(target));
  fsBtn.classList.add('mfv-btn', 'mfv-btn-fullscreen');
  toolbar.appendChild(fsBtn);

  target.appendChild(toolbar);
}

function openFullscreen(source) {
  const dialog = document.createElement('dialog');
  dialog.className = 'mfv-fullscreen-dialog';

  dialog.innerHTML = `
    <div class="mfv-dialog-toolbar">
      <button class="mfv-btn" data-action="zoom-out" title="Zoom out">−</button>
      <button class="mfv-btn" data-action="reset"    title="Reset (0)">⊙</button>
      <button class="mfv-btn" data-action="zoom-in"  title="Zoom in (+)">+</button>
      <button class="mfv-btn" data-action="close"    title="Close (Esc)">×</button>
    </div>
    <div class="mfv-dialog-canvas">
      <div class="mfv-dialog-stage"></div>
    </div>
  `;

  const stage = dialog.querySelector('.mfv-dialog-stage');
  const clone = source.cloneNode(true);

  // --- Cleanup 1: Strip our own toolbar from the clone. ---
  clone.querySelectorAll('.mfv-toolbar').forEach(t => t.remove());
  delete clone[VIEWER_MARKER];

  // --- Cleanup 2: Force visibility on the clone. ---
  // The page's CSS hides .mermaid-light in dark mode (and vice versa).
  // The clone carries the same class, so it inherits the hiding rule.
  // Strip theme-visibility classes and force display so the clone is
  // always visible inside the dialog regardless of the current theme.
  clone.style.display = 'block';
  clone.classList.remove('mermaid-light', 'mermaid-dark');

  // --- Cleanup 3: Fix SVG ID collisions for Mermaid diagrams. ---
  // Mermaid generates a unique ID per SVG (e.g., id="mermaid-1715...")
  // and embeds a <style> block inside the SVG with selectors scoped to
  // that ID (e.g., "#mermaid-1715... .node { fill: #fff; }").
  // cloneNode(true) duplicates the ID. When two elements share the same
  // ID, browsers resolve ID-scoped CSS to the FIRST match in document
  // order (the original), leaving the clone unstyled and invisible.
  // Fix: assign a new unique ID to each cloned SVG and rewrite the
  // selectors in its internal <style> tags to match.
  clone.querySelectorAll('svg[id]').forEach(svg => {
    const oldId = svg.getAttribute('id');
    const newId = oldId + '-mfv-' + Math.random().toString(36).slice(2, 8);
    svg.setAttribute('id', newId);

    // Rewrite every internal <style> block that references the old ID.
    svg.querySelectorAll('style').forEach(styleEl => {
      styleEl.textContent = styleEl.textContent.replaceAll(
        '#' + oldId, '#' + newId
      );
    });
  });

  // --- Cleanup 4: Size SVGs and images for the fullscreen viewport. ---
  clone.querySelectorAll('svg').forEach(svg => {
    // Mermaid sets width="100%" / height="100%" so the SVG fills its
    // inline parent. In the dialog the parent has no fixed size, so
    // the SVG would collapse to 0×0. Remove percentage dimensions and
    // force viewport-relative sizing; preserveAspectRatio (defaults to
    // xMidYMid meet) handles aspect ratio from viewBox.
    const w = svg.getAttribute('width');
    const h = svg.getAttribute('height');
    if (w && (w === '100%' || w.endsWith('%'))) svg.removeAttribute('width');
    if (h && (h === '100%' || h.endsWith('%'))) svg.removeAttribute('height');

    svg.style.width = 'min(90vw, 1400px)';
    svg.style.height = 'auto';
    svg.style.maxHeight = '88vh';
    svg.style.display = 'block';
  });

  // Handle <img> elements inside <figure> clones.
  clone.querySelectorAll('img').forEach(img => {
    img.style.maxWidth = 'min(90vw, 1400px)';
    img.style.maxHeight = '88vh';
    img.style.height = 'auto';
    img.style.display = 'block';
    img.style.objectFit = 'contain';
  });

  stage.appendChild(clone);

  // Pan + zoom state
  const state = { scale: 1, tx: 0, ty: 0 };
  const apply = (transition = true) => {
    stage.style.transform = `translate(${state.tx}px, ${state.ty}px) scale(${state.scale})`;
    stage.style.transition = transition ? 'transform 0.18s ease-out' : 'none';
  };
  const reset = () => { state.scale = 1; state.tx = 0; state.ty = 0; apply(); };
  const zoomBy = (factor) => {
    state.scale = clamp(state.scale * factor, 0.2, 8);
    apply();
  };

  // Toolbar actions
  dialog.addEventListener('click', (e) => {
    const action = e.target.closest('[data-action]')?.dataset?.action;
    if (action === 'zoom-in') zoomBy(1.25);
    else if (action === 'zoom-out') zoomBy(0.8);
    else if (action === 'reset') reset();
    else if (action === 'close') dialog.close();
    // Backdrop click (clicking the dialog itself outside content) closes too.
    else if (e.target === dialog) dialog.close();
  });

  // Keyboard shortcuts inside dialog
  dialog.addEventListener('keydown', (e) => {
    if (e.key === '+' || e.key === '=') { e.preventDefault(); zoomBy(1.25); }
    else if (e.key === '-' || e.key === '_') { e.preventDefault(); zoomBy(0.8); }
    else if (e.key === '0') { e.preventDefault(); reset(); }
  });

  // Mouse-wheel zoom
  const canvas = dialog.querySelector('.mfv-dialog-canvas');
  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    zoomBy(e.deltaY < 0 ? 1.1 : 0.9);
  }, { passive: false });

  // Drag-to-pan (mouse)
  let dragging = false, startX = 0, startY = 0;
  canvas.addEventListener('mousedown', (e) => {
    if (e.button !== 0) return;
    dragging = true;
    startX = e.clientX - state.tx;
    startY = e.clientY - state.ty;
    canvas.classList.add('mfv-dragging');
  });
  window.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    state.tx = e.clientX - startX;
    state.ty = e.clientY - startY;
    apply(false);
  });
  window.addEventListener('mouseup', () => {
    if (dragging) {
      dragging = false;
      canvas.classList.remove('mfv-dragging');
    }
  });

  // Touch drag-to-pan (mobile)
  canvas.addEventListener('touchstart', (e) => {
    if (e.touches.length !== 1) return;
    dragging = true;
    startX = e.touches[0].clientX - state.tx;
    startY = e.touches[0].clientY - state.ty;
    canvas.classList.add('mfv-dragging');
  }, { passive: true });
  canvas.addEventListener('touchmove', (e) => {
    if (!dragging || e.touches.length !== 1) return;
    e.preventDefault();
    state.tx = e.touches[0].clientX - startX;
    state.ty = e.touches[0].clientY - startY;
    apply(false);
  }, { passive: false });
  canvas.addEventListener('touchend', () => {
    if (dragging) {
      dragging = false;
      canvas.classList.remove('mfv-dragging');
    }
  });

  // Cleanup when the dialog closes
  dialog.addEventListener('close', () => {
    dialog.remove();
  });

  document.body.appendChild(dialog);
  dialog.showModal(); // Native: ESC closes, focus trap, inert background.
}

function makeButton(label, title, onClick) {
  const b = document.createElement('button');
  b.type = 'button';
  b.textContent = label;
  b.title = title;
  b.setAttribute('aria-label', title);
  if (onClick) b.addEventListener('click', (e) => { e.stopPropagation(); onClick(); });
  return b;
}

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

/* The widget mount is inside Shadow DOM, but our toolbar buttons get attached
 * to elements in the main document. So our styles need to be in the main
 * document, not in the shadow root. We inject a single <style> once.
 */
function injectStyles() {
  if (document.getElementById('mfv-styles')) return;
  const style = document.createElement('style');
  style.id = 'mfv-styles';
  style.textContent = `
    .mfv-toolbar {
      position: absolute;
      top: 0.5rem;
      right: 0.5rem;
      display: flex;
      gap: 0.25rem;
      opacity: 0;
      transition: opacity 0.15s ease;
      z-index: 10;
      pointer-events: none;
    }
    *:hover > .mfv-toolbar,
    .mfv-toolbar:hover {
      opacity: 1;
      pointer-events: auto;
    }
    .mfv-btn {
      background: rgba(255,255,255,0.92);
      color: #1f2937;
      border: 1px solid rgba(0,0,0,0.12);
      border-radius: 4px;
      padding: 0.2rem 0.5rem;
      font: 600 0.9rem system-ui, -apple-system, sans-serif;
      line-height: 1.2;
      cursor: pointer;
      box-shadow: 0 1px 2px rgba(0,0,0,0.06);
      transition: background 0.12s ease;
    }
    .mfv-btn:hover { background: white; }
    .mfv-btn:focus-visible { outline: 2px solid #2563eb; outline-offset: 1px; }
    html.dark .mfv-btn,
    html[data-theme="dark"] .mfv-btn {
      background: rgba(31,41,55,0.92);
      color: #f3f4f6;
      border-color: rgba(255,255,255,0.15);
    }
    html.dark .mfv-btn:hover,
    html[data-theme="dark"] .mfv-btn:hover { background: rgb(31,41,55); }

    .mfv-fullscreen-dialog {
      width: 96vw;
      height: 96vh;
      max-width: 96vw;
      max-height: 96vh;
      padding: 0;
      border: none;
      background: white;
      border-radius: 8px;
      box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
    }
    .mfv-fullscreen-dialog::backdrop {
      background: rgba(0,0,0,0.7);
      backdrop-filter: blur(2px);
    }
    html.dark .mfv-fullscreen-dialog,
    html[data-theme="dark"] .mfv-fullscreen-dialog {
      background: #1f2937;
      color: #f3f4f6;
    }

    .mfv-dialog-toolbar {
      position: absolute;
      top: 1rem;
      right: 1rem;
      display: flex;
      gap: 0.5rem;
      z-index: 100;
    }
    .mfv-dialog-toolbar .mfv-btn {
      font-size: 1.1rem;
      padding: 0.35rem 0.7rem;
    }

    .mfv-dialog-canvas {
      width: 100%;
      height: 100%;
      overflow: hidden;
      cursor: grab;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .mfv-dialog-canvas.mfv-dragging { cursor: grabbing; }
    .mfv-dialog-stage {
      transform-origin: center center;
      will-change: transform;
      max-width: 100%;
      max-height: 100%;
    }
    .mfv-dialog-stage > * {
      max-width: 90vw;
      max-height: 88vh;
    }
    .mfv-dialog-stage svg {
      width: auto;
      height: auto;
      max-width: 90vw;
      max-height: 88vh;
    }
  `;
  document.head.appendChild(style);
}

export default { render };
