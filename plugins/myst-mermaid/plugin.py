#!/usr/bin/env python3
"""
myst-mermaid — a generic MyST executable plugin for Mermaid diagrams.

What it does
------------
Walks the MyST AST looking for Mermaid blocks (either `{mermaid}` directives
or fenced code blocks tagged ```mermaid``) and rewrites each block into two
parallel renderings — one with the user-configured light theme and one
forced into Mermaid's `dark` theme — wrapped in `.mermaid-light` and
`.mermaid-dark` containers. Companion CSS (shipped in the docs toolkit's
`css/site.css`) hides the variant that doesn't match the page's color
scheme, so the same diagram renders correctly in both light and dark mode.

Single-render mode is supported too (see `dual_render: false` below).

Configuration
-------------
The plugin looks for a `myst-mermaid.yml` file in the current working
directory and walks parent directories until it finds one. Every key in
the file is passed to mermaid.js as a config value, EXCEPT for these two
plugin-level keys:

  dual_render: true | false      — emit light + dark variants (default: true)
  config_file: path/to/file.yml  — load mermaid config from a separate file

Per-diagram frontmatter inside a mermaid block (a YAML `---` block at the
top of the block's body) overrides the global config for that diagram.

Example `myst-mermaid.yml`:

    dual_render: true
    theme: default
    themeVariables:
      primaryColor: '#1f2937'
      primaryTextColor: '#f9fafb'

Installation in a MyST project
-------------------------------
Add to `myst.yml`:

    project:
      plugins:
        - type: executable
          path: _toolkit/plugins/myst-mermaid/plugin.py

Dependencies: `pyyaml`, `jsonschema`. Install with `pip install pyyaml jsonschema`.

Usage in markdown
-----------------
Either of these forms is recognized:

    ```{mermaid}
    graph LR; A --> B
    ```

    ```mermaid
    graph LR; A --> B
    ```

Per-diagram overrides go in a frontmatter block at the top of the body:

    ```{mermaid}
    ---
    config:
      theme: forest
    ---
    graph LR; A --> B
    ```

Reserved keys popped before passing to mermaid.js:
  - `dual_render`, `config_file` — plugin-level settings
  - `plugin` — reserved namespace for future plugin keys

License: MIT (matches the parent myst-docs-toolkit repo).
"""

import argparse
import copy
import json
import os
import sys
from urllib.request import urlopen

try:
    import yaml
except ImportError:
    print(
        "[myst-mermaid] ERROR: pyyaml is not installed. Run: pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from jsonschema import ValidationError, validate
except ImportError:
    validate = None
    ValidationError = Exception

PLUGIN_NAME = "myst-mermaid"
TRANSFORM_NAME = "mermaid-dual"
CONFIG_FILENAME = "myst-mermaid.yml"

SCHEMA_URL = "https://mermaid.js.org/schemas/config.schema.json"
SCHEMA_CACHE_FILE = "mermaid.schema.json"

PLUGIN_LEVEL_KEYS = {"dual_render", "config_file", "plugin"}


def log(msg):
    """Log to stderr so messages surface in MyST build logs."""
    print(f"[{PLUGIN_NAME}] {msg}", file=sys.stderr)


# ─────────────────────────────────────────────────────────────────────────────
# Config loading
# ─────────────────────────────────────────────────────────────────────────────

def find_config(start_dir=None):
    """
    Locate `myst-mermaid.yml` starting at `start_dir` (or CWD) and walking
    upward until the filesystem root. Returns absolute path or None.
    """
    current = os.path.abspath(start_dir or os.getcwd())
    while True:
        candidate = os.path.join(current, CONFIG_FILENAME)
        if os.path.exists(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def load_config(start_dir=None):
    """
    Load `myst-mermaid.yml` plus any external `config_file` referenced
    inside it. Returns a single merged dict.
    """
    config_path = find_config(start_dir)
    if not config_path:
        return {}

    try:
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f) or {}
    except Exception as e:
        log(f"WARNING: failed to parse {config_path}: {e}")
        return {}

    log(f"loaded config from {config_path}")

    # Optionally pull in mermaid config from a separate file.
    external = cfg.get("config_file")
    if external:
        external_path = os.path.join(os.path.dirname(config_path), external)
        if os.path.exists(external_path):
            try:
                with open(external_path, "r") as f:
                    external_cfg = yaml.safe_load(f) or {}
                # External keys are mermaid-config keys; merge into cfg as
                # baseline, then let in-file keys override.
                merged = deep_merge(external_cfg, copy.deepcopy(cfg))
                cfg = merged
                log(f"merged mermaid config from {external_path}")
            except Exception as e:
                log(f"WARNING: failed to load config_file {external_path}: {e}")
        else:
            log(f"WARNING: config_file not found at {external_path}")

    return cfg


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def deep_merge(source, destination):
    """
    Merge `source` into `destination` recursively. Existing keys in
    `destination` win — `source` provides defaults. Returns `destination`.
    """
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            deep_merge(value, node)
        elif key not in destination:
            destination[key] = value
    return destination


def split_plugin_and_mermaid(cfg):
    """
    Separate plugin-level keys from mermaid config keys.
    Returns (plugin_settings_dict, mermaid_config_dict).
    """
    plugin_settings = {}
    mermaid_config = {}
    for k, v in cfg.items():
        if k in PLUGIN_LEVEL_KEYS:
            plugin_settings[k] = v
        else:
            mermaid_config[k] = v
    return plugin_settings, mermaid_config


def get_schema():
    """
    Return the cached Mermaid config JSON Schema. Fetches from mermaid.js.org
    on first miss if network is available; falls back to None on failure.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cache_path = os.path.join(script_dir, SCHEMA_CACHE_FILE)

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except Exception:
            log("schema cache unreadable, attempting refetch")

    try:
        log(f"fetching schema from {SCHEMA_URL}")
        with urlopen(SCHEMA_URL) as resp:
            schema = json.loads(resp.read().decode())
        with open(cache_path, "w") as f:
            json.dump(schema, f)
        return schema
    except Exception as e:
        log(f"WARNING: failed to fetch schema ({e}); skipping validation")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Mermaid node construction
# ─────────────────────────────────────────────────────────────────────────────

def build_mermaid_node(original_node, mermaid_config, wrapper_class):
    """
    Take an existing mermaid node, merge its inline frontmatter (if any)
    with `mermaid_config`, validate against the Mermaid schema, and return
    a new mermaid node (optionally wrapped in a container div with the
    given class).
    """
    body = original_node.get("value", "")
    inline_config = {}
    diagram_code = body

    # Pull config out of a leading `--- ... ---` frontmatter block.
    if body.strip().startswith("---"):
        parts = body.split("---", 2)
        if len(parts) >= 3:
            try:
                parsed = yaml.safe_load(parts[1]) or {}
                if isinstance(parsed, dict) and "config" in parsed:
                    inline_config = parsed["config"]
                    diagram_code = parts[2]
            except Exception:
                pass  # Malformed frontmatter — leave body untouched.

    # Per-diagram inline config wins; the project config provides defaults.
    merged = copy.deepcopy(inline_config)
    deep_merge(mermaid_config, merged)

    # Strip any plugin-level keys that may have been merged in.
    for k in PLUGIN_LEVEL_KEYS:
        merged.pop(k, None)

    # Best-effort schema validation. Failures log but don't abort the build.
    if validate is not None:
        schema = get_schema()
        if schema:
            try:
                validate(instance=merged, schema=schema)
            except ValidationError as e:
                log(f"WARNING: mermaid config does not validate: {e.message}")

    # Rebuild the node body with the merged config as new frontmatter.
    try:
        yml = yaml.dump(merged, default_flow_style=False)
        indented = "\n".join("  " + line for line in yml.splitlines())
        new_body = f"---\nconfig:\n{indented}\n---\n{diagram_code.strip()}"
    except Exception as e:
        log(f"WARNING: failed to serialize config back to frontmatter: {e}")
        new_body = body

    new_node = copy.deepcopy(original_node)
    new_node["type"] = "mermaid"
    new_node["value"] = new_body

    if wrapper_class:
        return {
            "type": "container",
            "kind": "div",
            "class": wrapper_class,
            "children": [new_node],
        }
    return new_node


# ─────────────────────────────────────────────────────────────────────────────
# AST walk
# ─────────────────────────────────────────────────────────────────────────────

def is_mermaid_node(node):
    """True if `node` is a mermaid block in any of the recognized forms."""
    t = node.get("type", "")
    if t == "mermaid":
        return True
    if t == "code" and (node.get("lang") or "").strip().lower() == "mermaid":
        return True
    if t == "mystDirective" and node.get("name", "").strip().lower() == "mermaid":
        return True
    return False


def normalize_mermaid_node(node):
    """
    For directive-form mermaid blocks, convert to a plain mermaid node so
    downstream code only sees one shape.
    """
    if node.get("type") == "mystDirective" and node.get("name", "").lower() == "mermaid":
        return {"type": "mermaid", "value": node.get("value", "")}
    return node


def transform(node, mermaid_config, plugin_settings):
    """
    Recursively transform `node`. Returns a list of replacement nodes
    (usually one; for dual-render, the mermaid node becomes one container
    node wrapping two children).
    """
    if is_mermaid_node(node):
        node = normalize_mermaid_node(node)
        dual = plugin_settings.get("dual_render", True)

        if not dual:
            return [build_mermaid_node(node, copy.deepcopy(mermaid_config), None)]

        light_cfg = copy.deepcopy(mermaid_config)
        dark_cfg = copy.deepcopy(mermaid_config)
        dark_cfg["theme"] = "dark"

        light = build_mermaid_node(node, light_cfg, "mermaid-light")
        dark = build_mermaid_node(node, dark_cfg, "mermaid-dark")

        # Hoist identifier/label/html_id from the original mermaid node to
        # the container so cross-references still resolve.
        ident = node.get("identifier")
        lbl = node.get("label")
        html_id = node.get("html_id")
        for target in (light, dark):
            for attr in ("identifier", "label", "html_id"):
                target.pop(attr, None)
                if target.get("children"):
                    target["children"][0].pop(attr, None)

        wrapper = {
            "type": "container",
            "kind": "div",
            "class": "mermaid-dual-container",
            "children": [light, dark],
        }
        if ident:
            wrapper["identifier"] = ident
        if lbl:
            wrapper["label"] = lbl
        if html_id:
            wrapper["html_id"] = html_id

        return [wrapper]

    if "children" in node and isinstance(node["children"], list):
        new_children = []
        for child in node["children"]:
            new_children.extend(transform(child, mermaid_config, plugin_settings))
        node["children"] = new_children

    return [node]


def run_transform(data, cfg):
    """Top-level transform entry — receives MDAST, returns MDAST."""
    plugin_settings, mermaid_config = split_plugin_and_mermaid(cfg or {})
    plugin_settings.setdefault("dual_render", True)

    if isinstance(data.get("children"), list):
        new_children = []
        for child in data["children"]:
            new_children.extend(transform(child, mermaid_config, plugin_settings))
        data["children"] = new_children

    return data


# ─────────────────────────────────────────────────────────────────────────────
# MyST plugin protocol
# ─────────────────────────────────────────────────────────────────────────────

PLUGIN_SPEC = {
    "name": PLUGIN_NAME,
    "directives": [],
    "transforms": [
        {"name": TRANSFORM_NAME, "stage": "document"},
    ],
}


def main():
    parser = argparse.ArgumentParser(description=f"{PLUGIN_NAME} MyST plugin")
    parser.add_argument("--transform", help="transform name to apply")
    parser.add_argument("--format", default="json")
    parser.add_argument("--config-dir", default=None,
                        help="base directory to search for myst-mermaid.yml")
    args, _ = parser.parse_known_args()

    if args.transform:
        if args.transform != TRANSFORM_NAME:
            # Unknown transform — pass through.
            sys.stdout.write(sys.stdin.read())
            return

        cfg = load_config(args.config_dir)
        try:
            raw = sys.stdin.read()
            if not raw.strip():
                return
            data = json.loads(raw)
            result = run_transform(data, cfg)
            sys.stdout.write(json.dumps(result))
        except Exception as e:
            log(f"ERROR during transform: {e}")
            sys.exit(1)
    else:
        print(json.dumps(PLUGIN_SPEC))


if __name__ == "__main__":
    main()
