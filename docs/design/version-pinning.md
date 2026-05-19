---
title: Version Pinning
---

# Version Pinning

A consuming docs site pins the toolkit to a specific version. This
makes builds reproducible and lets you upgrade deliberately.

## What's pinned where

| What | Pinned by | File |
|---|---|---|
| **Toolkit version** consumed by a docs site | Workflow + setup script ref | `env.TOOLKIT_REF` in the deploy workflow, `TOOLKIT_REF` env in `bin/setup-dev.sh` |
| **book-theme version** inside the toolkit | Git submodule SHA | `.toolkit-version` at the toolkit repo root |

## Why two pins, not one

The toolkit doesn't auto-update book-theme. It vendors a specific
commit as a submodule. When the toolkit publishes a new release, the
release notes call out whether the bundled book-theme changed.

This lets a consumer trust that `myst-docs-toolkit@v1.0` will *always*
render with the same `book-theme` build — no matter when they fetch it.

## How to pin

In a consuming docs site:

**`.github/workflows/eka-pages-deploy.yml`:**

```yaml
env:
  TOOLKIT_REPO: snap2insight/myst-docs-toolkit
  TOOLKIT_REF:  v1.0.0           # or a commit SHA, or "main" for trunk
```

**`bin/setup-dev.sh`:**

```bash
TOOLKIT_REF="${TOOLKIT_REF:-v1.0.0}"   # same default as the workflow
```

Keep these in sync — local builds and CI builds should resolve to the
same toolkit.

## Reading the current pin

In any docs repo that has the toolkit fetched:

```bash
cd _toolkit
git log -1 --oneline                       # current toolkit commit
cat .toolkit-version                       # bundled book-theme commit
git submodule status templates/book-theme  # ditto, verbose
```

## Upgrading

1. **In the toolkit repo:** decide a new ref to publish, optionally
   bump the bundled `book-theme` submodule, tag, push.
2. **In each consuming docs site:** change `TOOLKIT_REF` in the workflow
   (and `setup-dev.sh` default), open a PR, verify the build still
   succeeds, merge.

Rollbacks are symmetric: change the ref back.

## When to use tags vs `main`

- **For published docs sites:** tag a stable toolkit version and pin
  to it. Trunk-following ("main") is fine while the toolkit is young,
  but at some point you want reproducibility.
- **For your own private branding repo:** trunk-follow is reasonable
  since you control both sides.

## What is *not* pinned

- The version of MyST itself. That comes from your workflow's
  `npm install -g mystmd` step. Pin it there if you want.
- The version of `pyyaml` / `jsonschema` for the mermaid plugin. Pin
  in your workflow's `pip install pyyaml==X jsonschema==Y` if you care.

The toolkit only pins its own contents and the things vendored inside
it. The wider runtime is the consuming repo's responsibility.
