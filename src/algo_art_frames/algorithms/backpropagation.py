"""Backpropagation: run the network forward, then send the error backward
through those same connections to update every weight.

Layers are drawn as 8 real columns, (0), (1), (2), (3), then (L-3), (L-2),
(L-1), (L), with the hidden layers in between collapsed into a plain "..."
marker, the same truncation convention textbooks use when diagramming deep
networks. Forward edges are curved and arrowed, and backward edges are a
second, parallel, accent-colored curve tracing those same connections in
reverse, also arrowed, but pointing the other way. Two framing arrows label
the overall flow direction: "Training" above, running left-to-right, and
"Backpropagation" below, running right-to-left. The pseudocode block at the
bottom is real matrix calculus, typeset with true super/subscripts. On top
of all that, a spray-painted "GO DEEP!" tag traces its strokes through the
network's own node positions.
"""

import itertools
import math
import random
import re

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import (
    MARGIN,
    PSEUDOCODE_LINE_HEIGHT,
    ContentBox,
    RenderContext,
    new_canvas,
)

TITLE = "Backpropagation"
TAGLINE = "Learn by sending the error backward."

PSEUDOCODE = [
    "z^(l) = W^(l) . phi^(l-1) + b^(l)",
    "phi^(l) = sigma(z^(l))",
    "delta^(L) = (phi^(L) - y) * sigma'(z^(L))",
    "delta^(l) = (W^(l+1))^T . delta^(l+1) * sigma'(z^(l))",
    "dE/dW^(l) = delta^(l) . (phi^(l-1))^T",
    "dE/db^(l) = delta^(l)",
    "W^(l) <- W^(l) - eta . dE/dW^(l)",
]

# This is a rich-markup version of the same 7 steps, used only inside
# draw(): ^{...} means superscript, and _{...} means subscript.
# PLUGIN.pseudocode above stays plain ASCII, since that field is part of the
# plugin's metadata and gets used outside of this SVG.
FORMULA_LINES = [
    "z^{(l)} = W^{(l)} · φ^{(l-1)} + b^{(l)}",
    "φ^{(l)} = σ(z^{(l)})",
    "δ^{(L)} = (φ^{(L)} - y) ⊙ σ'(z^{(L)})",
    "δ^{(l)} = (W^{(l+1)})^{T} δ^{(l+1)} ⊙ σ'(z^{(l)})",
    "∂E/∂W^{(l)} = δ^{(l)} (φ^{(l-1)})^{T}",
    "∂E/∂b^{(l)} = δ^{(l)}",
    "W^{(l)} ← W^{(l)} - η · ∂E/∂W^{(l)}",
]

# There are 8 real node-columns here, 4 per cluster, plus 1 collapsed "..."
# gap in the middle. Drawing a fake edge across that gap would wrongly imply
# that column 3 and column L-3 are adjacent, when in reality 2 real hidden
# layers (4, 5) are elided there. Each cluster's 4 columns are spaced within
# their own span, with a deliberately narrow GAP_FRAC left between the two
# clusters, narrower than an evenly-spaced 9th "slot" would be, since the
# whole point of widening each cluster from 3 to 4 columns was to shrink
# this gap, not merely relocate it.
REAL_SYMBOLS = ["0", "1", "2", "3", "L-3", "L-2", "L-1", "L"]
REAL_COUNTS = [3, 4, 4, 4, 4, 4, 3, 2]
REAL_ROLES = ["input", "hidden", "hidden", "hidden", "hidden", "hidden", "hidden", "output"]
# This is the layer index used for the cold-to-hot gradient below: the
# conceptual depth (0..L_TOTAL), not the drawn column's position in
# REAL_SYMBOLS, so that the gradient still reflects the true depth jump
# across the collapsed layers.
REAL_LAYER_INDICES = [0, 1, 2, 3, 6, 7, 8, 9]
L_TOTAL = 9

CLUSTER_SIZE = 4
SLOT_START_FRAC = 0.06
SLOT_END_FRAC = 0.94
GAP_FRAC = 0.08  # fraction of diagram width reserved for the middle ellipsis gap
CLUSTER_SPAN_FRAC = (SLOT_END_FRAC - SLOT_START_FRAC - GAP_FRAC) / 2

COLD_COLOR = "#5EC8F8"  # same cool hue A* uses for its start-of-path gradient end
HOT_COLOR = "#FF3B30"  # a fixed thermal "hot" red, independent of ctx.theme.accent

NODE_R = 18
NODE_LABEL_FONT_SIZE = 10
INPUT_LABEL_FONT_SIZE = 12
CAPTION_FONT_SIZE = 11
ELLIPSIS_FONT_SIZE = 24

# The vertical layout, top to bottom, goes like this: the "Training" flow
# arrow, the "(idx)" captions (sitting close above the nodes, not the
# arrow), the node area, and then the "Backpropagation" flow arrow. The node
# area's per-node pitch is computed from diagram_box's actual height
# (filling essentially all of it, minus these small fixed reserves for the
# arrows and captions) rather than from a fixed pixel value, so the chart
# scales up to use the available vertical space on a tall canvas instead of
# staying a small fixed size centered in a mostly-empty box. Node *count*
# still governs each column's own footprint through the shared pitch (see
# _layer_positions), so the input/output columns, which have fewer nodes,
# still come out smaller and centered rather than stretched to match the
# deepest (4-node) columns. Only the *scale* of that footprint grows with
# the box.
TOP_LINE_Y_OFFSET = 24  # diagram_box.y -> the "Training" arrow's line
CAPTION_Y_OFFSET = 46  # diagram_box.y -> the "(idx)" caption baseline
NODE_AREA_TOP_GAP = 18  # caption baseline -> node_area_top (1.5x the original 12px)
NODE_AREA_BOTTOM_GAP = 24  # node_area_bottom -> the "Backpropagation" arrow's line (1.5x the original 16px)
BOTTOM_ARROW_MARGIN = 14  # the bottom arrow's own footprint -> diagram_box's bottom edge
MIN_NODE_PITCH = 2 * NODE_R + 24  # floor, so nodes can't crowd together on a very short canvas

FLOW_ARROW_INSET = 24  # horizontal inset of the big flow arrows from diagram_box's edges
FLOW_ARROW_FONT_SIZE = 12
FLOW_ARROW_HEAD_LEN = 10
FLOW_ARROW_HEAD_HALF_W = 4

FORWARD_BULGE = 8  # px the forward curve's control point bulges off the straight line
BACKWARD_OFFSET = 5  # px the backward curve is translated, parallel to the forward one
ARROW_LEN = 8
ARROW_HALF_W = 3.5

FORMULA_FONT_SIZE = 13
FORMULA_LINE_HEIGHT = 20  # drawing pitch, note the reservation math below uses PSEUDOCODE_LINE_HEIGHT instead

# This is a mini-markup syntax for super/subscript text: ^{...} raises text,
# _{...} lowers it, and only a single level is supported (none of
# FORMULA_LINES, nor the x_i node labels, ever nest one inside the other).
_SCRIPT_RE = re.compile(r"\^\{(?P<sup>[^{}]*)\}|_\{(?P<sub>[^{}]*)\}")
SCRIPT_FONT_RATIO = 0.62
SCRIPT_SHIFT_RATIO = 0.45

# This is a "spray tag" written on top of the finished diagram: bold,
# single-stroke graffiti letters (all-caps, since tags tend to be
# stylized/capitalized anyway) sized to each cluster's own footprint, with
# stroke endpoints snapped onto real node coordinates wherever one happens
# to be close enough. That way the tag reads as if it were traced from the
# network's own connections, rather than just text pasted over it. Each
# glyph is one or more polyline strokes in a normalized 0..1 unit box.
GRAFFITI_GLYPHS: dict[str, list[list[tuple[float, float]]]] = {
    "G": [
        [
            (0.9, 0.16),
            (0.6, 0.02),
            (0.3, 0.06),
            (0.07, 0.3),
            (0.0, 0.56),
            (0.09, 0.82),
            (0.36, 0.98),
            (0.7, 0.97),
            (0.9, 0.8),
            (0.9, 0.54),
            (0.58, 0.54),
        ]
    ],
    "O": [
        [
            (0.5, 0.0),
            (0.82, 0.12),
            (1.0, 0.4),
            (1.0, 0.62),
            (0.82, 0.9),
            (0.5, 1.0),
            (0.18, 0.9),
            (0.0, 0.62),
            (0.0, 0.4),
            (0.18, 0.12),
            (0.5, 0.0),
        ]
    ],
    "D": [
        [(0.05, 0.0), (0.05, 1.0)],
        [(0.05, 0.0), (0.55, 0.0), (0.92, 0.28), (0.92, 0.72), (0.55, 1.0), (0.05, 1.0)],
    ],
    "E": [
        [(0.88, 0.0), (0.05, 0.0), (0.05, 1.0), (0.88, 1.0)],
        [(0.05, 0.52), (0.66, 0.52)],
    ],
    "P": [
        [(0.05, 1.0), (0.05, 0.0), (0.55, 0.0), (0.88, 0.22), (0.88, 0.46), (0.55, 0.58), (0.05, 0.58)],
    ],
    "!": [
        [(0.5, 0.0), (0.4, 0.68)],
        [(0.46, 0.85), (0.42, 0.97)],
    ],
}
GRAFFITI_WORDS = ("GO", "DEEP!")  # one word per cluster, left then right
GRAFFITI_COLOR = "#2ECC40"
GRAFFITI_SHADOW_COLOR = "#04120a"
GRAFFITI_STROKE_WIDTH = 11
GRAFFITI_SHADOW_OFFSET = 3
GRAFFITI_JITTER = 3  # px of random wobble on non-snapped points, for a hand-sprayed feel
GRAFFITI_ASPECT = 2.1  # height/width per glyph, tall and stretched, in true graffiti-style proportions
GRAFFITI_GAP_RATIO = 0.32  # inter-glyph gap, as a fraction of one glyph's width
GRAFFITI_SNAP_RADIUS = 46  # px, a stroke vertex this close to a real node snaps onto it exactly
GRAFFITI_MAX_HEIGHT_RATIO = 0.85  # clamp on glyph height vs. the vertical room available

# This gives the tag its aerosol texture: a soft, wide, low-opacity "halo"
# pass drawn under the solid stroke (simulating overspray bleeding past the
# can's true line), plus a scatter of small speckle dots along it
# (simulating spray paint's grain), so that the stroke does not read as one
# flat, mechanically clean line.
GRAFFITI_HALO_WIDTH_RATIO = 2.4  # halo stroke width = GRAFFITI_STROKE_WIDTH * this
GRAFFITI_HALO_OPACITY = 0.14
GRAFFITI_SPECKLE_DENSITY = 0.06  # speckles per px of stroke length
GRAFFITI_SPECKLE_MAX_PER_STROKE = 100
GRAFFITI_SPECKLE_SPREAD = 9  # std. dev. (px) of a speckle's perpendicular offset from the stroke
GRAFFITI_SPECKLE_MIN_R = 0.6
GRAFFITI_SPECKLE_MAX_R = 2.6
GRAFFITI_SPECKLE_MIN_OPACITY = 0.12
GRAFFITI_SPECKLE_MAX_OPACITY = 0.5


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def _lerp_color(start: str, end: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(start)
    r2, g2, b2 = _hex_to_rgb(end)
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _contrast_text_color(fill: str) -> str:
    """Dark or light ink, whichever actually reads against `fill`. Every
    point along the cold-to-hot gradient is bright and light, so this
    mostly ends up picking dark ink, but it stays correct even if the
    gradient's colors are ever swapped."""
    r, g, b = _hex_to_rgb(fill)
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#0b0e14" if luminance > 140 else "#f7f7f5"


def _rich_text(dwg, insert, markup, *, fill, font_family, font_size, text_anchor="start"):
    """Render `markup` (plain text plus ^{...}/_{...} runs) as one <text>
    element, with a <tspan> child per run. Note that SVG's `dy` on a tspan
    is relative to the previous baseline, not absolute, so a scripted run's
    dy has to be undone by the next run's dy before it can render at the
    normal baseline again, `baseline_offset` is what tracks how far
    off-baseline the pen currently sits. No tspan ever sets its own x/y, so
    all the runs stay within one SVG "text chunk", and `text_anchor` still
    centers or aligns the whole label correctly."""
    text_el = dwg.text(
        "", insert=insert, fill=fill, font_family=font_family, font_size=font_size, text_anchor=text_anchor
    )
    pos = 0
    baseline_offset = 0.0
    for match in _SCRIPT_RE.finditer(markup):
        if match.start() > pos:
            literal = markup[pos : match.start()]
            if baseline_offset:
                text_el.add(dwg.tspan(literal, dy=[-baseline_offset]))
                baseline_offset = 0.0
            else:
                text_el.add(dwg.tspan(literal))
        sup, sub = match.group("sup"), match.group("sub")
        shift = -SCRIPT_SHIFT_RATIO * font_size if sup is not None else SCRIPT_SHIFT_RATIO * font_size
        scripted = sup if sup is not None else sub
        text_el.add(dwg.tspan(scripted, dy=[shift - baseline_offset], font_size=SCRIPT_FONT_RATIO * font_size))
        baseline_offset = shift
        pos = match.end()
    if pos < len(markup):
        literal = markup[pos:]
        if baseline_offset:
            text_el.add(dwg.tspan(literal, dy=[-baseline_offset]))
        else:
            text_el.add(dwg.tspan(literal))
    return text_el


def _column_frac(cluster_index: int, position_in_cluster: int) -> float:
    start = SLOT_START_FRAC if cluster_index == 0 else SLOT_END_FRAC - CLUSTER_SPAN_FRAC
    return start + CLUSTER_SPAN_FRAC * position_in_cluster / (CLUSTER_SIZE - 1)


def _layer_positions(box):
    max_count = max(REAL_COUNTS)
    # NODE_AREA_TOP_GAP and NODE_AREA_BOTTOM_GAP are the clearance to a
    # node's *circle edge*, not to its center. The center itself needs to
    # sit an extra NODE_R further in, otherwise the topmost or bottommost
    # circle (in the tallest, 4-node columns) would overlap the
    # caption/arrow sitting right above or below it.
    top_reserve = CAPTION_Y_OFFSET + NODE_AREA_TOP_GAP + NODE_R
    bottom_reserve = NODE_AREA_BOTTOM_GAP + NODE_R + BOTTOM_ARROW_MARGIN
    node_block_height = max(box.height - top_reserve - bottom_reserve, 0)
    pitch = node_block_height / (max_count - 1) if max_count > 1 else 0.0
    pitch = max(pitch, MIN_NODE_PITCH)
    node_block_height = (max_count - 1) * pitch

    top_line_y = box.y + TOP_LINE_Y_OFFSET
    caption_y = box.y + CAPTION_Y_OFFSET
    node_area_top = caption_y + NODE_AREA_TOP_GAP + NODE_R
    node_area_bottom = node_area_top + node_block_height
    bottom_line_y = node_area_bottom + NODE_R + NODE_AREA_BOTTOM_GAP
    center_y = (node_area_top + node_area_bottom) / 2

    layers = []
    for i, (symbol, count, role, layer_index) in enumerate(
        zip(REAL_SYMBOLS, REAL_COUNTS, REAL_ROLES, REAL_LAYER_INDICES)
    ):
        cluster_index, position_in_cluster = divmod(i, CLUSTER_SIZE)
        x = box.x + box.width * _column_frac(cluster_index, position_in_cluster)
        if count == 1:
            ys = [center_y]
        else:
            col_top = center_y - (count - 1) * pitch / 2
            ys = [col_top + j * pitch for j in range(count)]
        layers.append((x, ys, role, symbol, layer_index))
    ellipsis_x = box.x + box.width * (SLOT_START_FRAC + CLUSTER_SPAN_FRAC + GAP_FRAC / 2)
    return layers, caption_y, ellipsis_x, center_y, top_line_y, bottom_line_y


def _perp_unit(x0: float, y0: float, x1: float, y1: float) -> tuple[float, float]:
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy) or 1.0
    return -dy / length, dx / length


def _forward_curve(x0: float, y0: float, x1: float, y1: float) -> tuple[str, float, float]:
    px, py = _perp_unit(x0, y0, x1, y1)
    mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
    cx, cy = mid_x + px * FORWARD_BULGE, mid_y + py * FORWARD_BULGE
    return f"M {x0} {y0} Q {cx} {cy} {x1} {y1}", cx, cy


def _backward_curve(
    x0: float, y0: float, cx: float, cy: float, x1: float, y1: float
) -> tuple[str, float, float, float, float]:
    """The same curve as `_forward_curve`, translated parallel to itself. It
    also returns the offset start point and offset control point, so the
    caller can place an arrowhead at the (offset) source end. The tangent
    there, for a quadratic Bezier, is simply (control - start), the same as
    at the destination end in `_arrowhead_points`."""
    px, py = _perp_unit(x0, y0, x1, y1)
    ox, oy = px * BACKWARD_OFFSET, py * BACKWARD_OFFSET
    bx0, by0 = x0 + ox, y0 + oy
    bcx, bcy = cx + ox, cy + oy
    bx1, by1 = x1 + ox, y1 + oy
    return f"M {bx0} {by0} Q {bcx} {bcy} {bx1} {by1}", bx0, by0, bcx, bcy


def _arrowhead_points(x1: float, y1: float, cx: float, cy: float, node_r: float) -> list[tuple[float, float]]:
    """A triangle at (x1, y1), oriented along the curve's true tangent at
    that point (exact for a quadratic Bezier: direction (x1-cx, y1-cy)), and
    pulled back by `node_r` so the tip does not disappear under the
    destination circle."""
    dx, dy = x1 - cx, y1 - cy
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    tip_x, tip_y = x1 - ux * node_r, y1 - uy * node_r
    base_x, base_y = tip_x - ux * ARROW_LEN, tip_y - uy * ARROW_LEN
    perp_x, perp_y = -uy, ux
    return [
        (tip_x, tip_y),
        (base_x + perp_x * ARROW_HALF_W, base_y + perp_y * ARROW_HALF_W),
        (base_x - perp_x * ARROW_HALF_W, base_y - perp_y * ARROW_HALF_W),
    ]


def _iter_edges(cluster):
    columns = [(x, ys) for x, ys, _, _, _ in cluster]
    for (x1, ys1), (x2, ys2) in itertools.pairwise(columns):
        for y1 in ys1:
            for y2 in ys2:
                yield x1, y1, x2, y2


def _flow_arrow(dwg, ctx, y: float, x_start: float, x_end: float, label: str, color: str) -> None:
    """A big framing arrow spanning the whole diagram width, labeled above
    its own line. When `x_start > x_end`, it draws itself (arrowhead
    included) pointing right-to-left, which is exactly what the
    "Backpropagation" arrow's reverse direction needs."""
    dwg.add(dwg.line(start=(x_start, y), end=(x_end, y), stroke=color, stroke_width=1.5))
    direction = 1 if x_end >= x_start else -1
    base_x = x_end - direction * FLOW_ARROW_HEAD_LEN
    dwg.add(
        dwg.polygon(
            points=[
                (x_end, y),
                (base_x, y - FLOW_ARROW_HEAD_HALF_W),
                (base_x, y + FLOW_ARROW_HEAD_HALF_W),
            ],
            fill=color,
        )
    )
    dwg.add(
        dwg.text(
            label,
            insert=((x_start + x_end) / 2, y - 8),
            fill=color,
            font_family=ctx.theme.font_family,
            font_size=FLOW_ARROW_FONT_SIZE,
            font_weight="bold",
            text_anchor="middle",
        )
    )


def _place_word(word: str, x_min: float, x_max: float, y_center: float, max_height: float):
    """Glyph boxes for `word`, filling [x_min, x_max] edge to edge. The
    letter count varies per cluster (2 for "GO", 5 for "DEEP!"), so words
    naturally come out different sizes. That unevenness is part of the
    tag's raw, hand-made feel, it is not a bug that needs normalizing away."""
    n = len(word)
    total_units = n + (n - 1) * GRAFFITI_GAP_RATIO
    unit_w = (x_max - x_min) / total_units
    gap_w = unit_w * GRAFFITI_GAP_RATIO
    glyph_h = min(unit_w * GRAFFITI_ASPECT, max_height)

    placements = []
    cursor = x_min
    for ch in word:
        placements.append((ch, cursor, y_center - glyph_h / 2, unit_w, glyph_h))
        cursor += unit_w + gap_w
    return placements


def _snap_point(
    x: float, y: float, nodes: list[tuple[float, float]], radius: float
) -> tuple[tuple[float, float], bool]:
    best = None
    best_d2 = radius * radius
    for nx, ny in nodes:
        d2 = (nx - x) ** 2 + (ny - y) ** 2
        if d2 <= best_d2:
            best_d2 = d2
            best = (nx, ny)
    if best is not None:
        return best, True
    return (x, y), False


def _sample_along_polyline(points: list[tuple[float, float]], t: float) -> tuple[float, float, float, float]:
    """Point at distance-fraction `t` in [0, 1] along `points`, along with the
    unit tangent of the segment it falls on (this is used to offset
    speckles perpendicular to the stroke, rather than scattering them with
    no relation at all to its shape)."""
    seg_lengths = [math.hypot(x1 - x0, y1 - y0) for (x0, y0), (x1, y1) in itertools.pairwise(points)]
    total = sum(seg_lengths) or 1.0
    target = t * total
    acc = 0.0
    for ((x0, y0), (x1, y1)), seg_len in zip(itertools.pairwise(points), seg_lengths, strict=True):
        seg_len = seg_len or 1e-6
        if acc + seg_len >= target:
            u = (target - acc) / seg_len
            return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, (x1 - x0) / seg_len, (y1 - y0) / seg_len
        acc += seg_len
    x0, y0 = points[-1]
    return x0, y0, 1.0, 0.0


def _draw_spray_speckles(dwg, points: list[tuple[float, float]], rng: random.Random) -> None:
    seg_lengths = [math.hypot(x1 - x0, y1 - y0) for (x0, y0), (x1, y1) in itertools.pairwise(points)]
    count = min(int(sum(seg_lengths) * GRAFFITI_SPECKLE_DENSITY), GRAFFITI_SPECKLE_MAX_PER_STROKE)
    for _ in range(count):
        bx, by, ux, uy = _sample_along_polyline(points, rng.random())
        perp_x, perp_y = -uy, ux
        offset = rng.gauss(0, GRAFFITI_SPECKLE_SPREAD)
        dwg.add(
            dwg.circle(
                center=(bx + perp_x * offset, by + perp_y * offset),
                r=rng.uniform(GRAFFITI_SPECKLE_MIN_R, GRAFFITI_SPECKLE_MAX_R),
                fill=GRAFFITI_COLOR,
                opacity=rng.uniform(GRAFFITI_SPECKLE_MIN_OPACITY, GRAFFITI_SPECKLE_MAX_OPACITY),
            )
        )


def _draw_graffiti_word(
    dwg,
    word: str,
    x_min: float,
    x_max: float,
    y_center: float,
    max_height: float,
    nodes: list[tuple[float, float]],
    rng: random.Random,
) -> None:
    for ch, gx, gy, gw, gh in _place_word(word, x_min, x_max, y_center, max_height):
        for stroke in GRAFFITI_GLYPHS.get(ch, []):
            points = []
            for u, v in stroke:
                px, py = gx + u * gw, gy + v * gh
                (px, py), snapped = _snap_point(px, py, nodes, GRAFFITI_SNAP_RADIUS)
                if not snapped:
                    px += rng.uniform(-GRAFFITI_JITTER, GRAFFITI_JITTER)
                    py += rng.uniform(-GRAFFITI_JITTER, GRAFFITI_JITTER)
                points.append((px, py))
            shadow_points = [(px + GRAFFITI_SHADOW_OFFSET, py + GRAFFITI_SHADOW_OFFSET) for px, py in points]
            dwg.add(
                dwg.polyline(
                    points=shadow_points,
                    fill="none",
                    stroke=GRAFFITI_SHADOW_COLOR,
                    stroke_width=GRAFFITI_STROKE_WIDTH,
                    stroke_linecap="round",
                    stroke_linejoin="round",
                    opacity=0.55,
                )
            )
            # This is the soft, wide, low-opacity halo, simulated overspray
            # bleeding past the can's true line, drawn before the solid core
            # stroke.
            dwg.add(
                dwg.polyline(
                    points=points,
                    fill="none",
                    stroke=GRAFFITI_COLOR,
                    stroke_width=GRAFFITI_STROKE_WIDTH * GRAFFITI_HALO_WIDTH_RATIO,
                    stroke_linecap="round",
                    stroke_linejoin="round",
                    opacity=GRAFFITI_HALO_OPACITY,
                )
            )
            dwg.add(
                dwg.polyline(
                    points=points,
                    fill="none",
                    stroke=GRAFFITI_COLOR,
                    stroke_width=GRAFFITI_STROKE_WIDTH,
                    stroke_linecap="round",
                    stroke_linejoin="round",
                    opacity=0.94,
                )
            )
            # This adds speckle grain on top of the solid stroke, the actual
            # aerosol "spray" texture, rather than just a clean marker line.
            _draw_spray_speckles(dwg, points, rng)


def _draw_graffiti(dwg, clusters) -> None:
    for cluster, word, seed in zip(clusters, GRAFFITI_WORDS, (1, 2)):
        xs = [x for x, _, _, _, _ in cluster]
        nodes = [(x, y) for x, ys, _, _, _ in cluster for y in ys]
        ys_all = [y for _, y in nodes]
        y_min, y_max = min(ys_all), max(ys_all)
        y_center = (y_min + y_max) / 2
        max_height = (y_max - y_min) * GRAFFITI_MAX_HEIGHT_RATIO
        _draw_graffiti_word(dwg, word, min(xs), max(xs), y_center, max_height, nodes, random.Random(seed))


def draw(ctx: RenderContext) -> str:
    # The formula block is hand-drawn here, since true super/subscript
    # typesetting is something new_canvas's plain-text pseudocode block
    # simply cannot do, so the built-in block is suppressed and its space
    # reservation is replicated manually instead.
    dwg, box = new_canvas(
        ctx,
        title=TITLE,
        tagline=TAGLINE,
        pseudocode=[],
    )

    if ctx.show_pseudocode and FORMULA_LINES:
        block_height = len(FORMULA_LINES) * PSEUDOCODE_LINE_HEIGHT + MARGIN
        content_bottom = box.y + box.height - block_height
        block_y = content_bottom + MARGIN // 2
        diagram_box = ContentBox(x=box.x, y=box.y, width=box.width, height=content_bottom - box.y)
    else:
        diagram_box = box
        block_y = None

    layers, caption_y, ellipsis_x, ellipsis_y, top_line_y, bottom_line_y = _layer_positions(diagram_box)
    clusters = (layers[0:4], layers[4:8])

    # Forward edges: curved, arrowed, and muted, drawn for both clusters first.
    for cluster in clusters:
        for x1, y1, x2, y2 in _iter_edges(cluster):
            path_d, cx, cy = _forward_curve(x1, y1, x2, y2)
            dwg.add(dwg.path(d=path_d, fill="none", stroke=ctx.theme.muted, stroke_width=0.75))
            dwg.add(dwg.polygon(points=_arrowhead_points(x2, y2, cx, cy, NODE_R), fill=ctx.theme.muted))

    # Backward edges: the same curves, translated parallel to themselves, in
    # the accent color, arrowed at the (offset) source end. They point the
    # opposite way from the forward arrows above, while following those same
    # connections.
    for cluster in clusters:
        for x1, y1, x2, y2 in _iter_edges(cluster):
            _, cx, cy = _forward_curve(x1, y1, x2, y2)
            back_d, bx0, by0, bcx, bcy = _backward_curve(x1, y1, cx, cy, x2, y2)
            dwg.add(dwg.path(d=back_d, fill="none", stroke=ctx.theme.accent, stroke_width=1))
            dwg.add(dwg.polygon(points=_arrowhead_points(bx0, by0, bcx, bcy, NODE_R), fill=ctx.theme.accent))

    _flow_arrow(
        dwg,
        ctx,
        top_line_y,
        diagram_box.x + FLOW_ARROW_INSET,
        diagram_box.x + diagram_box.width - FLOW_ARROW_INSET,
        "Training",
        ctx.theme.muted,
    )
    _flow_arrow(
        dwg,
        ctx,
        bottom_line_y,
        diagram_box.x + diagram_box.width - FLOW_ARROW_INSET,
        diagram_box.x + FLOW_ARROW_INSET,
        "Backpropagation",
        ctx.theme.accent,
    )

    dwg.add(
        dwg.text(
            "⋯",
            insert=(ellipsis_x, ellipsis_y + 8),
            fill=ctx.theme.muted,
            font_family=ctx.theme.font_family,
            font_size=ELLIPSIS_FONT_SIZE,
            text_anchor="middle",
        )
    )

    for x, ys, role, symbol, layer_index in layers:
        color = _lerp_color(COLD_COLOR, HOT_COLOR, layer_index / L_TOTAL)
        text_color = _contrast_text_color(color)
        label_font_size = INPUT_LABEL_FONT_SIZE if role == "input" else NODE_LABEL_FONT_SIZE
        for i, y in enumerate(ys):
            dwg.add(dwg.circle(center=(x, y), r=NODE_R, fill=color))
            if role == "input":
                label_markup = f"x_{{{i}}}"
            elif role == "output":
                label_markup = "φ"
            else:
                label_markup = "z|φ"
            dwg.add(
                _rich_text(
                    dwg,
                    (x, y + 3),
                    label_markup,
                    fill=text_color,
                    font_family=ctx.theme.font_family,
                    font_size=label_font_size,
                    text_anchor="middle",
                )
            )
        dwg.add(
            dwg.text(
                f"({symbol})",
                insert=(x, caption_y),
                fill=ctx.theme.muted,
                font_family=ctx.theme.font_family,
                font_size=CAPTION_FONT_SIZE,
                text_anchor="middle",
            )
        )

    # The graffiti tag is a decorative layer on top of the finished network,
    # drawn last so that it sits over every edge, node, and label beneath
    # it. At small render sizes, the letters shrink past legibility, so
    # this is gated behind show_tagline, the same flag small renders already
    # turn off (alongside the title, pseudocode, and author) to keep the
    # poster clean.
    if ctx.show_tagline:
        _draw_graffiti(dwg, clusters)

    if ctx.show_pseudocode and FORMULA_LINES:
        for i, markup in enumerate(FORMULA_LINES):
            y = block_y + i * FORMULA_LINE_HEIGHT
            dwg.add(
                _rich_text(
                    dwg,
                    (MARGIN, y),
                    markup,
                    fill=ctx.theme.muted,
                    font_family=ctx.theme.font_family,
                    font_size=FORMULA_FONT_SIZE,
                )
            )

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="backpropagation",
    title=TITLE,
    tagline=TAGLINE,
    category=AlgorithmCategory.MACHINE_LEARNING,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#F2775A",
    author="Andrei Rukavina",
    date="2026-08-29",
)
