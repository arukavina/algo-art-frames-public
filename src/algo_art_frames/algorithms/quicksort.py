"""Quicksort: partition around a pivot, then recurse on both halves.

It is drawn as a binary recursion tree, where each split represents one
partition step, and the depth of the tree corresponds directly to the
recursion depth.
"""

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import RenderContext, new_canvas

TITLE = "Quicksort"
TAGLINE = "Divide to conquer. Order emerges from partition."

PSEUDOCODE = [
    "if len(A) <= 1: return A",
    "pivot = choose(A)",
    "L = quicksort([x for x in A if x < pivot])",
    "R = quicksort([x for x in A if x >= pivot])",
    "return L + [pivot] + R",
]

LEVEL_PALETTE = ["#C792EA", "#5EC8F8", "#F2994A", "#4FD1C5"]
NUM_LEVELS = 4  # the root plus 3 more levels (1, 2, 4, 8 nodes per level)
HIGHLIGHT_LEAF = 5  # which leaf, 0-indexed among the 8 leaves, the highlight path ends at


def _path_indices() -> list[int]:
    """Index, within its own level, of each node on the root-to-leaf highlight path."""
    indices = [HIGHLIGHT_LEAF]
    for _ in range(NUM_LEVELS - 2):
        indices.append(indices[-1] // 2)
    indices.append(0)
    return list(reversed(indices))  # root first, leaf last


def draw(ctx: RenderContext) -> str:
    dwg, box = new_canvas(
        ctx,
        title=TITLE,
        tagline=TAGLINE,
        pseudocode=PSEUDOCODE,
    )

    path = _path_indices()
    level_y = [box.y + level * (box.height / (NUM_LEVELS - 1)) for level in range(NUM_LEVELS)]
    positions: list[list[tuple[float, float]]] = []

    for level in range(NUM_LEVELS):
        count = 2**level
        row = []
        for i in range(count):
            x = box.x + (i + 0.5) * (box.width / count)
            row.append((x, level_y[level]))
        positions.append(row)

    # Edges are drawn first, so the nodes end up on top of them.
    for level in range(NUM_LEVELS - 1):
        on_path_parent = path[level]
        on_path_child = path[level + 1] if level + 1 < len(path) else None
        for i, (x, y) in enumerate(positions[level]):
            for child in (2 * i, 2 * i + 1):
                cx, cy = positions[level + 1][child]
                is_path_edge = i == on_path_parent and child == on_path_child
                dwg.add(
                    dwg.line(
                        start=(x, y),
                        end=(cx, cy),
                        stroke=ctx.theme.accent if is_path_edge else ctx.theme.muted,
                        stroke_width=2 if is_path_edge else 1,
                    )
                )

    for level in range(NUM_LEVELS):
        for i, (x, y) in enumerate(positions[level]):
            is_on_path = path[level] == i
            color = ctx.theme.accent if is_on_path else LEVEL_PALETTE[level % len(LEVEL_PALETTE)]
            radius = 9 if level < NUM_LEVELS - 1 else 6
            dwg.add(dwg.circle(center=(x, y), r=radius, fill=color))

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="quicksort",
    title=TITLE,
    tagline=TAGLINE,
    category=AlgorithmCategory.SORTING,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#C792EA",
    author="Andrei Rukavina",
    date="2026-08-26",
)
