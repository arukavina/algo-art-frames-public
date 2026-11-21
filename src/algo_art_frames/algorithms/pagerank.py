"""PageRank: importance flows through links, meaning a page is important
precisely when important pages link to it."""

import math
import random

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import RenderContext, new_canvas

PSEUDOCODE = ["A page is important if important pages link to it."]

PERIPHERAL_COLOR = "#5EC8F8"
NODE_COUNT = 12


def draw(ctx: RenderContext) -> str:
    dwg, box = new_canvas(
        ctx,
        title="PageRank",
        tagline="Importance flows through connections.",
        pseudocode=PSEUDOCODE,
    )

    cx = box.x + box.width / 2
    cy = box.y + box.height / 2
    center_r = min(box.width, box.height) * 0.045

    rng = random.Random(5)
    max_dist = min(box.width, box.height) * 0.42
    min_dist = min(box.width, box.height) * 0.20
    peripherals = []
    for i in range(NODE_COUNT):
        angle = (2 * math.pi * i / NODE_COUNT) + rng.uniform(-0.15, 0.15)
        dist = rng.uniform(min_dist, max_dist)
        x = cx + dist * math.cos(angle)
        y = cy + dist * math.sin(angle)
        radius = 4 + 8 * (1 - (dist - min_dist) / (max_dist - min_dist))
        peripherals.append((x, y, radius))

    for x, y, _radius in peripherals:
        dwg.add(dwg.line(start=(cx, cy), end=(x, y), stroke=ctx.theme.muted, stroke_width=1))

    for i in range(NODE_COUNT):
        j = (i + 4) % NODE_COUNT
        x1, y1, _ = peripherals[i]
        x2, y2, _ = peripherals[j]
        dwg.add(
            dwg.line(start=(x1, y1), end=(x2, y2), stroke=ctx.theme.muted, stroke_width=0.75)
        )

    for x, y, radius in peripherals:
        dwg.add(dwg.circle(center=(x, y), r=radius, fill=PERIPHERAL_COLOR))

    dwg.add(dwg.circle(center=(cx, cy), r=center_r, fill=ctx.theme.accent))

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="pagerank",
    title="PageRank",
    tagline="Importance flows through connections.",
    category=AlgorithmCategory.GRAPH,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#F2C14E",
    author="Andrei Rukavina",
    date="2026-08-26",
)
