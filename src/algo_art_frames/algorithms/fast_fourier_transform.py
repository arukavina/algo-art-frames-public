"""Fast Fourier Transform: from the time domain to the frequency domain, recursively."""

import math

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import RenderContext, new_canvas

TITLE = "Fast Fourier Transform"
TAGLINE = "From time to frequency. Reduce. Reuse. Conquer."

PSEUDOCODE = [
    "FFT(x):",
    "    if N == 1: return x",
    "    even = FFT(x[0::2])",
    "    odd  = FFT(x[1::2])",
    "    combine(even, odd)",
]

BAR_HEIGHTS = [0.35, 0.55, 1.0, 0.85, 0.4, 0.25, 0.15]
TALL_BAR_COUNT = 2


def _waveform_points(x: float, y: float, w: float, h: float) -> list[tuple[float, float]]:
    samples = 200
    points = []
    for i in range(samples + 1):
        t = i / samples
        value = math.sin(2 * math.pi * 3 * t) + 0.5 * math.sin(2 * math.pi * 9 * t)
        px = x + t * w
        py = y + h / 2 - value * (h / 2) * 0.8
        points.append((px, py))
    return points


def draw(ctx: RenderContext) -> str:
    dwg, box = new_canvas(
        ctx,
        title=TITLE,
        tagline=TAGLINE,
        pseudocode=PSEUDOCODE,
    )

    gap = 24
    panel_w = (box.width - 2 * gap) / 3
    panel_h = box.height

    # Panel 1: the waveform.
    p1_x = box.x
    dwg.add(
        dwg.polyline(
            points=_waveform_points(p1_x, box.y, panel_w, panel_h),
            fill="none",
            stroke=ctx.theme.foreground,
            stroke_width=2,
        )
    )

    # Panel 2: the butterfly network, connecting two columns of 8 dots.
    p2_x = p1_x + panel_w + gap
    n = 8
    col_gap = panel_w * 0.7
    left_x = p2_x + panel_w * 0.15
    right_x = left_x + col_gap
    slot = panel_h / (n - 1)
    left_pts = [(left_x, box.y + i * slot) for i in range(n)]
    right_pts = [(right_x, box.y + i * slot) for i in range(n)]
    half = n // 2
    for i in range(n):
        partner = (i + half) % n
        for target in (i, partner):
            dwg.add(
                dwg.line(
                    start=left_pts[i],
                    end=right_pts[target],
                    stroke=ctx.theme.muted,
                    stroke_width=1,
                )
            )
    for x, y in left_pts + right_pts:
        dwg.add(dwg.circle(center=(x, y), r=3.5, fill=ctx.theme.foreground))

    # Panel 3: the frequency bar chart.
    p3_x = p2_x + panel_w + gap
    bars = len(BAR_HEIGHTS)
    bar_gap = 10
    bar_w = (panel_w - bar_gap * (bars - 1)) / bars
    ranked = sorted(range(bars), key=lambda i: BAR_HEIGHTS[i], reverse=True)
    tall = set(ranked[:TALL_BAR_COUNT])
    for i, height_ratio in enumerate(BAR_HEIGHTS):
        bar_h = panel_h * height_ratio
        x = p3_x + i * (bar_w + bar_gap)
        y = box.y + (panel_h - bar_h)
        color = ctx.theme.accent if i in tall else ctx.theme.muted
        dwg.add(dwg.rect(insert=(x, y), size=(bar_w, bar_h), fill=color, rx=2))

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="fast-fourier-transform",
    title=TITLE,
    tagline=TAGLINE,
    category=AlgorithmCategory.SIGNAL_PROCESSING,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#4FD1C5",
    author="Andrei Rukavina",
    date="2026-08-26",
)
