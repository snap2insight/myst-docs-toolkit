---
title: Local Development
---

# Local Development

This page is the practical guide for anyone hacking on the toolkit
itself — building the docs, running the plugin test suite, composing
CSS, vendoring assets into a downstream site. Every command listed
here is also what CI runs, so what works locally works on push.

For the design rationale behind the tooling choices below, see
[CI Architecture](../design/ci-architecture.md).

## One-time setup

Install [`just`](https://github.com/casey/just) (task runner) and
[`uv`](https://docs.astral.sh/uv/) (Python venv + deps manager):

```bash
# macOS via Homebrew
brew install just uv

# Linux / Windows — see the project pages above for installers
```

Then bootstrap the repo:

```bash
git clone --recurse-submodules https://github.com/snap2insight/myst-docs-toolkit
cd myst-docs-toolkit
just setup
```

`just setup` does three things:

1. Creates a `.venv/` via `uv venv` (idempotent — re-running is a no-op).
2. `uv pip install -r requirements.txt` into the venv (pyyaml, jsonschema, pytest, pytest-xdist).
3. `npm install -g mystmd` if `myst` isn't already on `PATH`.

Run `just` (no args) at any point to list every recipe with its docstring.

## Daily commands

### Building the docs site

```bash
just docs              # one-shot build → docs/_build/html/
just docs-dev          # live dev server with hot reload (uses myst start)
just docs-preview      # build + static-serve, matches what GH Pages sees
just docs-clean        # wipe docs/_build/
```

The difference between `docs-dev` and `docs-preview` matters more than it
looks: `myst start` is a dev server with its own routing that papers over
some multi-project setup issues. **If you're debugging a "works locally
but 404s on GH Pages" problem, use `just docs-preview`** — it static-serves
the built output the same way GH Pages does.

### Updating dates

```bash
just update-dates
```

Walks every changed markdown file and writes the appropriate
`substitutions.date:` into its frontmatter. This recipe is what
populates `{{ date }}` in the rendered HTML on every CI build, so
running it locally before a PR shows you what frontmatter changes
you'd commit.

If you have local edits that haven't been committed yet, the script
falls back to the repo-wide latest commit date. Once you commit, the
per-file dates resolve correctly.

### Recomposing the CSS overlay

```bash
just build-css
```

Reads the sources under `css/sources/` plus
`plugins/myst-mermaid/css/mermaid.css` and writes the composed
`css/site.css`. Edit a source, run this, commit both the source and
the generated output.

### Vendoring the toolkit into a downstream docs site

```bash
just sync ../enterprise-knowledge-architecture
```

Copies the toolkit's templates, CSS, parts, and version pin into the
target site's `_toolkit/` directory. Used for environments that can't
use git symlinks or fresh clones at build time.

### Running the plugin tests

```bash
just test              # everything: Python unit + mmdc integration
just test-python       # fast — pure Python AST shape assertions
just test-mmdc         # slower — feeds the plugin's output through
                       # @mermaid-js/mermaid-cli and validates the SVG
just test-mmdc-smoke   # one-shot mmdc renderability check
```

`just test-mmdc` parallelizes via `pytest-xdist -n auto` because each
mermaid test spins up its own Chrome. On a 4-core machine the four
integration tests run in roughly the time the slowest one takes
(~3-4 seconds).

If `mmdc` or its Chrome aren't installed yet, `just test-mmdc` will
install them via npm + puppeteer the first time. Subsequent runs
re-use the cached binaries.

## When to skip uv / just

Both tools are friction-removers, not requirements. If you're doing a
single quick edit and don't want to install them:

- `myst build --html` directly works fine if you have mystmd installed.
- `pytest plugins/myst-mermaid/tests/test_plugin.py` runs the Python
  unit tests with any pytest install.
- `bin/build-css.sh` and `bin/sync.sh` are plain shell scripts.

The `just` recipes just wrap these with the right environment so
contributors don't have to remember the right invocation.

## Workflow ↔ recipe parity

This is the design point that drove the Justfile in the first place:
the CI workflows are thin wrappers around `just` recipes.

| CI workflow | Recipe it calls | What runs locally |
|-------------|-----------------|-------------------|
| [`ci.yml`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/.github/workflows/ci.yml) python-unit job | `just test-python` | `just test-python` |
| [`ci.yml`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/.github/workflows/ci.yml) mermaid-cli-integration job | `just test-mmdc-smoke && just test-mmdc` | same |
| [`docs.yml`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/.github/workflows/docs.yml) build job | `just ci-docs` | same (which itself runs `just update-dates && just docs`) |
| [`release.yml`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/.github/workflows/release.yml) | `gh release create --generate-notes` | n/a (only fires on tag push) |

Practical implication: if a CI step fails, you can almost always
reproduce it locally by running the same `just` recipe. The exception
is the BASE_URL resolution step in `docs.yml`, which queries the GH
Pages API and only matters for the deployed site.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `just venv` errors with "virtual environment already exists" | Stale `.venv/` from a previous tool version | `rm -rf .venv && just setup` |
| `mmdc` works locally but tests fail with "Chrome not found" | puppeteer Chrome cache wiped | `rm -rf ~/.cache/puppeteer && just _install-mmdc` |
| `myst start` shows correct routing but `myst build` 404s | Multi-project layout — root project has its own slug | Use `just docs-preview` to reproduce; see [docs.yml comments](https://github.com/snap2insight/myst-docs-toolkit/blob/main/.github/workflows/docs.yml) on the static-host redirect |
| Pre-commit hook rejects `last_reviewed` removal | Frontmatter convention enforced by hook | The `last_reviewed` field is now derived from `{{ date }}` via `just update-dates`; remove the manual one |
| `npm install -g` keeps reinstalling mmdc / mystmd on every CI run | Pre-fix; should not happen after commit 04549b0 | See [CI Architecture §npm prefix](../design/ci-architecture.md#npm-prefix-trick) for why |

## Submitting changes

1. Branch off `main`.
2. Run `just check` (where applicable) and `just test` before pushing.
3. Open a PR. CI runs `just ci-docs` (docs build) and `just ci-test`
   (plugin tests) automatically. The full pipeline finishes in ~30s
   on warm cache.
4. After merge, the docs site at the project's GH Pages URL refreshes
   within ~40 seconds of the push.

## See also

- [CI Architecture](../design/ci-architecture.md) — why the tooling
  looks the way it does (caching strategy, per-workflow scoping,
  Justfile vs Makefile vs inline-bash, etc.).
- [Releases](releases.md) — how to cut a tagged release.
- [Adding a plugin](adding-plugins.md) — the plugin-development flow.
