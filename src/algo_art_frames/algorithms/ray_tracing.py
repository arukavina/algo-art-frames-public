"""Ray tracing: cast one ray per pixel, bounce it off whatever surface is
nearest, and shade the point where it finally lands."""

import math
import re
from dataclasses import dataclass

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import (
    MARGIN,
    PSEUDOCODE_INDENT_PX,
    PSEUDOCODE_LINE_HEIGHT,
    PSEUDOCODE_SIZE,
    ContentBox,
    RenderContext,
    new_canvas,
)
from algo_art_frames.render.syntax import SYNTAX_COLORS, tokenize_line

PSEUDOCODE = [
    "set camera and viewport as desired",
    "for each pixel in viewport:",
    "    find which square on the viewport corresponds to this pixel",
    "    find the color seen through that square",
    "    paint the pixel with that color",
]

COLD_COLOR = "#5EC8F8"
BALL_COLOR = "#FFD700"
FLAG_WHITE = "#FFFFFF"
FLAG_BLUE = "#74ACDF"
FACE_COLOR = "#843511"

CAMERA_RAY_COUNT = 44
FACE_YAW = math.radians(25)

# Facial-feature path data (right half only) and the pupil, lifted from the
# public-domain Sol de Mayo reference artwork:
# https://commons.wikimedia.org/wiki/File:Sol_de_Mayo-Bandera_de_Argentina.svg
# The left half is the same geometry mirrored across x=0, matching how the
# source file itself builds it via a single <use transform="scale(-1,1)">.
FACE_PATHS = {
    "eyebrow_nose": (
        "M 41,-14 C 29.5,-24 15,-25.5 7,-18 A 140,50 10 0,0 8.5,8.5 "
        "C 8,8.5 7,9 6.5,9.5 A 80,50 10 0,1 4,-19 C 15,-28 30,-29 41,-14"
    ),
    "uppalpebra": (
        "M 23,-17 C 16.5,-17 15,-15.5 12,-13 S 7.5,-11 7,-10.5 S 7,-8.5 8,-9 "
        "S 11,-10.5 14,-13 S 20,-15.5 23,-15.5 C 32,-15.5 37,-8 38,-8.5 S 33,-17 23,-17"
    ),
    "upeyecontour": "M 34.5,-8.5 C 28,-15.5 16,-16 11,-8 H 13 C 18,-16 30,-12.5 31,-9 v 1",
    "loweyecontour": "M 11,-8 C 16,-3.5 27,-3 34.5,-8.5 L 31,-9 C 26,-3.5 18,-4 13,-8 v -1",
    "lowpalpebra": "M 35,-6 C 26.5,0.5 18,0 13,-3 S 8,-7 9,-7 S 11,-6 15,-4 S 25,-2 35,-6",
    "nose": (
        "M 10.5,9 A 3,3 0 1,1 6.5,12 C 6,13 4,16 0,16 h -1 l 1,1.5 "
        "C 1,17.5 4,17.5 6,16 A 4.5,4.5 0 1,0 10.5,9"
    ),
    "uplip1": (
        "M 16.5,30 C 12,27 10,22.5 5,22.5 C 4,22.5 2,23 0,24 h -1 L 0,25.5 "
        "C 2,25.5 5,23 8.5,25 S 14,29 16.5,30"
    ),
    "midlip": "M 15,30 C 5,27 3,29 0,29 h -1 l 1,2 C 4,31 6,28 15,30",
    "uplip2": "M 16.5,30 C 5.5,29 9,35.5 0,35.5 h -1 L 0,37 C 11,37 6,31 16.5,30",
    "chin": "M 9,46 a 9,9 0 0,0 -18,0 a 9.25,9.25 0 0,1 18,0",
}
PUPIL = (22.0, -9.0, 4.5)
FACE_SOURCE_RADIUS = 65.0


# --- Small geometry helpers --------------------------------------------------


def _lerp_hex(color_a: str, color_b: str, t: float) -> str:
    """Linearly interpolate between two hex colors."""
    a = tuple(int(color_a[i : i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(color_b[i : i + 2], 16) for i in (1, 3, 5))
    mixed = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return "#{:02x}{:02x}{:02x}".format(*mixed)


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _direction(origin, target):
    """Unit vector pointing from origin to target."""
    dx, dy = _sub(target, origin)
    length = math.hypot(dx, dy)
    return (dx / length, dy / length)


def _clip_to_box(origin, direction, box: ContentBox):
    """t at which the ray first leaves the content box, checking whichever
    edge (right, top, or bottom) it reaches first."""
    t = (box.x + box.width - origin[0]) / direction[0]
    if direction[1] > 0:
        t = min(t, (box.y + box.height - origin[1]) / direction[1])
    elif direction[1] < 0:
        t = min(t, (box.y - origin[1]) / direction[1])
    return t


def _ray_sphere_t(origin, direction, center, radius):
    """Nearest positive t where origin + t*direction hits the sphere, or None
    if the ray (direction must be a unit vector) misses it entirely."""
    ocx, ocy = _sub(origin, center)
    b = 2 * (ocx * direction[0] + ocy * direction[1])
    c = ocx * ocx + ocy * ocy - radius * radius
    disc = b * b - 4 * c
    if disc < 0:
        return None
    t = (-b - math.sqrt(disc)) / 2
    return t if t > 0 else None


def _ray_rect_t(origin, direction, x0, x1, y0, y1):
    """Nearest positive t where origin + t*direction enters the axis-aligned
    box [x0, x1] x [y0, y1], or None if it never does (the standard slab
    method for ray/AABB intersection)."""
    if direction[0] == 0:
        if not x0 <= origin[0] <= x1:
            return None
        tx0, tx1 = -math.inf, math.inf
    else:
        tx0, tx1 = (x0 - origin[0]) / direction[0], (x1 - origin[0]) / direction[0]
        if tx0 > tx1:
            tx0, tx1 = tx1, tx0
    if direction[1] == 0:
        if not y0 <= origin[1] <= y1:
            return None
        ty0, ty1 = -math.inf, math.inf
    else:
        ty0, ty1 = (y0 - origin[1]) / direction[1], (y1 - origin[1]) / direction[1]
        if ty0 > ty1:
            ty0, ty1 = ty1, ty0

    t_enter, t_exit = max(tx0, ty0), min(tx1, ty1)
    if t_enter > t_exit or t_exit < 0:
        return None
    return t_enter if t_enter > 0 else t_exit


# --- SVG path flattening, for the Sol de Mayo face artwork below ------------

_PATH_TOKEN_RE = re.compile(r"[MLHVCSAZmlhvcsaz]|-?\d*\.?\d+(?:[eE]-?\d+)?")


def _flatten_cubic(p0, p1, p2, p3, samples):
    """Sample a cubic bezier at `samples` evenly spaced steps, excluding p0."""
    points = []
    for k in range(1, samples + 1):
        t = k / samples
        mt = 1 - t
        x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
        points.append((x, y))
    return points


def _flatten_arc(p0, rx, ry, phi_deg, large_arc, sweep, p1, samples):
    """Sample an SVG elliptical arc, using the endpoint-to-center
    parameterization from the SVG spec, excluding p0."""
    if rx == 0 or ry == 0 or p0 == p1:
        return [p1]
    phi = math.radians(phi_deg)
    cos_phi, sin_phi = math.cos(phi), math.sin(phi)
    dx2, dy2 = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
    x1p = cos_phi * dx2 + sin_phi * dy2
    y1p = -sin_phi * dx2 + cos_phi * dy2

    rx, ry = abs(rx), abs(ry)
    lam = (x1p**2) / (rx**2) + (y1p**2) / (ry**2)
    if lam > 1:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s

    sign = -1 if large_arc == sweep else 1
    num = rx**2 * ry**2 - rx**2 * y1p**2 - ry**2 * x1p**2
    den = rx**2 * y1p**2 + ry**2 * x1p**2
    co = sign * math.sqrt(max(num, 0) / den) if den else 0
    cxp, cyp = co * (rx * y1p / ry), co * (-ry * x1p / rx)
    cx = cos_phi * cxp - sin_phi * cyp + (p0[0] + p1[0]) / 2
    cy = sin_phi * cxp + cos_phi * cyp + (p0[1] + p1[1]) / 2

    def angle(ux, uy, vx, vy):
        dot = ux * vx + uy * vy
        length = math.hypot(ux, uy) * math.hypot(vx, vy)
        ang = math.acos(max(-1, min(1, dot / length)))
        return ang if (ux * vy - uy * vx) >= 0 else -ang

    theta1 = angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dtheta = angle((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if sweep == 0 and dtheta > 0:
        dtheta -= 2 * math.pi
    elif sweep == 1 and dtheta < 0:
        dtheta += 2 * math.pi

    points = []
    for k in range(1, samples + 1):
        t = theta1 + dtheta * k / samples
        x = cx + rx * math.cos(t) * cos_phi - ry * math.sin(t) * sin_phi
        y = cy + rx * math.cos(t) * sin_phi + ry * math.sin(t) * cos_phi
        points.append((x, y))
    return points


def _parse_path(d, samples=14):
    """Flatten an SVG path's 'd' data (M/L/H/V/C/S/A, upper or lowercase)
    into a single polyline of (x, y) points. Sufficient for simple
    single-subpath outlines like the face features below; not a general
    SVG path parser (no separate subpaths, no Q/T commands)."""
    tokens = _PATH_TOKEN_RE.findall(d)
    points = []
    i = 0
    cur = (0.0, 0.0)
    start = (0.0, 0.0)
    prev_ctrl = None
    cmd = None

    def nums(count):
        nonlocal i
        values = [float(tokens[i + k]) for k in range(count)]
        i += count
        return values

    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1

        if cmd in ("M", "m"):
            x, y = nums(2)
            if cmd == "m" and points:
                x, y = cur[0] + x, cur[1] + y
            cur = start = (x, y)
            points.append(cur)
            prev_ctrl = None
            cmd = "L" if cmd == "M" else "l"
        elif cmd in ("L", "l"):
            x, y = nums(2)
            if cmd == "l":
                x, y = cur[0] + x, cur[1] + y
            cur = (x, y)
            points.append(cur)
            prev_ctrl = None
        elif cmd in ("H", "h"):
            (x,) = nums(1)
            cur = (x if cmd == "H" else cur[0] + x, cur[1])
            points.append(cur)
            prev_ctrl = None
        elif cmd in ("V", "v"):
            (y,) = nums(1)
            cur = (cur[0], y if cmd == "V" else cur[1] + y)
            points.append(cur)
            prev_ctrl = None
        elif cmd in ("C", "c"):
            x1, y1, x2, y2, x, y = nums(6)
            if cmd == "c":
                x1, y1, x2, y2, x, y = (
                    cur[0] + x1,
                    cur[1] + y1,
                    cur[0] + x2,
                    cur[1] + y2,
                    cur[0] + x,
                    cur[1] + y,
                )
            points.extend(_flatten_cubic(cur, (x1, y1), (x2, y2), (x, y), samples))
            prev_ctrl, cur = (x2, y2), (x, y)
        elif cmd in ("S", "s"):
            x2, y2, x, y = nums(4)
            if cmd == "s":
                x2, y2, x, y = cur[0] + x2, cur[1] + y2, cur[0] + x, cur[1] + y
            if prev_ctrl is not None:
                x1, y1 = 2 * cur[0] - prev_ctrl[0], 2 * cur[1] - prev_ctrl[1]
            else:
                x1, y1 = cur
            points.extend(_flatten_cubic(cur, (x1, y1), (x2, y2), (x, y), samples))
            prev_ctrl, cur = (x2, y2), (x, y)
        elif cmd in ("A", "a"):
            rx, ry, rot, large, sweep, x, y = nums(7)
            if cmd == "a":
                x, y = cur[0] + x, cur[1] + y
            points.extend(_flatten_arc(cur, rx, ry, rot, large, sweep, (x, y), samples))
            cur, prev_ctrl = (x, y), None
        elif cmd in ("Z", "z"):
            cur = start
            points.append(cur)
        else:
            raise ValueError(f"unsupported path command {cmd!r}")

    return points


# --- Sol de Mayo: spherical projection --------------------------------------

_FACE_FEATURES = {name: _parse_path(d) for name, d in FACE_PATHS.items()}
_PUPIL_OUTLINE = [
    (PUPIL[0] + PUPIL[2] * math.cos(a), PUPIL[1] + PUPIL[2] * math.sin(a))
    for a in (k * 2 * math.pi / 20 for k in range(20))
]


def _sphere_project(x, y, radius, yaw):
    """Project a point from the sun's own flat reference disc onto a sphere
    of the given radius, yawed (turned left/right) by `yaw` radians, viewed
    orthographically. Returns None if the yaw has rotated that point onto
    the far side of the sphere, hidden from view."""
    nx, ny = x / radius, y / radius
    r2 = nx * nx + ny * ny
    if r2 > 1:
        return None
    nz = math.sqrt(1 - r2)
    rx = nx * math.cos(yaw) + nz * math.sin(yaw)
    rz = -nx * math.sin(yaw) + nz * math.cos(yaw)
    if rz < 0:
        return None
    return (rx * radius, y)


def _face_overlay(dwg, center, radius, yaw, color):
    """Sol de Mayo face, warped onto a sphere of `radius` centered at
    `center` and turned by `yaw`, scaled from the reference artwork's own
    65-unit face radius. Returns a list of elements to add to the drawing;
    a feature is skipped entirely if the yaw has turned any part of it out
    of view rather than rendering a partial, broken outline."""
    scale = radius / FACE_SOURCE_RADIUS
    elements = []

    def project_shape(points, mirror):
        projected = []
        for x, y in points:
            sx = -x if mirror else x
            hit = _sphere_project(sx, y, FACE_SOURCE_RADIUS, yaw)
            if hit is None:
                return None
            projected.append((center[0] + hit[0] * scale, center[1] + hit[1] * scale))
        return projected

    for points in _FACE_FEATURES.values():
        for mirror in (False, True):
            screen_points = project_shape(points, mirror)
            if screen_points is not None:
                elements.append(dwg.polygon(points=screen_points, fill=color))

    for mirror in (False, True):
        screen_points = project_shape(_PUPIL_OUTLINE, mirror)
        if screen_points is not None:
            elements.append(dwg.polygon(points=screen_points, fill=color))

    return elements


# --- Poster layout -----------------------------------------------------------


@dataclass
class Layout:
    box: ContentBox
    camera: tuple[float, float]
    viewport_x: float
    viewport_half_h: float
    viewport_w: float
    pixel_h: float
    sphere_center: tuple[float, float]
    sphere_r: float
    flag_rects: list[tuple[float, float, float, float, str]]


def _flag_rects(sphere_center, sphere_r, camera, flag_w):
    """The Argentine flag totem flanking the ball: a white band flush
    against it on each side, then a blue band twice as tall further out,
    mirrored across the camera's x-axis. The bands are thin (about as wide
    as the viewport) rather than as wide as the ball, with the top pair
    hugging the ball's near (left) edge and the bottom pair its far (right)
    edge, so the two halves read as offset rather than one plain column.
    Each also falls short of the ray fan's full spread, so the widest-angle
    rays clear over and under them.

    The top pair sits closer to the camera than the bottom pair, and how
    far a ray strays from the axis grows in direct proportion to distance
    traveled -- left alone, the nearer top pair would read larger in the
    viewport for the same physical height, so it's scaled down by the ratio
    of the two pairs' depths.
    """
    top_x0, top_x1 = sphere_center[0] - sphere_r, sphere_center[0] - sphere_r + flag_w
    bottom_x0, bottom_x1 = sphere_center[0] + sphere_r - flag_w, sphere_center[0] + sphere_r

    white_h = sphere_r * 0.8
    blue_h = white_h * 2
    depth_scale = (top_x0 - camera[0]) / (bottom_x0 - camera[0])
    top_white_h = white_h * depth_scale
    top_blue_h = blue_h * depth_scale

    top_y = sphere_center[1] - sphere_r
    bottom_y = sphere_center[1] + sphere_r

    return [
        (top_x0, top_x1, top_y - top_white_h - top_blue_h, top_y - top_white_h, FLAG_BLUE),
        (top_x0, top_x1, top_y - top_white_h, top_y, FLAG_WHITE),
        (bottom_x0, bottom_x1, bottom_y, bottom_y + white_h, FLAG_WHITE),
        (bottom_x0, bottom_x1, bottom_y + white_h, bottom_y + white_h + blue_h, FLAG_BLUE),
    ]


def _compute_layout(box: ContentBox) -> Layout:
    camera = (box.x + box.width * 0.07, box.y + box.height * 0.5)
    viewport_x = box.x + box.width * 0.30
    viewport_half_h = box.height * 0.20
    viewport_w = 10
    sphere_center = (box.x + box.width * 0.66, camera[1])
    sphere_r = box.width * 0.03
    pixel_h = (viewport_half_h * 2) / (CAMERA_RAY_COUNT - 1)

    return Layout(
        box=box,
        camera=camera,
        viewport_x=viewport_x,
        viewport_half_h=viewport_half_h,
        viewport_w=viewport_w,
        pixel_h=pixel_h,
        sphere_center=sphere_center,
        sphere_r=sphere_r,
        flag_rects=_flag_rects(sphere_center, sphere_r, camera, viewport_w),
    )


def _closest_hit(origin, direction, layout: Layout):
    """Cast a ray from `origin` and return (t, color) for whichever surface
    -- the ball or one of the flag bands -- it hits nearest, or (None,
    None) if it hits nothing."""
    candidates = []
    sphere_t = _ray_sphere_t(origin, direction, layout.sphere_center, layout.sphere_r)
    if sphere_t is not None:
        candidates.append((sphere_t, BALL_COLOR))
    for x0, x1, y0, y1, color in layout.flag_rects:
        rect_t = _ray_rect_t(origin, direction, x0, x1, y0, y1)
        if rect_t is not None:
            candidates.append((rect_t, color))
    return min(candidates, default=(None, None), key=lambda hit: hit[0])


# --- The highlighted beam and its "Light is geometry" label -----------------

# Which two adjacent rays of the fan get picked out as a single solid beam.
BEAM_RAY_A, BEAM_RAY_B = 9, 10

LIGHT_LABEL = "Light is geometry"
LIGHT_LABEL_CHAR_WIDTH_RATIO = 0.6  # approx. advance width of one glyph, in ems
LIGHT_LABEL_FIT = 0.8  # how much of the available gap each letter's font-size fills
LIGHT_LABEL_EDGE_INSET = 12  # px kept clear between the last letter and the frame edge


@dataclass
class Beam:
    edge_a: tuple[float, float]
    edge_b: tuple[float, float]
    color_a: str
    color_b: str
    direction: tuple[float, float]
    angle_deg: float
    frame_anchor: tuple[float, float]


def _beam_geometry(ctx: RenderContext, layout: Layout) -> Beam:
    """Where rays 9 and 10 land, their two colors, and where the beam
    between them exits the frame -- everything the wedge fill and the
    "Light is geometry" label both need."""
    camera = layout.camera
    t_a = BEAM_RAY_A / (CAMERA_RAY_COUNT - 1)
    t_b = BEAM_RAY_B / (CAMERA_RAY_COUNT - 1)
    y_a = camera[1] - layout.viewport_half_h + layout.viewport_half_h * 2 * t_a
    y_b = camera[1] - layout.viewport_half_h + layout.viewport_half_h * 2 * t_b
    dir_a = _direction(camera, (layout.viewport_x, y_a))
    dir_b = _direction(camera, (layout.viewport_x, y_b))

    edge_a_t = _clip_to_box(camera, dir_a, layout.box)
    edge_b_t = _clip_to_box(camera, dir_b, layout.box)
    edge_a = (camera[0] + dir_a[0] * edge_a_t, camera[1] + dir_a[1] * edge_a_t)
    edge_b = (camera[0] + dir_b[0] * edge_b_t, camera[1] + dir_b[1] * edge_b_t)

    sum_x, sum_y = dir_a[0] + dir_b[0], dir_a[1] + dir_b[1]
    sum_len = math.hypot(sum_x, sum_y)
    direction = (sum_x / sum_len, sum_y / sum_len)

    return Beam(
        edge_a=edge_a,
        edge_b=edge_b,
        color_a=_lerp_hex(COLD_COLOR, ctx.theme.accent, t_a),
        color_b=_lerp_hex(COLD_COLOR, ctx.theme.accent, t_b),
        direction=direction,
        angle_deg=math.degrees(math.atan2(direction[1], direction[0])),
        frame_anchor=((edge_a[0] + edge_b[0]) / 2, (edge_a[1] + edge_b[1]) / 2),
    )


def _draw_beam_wedge(dwg, layout: Layout, beam: Beam):
    """Fill the wedge between the two highlighted rays with a gradient
    between their own colors, painting that one beam in solid."""
    gradient = dwg.linearGradient(
        start=beam.edge_a, end=beam.edge_b, gradientUnits="userSpaceOnUse"
    )
    gradient.add_stop_color(offset=0, color=beam.color_a)
    gradient.add_stop_color(offset=1, color=beam.color_b)
    dwg.defs.add(gradient)
    dwg.add(
        dwg.polygon(
            points=[layout.camera, beam.edge_a, beam.edge_b], fill=gradient.get_paint_server()
        )
    )


def _draw_light_label(dwg, ctx: RenderContext, layout: Layout, beam: Beam):
    """Letter the beam with "Light is geometry", one size per letter. The
    gap between ray 9 and ray 10 widens in direct proportion to distance
    from the camera, so sizing each letter to a fixed fraction of that gap
    turns the whole progression into a geometric sequence -- solved here in
    closed form so the last letter lands exactly at the beam's edge."""
    camera = layout.camera
    letter_count = len(LIGHT_LABEL)
    beam_len = math.hypot(*_sub(beam.frame_anchor, camera)) - LIGHT_LABEL_EDGE_INSET
    edge_width = math.hypot(*_sub(beam.edge_a, beam.edge_b))
    width_per_r = edge_width / beam_len

    growth = 1 + LIGHT_LABEL_FIT * width_per_r * LIGHT_LABEL_CHAR_WIDTH_RATIO
    start_r = beam_len / growth**letter_count
    sizes = [LIGHT_LABEL_FIT * width_per_r * start_r * growth**i for i in range(letter_count)]

    start_x = camera[0] + beam.direction[0] * start_r
    start_y = camera[1] + beam.direction[1] * start_r + 7
    text = dwg.text(
        "",
        insert=(start_x, start_y),
        font_family=ctx.theme.font_family,
        fill=ctx.theme.accent,
        transform=f"rotate({beam.angle_deg:.2f}, {start_x:.2f}, {start_y:.2f})",
    )
    # No manual dx: sibling tspans without their own x/y already flow one
    # after another using each glyph's own rendered width, so adding an
    # estimated dx on top of that would double-count each letter's advance.
    for letter, size in zip(LIGHT_LABEL, sizes):
        text.add(dwg.tspan(letter, font_size=size))
    dwg.add(text)


# --- Drawing ------------------------------------------------------------------


def _draw_viewport_frame(dwg, ctx: RenderContext, layout: Layout):
    top = layout.camera[1] - layout.viewport_half_h - layout.pixel_h / 2
    dwg.add(
        dwg.rect(
            insert=(layout.viewport_x - layout.viewport_w / 2, top),
            size=(layout.viewport_w, layout.viewport_half_h * 2 + layout.pixel_h),
            fill="none",
            stroke=ctx.theme.muted,
            stroke_width=1.5,
        )
    )


def _draw_z_axis(dwg, ctx: RenderContext, layout: Layout):
    """A dashed reference line along the camera's optical (z) axis, with an
    arrowhead and label at the far end."""
    camera = layout.camera
    end_x = layout.box.x + layout.box.width - 14
    dwg.add(
        dwg.line(
            start=camera,
            end=(end_x, camera[1]),
            stroke=ctx.theme.muted,
            stroke_width=1,
            stroke_dasharray="4,3",
        )
    )
    dwg.add(
        dwg.polygon(
            points=[(end_x, camera[1] - 4), (end_x, camera[1] + 4), (end_x + 8, camera[1])],
            fill=ctx.theme.muted,
        )
    )
    dwg.add(
        dwg.text(
            "z",
            insert=(end_x + 12, camera[1] + 4),
            fill=ctx.theme.muted,
            font_family=ctx.theme.font_family,
            font_size=12,
            font_style="italic",
        )
    )


def _draw_camera_rays(dwg, ctx: RenderContext, layout: Layout):
    """The fan of camera rays: paint each one's viewport pixel with
    whatever it hits, then draw the ray itself out to that hit (or, on a
    miss, out to the edge of the frame)."""
    camera = layout.camera
    for i in range(CAMERA_RAY_COUNT):
        t = i / (CAMERA_RAY_COUNT - 1)
        target_y = camera[1] - layout.viewport_half_h + layout.viewport_half_h * 2 * t
        direction = _direction(camera, (layout.viewport_x, target_y))
        color = _lerp_hex(COLD_COLOR, ctx.theme.accent, t)

        hit_t, hit_color = _closest_hit(camera, direction, layout)
        pixel_color = hit_color if hit_t is not None else ctx.theme.background
        dwg.add(
            dwg.rect(
                insert=(layout.viewport_x - layout.viewport_w / 2, target_y - layout.pixel_h / 2),
                size=(layout.viewport_w, layout.pixel_h),
                fill=pixel_color,
                stroke=ctx.theme.muted,
                stroke_width=0.4,
            )
        )

        if hit_t is not None:
            end = (camera[0] + direction[0] * hit_t, camera[1] + direction[1] * hit_t)
        else:
            edge_t = _clip_to_box(camera, direction, layout.box)
            end = (camera[0] + direction[0] * edge_t, camera[1] + direction[1] * edge_t)

        dwg.add(dwg.line(start=camera, end=end, stroke=color, stroke_width=1.25))
        if hit_t is not None:
            dwg.add(dwg.circle(center=end, r=2.5, fill=color))


def _draw_camera_icon(dwg, ctx: RenderContext, layout: Layout):
    cx, cy = layout.camera
    dwg.add(
        dwg.polygon(
            points=[(cx - 7, cy - 6), (cx - 7, cy + 6), (cx + 4, cy)], fill=ctx.theme.foreground
        )
    )


def _draw_flag_bands(dwg, layout: Layout):
    for x0, x1, y0, y1, color in layout.flag_rects:
        dwg.add(dwg.rect(insert=(x0, y0), size=(x1 - x0, y1 - y0), fill=color))


def _draw_sun(dwg, layout: Layout):
    dwg.add(dwg.circle(center=layout.sphere_center, r=layout.sphere_r, fill=BALL_COLOR))
    for element in _face_overlay(dwg, layout.sphere_center, layout.sphere_r, FACE_YAW, FACE_COLOR):
        dwg.add(element)


def _draw_labels(dwg, ctx: RenderContext, layout: Layout):
    camera = layout.camera
    dwg.add(
        dwg.text(
            "camera",
            insert=(camera[0] - 14, camera[1] + 4),
            fill=ctx.theme.muted,
            font_family=ctx.theme.font_family,
            font_size=11,
            text_anchor="end",
        )
    )
    dwg.add(
        dwg.text(
            "viewport",
            insert=(
                layout.viewport_x - 24,
                camera[1] - layout.viewport_half_h - layout.pixel_h / 2 - 16,
            ),
            fill=ctx.theme.muted,
            font_family=ctx.theme.font_family,
            font_size=11,
        )
    )


def _draw_pseudocode(dwg, ctx: RenderContext, box: ContentBox):
    """Drawn by hand with syntax highlighting instead of new_canvas's plain
    muted-text block; draw() carves out the same layout space for it."""
    palette = SYNTAX_COLORS[ctx.theme.name]
    block_y = box.y + box.height + MARGIN // 2
    for i, line in enumerate(PSEUDOCODE):
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        text_el = dwg.text(
            "",
            insert=(box.x + indent * PSEUDOCODE_INDENT_PX, block_y + i * PSEUDOCODE_LINE_HEIGHT),
            font_family=ctx.theme.font_family,
            font_size=PSEUDOCODE_SIZE,
        )
        for token_text, color in tokenize_line(stripped, palette):
            text_el.add(dwg.tspan(token_text, fill=color))
        dwg.add(text_el)


def draw(ctx: RenderContext) -> str:
    dwg, full_box = new_canvas(
        ctx, title="Ray Tracing", tagline="Simulate the path of light.", pseudocode=[]
    )
    box = full_box
    if ctx.show_pseudocode:
        block_height = len(PSEUDOCODE) * PSEUDOCODE_LINE_HEIGHT + MARGIN
        box = ContentBox(
            x=full_box.x,
            y=full_box.y,
            width=full_box.width,
            height=max(full_box.height - block_height, 0),
        )

    layout = _compute_layout(box)
    beam = _beam_geometry(ctx, layout)

    _draw_viewport_frame(dwg, ctx, layout)
    _draw_z_axis(dwg, ctx, layout)
    _draw_beam_wedge(dwg, layout, beam)
    _draw_camera_rays(dwg, ctx, layout)
    _draw_camera_icon(dwg, ctx, layout)
    _draw_flag_bands(dwg, layout)
    _draw_sun(dwg, layout)
    _draw_light_label(dwg, ctx, layout, beam)
    _draw_labels(dwg, ctx, layout)
    if ctx.show_pseudocode:
        _draw_pseudocode(dwg, ctx, box)

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="ray-tracing",
    title="Ray Tracing",
    tagline="Simulate the path of light.",
    category=AlgorithmCategory.GRAPHICS,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#F250B6",
    author="Andrei Rukavina",
    date="2026-09-08",
)
