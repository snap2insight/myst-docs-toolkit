---
title: Vendoring Modes
---

# Vendoring Modes

A consuming docs site needs the toolkit's content at build time. There
are three ways to make that happen; each has trade-offs.

## Mode A — Symlink (preferred for local dev)

You have a checkout of `myst-docs-toolkit` somewhere on your machine
(typically a sibling directory of your docs sites). A `_toolkit/`
symlink in each docs site points at it.

```
~/wrk/code/
├── myst-docs-toolkit/          ← one clone
├── my-docs-site-a/
│   └── _toolkit -> ../myst-docs-toolkit
└── my-docs-site-b/
    └── _toolkit -> ../myst-docs-toolkit
```

**Pros:**
- One toolkit clone on disk serves any number of docs sites.
- Toolkit changes (e.g., editing CSS) are visible immediately in every
  consuming site.
- Zero CI cost — but symlinks don't survive standalone deployment.

**Cons:**
- Won't work in CI, where docs repos are checked out alone. CI uses
  Mode B instead.

**Setup:**

```bash
TOOLKIT_LOCAL=../myst-docs-toolkit ./bin/setup-dev.sh
```

## Mode B — Clone-in-place (CI default, also fine locally)

A fresh clone of the toolkit is placed at `_toolkit/` inside the docs
repo. CI uses this via `actions/checkout`. Local devs can use it too.

```bash
git clone --depth 1 --branch main --recurse-submodules \
  https://github.com/snap2insight/myst-docs-toolkit.git _toolkit
```

In a GitHub Actions workflow:

```yaml
- uses: actions/checkout@v5
  with:
    repository: snap2insight/myst-docs-toolkit
    ref: main
    path: _toolkit
    submodules: true
```

**Pros:**
- Works identically in local and CI environments.
- Standalone — the docs repo can build without anything external in a
  sibling path.
- Pinning a specific ref (tag or commit) is one workflow line.

**Cons:**
- One clone per docs site; for many sites on one machine, that's some
  redundant disk. Not a problem in CI (ephemeral runners).

## Mode C — Copy-only vendor (legacy / offline)

For environments that can't symlink and can't reach GitHub at build
time, the toolkit ships [`bin/sync.sh`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/bin/sync.sh)
which copies a small subset (CSS + parts) into `_toolkit/`. The book-
theme template still needs to come from somewhere (a separate vendored
copy, or by switching `template:` back to MyST's by-name registry
fetch).

**Pros:**
- Works completely offline once seeded.
- No symlinks needed.

**Cons:**
- You lose template pinning (book-theme has to be fetched some other
  way).
- Drift risk: each site has its own committed copy of CSS that can
  diverge.

Most teams should never need this mode.

## Choosing

| You are | Use |
|---|---|
| Working locally on one docs site | Mode B (`./bin/setup-dev.sh` with no env vars) |
| Working locally on several docs sites | Mode A (`TOOLKIT_LOCAL=../myst-docs-toolkit ./bin/setup-dev.sh`) |
| GitHub Actions / CI | Mode B (built into the deploy workflow) |
| Air-gapped builds | Mode C |

All three result in the same `shared-theme.yml` paths working — the
asset paths in your config are stable across modes.
