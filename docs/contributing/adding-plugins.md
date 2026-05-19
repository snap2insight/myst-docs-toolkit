---
title: Adding a Plugin
---

# Adding a Plugin

How to add a new plugin to the toolkit.

## Decide the plugin's type

| Type | Language | When to use |
|---|---|---|
| **Executable** | Python (or anything that can read/write JSON on stdin/stdout) | Transforms that walk the MDAST; cross-language friendly |
| **JavaScript** | JS/TS | Custom directives, roles, or transforms that need to integrate with MyST's JS runtime |

The current `myst-mermaid` is executable Python. Add a JS plugin if
you need a directive (e.g., a new `{video}` directive) — that's where
JS support is cleaner.

## Layout

Create a new subdirectory under `plugins/`:

```
plugins/
└── your-plugin/
    ├── plugin.py                          ← or plugin.mjs for JS
    ├── README.md                          ← what it does, how to use
    ├── examples/
    │   └── your-plugin.example.yml        ← starter config
    └── (any schemas, assets, etc.)
```

For multi-file Python plugins, keep `plugin.py` as the entry point and
add modules next to it as the plugin grows. There's no requirement to
make it a `pip`-installable package — the plugin lives inside the
toolkit, period.

## Implement the MyST plugin protocol

For an executable plugin, your entry point:

1. When invoked with no `--transform` flag, prints a JSON
   `PLUGIN_SPEC` to stdout (name + directives/roles/transforms).
2. When invoked with `--transform <name>`, reads MDAST JSON from
   stdin, applies the transform, writes MDAST JSON to stdout.

A skeleton:

```python
#!/usr/bin/env python3
import argparse, json, sys

PLUGIN_NAME = "your-plugin"
TRANSFORM_NAME = "your-transform"

PLUGIN_SPEC = {
    "name": PLUGIN_NAME,
    "directives": [],
    "transforms": [{"name": TRANSFORM_NAME, "stage": "document"}],
}

def run_transform(data):
    # Walk data["children"], modify in place, return data
    return data

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--transform")
    args, _ = p.parse_known_args()
    if args.transform == TRANSFORM_NAME:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        sys.stdout.write(json.dumps(run_transform(json.loads(raw))))
    else:
        print(json.dumps(PLUGIN_SPEC))

if __name__ == "__main__":
    main()
```

See `plugins/myst-mermaid/plugin.py` for a fuller example with config
loading and validation.

## Update toolkit docs

1. Add a row to [`plugins/README.md`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/plugins/README.md).
2. Add a `docs/plugins/your-plugin.md` page (modeled on
   [`docs/plugins/myst-mermaid.md`](../plugins/myst-mermaid.md)).
3. Add it to [`docs/toc.yml`](https://github.com/snap2insight/myst-docs-toolkit/blob/main/docs/toc.yml)
   under the Plugins section.
4. Mention it in [`docs/capabilities/plugins.md`](../capabilities/plugins.md)'s
   "Current plugins" table.

## Dogfood it in the docs site

If your plugin has a visible effect on rendered pages, demo it on its
own docs page. The mermaid plugin does this — see the diagram on
[its page](../plugins/myst-mermaid.md).

Doing so means the docs deploy workflow has to enable the plugin and
install its runtime deps. Mention these in your PR description so
they get added to `.github/workflows/docs-deploy.yml`.

## What plugins should *not* do

- **Don't depend on the consumer's branding.** Plugins should work for
  any user of the toolkit, not assume a particular CSS theme or org
  context.
- **Don't fetch remote resources at build time** without a clear
  fallback. The mermaid plugin caches the schema; if you need
  network, do the same.
- **Don't write outside `_build/`.** Plugins receive an AST and return
  an AST. Side effects on disk are surprising and harder to debug.

## Asking for review

Tag the PR with `plugin` and mention what AST shapes the plugin
operates on and what nodes it produces. A maintainer will look at
correctness, naming, and whether the plugin belongs in the toolkit vs
as a separate package.
