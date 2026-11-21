"""RSA encryption: multiplication is easy, factorization is hard.

That asymmetry between computing p * q and factoring n back into p and q is
the whole security model behind RSA, and the diagram draws it directly: two
small prime "seeds" merge into one dense composite, which then fans out
into many thin candidate-factor branches that have to be searched.
"""

import math
import random

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import RenderContext, new_canvas

TEAL = "#5EC8F8"
PINK = "#C792EA"

PSEUDOCODE = [
    "n = p x q",
    "Multiplication is easy.",
    "Factorization is hard.",
]


def _dot_disc(dwg, cx, cy, r, color, count, seed):
    rng = random.Random(seed)
    for _ in range(count):
        angle = rng.uniform(0, 6.28318)
        radius = r * (rng.random() ** 0.5)
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        dwg.add(dwg.circle(center=(x, y), r=1.1, fill=color, opacity=0.85))


def draw(ctx: RenderContext) -> str:
    dwg, box = new_canvas(
        ctx,
        title="RSA Encryption",
        tagline="Easy to lock. Hard to unlock without the key.",
        pseudocode=PSEUDOCODE,
    )

    cy = box.y + box.height * 0.42
    p_x = box.x + box.width * 0.12
    q_x = box.x + box.width * 0.12
    p_y = cy - box.height * 0.16
    q_y = cy + box.height * 0.16
    seed_r = min(box.width, box.height) * 0.08

    _dot_disc(dwg, p_x, p_y, seed_r, TEAL, 90, seed=1)
    _dot_disc(dwg, q_x, q_y, seed_r, PINK, 90, seed=2)
    dwg.add(
        dwg.text(
            "p",
            insert=(p_x, p_y - seed_r - 8),
            fill=ctx.theme.muted,
            font_family=ctx.theme.font_family,
            font_size=14,
            text_anchor="middle",
        )
    )
    dwg.add(
        dwg.text(
            "q",
            insert=(q_x, q_y - seed_r - 8),
            fill=ctx.theme.muted,
            font_family=ctx.theme.font_family,
            font_size=14,
            text_anchor="middle",
        )
    )
    dwg.add(
        dwg.text(
            "EASY",
            insert=(p_x, cy + seed_r + 34),
            fill=ctx.theme.muted,
            font_family=ctx.theme.font_family,
            font_size=11,
            text_anchor="middle",
        )
    )

    n_x = box.x + box.width * 0.42
    n_r = seed_r * 1.6
    dwg.add(
        dwg.line(
            start=(p_x + seed_r, p_y),
            end=(n_x - n_r, cy),
            stroke=ctx.theme.muted,
            stroke_width=1,
        )
    )
    dwg.add(
        dwg.line(
            start=(q_x + seed_r, q_y),
            end=(n_x - n_r, cy),
            stroke=ctx.theme.muted,
            stroke_width=1,
        )
    )
    _dot_disc(dwg, n_x, cy, n_r, TEAL, 90, seed=3)
    _dot_disc(dwg, n_x, cy, n_r, PINK, 90, seed=4)
    dwg.add(
        dwg.text(
            "n = p x q",
            insert=(n_x, cy - n_r - 12),
            fill=ctx.theme.foreground,
            font_family=ctx.theme.font_family,
            font_size=14,
            text_anchor="middle",
        )
    )

    fan_x0 = n_x + n_r
    fan_x1 = box.x + box.width * 0.94
    rng = random.Random(5)
    for i in range(14):
        spread = (i - 6.5) / 6.5
        end_y = cy + spread * box.height * 0.32 + rng.uniform(-6, 6)
        dwg.add(
            dwg.line(
                start=(fan_x0, cy),
                end=(fan_x1, end_y),
                stroke=ctx.theme.accent,
                stroke_width=1,
                opacity=0.6,
            )
        )
    dwg.add(
        dwg.text(
            "HARD",
            insert=(fan_x1 - 10, cy - box.height * 0.32 - 14),
            fill=ctx.theme.accent,
            font_family=ctx.theme.font_family,
            font_size=11,
            text_anchor="end",
        )
    )

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="rsa-encryption",
    title="RSA Encryption",
    tagline="Easy to lock. Hard to unlock without the key.",
    category=AlgorithmCategory.CRYPTOGRAPHY,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#F2C14E",
    author="Andrei Rukavina",
    date="2026-08-26",
)
