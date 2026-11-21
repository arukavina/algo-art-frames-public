"""Shared SVG scaffolding: background, title/tagline, pseudocode block, margins.

Every algorithm's draw() starts by calling new_canvas(), which hands back a
Drawing plus the content box left over for the algorithm to draw its own
diagram into. The whole point of this is that layout boilerplate (title,
tagline, pseudocode, margins) does not need to be duplicated in every single
algorithm module.
"""

from dataclasses import dataclass

import svgwrite

from algo_art_frames.render.theme import Theme

MARGIN = 32
TITLE_SIZE = 28
TAGLINE_SIZE = 14
PSEUDOCODE_LINE_HEIGHT = 18
PSEUDOCODE_SIZE = 12
PSEUDOCODE_INDENT_PX = 7  # approx. width of one monospace char at PSEUDOCODE_SIZE
FRAME_INSET = 10  # gap between the canvas edge and the accent frame
FRAME_STROKE_WIDTH = 2


@dataclass
class RenderContext:
    theme: Theme
    width: int
    height: int
    show_tagline: bool = True
    show_pseudocode: bool = True
    show_author: bool = True
    author: str | None = None
    date: str | None = None
    show_frame: bool = False


@dataclass
class ContentBox:
    x: float
    y: float
    width: float
    height: float


def new_canvas(
    ctx: RenderContext,
    title: str,
    tagline: str,
    pseudocode: list[str],
) -> tuple[svgwrite.Drawing, ContentBox]:
    dwg = svgwrite.Drawing(size=(ctx.width, ctx.height))
    # It is worth explaining why this viewBox call matters: without it, an
    # inline <svg> (unlike an <img src="...svg">) does not scale its content
    # when CSS resizes it, it simply clips at the new viewport size instead.
    # Since posters are usually displayed at many sizes through CSS, this
    # call is required.
    dwg.viewbox(0, 0, ctx.width, ctx.height)
    dwg.add(dwg.rect(insert=(0, 0), size=(ctx.width, ctx.height), fill=ctx.theme.background))

    if ctx.show_frame:
        # This draws a thin accent-colored mat, sitting close to the edge with
        # a minimal gap to both the canvas border and the content. The idea is
        # to give the poster a defined edge to crop or frame to when printed,
        # without eating into the MARGIN gutter that the title, tagline, and
        # content already depend on.
        dwg.add(
            dwg.rect(
                insert=(FRAME_INSET, FRAME_INSET),
                size=(ctx.width - 2 * FRAME_INSET, ctx.height - 2 * FRAME_INSET),
                fill="none",
                stroke=ctx.theme.accent,
                stroke_width=FRAME_STROKE_WIDTH,
            )
        )

    cursor_y = MARGIN + TITLE_SIZE
    dwg.add(
        dwg.text(
            title,
            insert=(MARGIN, cursor_y),
            fill=ctx.theme.foreground,
            font_family=ctx.theme.font_family,
            font_size=TITLE_SIZE,
            font_weight="bold",
        )
    )

    if ctx.show_tagline and tagline:
        cursor_y += TAGLINE_SIZE + 8
        dwg.add(
            dwg.text(
                tagline,
                insert=(MARGIN, cursor_y),
                fill=ctx.theme.muted,
                font_family=ctx.theme.font_family,
                font_size=TAGLINE_SIZE,
            )
        )

    content_top = cursor_y + MARGIN
    content_bottom = ctx.height - MARGIN

    if ctx.show_pseudocode and pseudocode:
        block_height = len(pseudocode) * PSEUDOCODE_LINE_HEIGHT + MARGIN
        content_bottom = ctx.height - MARGIN - block_height
        block_y = content_bottom + MARGIN // 2
        for i, line in enumerate(pseudocode):
            # A small detail worth noting: SVG <text> collapses leading
            # whitespace unless xml:space="preserve" is set, so indentation
            # here has to be expressed as an x-offset rather than as literal
            # spaces.
            stripped = line.lstrip(" ")
            indent = len(line) - len(stripped)
            dwg.add(
                dwg.text(
                    stripped,
                    insert=(MARGIN + indent * PSEUDOCODE_INDENT_PX, block_y + i * PSEUDOCODE_LINE_HEIGHT),
                    fill=ctx.theme.muted,
                    font_family=ctx.theme.font_family,
                    font_size=PSEUDOCODE_SIZE,
                )
            )

    if ctx.show_author and (ctx.author or ctx.date):
        # The baseline is placed well clear of the optional accent frame
        # (10px inset, 2px stroke) rather than hugging the very edge, since
        # otherwise the frame line would cut straight through the text.
        label = " · ".join(part for part in (ctx.author, ctx.date) if part)
        dwg.add(
            dwg.text(
                label,
                insert=(ctx.width - MARGIN, ctx.height - MARGIN + 8),
                fill=ctx.theme.muted,
                font_family=ctx.theme.font_family,
                font_size=11,
                text_anchor="end",
            )
        )

    content_box = ContentBox(
        x=MARGIN,
        y=content_top,
        width=ctx.width - 2 * MARGIN,
        height=max(content_bottom - content_top, 0),
    )
    return dwg, content_box
