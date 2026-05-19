"""
Integration test: feeds the plugin's output through @mermaid-js/mermaid-cli
(`mmdc`) and verifies that the rendered SVG is valid.

This catches the class of bug where the plugin emits a frontmatter
config block that mermaid.js itself rejects — e.g., bad theme name,
malformed themeVariables, missing required keys. Without this test we
only know the AST shape is right; we don't know whether mermaid will
actually render it.

Requires: `npx @mermaid-js/mermaid-cli` available on PATH (Node 18+).
Skipped automatically if `mmdc` isn't installed.

Run:
  npm install -g @mermaid-js/mermaid-cli
  pytest plugins/myst-mermaid/tests/test_mermaid_cli.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1] / "plugin.py"


def has_mmdc() -> bool:
    return shutil.which("mmdc") is not None


pytestmark = pytest.mark.skipif(
    not has_mmdc(),
    reason="mermaid-cli (mmdc) not installed. Install with `npm install -g @mermaid-js/mermaid-cli`.",
)


def run_plugin(stdin: str, args: list[str]) -> dict:
    proc = subprocess.run(
        [sys.executable, str(PLUGIN), *args],
        input=stdin,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"plugin failed: {proc.stderr}")
    return json.loads(proc.stdout)


def extract_mermaid_body(transformed_root: dict, variant: str) -> str:
    """Pull the mermaid-block body string out of the transformed AST."""
    wrapper = transformed_root["children"][0]
    assert wrapper["class"] == "mermaid-dual-container"
    for v in wrapper["children"]:
        if v["class"] == variant:
            return v["children"][0]["value"]
    raise AssertionError(f"variant {variant} not found")


def render_with_mmdc(mermaid_body: str, out_dir: Path, name: str) -> Path:
    """Run mmdc to render the body to SVG. Returns the SVG path.

    If mmdc fails because puppeteer can't find a Chrome binary (very common
    in local environments), the test is skipped rather than failed — we
    can't validate mermaid output without a renderer. Genuine mermaid
    config errors still surface as failures.
    """
    in_path = out_dir / f"{name}.mmd"
    out_path = out_dir / f"{name}.svg"
    in_path.write_text(mermaid_body)

    proc = subprocess.run(
        ["mmdc", "-i", str(in_path), "-o", str(out_path), "--quiet"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        combined = proc.stdout + proc.stderr
        if "Could not find Chrome" in combined or "puppeteer browsers install" in combined:
            pytest.skip(
                "mmdc can't find a compatible Chrome. "
                "Install with: `npx puppeteer browsers install chrome-headless-shell`. "
                "CI workflows install this explicitly."
            )
        raise RuntimeError(
            f"mmdc failed (exit {proc.returncode}):\n"
            f"stdout: {proc.stdout}\n"
            f"stderr: {proc.stderr}\n"
            f"input was:\n{mermaid_body}"
        )
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMmdcCanRenderPluginOutput:
    DIAGRAM = "graph LR\nA[Start] --> B[End]"

    def _transform(self):
        ast = {"type": "root", "children": [
            {"type": "code", "lang": "mermaid", "value": self.DIAGRAM}
        ]}
        return run_plugin(json.dumps(ast), ["--transform", "mermaid-dual"])

    def test_light_variant_renders_to_svg(self, tmp_path):
        out = self._transform()
        body = extract_mermaid_body(out, "mermaid-light")
        svg_path = render_with_mmdc(body, tmp_path, "light")
        assert svg_path.exists()
        assert svg_path.stat().st_size > 0
        # Should be parseable XML.
        ET.parse(svg_path)

    def test_dark_variant_renders_to_svg(self, tmp_path):
        out = self._transform()
        body = extract_mermaid_body(out, "mermaid-dark")
        svg_path = render_with_mmdc(body, tmp_path, "dark")
        assert svg_path.exists()
        assert svg_path.stat().st_size > 0
        ET.parse(svg_path)

    def test_both_variants_produce_distinct_svgs(self, tmp_path):
        out = self._transform()
        light_body = extract_mermaid_body(out, "mermaid-light")
        dark_body = extract_mermaid_body(out, "mermaid-dark")

        light_svg = render_with_mmdc(light_body, tmp_path, "L")
        dark_svg = render_with_mmdc(dark_body, tmp_path, "D")

        light_content = light_svg.read_text()
        dark_content = dark_svg.read_text()

        # Both should be SVG.
        assert "<svg" in light_content
        assert "<svg" in dark_content

        # Same diagram structure (same nodes), so size will be close but
        # the colors should differ — mermaid bakes theme colors in.
        # We can't easily compare colors without parsing the SVG; here we
        # just sanity-check that mermaid produced different output for
        # the two themes (because content differs in at least theme-driven
        # color strings).
        assert light_content != dark_content


class TestUserProjectConfigIsValid:
    """
    Sanity-check the mermaid config the toolkit's own docs site uses —
    if the docs-site config (docs/myst-mermaid.yml) ever produces output
    mmdc can't render, this test catches it.
    """

    def test_docs_site_config_renders(self, tmp_path):
        docs_config = (
            Path(__file__).resolve().parents[3]
            / "docs" / "myst-mermaid.yml"
        )
        assert docs_config.exists(), f"missing {docs_config}"

        ast = {"type": "root", "children": [
            {"type": "code", "lang": "mermaid", "value": "graph LR\nA --> B"}
        ]}
        out = run_plugin(
            json.dumps(ast),
            ["--transform", "mermaid-dual", "--config-dir", str(docs_config.parent)],
        )
        for variant in ("mermaid-light", "mermaid-dark"):
            body = extract_mermaid_body(out, variant)
            render_with_mmdc(body, tmp_path, variant)
