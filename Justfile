# myst-docs-toolkit — task automation.
#
# Same recipes run locally and in CI. Run `just` (no args) to list them.
# Install just: https://github.com/casey/just#installation
# Install uv:   https://docs.astral.sh/uv/getting-started/installation/
#
# Layout assumptions:
#   - Toolkit code at the repo root (templates/, plugins/, css/, parts/, bin/)
#   - Dogfood docs site at docs/  (its own myst.yml + toc.yml + _build/)
#   - Python venv at .venv/       (uv-managed; gitignored)

# ── Vars ──────────────────────────────────────────────────────────────────
root          := justfile_directory()
venv          := root + "/.venv"
venv_bin      := venv + "/bin"
python        := venv_bin + "/python"
pytest        := venv_bin + "/pytest"
requirements  := root + "/requirements.txt"

# ── Default ───────────────────────────────────────────────────────────────

# Show the available recipes.
default:
    @just --list --unsorted

# ── Setup ─────────────────────────────────────────────────────────────────

# Bootstrap: Python venv (uv) + npm-global mystmd. Run once after clone.
setup: venv python-deps node-deps
    @echo ""
    @echo "✅ Setup complete. Try: just docs-dev"

# Create a uv-managed Python virtualenv at .venv/.
venv:
    @command -v uv >/dev/null || { echo "❌ Install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }
    uv venv {{venv}}

# Install Python dependencies from requirements.txt into the venv.
python-deps: venv
    uv pip install --python {{python}} -r {{requirements}}

# Install mystmd globally via npm.
node-deps:
    @command -v myst >/dev/null || npm install -g mystmd

# ── Docs (dogfood site at docs/) ──────────────────────────────────────────

# Build the toolkit's docs site. Reads BASE_URL env (defaults to empty).
docs:
    cd docs && BASE_URL="${BASE_URL:-}" myst build --html
    @echo "✅ Built docs/_build/html/"

# Live dev server for the docs site (hot reload).
docs-dev:
    cd docs && myst start

# Static-serve the built docs at :8000. Matches what GH Pages will serve.
# (Crucial debug tool: `myst start` is a dev-server with different routing.)
docs-preview: docs
    @echo "Serving docs/_build/html at http://localhost:8000 — Ctrl+C to stop"
    cd docs/_build/html && python3 -m http.server 8000

# Wipe docs build output.
docs-clean:
    rm -rf docs/_build

# Update last-updated dates in frontmatter from git history (wraps
# bin/update-dates.py). Run before `just docs` to refresh `{{ date }}`
# substitutions in docs/.
update-dates: python-deps
    cd docs && {{python}} ../bin/update-dates.py

# ── CSS ───────────────────────────────────────────────────────────────────

# Compose css/site.css from sources (wraps bin/build-css.sh).
build-css:
    ./bin/build-css.sh

# ── Sync (vendor toolkit into a downstream docs site) ─────────────────────

# Copy toolkit assets into a downstream site (wraps bin/sync.sh).
#   just sync ../enterprise-knowledge-architecture
sync target:
    ./bin/sync.sh {{target}}

# ── Tests (plugins) ───────────────────────────────────────────────────────

# Run all plugin tests (Python + mermaid-cli integration).
test: test-python test-mmdc

# Python unit tests for the myst-mermaid plugin.
test-python: python-deps
    {{pytest}} plugins/myst-mermaid/tests/test_plugin.py -v

# mermaid-cli integration tests — installs mmdc + chrome if needed.
test-mmdc: python-deps
    @command -v mmdc >/dev/null || npm install -g @mermaid-js/mermaid-cli
    @MMDC_DIR="$(npm root -g)/@mermaid-js/mermaid-cli" && \
     (cd "$MMDC_DIR" && npx --yes puppeteer browsers install chrome-headless-shell --quiet) || true
    {{pytest}} plugins/myst-mermaid/tests/test_mermaid_cli.py -v

# Smoke-test that mmdc renders a trivial graph cleanly.
test-mmdc-smoke:
    @echo "graph LR; A --> B" > /tmp/smoke.mmd
    mmdc -i /tmp/smoke.mmd -o /tmp/smoke.svg \
         -p plugins/myst-mermaid/tests/puppeteer-config.json \
         --quiet
    @test -s /tmp/smoke.svg && echo "✅ mmdc renders cleanly"

# ── CI entrypoints ────────────────────────────────────────────────────────
# CI workflows call these single recipes — keeps build logic out of YAML.

# Used by .github/workflows/docs-deploy.yml.
ci-docs: update-dates docs

# Used by .github/workflows/plugin-tests.yml.
ci-test: test
