from types import SimpleNamespace
from xml.etree import ElementTree

import pytest

from algo_art_frames.algorithms import REGISTRY, _build_registry
from algo_art_frames.render.canvas import RenderContext
from algo_art_frames.render.theme import DARK, LIGHT

EXPECTED_SLUGS = {
    "binary-search",
    "quicksort",
    "a-star-search",
    "rsa-encryption",
    "fast-fourier-transform",
    "k-means-clustering",
    "knuth-morris-pratt",
    "minimax",
    "monte-carlo",
    "genetic-algorithms",
    "ray-tracing",
    "singular-value-decomposition",
    "deflate-compression",
    "hyperloglog",
    "pagerank",
    "backpropagation",
}


def test_registry_has_all_sixteen_algorithms():
    assert set(REGISTRY) == EXPECTED_SLUGS


def test_build_registry_rejects_duplicate_slugs():
    duplicate_modules = (
        SimpleNamespace(PLUGIN=SimpleNamespace(slug="binary-search")),
        SimpleNamespace(PLUGIN=SimpleNamespace(slug="binary-search")),
    )
    with pytest.raises(ValueError, match="Duplicate algorithm slug"):
        _build_registry(duplicate_modules)


@pytest.mark.parametrize("slug", sorted(EXPECTED_SLUGS))
@pytest.mark.parametrize("theme", [DARK, LIGHT])
def test_plugin_draw_returns_valid_svg(slug, theme):
    plugin = REGISTRY[slug]
    ctx = RenderContext(theme=theme, width=1200, height=1600)

    svg = plugin.draw(ctx)

    assert svg.strip().startswith("<svg")
    root = ElementTree.fromstring(svg)
    assert root.tag.endswith("svg")


@pytest.mark.parametrize("slug", sorted(EXPECTED_SLUGS))
def test_plugin_has_signature_accent(slug):
    plugin = REGISTRY[slug]
    assert plugin.accent.startswith("#") and len(plugin.accent) in (4, 7)
