"""Safety and consistency checks every algorithm plugin must pass.

Merged plugins are published automatically, so these checks keep plugin
code limited to drawing: no file, network or process access, a bounded
render time and output size, and consistent metadata.
"""

import ast
import os
import re
import subprocess
import time
from pathlib import Path

import pytest

from algo_art_frames.algorithms import REGISTRY
from algo_art_frames.algorithms.base import AlgorithmCategory
from algo_art_frames.render.canvas import RenderContext
from algo_art_frames.render.theme import PRESETS, resolve_theme

ALGORITHMS_DIR = (
    Path(__file__).resolve().parents[1] / "src" / "algo_art_frames" / "algorithms"
)
PLUGIN_FILES = sorted(
    p for p in ALGORITHMS_DIR.glob("*.py") if not p.name.startswith("_") and p.name != "base.py"
)

ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "algo_art_frames",
    "collections",
    "dataclasses",
    "enum",
    "functools",
    "heapq",
    "itertools",
    "math",
    "random",
    "re",
    "typing",
}
FORBIDDEN_CALLS = {
    "__import__",
    "breakpoint",
    "compile",
    "eval",
    "exec",
    "getattr",
    "globals",
    "input",
    "locals",
    "open",
    "setattr",
    "vars",
}
FORBIDDEN_ATTRIBUTES = {"__builtins__", "__class__", "__globals__", "__subclasses__", "__code__"}

MAX_RENDER_SECONDS = 2.0
MAX_SVG_BYTES = 1_000_000
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def _import_roots(tree: ast.AST) -> set[str]:
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                roots.add("algo_art_frames")
            elif node.module:
                roots.add(node.module.split(".")[0])
    return roots


@pytest.mark.parametrize("path", PLUGIN_FILES, ids=lambda p: p.name)
def test_plugin_imports_only_allowed_modules(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    disallowed = _import_roots(tree) - ALLOWED_IMPORT_ROOTS
    assert not disallowed, (
        f"{path.name} imports {sorted(disallowed)}. Plugins may only import "
        f"{sorted(ALLOWED_IMPORT_ROOTS)}."
    )


@pytest.mark.parametrize("path", PLUGIN_FILES, ids=lambda p: p.name)
def test_plugin_avoids_forbidden_builtins(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    problems = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_CALLS:
            problems.append(f"line {node.lineno}: {node.id}")
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRIBUTES:
            problems.append(f"line {node.lineno}: .{node.attr}")
    assert not problems, f"{path.name} uses forbidden names: {problems}"


def test_every_plugin_file_is_registered():
    registered = {plugin.draw.__module__.rsplit(".", 1)[-1] for plugin in REGISTRY.values()}
    unregistered = {p.stem for p in PLUGIN_FILES} - registered
    assert not unregistered, (
        f"{sorted(unregistered)} not registered: add them to _MODULES in algorithms/__init__.py"
    )


@pytest.mark.parametrize("slug", sorted(REGISTRY))
def test_plugin_metadata(slug):
    plugin = REGISTRY[slug]
    assert SLUG_RE.match(plugin.slug), f"slug '{plugin.slug}' is not kebab-case"
    module_name = plugin.draw.__module__.rsplit(".", 1)[-1]
    assert module_name == plugin.slug.replace("-", "_"), (
        f"slug '{plugin.slug}' should live in {plugin.slug.replace('-', '_')}.py, "
        f"not {module_name}.py"
    )
    assert HEX_RE.match(plugin.accent), f"accent '{plugin.accent}' is not a hex color"
    assert isinstance(plugin.category, AlgorithmCategory)
    assert plugin.title.strip() and plugin.tagline.strip()
    assert plugin.pseudocode and all(isinstance(line, str) for line in plugin.pseudocode)
    assert "TODO" not in " ".join([plugin.title, plugin.tagline, *plugin.pseudocode])


@pytest.mark.parametrize("slug", sorted(REGISTRY))
@pytest.mark.parametrize("theme_name", sorted(PRESETS))
def test_plugin_render_budget(slug, theme_name):
    plugin = REGISTRY[slug]
    ctx = RenderContext(
        theme=resolve_theme(theme_name, plugin.accent),
        width=1200,
        height=1600,
        author=plugin.author,
        date=plugin.date,
    )
    start = time.perf_counter()
    svg = plugin.draw(ctx)
    elapsed = time.perf_counter() - start
    assert elapsed < MAX_RENDER_SECONDS, f"{slug} took {elapsed:.2f}s (limit {MAX_RENDER_SECONDS}s)"
    size = len(svg.encode("utf-8"))
    assert size < MAX_SVG_BYTES, f"{slug} produced {size} bytes of SVG (limit {MAX_SVG_BYTES})"


DISPLAY_TOGGLES = {
    "show_frame": True,
    "show_pseudocode": False,
    "show_tagline": False,
    "show_author": False,
}


@pytest.mark.parametrize("slug", sorted(REGISTRY))
@pytest.mark.parametrize("toggle", sorted(DISPLAY_TOGGLES))
def test_plugin_honors_display_options(slug, toggle):
    """Every display option a viewer can switch must visibly change the poster.
    Build the poster with new_canvas(ctx, ...) and use the content box it
    returns, so the frame, pseudocode, tagline and author are handled for you."""
    plugin = REGISTRY[slug]

    def render(**overrides):
        ctx = RenderContext(
            theme=resolve_theme("dark", plugin.accent),
            width=1200,
            height=1600,
            author=plugin.author or "Test Author",
            date=plugin.date,
            **overrides,
        )
        return plugin.draw(ctx)

    assert render(**{toggle: DISPLAY_TOGGLES[toggle]}) != render(), f"{slug} ignores {toggle}"


def _git_base_slugs() -> set[str] | None:
    """Slugs registered on the PR's base branch, or None when there's no base to compare to."""
    base_ref = os.environ.get("BASE_REF")
    if not base_ref:
        return None
    init_path = "src/algo_art_frames/algorithms/"
    try:
        listing = subprocess.run(
            ["git", "ls-tree", "--name-only", base_ref, init_path],
            check=True,
            capture_output=True,
            encoding="utf-8",
        ).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        pytest.fail(f"could not read base ref '{base_ref}' (fetch it before running the tests)")
    slugs = set()
    for name in listing:
        file_name = name.rsplit("/", 1)[-1]
        if file_name.startswith("_") or file_name == "base.py" or not file_name.endswith(".py"):
            continue
        source = subprocess.run(
            ["git", "show", f"{base_ref}:{name}"], check=True, capture_output=True, encoding="utf-8"
        ).stdout
        match = re.search(r"\bslug\s*=\s*['\"]([^'\"]+)['\"]", source)
        if match:
            slugs.add(match.group(1))
    return slugs


def test_no_slug_removed_or_renamed():
    """Slugs are append-only: published posters are identified by their slug.

    Runs in CI with BASE_REF set to the PR's base branch (e.g. origin/main).
    To deliberately retire a slug, a maintainer sets ALLOW_SLUG_REMOVAL=1 for
    that run.
    """
    base_slugs = _git_base_slugs()
    if base_slugs is None:
        pytest.skip("BASE_REF not set, nothing to compare against")
    if os.environ.get("ALLOW_SLUG_REMOVAL") == "1":
        pytest.skip("slug removal explicitly allowed for this run")
    removed = base_slugs - set(REGISTRY)
    assert not removed, f"slug(s) removed or renamed: {sorted(removed)}"
