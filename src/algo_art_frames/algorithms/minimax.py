"""Minimax: MAX and MIN take turns, each one picking the best score for itself.

It is drawn as a 3-level game tree over 8 leaf outcomes, with the truly
optimal line of play (computed for real here, never hardcoded) picked out
in the accent color.
"""

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import RenderContext, new_canvas

TITLE = "Minimax"
TAGLINE = "Think ahead. Act optimally."

PSEUDOCODE = [
    "MAX chooses the highest score.",
    "MIN chooses the lowest.",
]

LEAVES = [3, 5, 2, 9, 12, 5, 0, 7]
ROLES = ["MAX", "MIN", "MAX"]  # root, level 1, level 2 (the leaves are terminal values, not a turn)


def _evaluate() -> tuple[list[int], list[int], int, list[int]]:
    """Bottom-up minimax over LEAVES. Returns each level's node values, along
    with the winning path of node indices (root first) at every internal
    level."""
    level2 = [max(LEAVES[2 * i], LEAVES[2 * i + 1]) for i in range(4)]
    level1 = [min(level2[2 * i], level2[2 * i + 1]) for i in range(2)]
    root = max(level1[0], level1[1])

    r1 = max(range(2), key=lambda i: level1[i])
    r2_local = min(range(2), key=lambda i: level2[2 * r1 + i])
    r2 = 2 * r1 + r2_local
    leaf_local = max(range(2), key=lambda i: LEAVES[2 * r2 + i])
    leaf = 2 * r2 + leaf_local

    return level2, level1, root, [0, r1, r2, leaf]


def draw(ctx: RenderContext) -> str:
    dwg, box = new_canvas(
        ctx,
        title=TITLE,
        tagline=TAGLINE,
        pseudocode=PSEUDOCODE,
    )

    level2_vals, level1_vals, root_val, path = _evaluate()
    counts = [1, 2, 4, 8]
    level_y = [box.y + level * (box.height * 0.8 / 3) for level in range(4)]
    positions: list[list[tuple[float, float]]] = []
    for level, count in enumerate(counts):
        row = [(box.x + (i + 0.5) * (box.width / count), level_y[level]) for i in range(count)]
        positions.append(row)

    for level in range(3):
        for i, (x, y) in enumerate(positions[level]):
            for child in (2 * i, 2 * i + 1):
                cx, cy = positions[level + 1][child]
                on_path = path[level] == i and (level + 1 >= len(path) or path[level + 1] == child)
                dwg.add(
                    dwg.line(
                        start=(x, y),
                        end=(cx, cy),
                        stroke=ctx.theme.accent if on_path else ctx.theme.muted,
                        stroke_width=2.5 if on_path else 1,
                    )
                )

    node_values = [[root_val], level1_vals, level2_vals, LEAVES]
    for level in range(4):
        role = ROLES[level] if level < len(ROLES) else None
        for i, (x, y) in enumerate(positions[level]):
            on_path = path[level] == i if level < len(path) else False
            color = ctx.theme.accent if on_path else ctx.theme.foreground
            if level < 3:
                dwg.add(
                    dwg.circle(
                        center=(x, y),
                        r=13,
                        fill="none",
                        stroke=color,
                        stroke_width=2 if on_path else 1.5,
                    )
                )
                dwg.add(
                    dwg.text(
                        str(node_values[level][i]),
                        insert=(x, y + 4),
                        fill=color,
                        font_family=ctx.theme.font_family,
                        font_size=11,
                        text_anchor="middle",
                    )
                )
                if role:
                    dwg.add(
                        dwg.text(
                            role,
                            insert=(x, y - 18),
                            fill=ctx.theme.muted,
                            font_family=ctx.theme.font_family,
                            font_size=10,
                            text_anchor="middle",
                        )
                    )
            else:
                dwg.add(
                    dwg.text(
                        str(node_values[level][i]),
                        insert=(x, y + 5),
                        fill=color,
                        font_family=ctx.theme.font_family,
                        font_size=14,
                        font_weight="bold" if on_path else "normal",
                        text_anchor="middle",
                    )
                )

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="minimax",
    title=TITLE,
    tagline=TAGLINE,
    category=AlgorithmCategory.GAME_THEORY,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#F2C14E",
    author="Andrei Rukavina",
    date="2026-08-26",
)
