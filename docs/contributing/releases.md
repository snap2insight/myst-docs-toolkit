---
title: Releases
---

# Releases

The toolkit follows a simple, opinionated release flow. Consuming docs
sites pin to specific refs (see [Version Pinning](../design/version-pinning.md)),
so each release should be a deliberate decision point.

## Versioning scheme

Semantic versioning (`MAJOR.MINOR.PATCH`):

| Bump | When |
|---|---|
| **MAJOR** | Breaking change for consumers: removed CSS class, renamed plugin, changed plugin protocol, etc. |
| **MINOR** | New capability that consumers can opt into: new plugin, new CSS class, new part. Existing usage continues to work. |
| **PATCH** | Bug fixes, doc updates, internal refactors with no consumer-visible change. |

Bumping the bundled `book-theme` submodule is at minimum a MINOR bump
(consumer-visible). If the new book-theme has breaking changes itself,
it's a MAJOR bump.

## Release process

1. Open a release PR from `main` to `main` (or use a release branch if
   you need to stage multiple changes):
   - Edit `README.md` to note the new version.
   - Edit `CHANGELOG.md` (when we have one) with the diff highlights.
2. Merge.
3. Tag:
   ```bash
   git tag -a v1.2.0 -m "v1.2.0 — add header part, bump book-theme to 1.5"
   git push origin v1.2.0
   ```
4. Create a GitHub release from the tag with the highlights.

Consumers can now pin to `TOOLKIT_REF=v1.2.0` in their deploy workflows.

## What stays unreleased

- `main` may carry work-in-progress. Consumers pinned to a tag are
  unaffected.
- Internal CI tweaks, README typos, and similar non-consumer-visible
  changes don't need a release — they ship with the next functional
  release.

## Deprecation policy

When something has to be removed (a CSS class renamed, a plugin
flag dropped):

1. **Announce in the previous release.** Add a "Deprecated" section to
   the release notes describing what's going away and the replacement.
2. **Keep working for one MAJOR cycle.** A deprecated feature continues
   to function (perhaps emitting a build-time warning) for the
   remainder of the current MAJOR version.
3. **Remove in the next MAJOR.** The MAJOR bump release notes call out
   the removal.

This gives consumers a known window to migrate.

## Compatibility commitments

- The toolkit will not break `shared-theme.yml` paths
  (`_toolkit/templates/book-theme`, `_toolkit/css/site.css`,
  `_toolkit/parts/footer.md`) within a MAJOR version.
- CSS class names already shipped (`.split-image`, `.justified`,
  `.mermaid-light`, `.mermaid-dark`, `.mermaid-dual-container`,
  `.footer-grid`) won't be renamed mid-MAJOR.
- The mermaid plugin's `myst-mermaid.yml` schema won't add required
  keys mid-MAJOR. New keys may be added as optional.

## Pre-1.0

The toolkit is currently pre-1.0. We try to follow the policies above,
but breaking changes may happen on MINOR bumps until 1.0 ships. Once
the toolkit hits 1.0, semver applies strictly.

## Release cadence

There is no fixed cadence. Releases happen when there's something
worth releasing. A patch fix for a security issue may ship the same
day; a new plugin might take weeks to land.
