"""Linear congruential generator: pseudo-random numbers from one line of arithmetic.

The hero is two cubes. The left one is parameter space: its axes are a, c
and m, and each point is one generator that reaches its full period, cycling
through all m values before it repeats (the Hull-Dobell conditions). Good
generators turn out to be rare and form a sparse lattice. The right one is
the method's most famous flaw: the first 1000 outputs of RANDU (a=65539,
c=0, m=2^31) as consecutive triples (x[n], x[n+1], x[n+2]), seen from the
one angle where every point lines up on just 15 parallel planes ("random
numbers fall mainly in the planes", Marsaglia 1968). In both cubes, color
marks depth. Below, the first 1000 outputs of three parameter families are
drawn as dot charts, colored from first to last output, showing how a, c and
m decide how soon the sequence starts repeating itself.
"""

import math

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import RenderContext, new_canvas

TITLE = "Linear Congruential Generator"
TAGLINE = "One line of arithmetic, a stream of (almost-)random numbers."

PSEUDOCODE = [
    "x[n+1] = (a * x[n] + c) mod m",
    "u[n]   = x[n] / m",
]

SAMPLES = 1000

# Parameter space cube: every a and c in [0, m) for each m up to this bound.
# Since a and c stay below m, the points fill a pyramid; the camera looks up
# from the a = c = 0 side, so its tip sits at the bottom and each layer of m
# widens as it rises.
MAX_MODULUS = 64
PARAM_VIEW = (-1.0, -0.8, 0.35)

# RANDU: every consecutive triple satisfies 9*u[n] - 6*u[n+1] + u[n+2] = k for an
# integer k, so all the points sit on the planes perpendicular to this normal.
RANDU = (65539, 0, 2**31, 1)
RANDU_NORMAL = (9.0, -6.0, 1.0)

# (a, c, m, seed, label) for the dot charts, from shortest to longest period.
FAMILIES = (
    (13, 0, 64, 1, "a=13  c=0  m=64  period 16"),
    (21, 1, 256, 0, "a=21  c=1  m=256  period 256"),
    (1103515245, 12345, 2**31, 1, "a=1103515245  c=12345  m=2^31  period 2^31"),
)

LABEL_SIZE = 11

# Second color of the depth and sequence gradients: dots blend from the accent
# (nearest the camera, or first in the sequence) to this one (furthest, or
# last), so position along the hidden axis stays readable in a flat image.
SECONDARY = "#7C5CFF"


def lcg(a: int, c: int, m: int, seed: int, count: int) -> list[float]:
    """The first `count` outputs of the generator, scaled to [0, 1)."""
    values = []
    x = seed
    for _ in range(count):
        x = (a * x + c) % m
        values.append(x / m)
    return values


def _prime_factors(n: int) -> list[int]:
    factors = []
    p = 2
    while p * p <= n:
        if n % p == 0:
            factors.append(p)
            while n % p == 0:
                n //= p
        p += 1
    if n > 1:
        factors.append(n)
    return factors


def has_full_period(a: int, c: int, m: int) -> bool:
    """Hull-Dobell: the generator visits all m values before repeating iff c
    and m are coprime, a - 1 is divisible by every prime factor of m, and
    a - 1 is divisible by 4 whenever m is."""
    if math.gcd(c, m) != 1:
        return False
    if any((a - 1) % p for p in _prime_factors(m)):
        return False
    return m % 4 != 0 or (a - 1) % 4 == 0


def full_period_generators(max_modulus: int) -> list[tuple[int, int, int]]:
    return [
        (a, c, m)
        for m in range(2, max_modulus + 1)
        for a in range(1, m)
        for c in range(m)
        if has_full_period(a, c, m)
    ]


def _rgb(color: str) -> tuple[int, int, int]:
    hex_digits = color.lstrip("#")
    if len(hex_digits) == 3:
        hex_digits = "".join(ch * 2 for ch in hex_digits)
    return int(hex_digits[0:2], 16), int(hex_digits[2:4], 16), int(hex_digits[4:6], 16)


def _mix(start: str, end: str, t: float) -> str:
    """The color a fraction `t` of the way from `start` to `end`."""
    a, b = _rgb(start), _rgb(end)
    return "#{:02x}{:02x}{:02x}".format(
        *(round(x + (y - x) * t) for x, y in zip(a, b, strict=True))
    )


def _normalize(v):
    length = math.sqrt(sum(c * c for c in v))
    return tuple(c / length for c in v)


def _dot(u, v) -> float:
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


def _cross(u, v):
    return (
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    )


def _view_basis(view, up_axis):
    """Screen axes for an orthographic camera looking along `view`, with the
    cube axis `up_axis` projected onto the screen as "up"."""
    view = _normalize(view)
    axis = tuple(1.0 if i == up_axis else 0.0 for i in range(3))
    along = _dot(axis, view)
    up = _normalize(tuple(a - along * v for a, v in zip(axis, view, strict=True)))
    right = _cross(up, view)
    return right, up, view


def _randu_view():
    """Looks along the RANDU planes: the isometric diagonal (1, 1, 1) with its
    component along the plane normal removed, so each plane is seen edge-on
    and collapses to a line."""
    normal = _normalize(RANDU_NORMAL)
    diagonal = (1.0, 1.0, 1.0)
    along = _dot(diagonal, normal)
    return tuple(d - along * n for d, n in zip(diagonal, normal, strict=True))


def _draw_cube(dwg, ctx, cx, cy, size, view, up_axis, names, points, dot_radius, dot_opacity):
    """Draws a unit cube with its three axes labeled and `points` (each in
    [0, 1]^3) plotted inside it."""
    right, up, view = _view_basis(view, up_axis)

    def project(p):
        q = (p[0] - 0.5, p[1] - 0.5, p[2] - 0.5)
        return cx + _dot(q, right) * size, cy - _dot(q, up) * size

    corners = [(x, y, z) for x in (0, 1) for y in (0, 1) for z in (0, 1)]
    # The corner furthest from the camera is the hidden one: its three edges
    # are drawn dashed so the cube still reads as a solid.
    hidden = min(corners, key=lambda p: _dot(p, view))
    for i, a in enumerate(corners):
        for b in corners[i + 1 :]:
            if sum(abs(p - q) for p, q in zip(a, b, strict=True)) != 1:
                continue
            behind = a == hidden or b == hidden
            dwg.add(
                dwg.line(
                    start=project(a),
                    end=project(b),
                    stroke=ctx.theme.muted,
                    stroke_width=1,
                    stroke_dasharray="4,4" if behind else "none",
                    opacity=0.6 if behind else 0.9,
                )
            )

    # Label each axis on its outermost parallel edge, pushed away from the
    # cube's center, so the labels sit on the silhouette instead of inside it.
    for axis, name in enumerate(names):
        edges = []
        for p in corners:
            if p[axis] != 0:
                continue
            q = tuple(1 if i == axis else v for i, v in enumerate(p))
            mid = tuple((a + b) / 2 for a, b in zip(p, q, strict=True))
            mx, my = project(mid)
            edges.append((math.hypot(mx - cx, my - cy), mx, my))
        _, mx, my = max(edges)
        dx, dy = mx - cx, my - cy
        dist = math.hypot(dx, dy) or 1.0
        dwg.add(
            dwg.text(
                name,
                insert=(mx + dx / dist * 22, my + dy / dist * 22 + 4),
                fill=ctx.theme.foreground,
                font_family=ctx.theme.font_family,
                font_size=LABEL_SIZE + 2,
                text_anchor="middle",
            )
        )

    # Color by depth rank: the accent on the nearest point, SECONDARY on the
    # furthest. Ranking, rather than raw distance, spreads the full gradient
    # over the points even when most of them sit at middle depths. Points are
    # drawn back to front so the near ones sit on top.
    ordered = sorted(points, key=lambda p: _dot(p, view))
    last = max(len(ordered) - 1, 1)
    for rank, p in enumerate(ordered):
        x, y = project(p)
        t = 1 - rank / last
        dwg.add(
            dwg.circle(
                center=(round(x, 1), round(y, 1)),
                r=dot_radius,
                fill=_mix(ctx.theme.accent, SECONDARY, t),
                opacity=dot_opacity,
            )
        )


def _caption(dwg, ctx, x, y, text):
    dwg.add(
        dwg.text(
            text,
            insert=(x, y),
            fill=ctx.theme.muted,
            font_family=ctx.theme.font_family,
            font_size=LABEL_SIZE,
            text_anchor="middle",
        )
    )


def _draw_strip(dwg, ctx, x, y, width, height, family):
    a, c, m, seed, label = family
    dwg.add(
        dwg.text(
            label,
            insert=(x, y - 8),
            fill=ctx.theme.muted,
            font_family=ctx.theme.font_family,
            font_size=LABEL_SIZE,
        )
    )
    dwg.add(
        dwg.line(
            start=(x, y + height),
            end=(x + width, y + height),
            stroke=ctx.theme.muted,
            stroke_width=1,
        )
    )
    values = lcg(a, c, m, seed, SAMPLES)
    step = width / (SAMPLES - 1)
    # Dots rather than a connected line: a short period then shows up as a
    # few horizontal bands and a repeating motif, instead of a dense scribble.
    # The color runs from the accent (n = 0) to SECONDARY (the last output).
    for i, v in enumerate(values):
        dwg.add(
            dwg.circle(
                center=(round(x + i * step, 1), round(y + (1 - v) * height, 1)),
                r=1.4,
                fill=_mix(ctx.theme.accent, SECONDARY, i / (SAMPLES - 1)),
                opacity=0.9,
            )
        )


def draw(ctx: RenderContext) -> str:
    dwg, box = new_canvas(
        ctx,
        title=TITLE,
        tagline=TAGLINE,
        pseudocode=PSEUDOCODE,
    )

    # A unit cube's projection spans up to about 1.7 times `cube_size`, so the
    # size is capped by both the half-width slot and the hero's height.
    hero_height = box.height * 0.55
    half_width = box.width / 2
    cube_size = min(half_width * 0.56, (hero_height - 40) / 1.75)
    cube_y = box.y + hero_height / 2 - 14
    caption_y = cube_y + cube_size * 0.88 + 28

    # Left: parameter space. Each axis spans [0, MAX_MODULUS].
    generators = full_period_generators(MAX_MODULUS)
    total = sum(m * (m - 1) for m in range(2, MAX_MODULUS + 1))
    scale = float(MAX_MODULUS)
    left_x = box.x + half_width / 2
    _draw_cube(
        dwg,
        ctx,
        left_x,
        cube_y,
        cube_size,
        view=PARAM_VIEW,
        up_axis=2,
        names=("a", "c", "m"),
        points=[(a / scale, c / scale, m / scale) for a, c, m in generators],
        dot_radius=1.2,
        dot_opacity=0.85,
    )
    _caption(dwg, ctx, left_x, caption_y, f"full-period (a, c, m), m <= {MAX_MODULUS}")
    _caption(dwg, ctx, left_x, caption_y + 16, f"{len(generators)} of {total} generators")

    # Right: RANDU's triples, seen edge-on to its 15 planes.
    values = lcg(*RANDU, SAMPLES + 2)
    right_x = box.x + half_width * 1.5
    _draw_cube(
        dwg,
        ctx,
        right_x,
        cube_y,
        cube_size,
        view=_randu_view(),
        up_axis=2,
        names=("x[n]", "x[n+1]", "x[n+2]"),
        points=[(values[n], values[n + 1], values[n + 2]) for n in range(SAMPLES)],
        dot_radius=1.6,
        dot_opacity=0.85,
    )
    _caption(dwg, ctx, right_x, caption_y, "RANDU, a=65539 c=0 m=2^31")
    _caption(dwg, ctx, right_x, caption_y + 16, f"{SAMPLES} triples, 15 planes")

    strips_top = caption_y + 50
    dwg.add(
        dwg.text(
            f"FIRST {SAMPLES} OUTPUTS, x[n] / m",
            insert=(box.x, strips_top),
            fill=ctx.theme.muted,
            font_family=ctx.theme.font_family,
            font_size=LABEL_SIZE,
        )
    )
    gap = 30
    slot = (box.y + box.height - strips_top - 12) / len(FAMILIES)
    strip_height = max(slot - gap, 8)
    for i, family in enumerate(FAMILIES):
        _draw_strip(dwg, ctx, box.x, strips_top + gap + i * slot, box.width, strip_height, family)

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="linear-congruential-generator",
    title=TITLE,
    tagline=TAGLINE,
    category=AlgorithmCategory.RANDOMNESS,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#2FB56B",
    author="Andrei Rukavina",
    date="2026-11-21",
)
