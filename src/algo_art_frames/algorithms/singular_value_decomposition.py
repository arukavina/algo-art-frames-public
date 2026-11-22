"""Singular Value Decomposition: every matrix can be written as a sum of simple patterns."""

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import RenderContext, new_canvas

TITLE = "Singular Value Decomposition"
TAGLINE = "Every matrix is a combination of simple patterns."

PSEUDOCODE = [
    "A = U x Sigma x V^T",
    "U: features",
    "Sigma: importance",
    "V^T: patterns",
]

LINES_PER_SWATCH = 10


def _swatch(dwg, x: float, y: float, w: float, h: float, color: str, opacity: float = 1.0):
    line_h = h / LINES_PER_SWATCH
    for i in range(LINES_PER_SWATCH):
        ly = y + i * line_h + line_h / 2
        dwg.add(
            dwg.line(
                start=(x, ly),
                end=(x + w, ly),
                stroke=color,
                stroke_width=line_h * 0.6,
                opacity=opacity,
            )
        )


def draw(ctx: RenderContext) -> str:
    dwg, box = new_canvas(
        ctx,
        title=TITLE,
        tagline=TAGLINE,
        pseudocode=PSEUDOCODE,
    )

    swatch_h = box.height * 0.55
    swatch_y = box.y + (box.height - swatch_h) / 2 - 10
    label_y = swatch_y + swatch_h + 22

    a_w = box.width * 0.16
    small_w = box.width * 0.14
    gap = box.width * 0.06

    cursor_x = box.x

    # A
    _swatch(dwg, cursor_x, swatch_y, a_w, swatch_h, ctx.theme.muted)
    dwg.add(
        dwg.text(
            "A",
            insert=(cursor_x + a_w / 2, label_y),
            fill=ctx.theme.foreground,
            font_family=ctx.theme.font_family,
            font_size=14,
            text_anchor="middle",
        )
    )
    cursor_x += a_w + gap

    dwg.add(
        dwg.text(
            "=",
            insert=(cursor_x, swatch_y + swatch_h / 2 + 5),
            fill=ctx.theme.foreground,
            font_family=ctx.theme.font_family,
            font_size=18,
            text_anchor="middle",
        )
    )
    cursor_x += gap

    labels = [("U", ctx.theme.foreground, 0.85), ("Σ", ctx.theme.accent, 1.0), ("Vᵀ", ctx.theme.foreground, 0.85)]
    for i, (label, color, opacity) in enumerate(labels):
        _swatch(dwg, cursor_x, swatch_y, small_w, swatch_h, color, opacity)
        dwg.add(
            dwg.text(
                label,
                insert=(cursor_x + small_w / 2, label_y),
                fill=color,
                font_family=ctx.theme.font_family,
                font_size=14,
                text_anchor="middle",
            )
        )
        cursor_x += small_w + gap
        if i < len(labels) - 1:
            dwg.add(
                dwg.text(
                    "x",
                    insert=(cursor_x - gap / 2, swatch_y + swatch_h / 2 + 5),
                    fill=ctx.theme.muted,
                    font_family=ctx.theme.font_family,
                    font_size=16,
                    text_anchor="middle",
                )
            )

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="singular-value-decomposition",
    title=TITLE,
    tagline=TAGLINE,
    category=AlgorithmCategory.LINEAR_ALGEBRA,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#9AA5B1",
    author="Andrei Rukavina",
    date="2026-08-26",
)
