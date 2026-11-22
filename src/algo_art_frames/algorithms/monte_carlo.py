"""Monte Carlo estimation: scatter random points, then count what fraction of
them land inside a known shape.

It is drawn as a circle inscribed in a square, with the points that fall
inside the circle picked out in the accent color. Their ratio to the total
is exactly the pi estimate shown in the caption.
"""

import random

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import RenderContext, new_canvas

TITLE = "Monte Carlo"
TAGLINE = "Randomness can reveal the truth."

PSEUDOCODE = [
    "Estimate pi = 4 x (points in circle / total points)",
]

NUM_POINTS = 300
SEED = 7


def draw(ctx: RenderContext) -> str:
    dwg, box = new_canvas(
        ctx,
        title=TITLE,
        tagline=TAGLINE,
        pseudocode=PSEUDOCODE,
    )

    side = min(box.width, box.height)
    origin_x = box.x + (box.width - side) / 2
    origin_y = box.y + (box.height - side) / 2
    cx, cy = origin_x + side / 2, origin_y + side / 2
    radius = side / 2

    dwg.add(
        dwg.rect(
            insert=(origin_x, origin_y),
            size=(side, side),
            fill="none",
            stroke=ctx.theme.muted,
            stroke_width=1,
        )
    )

    rng = random.Random(SEED)
    for _ in range(NUM_POINTS):
        x = origin_x + rng.random() * side
        y = origin_y + rng.random() * side
        inside = (x - cx) ** 2 + (y - cy) ** 2 <= radius**2
        dwg.add(
            dwg.circle(
                center=(x, y),
                r=2.2,
                fill=ctx.theme.accent if inside else ctx.theme.muted,
            )
        )

    dwg.add(
        dwg.circle(
            center=(cx, cy),
            r=radius,
            fill="none",
            stroke=ctx.theme.accent,
            stroke_width=2,
        )
    )

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="monte-carlo",
    title=TITLE,
    tagline=TAGLINE,
    category=AlgorithmCategory.RANDOMNESS,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#F2994A",
    author="Andrei Rukavina",
    date="2026-08-26",
)
