---
title: Templates
---

# Templates

The toolkit ships exactly one MyST template:
**`templates/book-theme/`** — a vendored copy of
[`myst-templates/book-theme`](https://github.com/myst-templates/book-theme).

## Why vendored and pinned

MyST's default flow downloads `book-theme` at build time from the
template registry. That gives you the latest version on every build —
convenient, but two problems:

1. **Non-reproducible builds.** A theme update can quietly change
   rendering between yesterday and today.
2. **Network dependency.** Air-gapped or restricted-network builds
   can't reach the registry.

By vendoring `book-theme` as a git submodule and pinning the SHA in
`.toolkit-version`, every build that fetches the toolkit gets exactly
the same template version. Upgrading to a new `book-theme` release is a
deliberate one-PR action.

## How to use it

Reference the template by local path in `shared-theme.yml`:

```yaml
site:
  template: _toolkit/templates/book-theme
```

Where `_toolkit/` is the symlink or clone created by your `setup-dev.sh`
locally and by `actions/checkout` in CI.

## Critical CI detail

The book-theme is a **submodule** of the toolkit. The `actions/checkout`
step that fetches the toolkit must include `submodules: true`, otherwise
`_toolkit/templates/book-theme/` will be empty and MyST will fail to
find the template.

```yaml
- uses: actions/checkout@v5
  with:
    repository: snap2insight/myst-docs-toolkit
    ref: main
    path: _toolkit
    submodules: true     # ← required
```

Locally, the `setup-dev.sh` reference script in
[Getting Started](../intro/getting-started.md) uses
`git clone --recurse-submodules` for the same reason.

## Current version

The pinned commit is recorded in
[`.toolkit-version`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/.toolkit-version)
at the toolkit repo root. Look at it to confirm what `_toolkit/` resolves
to in your build.

## Upgrading the pinned version

In a clone of the toolkit:

```bash
cd templates/book-theme
git fetch origin
git checkout <new-tag-or-sha>
cd ../..
git rev-parse HEAD:templates/book-theme > .toolkit-version
git commit -am "Bump book-theme to <new-version>"
git push
```

Consuming docs sites will pick up the new version on their next build
(or you can tag the toolkit and have sites pin to a release tag).

## Why not fork the template?

We may eventually. For now, the goal is to add a thin layer of CSS and
plugins around the upstream template without modifying it. Anything we
genuinely need to change in `book-theme` itself should go upstream as
a PR.
