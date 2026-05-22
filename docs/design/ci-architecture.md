---
title: CI Architecture
---

# CI Architecture

This page documents how the toolkit's build, test, and deploy pipeline
is structured — and why. For practical "how to use it" instructions
see [Local Development](../contributing/local-development.md).

The architecture has three pieces:

1. A root `Justfile` containing every build/test/deploy recipe.
2. Three GitHub Actions workflows that are thin wrappers around `just`.
3. A four-cache strategy keyed to invalidate only what changed.

The design point that ties them together is **dev/CI parity**: the
same `just <recipe>` command runs on a contributor's laptop and on
the GitHub Actions runner. No "works on my machine" drift.

## Why `just` instead of `make` / inline bash / npm scripts

Three alternatives were considered:

| Option | Why we didn't pick it |
|--------|----------------------|
| **Make** — universal, no install needed | Tab/space hostility, recipe semantics confusing for non-make-natives, weak parameter handling |
| **Inline bash in the workflow YAML** — what we had originally | CI logic isn't reproducible locally; every contributor reads the YAML to figure out what the build actually does |
| **`scripts:` in `package.json`** | We don't have a real Node project; adding one just to host scripts is bigger surface than the Justfile |
| **`just`** — what we picked | One file, one line per recipe, parameters and dependencies expressed cleanly, runs identically locally and in CI |

The pattern matches what `choldgraf/myst-substitutions` and similar
MyST-ecosystem plugin repos do, which makes the toolkit feel native to
its community.

## Workflow structure

Three workflows, each scoped to one concern. Names are intuitive on
purpose (`ci`, `docs`, `release`) so a new contributor doesn't need
to map filenames to purposes.

```{mermaid}
flowchart LR
    Push[Push to main] --> Docs[docs.yml]
    PRPush[Push / PR to plugins] --> CI[ci.yml]
    Tag[Tag v*] --> Release[release.yml]

    Docs --> JustCiDocs["just ci-docs<br/>(update-dates + docs)"]
    CI --> JustCiTest["just ci-test<br/>(test-python + test-mmdc)"]
    Release --> GhRelease["gh release create<br/>--generate-notes"]

    JustCiDocs --> Pages[GitHub Pages]
    JustCiTest --> CheckMark((✓))
    GhRelease --> GhReleases[GitHub Releases]
```

| Workflow | Triggers | Recipe | Output |
|----------|----------|--------|--------|
| [`ci.yml`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/.github/workflows/ci.yml) | push / PR touching `plugins/**`, `Justfile`, `requirements.txt` | `just test-python` + `just test-mmdc` | Test results |
| [`docs.yml`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/.github/workflows/docs.yml) | push to `main` touching `docs/**`, `css/**`, etc. | `just ci-docs` | Deployed docs site |
| [`release.yml`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/.github/workflows/release.yml) | tag `v*` pushed, or manual dispatch | `gh release create --generate-notes` | GitHub Release with auto-generated notes |

Path filters on each workflow mean a doc-only change doesn't run the
plugin tests, and a plugin-only change doesn't redeploy the docs.

## Caching strategy

Total CI time dropped from ~50s to ~30s after caching. The savings
come from four caches, each scoped to invalidate on the smallest
possible signal so cache hits are common.

```{table} Cache inventory
:name: tbl-caches
| Cache | Path | Key | Invalidates when |
|-------|------|-----|------------------|
| **Python venv** | `.venv/` | `${{ runner.os }}-venv-${{ hashFiles('requirements.txt') }}` | requirements.txt changes |
| **npm globals (docs)** | `~/.npm-global`, `~/.npm` | `${{ runner.os }}-npm-docs-${{ hashFiles('Justfile') }}` | Justfile changes (the `npm install -g …` lines live there) |
| **npm globals (ci)** | same paths, scoped key | `${{ runner.os }}-npm-ci-${{ hashFiles('Justfile') }}` | same |
| **Puppeteer Chrome** | `~/.cache/puppeteer` | `${{ runner.os }}-puppeteer-chrome` (fixed) | Manually bumped if Chrome major version changes |
| **book-theme submodule** | `templates/book-theme`, `.git/modules/templates/book-theme` | `${{ runner.os }}-book-theme-${{ hashFiles('.gitmodules', '.toolkit-version') }}` | Submodule pin moves |
```

All caches are restored after toolchain setup (setup-node,
setup-python, setup-uv, setup-just) and before the install/build
recipes. Install commands in the Justfile (`node-deps`, `python-deps`,
`_install-mmdc`) are idempotent — they check `command -v <tool>` and
skip if the tool is already on PATH from the restored cache.

(npm-prefix-trick)=
### The `npm config set prefix` trick

There's a subtle interaction between `setup-node@v5` and
`npm install -g` that bit us during the caching refactor and is worth
recording.

By default, `npm install -g <pkg>` writes to `/usr/local/bin/<pkg>`
on the GH Actions runner. We can't `actions/cache@v4` that path
wholesale because `/usr/local/` is shared with the OS image and other
toolchains.

Setting `NPM_CONFIG_PREFIX=$HOME/.npm-global` as a workflow `env`
should redirect global installs into a path we *can* cache. But
**`setup-node@v5` writes an `.npmrc` file that defaults the prefix to
`/usr/local/`**, and `.npmrc` wins over the env var for the install
operation. So even with the env var set, `npm install -g` still wrote
to `/usr/local/`, the cache step saved an empty `~/.npm-global/`, and
the next run had nothing to restore — `npm install -g` re-ran on
every workflow, defeating the cache.

Fix: explicitly override with `npm config set prefix` after
`setup-node`:

```yaml
- name: Configure npm prefix + PATH
  run: |
    mkdir -p "$NPM_CONFIG_PREFIX/bin"
    npm config set prefix "$NPM_CONFIG_PREFIX"
    echo "$NPM_CONFIG_PREFIX/bin" >> "$GITHUB_PATH"
```

This wins because `npm config set` writes the user-level `.npmrc`,
overriding setup-node's. With this in place, global installs land in
`~/.npm-global/`, the cache saves and restores correctly, and the
20-second `npm install -g @mermaid-js/mermaid-cli` step skips entirely
on warm runs.

### Per-workflow cache scoping

When `ci.yml` and `docs.yml` both run on the same push, they race to
save the same cache key. `actions/cache@v4` permits only one writer
per key per moment, so the loser job emits:

```
Failed to save: Unable to reserve cache with key
Linux-npm-…, another job may be creating this cache.
```

Worse, the winner saves only what its job installed:

- docs.yml saves a cache containing `mystmd` only (it doesn't need mmdc)
- ci.yml's mermaid-cli job fails to save its cache (which had mmdc)
- Next run: both workflows restore the docs.yml cache → ci.yml's
  mmdc is missing → re-installs mmdc every run

Fix: scope the npm cache key per workflow:

- `docs.yml` uses `${{ runner.os }}-npm-docs-${{ hashFiles('Justfile') }}`
- `ci.yml` uses `${{ runner.os }}-npm-ci-${{ hashFiles('Justfile') }}`

Each workflow now owns its cache. The mystmd-or-mmdc binaries persist
where they belong. Cache footprint is ~5 MB per workflow.

### book-theme submodule cache + `.git/modules`

The `book-theme` upstream is vendored as a git submodule under
`templates/book-theme/`. A fetch via `actions/checkout@v5` with
`submodules: true` adds ~8 seconds of git history download per
workflow run.

Caching `templates/book-theme/` alone works for the build (myst reads
the files), but `actions/checkout@v5`'s post-step cleanup tries to
`git submodule foreach` for ssh config reset and fails with `fatal:
not a git repository: templates/book-theme/../../.git/modules/...
exit code 128` because the submodule's `.git/modules/` git-state
directory was never initialized.

The warning is harmless but noisy. Fix: cache **both** the working
tree and the submodule's git state:

```yaml
- name: Cache book-theme submodule (working tree + git state)
  uses: actions/cache@v4
  with:
    path: |
      templates/book-theme
      .git/modules/templates/book-theme
    key: ${{ runner.os }}-book-theme-${{ hashFiles('.gitmodules', '.toolkit-version') }}
```

Now post-step cleanup finds a consistent submodule, no warning, no
behavioral change.

## Test parallelization (pytest-xdist)

The mmdc integration tests each spin up a Chrome instance (~5s of
startup per test, ~4 tests = ~20s sequential). `pytest-xdist -n auto`
detects available cores (4 on a standard runner) and distributes
tests across worker processes. Each Chrome lives in its own worker,
so the suite finishes in roughly the slowest test's time.

Real numbers from a recent run: **4 passed in 3.58s** (down from
~20s sequential).

Applied selectively in the Justfile:

```just
# Parallel — tests are independent (each spins its own Chrome) and
# benefit from -n auto.
test-mmdc: python-deps _install-mmdc
    {{pytest}} plugins/myst-mermaid/tests/test_mermaid_cli.py -v -n auto

# Sequential — small suite (~18 unit tests, ~8s total). Parallel
# worker startup would be a net slowdown.
test-python: python-deps
    {{pytest}} plugins/myst-mermaid/tests/test_plugin.py -v
```

Rule of thumb: parallelize when individual tests are slow and have
significant per-test fixed cost (browser startup, container boot,
DB setup). Don't parallelize fast in-process tests.

## Cost model — where the time goes

A current warm-cache run breaks down approximately as:

```{table} Step timings on a warm-cache CI run (mermaid-cli job)
:name: tbl-step-timings
| Phase | Time |
|-------|------|
| Job setup (runner allocation) | ~2s |
| checkout, setup-node, setup-python, setup-uv, setup-just | ~7s |
| Cache restores (3 caches) | ~6s |
| Configure npm prefix | <1s |
| `just test-mmdc-smoke` + `just test-mmdc` | ~10s |
| ↳ of which: npm + Chrome install (cached, skipped) | <1s |
| ↳ of which: pytest with 4 parallel workers | ~4s |
| Post-step cleanup | ~1s |
| **Total wall-clock** | **~27s** |
```

The ~15 seconds of "fixed overhead" (runner allocation + toolchain
setup + post-steps) is not optimizable without custom runner images.
The remaining ~12 seconds is the actual work — well-cached, well-parallelized.

## Cache hygiene

GitHub Actions automatically evicts caches older than 7 days OR when
the repo's total cache size exceeds 10 GB (oldest-first). For a
small repo like the toolkit, the natural turnover is enough — but
after a refactor pass that bumps cache keys, the old keyed caches
remain for a week, taking up space.

To clean up manually:

```bash
gh cache list --limit 50
gh cache delete <cache-id>
```

A healthy cache footprint for this repo at steady state is **6
entries totaling ~490 MB**:

| Cache | Approx size |
|-------|-------------|
| `Linux-puppeteer-chrome` | 257 MB (the Chrome binary) |
| `Linux-npm-ci-…` | 195 MB (mmdc + 354 deps) |
| `Linux-book-theme-…` | 27 MB (vendored template) |
| `Linux-npm-docs-…` | 6 MB (mystmd) |
| `Linux-venv-…` | 4 MB (Python deps in .venv) |
| `setup-uv-1-…` (managed by setup-uv) | 1 MB (uv resolver cache) |

If the list grows beyond ~10 entries, look for stale keyed caches
left behind by a refactor and delete them.

## When to add a new workflow

The current three workflows cover: continuous test (ci), continuous
deploy (docs), tagged release (release). Add a new workflow when:

- A new concern needs its own trigger (e.g., a `nightly-stale-check.yml`
  on cron).
- A long-running operation shouldn't block ci/docs (e.g., a
  `link-check.yml` running browser-based link validation weekly).

Don't add a new workflow just because a step would be nice — extend
an existing workflow with a new step or a new job within the same
workflow.

## See also

- [Local Development](../contributing/local-development.md) — how to use
  what this page describes.
- [Releases](../contributing/releases.md) — what triggers `release.yml`.
- The [Justfile in the root of the repo](https://github.com/snap2insight/myst-docs-toolkit/blob/main/Justfile)
  is the source of truth for recipes; this page may lag.
