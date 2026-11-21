"""Deflate compression: LZ77 finds the repeats, and Huffman codes them efficiently.

The diagram shows both halves of Deflate at once: first the repeated text
collapsing into back-reference tokens (LZ77), and then a prefix-code tree
assigning shorter codes to whichever letters remain (Huffman).
"""

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import RenderContext, new_canvas

PSEUDOCODE = [
    "LZ77 finds repeats.",
    "Huffman codes them efficiently.",
]

SOURCE_LINE = "TOBEORNOTTOBEORNOT"
TOKENS = "TOBEORNOT[1,9]"

# (letter, code) pairs used to illustrate a small Huffman tree.
LEAVES = [
    ("T", "00"),
    ("O", "01"),
    ("B", "100"),
    ("E", "101"),
    ("R", "110"),
    ("N", "111"),
]


def draw(ctx: RenderContext) -> str:
    dwg, box = new_canvas(
        ctx,
        title="Deflate Compression",
        tagline="Find repetition. Remove redundancy.",
        pseudocode=PSEUDOCODE,
    )

    rows = 3
    row_gap = 20
    top_y = box.y + 16
    for i in range(rows):
        dwg.add(
            dwg.text(
                SOURCE_LINE,
                insert=(box.x, top_y + i * row_gap),
                fill=ctx.theme.muted,
                font_family=ctx.theme.font_family,
                font_size=13,
            )
        )

    arrow_y0 = top_y + rows * row_gap + 10
    arrow_y1 = arrow_y0 + 26
    dwg.add(
        dwg.line(
            start=(box.x + 10, arrow_y0),
            end=(box.x + 10, arrow_y1),
            stroke=ctx.theme.accent,
            stroke_width=1.5,
        )
    )
    dwg.add(
        dwg.line(
            start=(box.x + 10, arrow_y1),
            end=(box.x + 24, arrow_y1 - 6),
            stroke=ctx.theme.accent,
            stroke_width=1.5,
        )
    )
    dwg.add(
        dwg.line(
            start=(box.x + 10, arrow_y1),
            end=(box.x + 24, arrow_y1 + 6),
            stroke=ctx.theme.accent,
            stroke_width=1.5,
        )
    )
    dwg.add(
        dwg.text(
            TOKENS,
            insert=(box.x + 32, arrow_y1 + 5),
            fill=ctx.theme.accent,
            font_family=ctx.theme.font_family,
            font_size=14,
            font_weight="bold",
        )
    )

    tree_top = arrow_y1 + 50
    tree_bottom = box.y + box.height - 12
    tree_h = max(tree_bottom - tree_top, 60)
    n = len(LEAVES)
    leaf_gap = box.width / (n + 1)
    root_x = box.x + box.width / 2
    root_y = tree_top

    leaf_positions = []
    for i in range(n):
        lx = box.x + leaf_gap * (i + 1)
        ly = tree_top + tree_h
        leaf_positions.append((lx, ly))

    mid_y = tree_top + tree_h * 0.5
    left_mid_x = box.x + leaf_gap * 2
    right_mid_x = box.x + leaf_gap * (n - 1)
    dwg.add(dwg.line(start=(root_x, root_y), end=(left_mid_x, mid_y), stroke=ctx.theme.muted, stroke_width=1))
    dwg.add(dwg.line(start=(root_x, root_y), end=(right_mid_x, mid_y), stroke=ctx.theme.muted, stroke_width=1))

    for i, (lx, ly) in enumerate(leaf_positions):
        branch_x = left_mid_x if i < n / 2 else right_mid_x
        dwg.add(dwg.line(start=(branch_x, mid_y), end=(lx, ly), stroke=ctx.theme.muted, stroke_width=1))
        dwg.add(dwg.circle(center=(lx, ly), r=4, fill=ctx.theme.foreground))
        letter, code = LEAVES[i]
        dwg.add(
            dwg.text(
                letter,
                insert=(lx, ly + 18),
                fill=ctx.theme.foreground,
                font_family=ctx.theme.font_family,
                font_size=13,
                text_anchor="middle",
            )
        )
        dwg.add(
            dwg.text(
                code,
                insert=(lx, ly + 32),
                fill=ctx.theme.muted,
                font_family=ctx.theme.font_family,
                font_size=11,
                text_anchor="middle",
            )
        )

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="deflate-compression",
    title="Deflate Compression",
    tagline="Find repetition. Remove redundancy.",
    category=AlgorithmCategory.COMPRESSION,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#F2775A",
    author="Andrei Rukavina",
    date="2026-08-26",
)
