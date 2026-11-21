"""Knuth-Morris-Pratt: never recheck a prefix you have already matched.

On a mismatch, KMP does not slide the pattern back to the start, instead it
jumps ahead using the longest-prefix-that-is-also-a-suffix table. The
diagram shows the text and pattern rows, plus that jump drawn as a single
curved shift.
"""

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import RenderContext, new_canvas

PSEUDOCODE = [
    "for each mismatch:",
    "    shift pattern by LPS[j-1]",
    "    (longest prefix = suffix)",
]

TEXT = "ABABABACABABABD"
PATTERN = "ABABABD"
MISMATCH_INDEX = 6
OLD_OFFSET = 0
NEW_OFFSET = 4


def _lps(pattern: str) -> list[int]:
    """Longest-prefix-that-is-also-a-suffix table. lps[i] is how much of the
    pattern's own prefix repeats as a suffix ending at i, which is exactly
    how much KMP is allowed to skip re-checking on a mismatch."""
    lps = [0] * len(pattern)
    length = 0
    i = 1
    while i < len(pattern):
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length:
            length = lps[length - 1]
        else:
            lps[i] = 0
            i += 1
    return lps


def draw(ctx: RenderContext) -> str:
    dwg, box = new_canvas(
        ctx,
        title="Knuth-Morris-Pratt",
        tagline="Never recheck what you already know.",
        pseudocode=PSEUDOCODE,
    )

    n = len(TEXT)
    cell = box.width / n
    text_y = box.y + box.height * 0.28
    old_pattern_y = text_y + 46
    new_pattern_y = text_y + 46 + 70

    for i, ch in enumerate(TEXT):
        x = box.x + i * cell + cell / 2
        color = ctx.theme.accent if i == MISMATCH_INDEX else ctx.theme.foreground
        dwg.add(
            dwg.text(
                ch,
                insert=(x, text_y),
                fill=color,
                font_family=ctx.theme.font_family,
                font_size=15,
                text_anchor="middle",
            )
        )
        dwg.add(
            dwg.line(
                start=(box.x + i * cell, text_y + 10),
                end=(box.x + (i + 1) * cell, text_y + 10),
                stroke=ctx.theme.muted,
                stroke_width=0.5,
            )
        )

    def draw_pattern(y, offset, dim):
        color = ctx.theme.muted if dim else ctx.theme.foreground
        for j, ch in enumerate(PATTERN):
            x = box.x + (offset + j) * cell + cell / 2
            fill = ctx.theme.accent if (not dim and j == MISMATCH_INDEX - offset) else color
            dwg.add(
                dwg.text(
                    ch,
                    insert=(x, y),
                    fill=fill,
                    font_family=ctx.theme.font_family,
                    font_size=15,
                    text_anchor="middle",
                )
            )

    draw_pattern(old_pattern_y, OLD_OFFSET, dim=True)
    draw_pattern(new_pattern_y, NEW_OFFSET, dim=False)

    arrow_x0 = box.x + OLD_OFFSET * cell + cell / 2
    arrow_x1 = box.x + NEW_OFFSET * cell + cell / 2
    arrow_y0 = old_pattern_y + 10
    arrow_y1 = new_pattern_y - 22
    mid_y = (arrow_y0 + arrow_y1) / 2
    path_d = f"M {arrow_x0} {arrow_y0} Q {(arrow_x0 + arrow_x1) / 2} {mid_y + 18} {arrow_x1} {arrow_y1}"
    dwg.add(dwg.path(d=path_d, fill="none", stroke=ctx.theme.accent, stroke_width=1.5))
    dwg.add(
        dwg.line(
            start=(arrow_x1 - 5, arrow_y1 - 5),
            end=(arrow_x1, arrow_y1),
            stroke=ctx.theme.accent,
            stroke_width=1.5,
        )
    )
    dwg.add(
        dwg.line(
            start=(arrow_x1 + 5, arrow_y1 - 5),
            end=(arrow_x1, arrow_y1),
            stroke=ctx.theme.accent,
            stroke_width=1.5,
        )
    )
    dwg.add(
        dwg.text(
            f"shift by {NEW_OFFSET - OLD_OFFSET}",
            insert=((arrow_x0 + arrow_x1) / 2, mid_y + 30),
            fill=ctx.theme.accent,
            font_family=ctx.theme.font_family,
            font_size=11,
            text_anchor="middle",
        )
    )

    # The LPS table is essentially "what you already know": it is what lets
    # KMP shift by more than one character instead of re-checking everything
    # from scratch. It is placed as its own row further down in the box, so
    # the diagram makes use of the full canvas height rather than stopping
    # right after the shift illustration.
    lps = _lps(PATTERN)
    # This is anchored to the second pattern row, not to a fraction of
    # box.height, because the rows above it use fixed offsets from text_y,
    # and a height-fraction anchor could otherwise drift into collision with
    # them on shorter canvases.
    table_y = max(new_pattern_y + 60, box.y + box.height * 0.62)
    table_cell = min(cell * 1.3, 56)
    table_w = table_cell * len(PATTERN)
    table_x0 = box.x + (box.width - table_w) / 2

    dwg.add(
        dwg.text(
            "LPS[j]  (longest prefix = suffix)",
            insert=(box.x + box.width / 2, table_y - 16),
            fill=ctx.theme.muted,
            font_family=ctx.theme.font_family,
            font_size=11,
            text_anchor="middle",
        )
    )
    for j, (ch, value) in enumerate(zip(PATTERN, lps)):
        x = table_x0 + j * table_cell
        highlighted = j == MISMATCH_INDEX - OLD_OFFSET - 1
        color = ctx.theme.accent if highlighted else ctx.theme.foreground
        dwg.add(
            dwg.rect(
                insert=(x, table_y),
                size=(table_cell - 4, table_cell),
                rx=6,
                fill="none",
                stroke=color,
                stroke_width=1.5 if highlighted else 1,
                opacity=1 if highlighted else 0.6,
            )
        )
        dwg.add(
            dwg.text(
                ch,
                insert=(x + (table_cell - 4) / 2, table_y + table_cell * 0.4),
                fill=color,
                font_family=ctx.theme.font_family,
                font_size=13,
                text_anchor="middle",
                opacity=1 if highlighted else 0.6,
            )
        )
        dwg.add(
            dwg.text(
                str(value),
                insert=(x + (table_cell - 4) / 2, table_y + table_cell * 0.8),
                fill=color,
                font_family=ctx.theme.font_family,
                font_size=13,
                font_weight="bold",
                text_anchor="middle",
                opacity=1 if highlighted else 0.6,
            )
        )

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="knuth-morris-pratt",
    title="Knuth-Morris-Pratt",
    tagline="Never recheck what you already know.",
    category=AlgorithmCategory.STRINGS,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#C792EA",
    author="Andrei Rukavina",
    date="2026-08-26",
)
