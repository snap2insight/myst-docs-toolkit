---
title: Overview
---

# Contributing

Contributions are welcome. The toolkit is MIT-licensed and intended to
be useful beyond any single organization.

## Where to start

- **Bug reports / questions:**
  [open an issue](https://github.com/snap2insight/myst-docs-toolkit/issues/new).
- **Small fixes** (typos, CSS tweaks, README clarifications): send a
  PR directly.
- **New plugin or substantial feature:** open an issue first to discuss
  scope — saves a round of rework.

Read [Local Development](local-development.md) for the practical
`just`-recipe-driven dev loop, and [CI Architecture](../design/ci-architecture.md)
for the design rationale behind the build system (caching strategy,
per-workflow scoping, why we chose `just` over `make`).

## Repo layout for contributors

```
myst-docs-toolkit/
├── README.md                ← top-level overview
├── LICENSE                  ← MIT
├── .toolkit-version         ← pinned book-theme commit (SHA)
├── templates/
│   └── book-theme/          ← submodule of myst-templates/book-theme
├── css/
│   └── site.css             ← the CSS overlay
├── parts/
│   └── footer.md            ← default footer
├── plugins/
│   ├── README.md
│   └── myst-mermaid/        ← Python executable plugin
│       ├── plugin.py
│       ├── README.md
│       ├── mermaid.schema.json
│       └── examples/
├── bin/
│   └── sync.sh              ← copy-mode helper
├── docs/                    ← this docs site (deployed to Pages)
└── .github/workflows/
    └── docs-deploy.yml      ← builds + publishes docs/
```

## Development setup

```bash
git clone --recurse-submodules https://github.com/snap2insight/myst-docs-toolkit
cd myst-docs-toolkit

# Build the docs locally
cd docs
TOOLKIT_LOCAL=.. ./bin/setup-dev.sh   # not yet written; see below
myst build --html
```

(Or just open files in your editor — most of the toolkit is plain text;
no build step beyond the docs site itself.)

## Style guides

- **CSS:** keep `site.css` brand-neutral. Colors that aren't true
  grayscale belong in a branding layer.
- **Plugins:** prefer single-file Python plugins until a plugin grows
  past ~500 lines. Document with a per-plugin README and an
  `examples/` config.
- **Docs:** the docs site is the documentation. Add new pages to
  [`toc.yml`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/docs/toc.yml)
  in the right reading-order slot.

## Pull-request checklist

- [ ] CI builds the toolkit's own docs without warnings.
- [ ] If you changed CSS, you visually inspected the toolkit's docs
      site (the easiest dogfood test).
- [ ] If you added a plugin, you wrote a README and an example config.
- [ ] If you bumped the bundled `book-theme` submodule, you mentioned
      what changed in the PR description.

## Releases

See [Releases](releases.md) for how versions are cut.

## License

By contributing you agree your contributions are licensed under the
same terms as the toolkit (MIT). The `Co-Authored-By` trailer in commit
messages is fine if you used an AI assistant.
