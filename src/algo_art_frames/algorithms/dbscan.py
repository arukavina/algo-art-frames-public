"""DBSCAN: density-based clustering that finds clusters of any shape and
leaves the outliers out.

The hero is the classic set of shapes that defeat centroid methods such as
k-means: two interleaving moons, a ring around a blob, a snake and a lone
blob, sprinkled with uniform noise. DBSCAN is actually run on those points.
Every core point (one with at least minPts neighbors within ε) gets a faint
ε-disc in its cluster's color, so the overlapping discs trace out the dense
regions the algorithm "sees". Core points are solid, border points (reached
from a core point but not dense themselves) are hollow and noise is a muted
cross. One core point shows its ε radius. Below, three close-ups explain the
three roles a point can take.
"""

import math
import random

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import RenderContext, new_canvas

TITLE = "DBSCAN"
TAGLINE = "Clusters are crowds. Everything else is noise."

PSEUDOCODE = [
    "for each unvisited point p:",
    "    N = neighbors(p, eps)",
    "    if |N| < minPts: mark p as noise",
    "    else: start cluster C at p",
    "        expand C through every core point in N",
]

# Clustering runs in the unit square, so the result never depends on the
# canvas size or on which display options shrink the content box.
EPS = 0.045
MIN_PTS = 4
NOISE = -1

# Cluster 0 takes the theme accent; the rest cycle through these.
CLUSTER_COLORS = ["#C792EA", "#F2994A", "#2FB56B", "#E8615A", "#E0A526", "#5EC8F8"]

HERO_SHARE = 0.72
LABEL_SIZE = 11
DOT_RADIUS = 3.2


def _moons(rng: random.Random, count: int) -> list[tuple[float, float]]:
    """Two interleaving half circles of radius r, in the top-left of the square."""
    r, ox, oy = 0.2, 0.08 + 0.2, 0.08 + 0.2
    points = []
    for i in range(count):
        t = math.pi * i / (count - 1)
        # Upper moon, then the lower one shifted right by r and down by r/2.
        points.append((ox + r * math.cos(t), oy - r * math.sin(t)))
    for i in range(count):
        t = math.pi * i / (count - 1)
        points.append((ox + r - r * math.cos(t), oy - r / 2 + r * math.sin(t)))
    return [(x + rng.gauss(0, 0.009), y + rng.gauss(0, 0.009)) for x, y in points]


def _ring_and_core(rng: random.Random) -> list[tuple[float, float]]:
    cx, cy, radius = 0.30, 0.73, 0.17
    ring = []
    for i in range(96):
        t = 2 * math.pi * i / 96
        ring.append(
            (cx + radius * math.cos(t) + rng.gauss(0, 0.008),
             cy + radius * math.sin(t) + rng.gauss(0, 0.008))
        )
    core = [(cx + rng.gauss(0, 0.03), cy + rng.gauss(0, 0.03)) for _ in range(26)]
    return ring + core


def _snake(rng: random.Random) -> list[tuple[float, float]]:
    points = []
    for i in range(48):
        y = 0.08 + 0.36 * i / 47
        x = 0.85 + 0.06 * math.sin(y * 18)
        points.append((x + rng.gauss(0, 0.007), y + rng.gauss(0, 0.007)))
    return points


def _blob(rng: random.Random) -> list[tuple[float, float]]:
    return [(0.78 + rng.gauss(0, 0.045), 0.72 + rng.gauss(0, 0.045)) for _ in range(44)]


def dataset() -> list[tuple[float, float]]:
    rng = random.Random(7)
    points = _moons(rng, 56) + _ring_and_core(rng) + _snake(rng) + _blob(rng)
    points += [(rng.uniform(0.03, 0.97), rng.uniform(0.03, 0.97)) for _ in range(34)]
    return points


def dbscan(
    points: list[tuple[float, float]], eps: float, min_pts: int
) -> tuple[list[int], list[bool]]:
    """Plain DBSCAN. Returns each point's cluster id (NOISE for outliers) and
    whether it is a core point. A point counts itself as one of its own
    neighbors, as in the original paper."""
    neighbors = [
        [j for j, q in enumerate(points) if math.dist(p, q) <= eps] for p in points
    ]
    is_core = [len(n) >= min_pts for n in neighbors]
    labels: list[int | None] = [None] * len(points)
    cluster = 0
    for i in range(len(points)):
        if labels[i] is not None:
            continue
        if not is_core[i]:
            labels[i] = NOISE  # may still be claimed later as a border point
            continue
        labels[i] = cluster
        frontier = list(neighbors[i])
        while frontier:
            j = frontier.pop()
            if labels[j] == NOISE:
                labels[j] = cluster
            if labels[j] is not None:
                continue
            labels[j] = cluster
            if is_core[j]:
                frontier.extend(neighbors[j])
        cluster += 1
    return [NOISE if label is None else label for label in labels], is_core


def _color(ctx: RenderContext, label: int) -> str:
    if label == 0:
        return ctx.theme.accent
    return CLUSTER_COLORS[(label - 1) % len(CLUSTER_COLORS)]


def _cross(dwg, x, y, size, color, width=1.4):
    for dx in (-size, size):
        dwg.add(
            dwg.line(
                start=(round(x - dx, 1), round(y - size, 1)),
                end=(round(x + dx, 1), round(y + size, 1)),
                stroke=color,
                stroke_width=width,
            )
        )


def _point(dwg, ctx, x, y, label, core, radius=DOT_RADIUS):
    x, y = round(x, 1), round(y, 1)
    if label == NOISE:
        _cross(dwg, x, y, radius * 0.9, ctx.theme.muted)
    elif core:
        dwg.add(dwg.circle(center=(x, y), r=radius, fill=_color(ctx, label)))
    else:
        dwg.add(
            dwg.circle(
                center=(x, y),
                r=radius,
                fill=ctx.theme.background,
                stroke=_color(ctx, label),
                stroke_width=1.5,
            )
        )


def _text(dwg, ctx, x, y, text, size=LABEL_SIZE, color=None, anchor="middle"):
    dwg.add(
        dwg.text(
            text,
            insert=(round(x, 1), round(y, 1)),
            fill=color or ctx.theme.muted,
            font_family=ctx.theme.font_family,
            font_size=size,
            text_anchor=anchor,
        )
    )


def _eps_ring(dwg, ctx, x, y, radius, color, opacity=0.9):
    dwg.add(
        dwg.circle(
            center=(round(x, 1), round(y, 1)),
            r=round(radius, 1),
            fill="none",
            stroke=color,
            stroke_width=1,
            stroke_dasharray="4,3",
            opacity=opacity,
        )
    )


def _draw_hero(dwg, ctx, ox, oy, side, points, labels, is_core):
    def at(p):
        return ox + p[0] * side, oy + p[1] * side

    eps_px = EPS * side
    # Faint ε-discs first, so the dots sit on top of the density they form.
    for p, label, core in zip(points, labels, is_core, strict=True):
        if core and label != NOISE:
            x, y = at(p)
            dwg.add(
                dwg.circle(
                    center=(round(x, 1), round(y, 1)),
                    r=round(eps_px, 1),
                    fill=_color(ctx, label),
                    opacity=0.07,
                )
            )
    for p, label, core in zip(points, labels, is_core, strict=True):
        _point(dwg, ctx, *at(p), label, core)

    # Show ε on the leftmost core point of the first cluster, where the
    # radius line points into open space.
    anchor = min(
        (p for p, label, core in zip(points, labels, is_core, strict=True) if core and label == 0),
        key=lambda p: p[0],
    )
    ax, ay = at(anchor)
    _eps_ring(dwg, ctx, ax, ay, eps_px, ctx.theme.foreground)
    dwg.add(
        dwg.line(
            start=(round(ax, 1), round(ay, 1)),
            end=(round(ax - eps_px, 1), round(ay, 1)),
            stroke=ctx.theme.foreground,
            stroke_width=1,
        )
    )
    _text(dwg, ctx, ax - eps_px / 2, ay - 6, "ε", size=LABEL_SIZE + 3, color=ctx.theme.foreground)


def _legend_panel(dwg, ctx, cx, cy, radius, kind):
    """One close-up: a point at (cx, cy) with its ε-circle and neighbors."""
    accent = ctx.theme.accent
    if kind == "core":
        _eps_ring(dwg, ctx, cx, cy, radius, accent)
        for angle, dist in ((0.4, 0.55), (2.1, 0.7), (3.6, 0.45), (5.0, 0.8)):
            nx, ny = cx + math.cos(angle) * dist * radius, cy + math.sin(angle) * dist * radius
            _point(dwg, ctx, nx, ny, 0, True, radius=4)
        _point(dwg, ctx, cx, cy, 0, True, radius=6)
        return ("core", f"≥ {MIN_PTS} points within ε")
    if kind == "border":
        # A core neighbor sits inside the ring, so the border point joins its
        # cluster without being dense enough to grow it further.
        kx, ky = cx - radius * 0.65, cy + radius * 0.2
        _eps_ring(dwg, ctx, cx, cy, radius, ctx.theme.muted, opacity=0.7)
        _eps_ring(dwg, ctx, kx, ky, radius, accent, opacity=0.5)
        _point(dwg, ctx, kx, ky, 0, True, radius=4)
        _point(dwg, ctx, cx + radius * 0.3, cy - radius * 0.55, 0, False, radius=4)
        _point(dwg, ctx, cx, cy, 0, False, radius=6)
        return ("border", "near a core, not dense")
    _eps_ring(dwg, ctx, cx, cy, radius, ctx.theme.muted, opacity=0.7)
    _point(dwg, ctx, cx, cy, NOISE, False, radius=6)
    return ("noise", "nobody within ε")


def draw(ctx: RenderContext) -> str:
    dwg, box = new_canvas(
        ctx,
        title=TITLE,
        tagline=TAGLINE,
        pseudocode=PSEUDOCODE,
    )

    points = dataset()
    labels, is_core = dbscan(points, EPS, MIN_PTS)
    clusters = len({label for label in labels if label != NOISE})
    noise = labels.count(NOISE)

    hero_height = box.height * HERO_SHARE
    side = max(min(box.width, hero_height - 24), 0)
    ox = box.x + (box.width - side) / 2
    _draw_hero(dwg, ctx, ox, box.y, side, points, labels, is_core)
    _text(
        dwg,
        ctx,
        box.x + box.width / 2,
        box.y + side + 18,
        f"ε = {EPS}   minPts = {MIN_PTS}   →   {clusters} clusters, {noise} noise points",
    )

    legend_top = box.y + hero_height + 16
    legend_height = box.y + box.height - legend_top
    radius = max(min(legend_height * 0.3, box.width / 12), 4)
    cy = legend_top + radius + 6
    for i, kind in enumerate(("core", "border", "noise")):
        cx = box.x + box.width * (i + 0.5) / 3
        name, caption = _legend_panel(dwg, ctx, cx, cy, radius, kind)
        _text(dwg, ctx, cx, cy + radius + 22, name.upper(), size=LABEL_SIZE + 1,
              color=ctx.theme.foreground)
        _text(dwg, ctx, cx, cy + radius + 38, caption)

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="dbscan",
    title=TITLE,
    tagline=TAGLINE,
    category=AlgorithmCategory.MACHINE_LEARNING,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#14B8A6",
    author="Julio Rodriguez Martino",
    date="2026-11-23",
)
