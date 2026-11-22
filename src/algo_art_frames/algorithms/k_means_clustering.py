"""K-Means Clustering: discover structure in scattered data by repeatedly
iterating between assigning points and updating centroids."""

import random

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import RenderContext, new_canvas

TITLE = "K-Means Clustering"
TAGLINE = "Discover structure in scattered data."

PSEUDOCODE = [
    "repeat:",
    "    assign points to nearest centroid",
    "    update centroids as mean",
    "until convergence",
]

CLUSTER_COLORS = ["#F2994A", "#C792EA", "#E8615A"]
# Relative (cx, cy, spread) values for each cluster, expressed in unit box coordinates.
CLUSTERS = [
    (0.22, 0.28, 0.14),
    (0.75, 0.30, 0.12),
    (0.48, 0.75, 0.16),
]
POINTS_PER_CLUSTER = 30


def draw(ctx: RenderContext) -> str:
    dwg, box = new_canvas(
        ctx,
        title=TITLE,
        tagline=TAGLINE,
        pseudocode=PSEUDOCODE,
    )

    rng = random.Random(11)

    for cluster_idx, (cx_ratio, cy_ratio, spread) in enumerate(CLUSTERS):
        color = CLUSTER_COLORS[cluster_idx]
        cx = box.x + cx_ratio * box.width
        cy = box.y + cy_ratio * box.height
        for _ in range(POINTS_PER_CLUSTER):
            dx = rng.gauss(0, spread * box.width)
            dy = rng.gauss(0, spread * box.height)
            dwg.add(dwg.circle(center=(cx + dx, cy + dy), r=3, fill=color, opacity=0.75))

        dwg.add(
            dwg.line(
                start=(cx - 8, cy - 8),
                end=(cx + 8, cy + 8),
                stroke=ctx.theme.accent,
                stroke_width=3,
            )
        )
        dwg.add(
            dwg.line(
                start=(cx - 8, cy + 8),
                end=(cx + 8, cy - 8),
                stroke=ctx.theme.accent,
                stroke_width=3,
            )
        )

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="k-means-clustering",
    title=TITLE,
    tagline=TAGLINE,
    category=AlgorithmCategory.MACHINE_LEARNING,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#F2994A",
    author="Andrei Rukavina",
    date="2026-08-26",
)
