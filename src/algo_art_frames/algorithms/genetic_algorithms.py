"""Genetic Algorithms: evolve a population, generation by generation, toward fitter solutions."""

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import RenderContext, new_canvas

TITLE = "Genetic Algorithms"
TAGLINE = "Survival of the fittest solution."

PSEUDOCODE = [
    "Evaluate -> Select -> Recombine -> Mutate -> Repeat",
]

COLUMNS = ["POPULATION", "SELECTION", "CROSSOVER", "MUTATION", "NEXT GEN"]
DOT_PALETTE = ["#4FD1C5", "#F2C14E", "#C792EA", "#F2775A"]
ROWS = 8


def draw(ctx: RenderContext) -> str:
    dwg, box = new_canvas(
        ctx,
        title=TITLE,
        tagline=TAGLINE,
        pseudocode=PSEUDOCODE,
    )

    n = len(COLUMNS)
    col_gap = 36
    col_w = (box.width - col_gap * (n - 1)) / n
    row_gap = box.height * 0.75 / ROWS
    top = box.y + box.height * 0.08

    centers = []
    for col_idx, label in enumerate(COLUMNS):
        cx = box.x + col_idx * (col_w + col_gap) + col_w / 2
        col_points = []
        for row_idx in range(ROWS):
            cy = top + row_idx * row_gap
            color = DOT_PALETTE[(col_idx + row_idx) % len(DOT_PALETTE)]
            r = 7 if row_idx == 0 else 5
            dwg.add(dwg.circle(center=(cx, cy), r=r, fill=color))
            if row_idx == 0:
                dwg.add(
                    dwg.circle(
                        center=(cx, cy),
                        r=r + 4,
                        fill="none",
                        stroke=ctx.theme.accent,
                        stroke_width=2,
                    )
                )
            col_points.append((cx, cy))
        centers.append(col_points)

        dwg.add(
            dwg.text(
                label,
                insert=(cx, top + ROWS * row_gap + 20),
                fill=ctx.theme.muted,
                font_family=ctx.theme.font_family,
                font_size=11,
                text_anchor="middle",
            )
        )

    arrow_y = top + (ROWS - 1) * row_gap / 2
    for col_idx in range(n - 1):
        x1 = box.x + col_idx * (col_w + col_gap) + col_w
        x2 = x1 + col_gap
        dwg.add(dwg.line(start=(x1, arrow_y), end=(x2, arrow_y), stroke=ctx.theme.muted, stroke_width=1.5))

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="genetic-algorithms",
    title=TITLE,
    tagline=TAGLINE,
    category=AlgorithmCategory.OPTIMIZATION,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#4FD1C5",
    author="Andrei Rukavina",
    date="2026-08-26",
)
