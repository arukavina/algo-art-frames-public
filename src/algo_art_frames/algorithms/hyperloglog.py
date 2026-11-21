"""HyperLogLog: count billions of distinct items using just a handful of registers.

The diagram is drawn as a funnel: an unbounded stream converging down into a
fixed, tiny set of registers, where each one simply tracks the longest run
of leading zeros it has seen so far.
"""

import random

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import RenderContext, new_canvas

PSEUDOCODE = ["Small memory. Huge streams. Accurate estimate."]

REGISTER_COUNT = 8
_RNG = random.Random(11)
REGISTER_HEIGHTS = [_RNG.uniform(0.3, 1.0) for _ in range(REGISTER_COUNT)]


def draw(ctx: RenderContext) -> str:
    dwg, box = new_canvas(
        ctx,
        title="HyperLogLog",
        tagline="Count billions with a tiny memory.",
        pseudocode=PSEUDOCODE,
    )

    funnel_x0 = box.x
    funnel_x1 = box.x + box.width * 0.42
    funnel_mid_y = box.y + box.height * 0.32
    rng = random.Random(3)
    for _ in range(40):
        start_y = funnel_mid_y + rng.uniform(-1, 1) * box.height * 0.28
        dwg.add(
            dwg.line(
                start=(funnel_x0, start_y),
                end=(funnel_x1, funnel_mid_y),
                stroke=ctx.theme.muted,
                stroke_width=0.75,
                opacity=0.5,
            )
        )

    bars_left = funnel_x1 + 24
    bars_right = box.x + box.width
    n = REGISTER_COUNT
    gap = 14
    bar_w = (bars_right - bars_left - gap * (n - 1)) / n
    baseline = box.y + box.height * 0.78
    max_bar_h = box.height * 0.4

    for i in range(n):
        bx = bars_left + i * (bar_w + gap)
        h = REGISTER_HEIGHTS[i] * max_bar_h
        by = baseline - h
        opacity = 0.45 + 0.55 * REGISTER_HEIGHTS[i]
        dwg.add(
            dwg.rect(
                insert=(bx, by),
                size=(bar_w, h),
                fill=ctx.theme.accent,
                opacity=opacity,
                rx=2,
            )
        )
        label = str(i) if i < n - 1 else "m-1"
        dwg.add(
            dwg.text(
                label,
                insert=(bx + bar_w / 2, baseline + 16),
                fill=ctx.theme.muted,
                font_family=ctx.theme.font_family,
                font_size=11,
                text_anchor="middle",
            )
        )

    dwg.add(
        dwg.text(
            "REGISTERS",
            insert=((bars_left + bars_right) / 2, baseline - max_bar_h - 16),
            fill=ctx.theme.muted,
            font_family=ctx.theme.font_family,
            font_size=11,
            text_anchor="middle",
        )
    )

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="hyperloglog",
    title="HyperLogLog",
    tagline="Count billions with a tiny memory.",
    category=AlgorithmCategory.STREAMING,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#4FD1C5",
    author="Andrei Rukavina",
    date="2026-08-26",
)
