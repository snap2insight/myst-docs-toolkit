"""
Unit tests for plugins/myst-mermaid/plugin.py.

Runs the plugin as a subprocess (the same way MyST invokes it) and asserts
on the JSON it emits. Covers:

  - PLUGIN_SPEC is well-formed when invoked with no args.
  - Various input shapes (code block, mermaid node, directive) are recognized.
  - dual_render: true emits the three-node dual container.
  - dual_render: false emits a single mermaid node.
  - Per-diagram frontmatter overrides the project config.
  - Dark variant forces theme=dark regardless of light-mode config.
  - identifier / label / html_id hoist to the outer container.

Run:
  pytest plugins/myst-mermaid/tests/
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

PLUGIN = Path(__file__).resolve().parents[1] / "plugin.py"


def run_plugin(stdin: str | None = None, args: list[str] | None = None, cwd: str | None = None) -> dict[str, Any]:
    """Invoke plugin.py and return parsed JSON stdout."""
    cmd = [sys.executable, str(PLUGIN), *(args or [])]
    proc = subprocess.run(
        cmd,
        input=stdin,
        capture_output=True,
        text=True,
        cwd=cwd or os.getcwd(),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"plugin exited {proc.returncode}: {proc.stderr}")
    if not proc.stdout.strip():
        return {}
    return json.loads(proc.stdout)


def find_node(node, predicate):
    """Walk the AST and yield every node matching `predicate(node)`."""
    if isinstance(node, dict):
        if predicate(node):
            yield node
        for v in node.values():
            yield from find_node(v, predicate)
    elif isinstance(node, list):
        for item in node:
            yield from find_node(item, predicate)


# ─────────────────────────────────────────────────────────────────────────────
# Plugin spec
# ─────────────────────────────────────────────────────────────────────────────

class TestPluginSpec:
    def test_emits_spec_with_no_args(self):
        spec = run_plugin()
        assert spec["name"] == "myst-mermaid"
        assert spec["directives"] == []
        # We register exactly one transform; no roles or other extensions.
        assert len(spec["transforms"]) == 1
        assert spec["transforms"][0]["name"] == "mermaid-dual"
        assert spec["transforms"][0]["stage"] == "document"


# ─────────────────────────────────────────────────────────────────────────────
# Transform — recognition of input shapes
# ─────────────────────────────────────────────────────────────────────────────

class TestRecognition:
    def _run(self, child):
        ast = {"type": "root", "children": [child]}
        return run_plugin(stdin=json.dumps(ast), args=["--transform", "mermaid-dual"])

    def test_code_block_lang_mermaid_is_recognized(self):
        out = self._run({"type": "code", "lang": "mermaid", "value": "graph LR\nA --> B"})
        # Should produce a mermaid-dual-container.
        containers = list(find_node(out, lambda n: isinstance(n, dict) and n.get("class") == "mermaid-dual-container"))
        assert len(containers) == 1

    def test_bare_mermaid_node_is_recognized(self):
        out = self._run({"type": "mermaid", "value": "graph LR\nA --> B"})
        containers = list(find_node(out, lambda n: isinstance(n, dict) and n.get("class") == "mermaid-dual-container"))
        assert len(containers) == 1

    def test_mystdirective_mermaid_is_recognized(self):
        out = self._run({"type": "mystDirective", "name": "mermaid", "value": "graph LR\nA --> B"})
        containers = list(find_node(out, lambda n: isinstance(n, dict) and n.get("class") == "mermaid-dual-container"))
        assert len(containers) == 1

    def test_non_mermaid_passes_through(self):
        ast = {"type": "root", "children": [
            {"type": "paragraph", "children": [{"type": "text", "value": "Hello"}]},
            {"type": "code", "lang": "python", "value": "print('hi')"},
        ]}
        out = run_plugin(stdin=json.dumps(ast), args=["--transform", "mermaid-dual"])
        # No mermaid-dual-container should have been introduced.
        containers = list(find_node(out, lambda n: isinstance(n, dict) and n.get("class") == "mermaid-dual-container"))
        assert containers == []
        # And the original two children are preserved (same types).
        assert [c["type"] for c in out["children"]] == ["paragraph", "code"]


# ─────────────────────────────────────────────────────────────────────────────
# Transform — output shape and config
# ─────────────────────────────────────────────────────────────────────────────

class TestDualRenderOutput:
    AST_INPUT = {
        "type": "root",
        "children": [
            {"type": "code", "lang": "mermaid", "value": "graph LR\nA --> B"}
        ],
    }

    def setup_method(self):
        self.out = run_plugin(stdin=json.dumps(self.AST_INPUT), args=["--transform", "mermaid-dual"])

    def test_top_level_structure_is_dual_container(self):
        children = self.out["children"]
        assert len(children) == 1
        wrapper = children[0]
        assert wrapper["type"] == "container"
        assert wrapper["class"] == "mermaid-dual-container"

    def test_wrapper_has_two_children_light_then_dark(self):
        wrapper = self.out["children"][0]
        assert len(wrapper["children"]) == 2
        assert wrapper["children"][0]["class"] == "mermaid-light"
        assert wrapper["children"][1]["class"] == "mermaid-dark"

    def test_each_variant_wraps_exactly_one_mermaid_node(self):
        wrapper = self.out["children"][0]
        for variant in wrapper["children"]:
            assert variant["type"] == "container"
            assert len(variant["children"]) == 1
            mermaid_node = variant["children"][0]
            assert mermaid_node["type"] == "mermaid"
            assert "graph LR" in mermaid_node["value"]

    def test_dark_variant_forces_theme_dark(self):
        wrapper = self.out["children"][0]
        dark_value = wrapper["children"][1]["children"][0]["value"]
        # Look for `theme: dark` in the injected frontmatter.
        assert "theme: dark" in dark_value

    def test_light_variant_does_not_force_dark(self):
        wrapper = self.out["children"][0]
        light_value = wrapper["children"][0]["children"][0]["value"]
        # No theme: dark in the light variant (unless the user explicitly set it).
        assert "theme: dark" not in light_value


class TestSingleRender:
    def test_dual_render_off_emits_single_node(self, tmp_path):
        # Write a config that turns dual_render off in tmp_path; the plugin
        # walks parent dirs looking for myst-mermaid.yml, so we point it
        # at tmp_path via --config-dir.
        cfg = tmp_path / "myst-mermaid.yml"
        cfg.write_text("dual_render: false\n")

        ast = {"type": "root", "children": [
            {"type": "code", "lang": "mermaid", "value": "graph LR\nA --> B"}
        ]}
        out = run_plugin(
            stdin=json.dumps(ast),
            args=["--transform", "mermaid-dual", "--config-dir", str(tmp_path)],
            cwd=str(tmp_path),
        )

        # Single mermaid node at the top level — no dual-container.
        assert len(out["children"]) == 1
        node = out["children"][0]
        assert node["type"] == "mermaid"
        # And it's not wrapped.
        assert "class" not in node or node.get("class") not in (
            "mermaid-light", "mermaid-dark", "mermaid-dual-container"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Config handling
# ─────────────────────────────────────────────────────────────────────────────

class TestConfigMerging:
    def test_project_config_merged_into_variants(self, tmp_path):
        cfg = tmp_path / "myst-mermaid.yml"
        cfg.write_text("theme: forest\nfontFamily: 'system-ui'\n")

        ast = {"type": "root", "children": [
            {"type": "code", "lang": "mermaid", "value": "graph LR\nA --> B"}
        ]}
        out = run_plugin(
            stdin=json.dumps(ast),
            args=["--transform", "mermaid-dual", "--config-dir", str(tmp_path)],
            cwd=str(tmp_path),
        )

        light_value = out["children"][0]["children"][0]["children"][0]["value"]
        assert "theme: forest" in light_value
        assert "system-ui" in light_value

    def test_inline_frontmatter_overrides_project_config(self, tmp_path):
        cfg = tmp_path / "myst-mermaid.yml"
        cfg.write_text("theme: forest\n")

        # Inline frontmatter sets theme: neutral; should win.
        body = (
            "---\n"
            "config:\n"
            "  theme: neutral\n"
            "---\n"
            "graph LR\nA --> B"
        )
        ast = {"type": "root", "children": [
            {"type": "code", "lang": "mermaid", "value": body}
        ]}
        out = run_plugin(
            stdin=json.dumps(ast),
            args=["--transform", "mermaid-dual", "--config-dir", str(tmp_path)],
            cwd=str(tmp_path),
        )

        light_value = out["children"][0]["children"][0]["children"][0]["value"]
        assert "theme: neutral" in light_value
        # forest should NOT be the active theme (inline won).
        # It's fine if "forest" appears somewhere else, but theme: should be neutral.
        # Parse the frontmatter to be precise.
        import yaml
        parts = light_value.split("---")
        front = yaml.safe_load(parts[1])
        assert front["config"]["theme"] == "neutral"

    def test_plugin_level_keys_stripped_from_mermaid_config(self, tmp_path):
        # dual_render and config_file are plugin-level; they should be removed
        # from the mermaid-config-frontmatter the plugin embeds in nodes.
        cfg = tmp_path / "myst-mermaid.yml"
        cfg.write_text("dual_render: true\ntheme: default\n")

        ast = {"type": "root", "children": [
            {"type": "code", "lang": "mermaid", "value": "graph LR\nA --> B"}
        ]}
        out = run_plugin(
            stdin=json.dumps(ast),
            args=["--transform", "mermaid-dual", "--config-dir", str(tmp_path)],
            cwd=str(tmp_path),
        )

        light_value = out["children"][0]["children"][0]["children"][0]["value"]
        assert "dual_render" not in light_value
        assert "theme: default" in light_value


# ─────────────────────────────────────────────────────────────────────────────
# Identifier hoisting
# ─────────────────────────────────────────────────────────────────────────────

class TestIdentifierHoisting:
    def test_identifier_label_html_id_hoist_to_wrapper(self):
        ast = {"type": "root", "children": [{
            "type": "mermaid",
            "value": "graph LR\nA --> B",
            "identifier": "diagram-1",
            "label": "Diagram 1",
            "html_id": "diagram-1",
        }]}
        out = run_plugin(stdin=json.dumps(ast), args=["--transform", "mermaid-dual"])

        wrapper = out["children"][0]
        assert wrapper["class"] == "mermaid-dual-container"
        assert wrapper.get("identifier") == "diagram-1"
        assert wrapper.get("label") == "Diagram 1"
        assert wrapper.get("html_id") == "diagram-1"

        # And neither variant should carry the original identifier/label/id.
        for variant in wrapper["children"]:
            assert "identifier" not in variant
            assert "label" not in variant
            assert "html_id" not in variant
            # Inner mermaid node also stripped.
            assert "identifier" not in variant["children"][0]
            assert "label" not in variant["children"][0]
            assert "html_id" not in variant["children"][0]


# ─────────────────────────────────────────────────────────────────────────────
# Recursion — nested mermaid blocks
# ─────────────────────────────────────────────────────────────────────────────

class TestRecursion:
    def test_mermaid_inside_section_is_transformed(self):
        ast = {"type": "root", "children": [
            {"type": "section", "children": [
                {"type": "heading", "children": [{"type": "text", "value": "h"}]},
                {"type": "code", "lang": "mermaid", "value": "graph LR\nA --> B"},
            ]}
        ]}
        out = run_plugin(stdin=json.dumps(ast), args=["--transform", "mermaid-dual"])

        containers = list(find_node(out, lambda n: isinstance(n, dict) and n.get("class") == "mermaid-dual-container"))
        assert len(containers) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Edge cases
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_stdin_does_not_crash(self):
        # Plugin should handle empty input gracefully.
        proc = subprocess.run(
            [sys.executable, str(PLUGIN), "--transform", "mermaid-dual"],
            input="",
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0

    def test_unknown_transform_passes_through(self):
        ast = {"type": "root", "children": [
            {"type": "code", "lang": "mermaid", "value": "graph LR\nA --> B"}
        ]}
        out_raw = subprocess.run(
            [sys.executable, str(PLUGIN), "--transform", "some-other-transform"],
            input=json.dumps(ast),
            capture_output=True,
            text=True,
        )
        assert out_raw.returncode == 0
        # Should echo input unchanged.
        out = json.loads(out_raw.stdout)
        assert out["children"][0]["type"] == "code"
