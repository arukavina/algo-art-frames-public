"""Tests for the local preview CLI (python -m algo_art_frames.preview)."""

import xml.etree.ElementTree as ET

import pytest

from algo_art_frames.preview import Options, all_variations, main, render_svg
from algo_art_frames.render.theme import PRESETS

SLUG = "binary-search"


def written(tmp_path):
    return sorted(p.name for p in tmp_path.glob("*.svg"))


def test_default_writes_one_file_per_theme(tmp_path):
    assert main([SLUG, "--out", str(tmp_path)]) == 0
    assert written(tmp_path) == sorted(f"{SLUG}-{t}.svg" for t in PRESETS)


def test_options_go_into_the_filename(tmp_path):
    args = [SLUG, "--out", str(tmp_path), "--theme", "light", "--frame", "--no-pseudocode"]
    assert main(args + ["--no-tagline", "--no-author", "--accent", "#FF6B6B"]) == 0
    assert written(tmp_path) == [
        f"{SLUG}-light-frame-no-pseudocode-no-tagline-no-author-accent-ff6b6b.svg"
    ]


def test_variations_render_every_combination(tmp_path):
    assert main([SLUG, "--out", str(tmp_path), "--variations", "--theme", "dark"]) == 0
    files = written(tmp_path)
    assert len(files) == 16
    assert f"{SLUG}-dark.svg" in files
    assert f"{SLUG}-dark-frame-no-pseudocode-no-tagline-no-author.svg" in files
    for name in files:
        ET.parse(tmp_path / name)  # every file is well formed SVG


def test_variations_are_distinct():
    assert len(set(all_variations())) == 16
    assert len({o.suffix() for o in all_variations()}) == 16


def test_frame_and_accent_change_the_svg():
    plain = render_svg(SLUG, "dark", 600, 800)
    framed = render_svg(SLUG, "dark", 600, 800, Options(show_frame=True, accent="#123abc"))
    assert framed != plain
    assert "#123abc" in framed
    assert "#123abc" not in plain


def test_hiding_pseudocode_changes_the_svg():
    assert render_svg(SLUG, "dark", 600, 800, Options(show_pseudocode=False)) != render_svg(
        SLUG, "dark", 600, 800
    )


@pytest.mark.parametrize(
    "args",
    [
        ["--accent", "red"],
        ["--theme", "sepia"],
        ["--variations", "--frame"],
        ["not-a-real-slug"],
    ],
)
def test_bad_arguments_are_rejected(tmp_path, args):
    if args[0] != "not-a-real-slug":
        args = [SLUG, *args]
    with pytest.raises(SystemExit):
        main([*args, "--out", str(tmp_path)])
