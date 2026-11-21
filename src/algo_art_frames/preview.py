"""Render algorithm posters to SVG files so you can look at them locally.

Usage:
    python -m algo_art_frames.preview binary-search
    python -m algo_art_frames.preview binary-search --frame --no-pseudocode
    python -m algo_art_frames.preview binary-search --accent "#ff6b6b" --theme light
    python -m algo_art_frames.preview binary-search --variations
    python -m algo_art_frames.preview --all --out out/

By default each slug is written once per theme preset with its default look,
e.g. out/binary-search-dark.svg and out/binary-search-light.svg. Options that
change the look are added to the filename (out/binary-search-dark-frame.svg),
so the default renders are never overwritten. Open the files in any browser.
"""

import argparse
import itertools
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from algo_art_frames.algorithms import REGISTRY
from algo_art_frames.render.canvas import RenderContext
from algo_art_frames.render.theme import PRESETS, resolve_theme

DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 1600
HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


@dataclass(frozen=True)
class Options:
    """The display options a poster can be rendered with."""

    show_frame: bool = False
    show_pseudocode: bool = True
    show_tagline: bool = True
    show_author: bool = True
    accent: str | None = None  # None keeps the plugin's own accent

    def suffix(self) -> str:
        """Filename suffix naming every option that differs from the default look."""
        parts = []
        if self.show_frame:
            parts.append("frame")
        if not self.show_pseudocode:
            parts.append("no-pseudocode")
        if not self.show_tagline:
            parts.append("no-tagline")
        if not self.show_author:
            parts.append("no-author")
        if self.accent:
            parts.append("accent-" + self.accent.lstrip("#").lower())
        return "".join(f"-{p}" for p in parts)


def render_svg(
    slug: str,
    theme_name: str,
    width: int,
    height: int,
    options: Options | None = None,
) -> str:
    """Render one poster. Without options this is the default look: the
    plugin's own signature accent on top of the chosen theme preset."""
    options = options or Options()
    plugin = REGISTRY[slug]
    theme = resolve_theme(theme_name, options.accent or plugin.accent)
    ctx = RenderContext(
        theme=theme,
        width=width,
        height=height,
        show_tagline=options.show_tagline,
        show_pseudocode=options.show_pseudocode,
        show_author=options.show_author,
        author=plugin.author,
        date=plugin.date,
        show_frame=options.show_frame,
    )
    return plugin.draw(ctx)


def all_variations(accent: str | None = None) -> list[Options]:
    """Every combination of the on/off display options."""
    return [
        Options(
            show_frame=frame,
            show_pseudocode=pseudocode,
            show_tagline=tagline,
            show_author=author,
            accent=accent,
        )
        for frame, pseudocode, tagline, author in itertools.product(
            (False, True), (True, False), (True, False), (True, False)
        )
    ]


def accent_color(value: str) -> str:
    if not HEX_RE.match(value):
        raise argparse.ArgumentTypeError(f"'{value}' is not a hex color like #ff6b6b")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("slugs", nargs="*", help="algorithm slug(s) to render")
    parser.add_argument("--all", action="store_true", help="render every registered algorithm")
    parser.add_argument("--out", default="out", help="output directory (default: out/)")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument(
        "--theme",
        choices=sorted(PRESETS),
        action="append",
        help="render only this theme (repeatable; default: every theme)",
    )
    look = parser.add_argument_group("display options")
    look.add_argument("--frame", action="store_true", help="draw the thin accent frame")
    look.add_argument("--no-pseudocode", action="store_true", help="hide the pseudocode panel")
    look.add_argument("--no-tagline", action="store_true", help="hide the tagline")
    look.add_argument("--no-author", action="store_true", help="hide the author line")
    look.add_argument(
        "--accent",
        type=accent_color,
        help="override the plugin's accent color, as a hex color like #ff6b6b",
    )
    look.add_argument(
        "--variations",
        action="store_true",
        help="render every combination of frame, pseudocode, tagline and author "
        "(16 per theme; combine with --accent to use a custom accent)",
    )
    args = parser.parse_args(argv)

    slugs = sorted(REGISTRY) if args.all else args.slugs
    if not slugs:
        parser.error(f"give at least one slug or --all. Known slugs: {', '.join(sorted(REGISTRY))}")
    unknown = [s for s in slugs if s not in REGISTRY]
    if unknown:
        parser.error(f"unknown slug(s): {', '.join(unknown)}")
    toggles = args.frame or args.no_pseudocode or args.no_tagline or args.no_author
    if args.variations and toggles:
        parser.error("--variations already renders every on/off combination; drop the toggles")

    if args.variations:
        variants = all_variations(args.accent)
    else:
        variants = [
            Options(
                show_frame=args.frame,
                show_pseudocode=not args.no_pseudocode,
                show_tagline=not args.no_tagline,
                show_author=not args.no_author,
                accent=args.accent,
            )
        ]
    themes = list(dict.fromkeys(args.theme)) if args.theme else list(PRESETS)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for slug in slugs:
        for theme_name in themes:
            for options in variants:
                path = out_dir / f"{slug}-{theme_name}{options.suffix()}.svg"
                svg = render_svg(slug, theme_name, args.width, args.height, options)
                path.write_text(svg, encoding="utf-8")
                print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
