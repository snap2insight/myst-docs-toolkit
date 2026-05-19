---
title: Parts
---

# Parts

MyST's `site.parts` config lets you inject markdown into specific
slots in the rendered page chrome (footer, header, etc.). The toolkit
provides a default footer; consumers override by pointing at their own.

## Default footer

[`parts/footer.md`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/parts/footer.md):

```markdown
---
title: Footer
---

*Built with [MyST](https://mystmd.org).*
```

That's it — a one-line attribution. Suitable for any site that doesn't
have its own branded footer.

## How to use it

```yaml
site:
  parts:
    footer: _toolkit/parts/footer.md
```

## How to override

Point at your own markdown file. Two common patterns:

**Branded site (uses its own footer):**

```yaml
site:
  parts:
    footer: _branding/parts/footer.md
```

**No footer at all:**

Just don't set `site.parts.footer`. The book-theme renders nothing for
that slot.

## Future parts

The toolkit may grow more parts over time — header banner, sidebar
top/bottom slots, an announcement bar. They'll follow the same pattern:
a generic default here, organization-specific overrides in the branding
layer.

If a consumer needs a part the toolkit doesn't ship yet, they can just
add it themselves — the toolkit doesn't gate which parts a site uses.
