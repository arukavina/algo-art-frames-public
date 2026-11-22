"""Binary search: halve the search space every step.

This draws the elimination process as a funnel of narrowing rows, one per
iteration, connected by a path through each step's midpoint, rather than
showing just the final low/mid/high window. The pseudocode sits inside the
funnel itself (on the left side, in the gap between the 2nd and 3rd row) as
a backdrop card, the same treatment that A* gives its own pseudocode wall.
"""

import re

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import RenderContext, new_canvas

TITLE = "Binary Search"
TAGLINE = "Halve the search space every step."

ARRAY = [4, 9, 15, 23, 31, 42, 55, 68, 77, 89]
TARGET = 42

PSEUDOCODE = [
    "low, high = 0, len(arr) - 1",
    "while low <= high:",
    "    mid = (low + high) // 2",
    "    if arr[mid] == target: return mid",
    "    elif arr[mid] < target: low = mid + 1",
    "    else: high = mid - 1",
]

PSEUDO_FONT_SIZE = 14
PSEUDO_LINE_HEIGHT = 20
CHAR_WIDTH = PSEUDO_FONT_SIZE * 0.6  # approximate width of one monospace glyph
BACKDROP_PADDING = 12
GLOW_LAYERS = 5
GLOW_MAX_SPREAD = 22
GLOW_MAX_OPACITY = 0.16

HALF_TICK_EXTENSION = 16  # how far the half-tick pokes past the row's own top/bottom edge
HALF_LABEL_GAP = 8  # clearance between the end of the tick and its "half" label

RIGHT_COLOR = "#5EC8F8"  # cool hue for "arr[mid] < target: low = mid + 1" (the search moves right)
# ctx.theme.accent is the warm counterpart, used for "high = mid - 1" (the search moves left).
# It is the same two-hue language A* uses for its start/goal, reused here so the connecting
# line's color narrates which branch actually fired, and the mid badges warm up from
# RIGHT_COLOR toward the theme accent as the steps progress, giving the funnel a visible sense
# of motion toward the answer.

# This is a lightweight, rule-based syntax highlighter, the same approach as
# A*'s in-chart pseudocode card: it is not real Python, so a proper lexer
# would misfire on it.
_TOKEN_RE = re.compile(r"(\s+)|([A-Za-z_][A-Za-z0-9_]*)|(\d+)|([^\sA-Za-z0-9_])")
_KEYWORDS = {"while", "if", "elif", "else", "return"}
_SYNTAX_COLORS = {
    "dark": {"keyword": "#F97583", "call": "#79B8FF", "number": "#FFAB70", "punct": "#8B949E", "default": "#C9D1D9"},
    "light": {"keyword": "#D73A49", "call": "#005CC5", "number": "#B35900", "punct": "#6A737D", "default": "#24292E"},
}


def _tokenize_line(line: str, palette: dict[str, str]) -> list[tuple[str, str]]:
    """Split a pseudocode line into (text, color) runs."""
    runs: list[tuple[str, str]] = []
    for match in _TOKEN_RE.finditer(line):
        space, word, number, punct = match.groups()
        if space is not None:
            runs.append((space, palette["default"]))
        elif word is not None:
            if word in _KEYWORDS:
                color = palette["keyword"]
            elif line[match.end() : match.end() + 1] == "(":
                color = palette["call"]
            else:
                color = palette["default"]
            runs.append((word, color))
        elif number is not None:
            runs.append((number, palette["number"]))
        else:
            runs.append((punct, palette["punct"]))
    return runs


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
    """Dark or light ink, whichever actually reads against `fill`. The badge
    fill swings from a light cool blue, through a muddy midtone, to a
    mid-bright orange, so a single fixed text color (always
    ctx.theme.background, say) would read fine in dark mode but wash out in
    light mode, where the canvas background is itself near-white and close
    in luminance to these fills."""
    r, g, b = _hex_to_rgb(fill)
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#0b0e14" if luminance > 140 else "#f7f7f5"


def _half_boundary_x(box_x: float, box_w: float, gap: float, mid: int) -> float:
    """X position of the boundary right after `mid`, which is to say exactly
    where `mid = (low + high) // 2` (see PSEUDOCODE) splits the step's
    active range. This is the discrete floor-division midpoint, and it
    always lands in the gap between the mid cell and the next one, never on
    top of a digit, and never wobbling toward the mid cell's own center for
    odd-sized ranges."""
    return box_x + (mid + 1) * (box_w + gap) - gap / 2


def _iterations(arr: list[int], target: int) -> list[tuple[int, int, int, str]]:
    """Run binary search and return the (low, mid, high, direction) window at
    every step, not just the last one. This is drawn as a funnel of
    narrowing rows so the diagram shows the whole elimination process, not
    only its final result. `direction` is whichever pseudocode branch
    actually fired: "right" for "low = mid + 1", "left" for
    "high = mid - 1", and "found" for the terminal step."""
    steps: list[tuple[int, int, int, str]] = []
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            steps.append((low, mid, high, "found"))
            break
        if arr[mid] < target:
            steps.append((low, mid, high, "right"))
            low = mid + 1
        else:
            steps.append((low, mid, high, "left"))
            high = mid - 1
    return steps


def draw(ctx: RenderContext) -> str:
    # The pseudocode is drawn manually below, as a card inside the funnel,
    # instead of relying on new_canvas's usual bottom-of-poster block.
    dwg, box = new_canvas(
        ctx,
        title=TITLE,
        tagline=TAGLINE,
        pseudocode=[],
    )

    steps = _iterations(ARRAY, TARGET)
    n = len(ARRAY)
    gap = 8
    box_w = (box.width - gap * (n - 1)) / n
    row_h = min(box_w, box.height / (len(steps) + 0.5) * 0.6)
    row_gap = (box.height - row_h * len(steps)) / (len(steps) + 1)

    def row_y(step_i: int) -> float:
        return box.y + row_gap * (step_i + 1) + row_h * step_i

    # Pass 1: draw every cell's border, plus the number for the non-mid
    # cells, plus a per-step "half" tick marking the midpoint of that
    # particular step's active range (carried over from the previous
    # version, now repeated per row instead of appearing just once for the
    # original list). The mid cell's own number is deferred to pass 3, so
    # that it can be drawn, with an opaque backdrop, on top of the
    # connecting line, instead of having the line cut straight through the
    # digit.
    mid_entries: list[tuple[float, float, int, str, bool]] = []
    mid_tops: list[tuple[float, float]] = []
    mid_bottoms: list[tuple[float, float]] = []
    mid_directions: list[str] = []
    for step_i, (low, mid, high, direction) in enumerate(steps):
        y = row_y(step_i)
        is_last = step_i == len(steps) - 1
        # This warms from RIGHT_COLOR toward the theme accent as the steps
        # progress, so the funnel reads as actually moving toward the
        # answer, not just narrowing in place.
        progress_t = step_i / (len(steps) - 1) if len(steps) > 1 else 1.0
        mid_color = _lerp_color(RIGHT_COLOR, ctx.theme.accent, progress_t)

        half_x = _half_boundary_x(box.x, box_w, gap, mid)
        tick_top, tick_bottom = y - HALF_TICK_EXTENSION, y + row_h + HALF_TICK_EXTENSION
        dwg.add(
            dwg.line(
                start=(half_x, tick_top),
                end=(half_x, tick_bottom),
                stroke=ctx.theme.muted,
                stroke_width=1.5,
                stroke_dasharray="4,4",
                opacity=0.4,
            )
        )
        # This is labeled on every step, not just the first one. Placing the
        # label above the tick reads fine for rows 1-2, but the last row's
        # gap above is occupied by the pseudocode card, so its label goes
        # below the row instead, to stay clear of it.
        if is_last:
            label_y = tick_bottom + HALF_LABEL_GAP + 8
        else:
            label_y = tick_top - HALF_LABEL_GAP
        dwg.add(
            dwg.text(
                "half",
                insert=(half_x, label_y),
                fill=ctx.theme.muted,
                font_family=ctx.theme.font_family,
                font_size=11,
                text_anchor="middle",
            )
        )

        for i, value in enumerate(ARRAY):
            x = box.x + i * (box_w + gap)
            in_range = low <= i <= high
            is_mid = i == mid
            color = mid_color if is_mid else (ctx.theme.foreground if in_range else ctx.theme.muted)

            dwg.add(
                dwg.rect(
                    insert=(x, y),
                    size=(box_w, row_h),
                    rx=6,
                    fill="none",
                    stroke=color,
                    stroke_width=2 if is_mid else 1.5,
                    opacity=1 if in_range else 0.3,
                )
            )

            if is_mid:
                # This is anchored to the cell's top/bottom edge, not its
                # center, so that the connecting line (pass 2) never dips
                # inside the cell's own square, only ever crossing the empty
                # gap between rows.
                mid_tops.append((x + box_w / 2, y))
                mid_bottoms.append((x + box_w / 2, y + row_h))
                mid_entries.append((x, y, value, color, is_last))
                mid_directions.append(direction)
            else:
                dwg.add(
                    dwg.text(
                        str(value),
                        insert=(x + box_w / 2, y + row_h / 2 + 5),
                        fill=color,
                        font_family=ctx.theme.font_family,
                        font_size=14,
                        text_anchor="middle",
                        opacity=1 if in_range else 0.3,
                    )
                )

    # Pass 2: the connecting line through each step's mid, drawn before the
    # mid badges so that those badges (and the numbers on them) sit on top
    # of it. It runs from one row's bottom edge to the next row's top edge,
    # so it only ever crosses the empty gap between rows, never a cell's own
    # square. It is colored by whichever branch produced it, RIGHT_COLOR for
    # "low = mid + 1" and the theme accent for "high = mid - 1", so the line
    # itself narrates which pseudocode branch fired, not just the funnel's shape.
    for (start, end), direction in zip(zip(mid_bottoms, mid_tops[1:]), mid_directions):
        line_color = RIGHT_COLOR if direction == "right" else ctx.theme.accent
        dwg.add(
            dwg.line(
                start=start,
                end=end,
                stroke=line_color,
                stroke_width=1.5,
                opacity=0.5,
            )
        )

    # Pass 3: the mid-cell badges, a solid chip filled with the badge's own
    # (direction/progress) color, inset within the cell's still-visible
    # outline so that it reads as a filled disc floating inside a thin ring,
    # rather than just a bordered box. It is drawn opaque, so the line from
    # pass 2 disappears behind it instead of crossing through the digit. The
    # digit itself is "punched through" in the canvas background color,
    # since drawing it again in `color` would simply wash out against a
    # same-colored fill.
    for x, y, value, color, is_last in mid_entries:
        dwg.add(
            dwg.rect(
                insert=(x + 4, y + 4),
                size=(box_w - 8, row_h - 8),
                rx=4,
                fill=color,
                opacity=1,
            )
        )
        dwg.add(
            dwg.text(
                str(value),
                insert=(x + box_w / 2, y + row_h / 2 + 5),
                fill=_contrast_text_color(color),
                font_family=ctx.theme.font_family,
                font_size=14,
                font_weight="bold",
                text_anchor="middle",
            )
        )
        if is_last:
            dwg.add(
                dwg.text(
                    "found",
                    insert=(x + box_w / 2, y + row_h + 18),
                    fill=color,
                    font_family=ctx.theme.font_family,
                    font_size=11,
                    text_anchor="middle",
                )
            )

    # This is the pseudocode card, left-aligned and centered in the gap
    # between the 2nd and 3rd row, drawn last so that it sits on top of the
    # funnel beneath it.
    if ctx.show_pseudocode and len(steps) >= 3:
        block_width = 0.0
        for line in PSEUDOCODE:
            stripped = line.lstrip(" ")
            indent = len(line) - len(stripped)
            block_width = max(block_width, indent * CHAR_WIDTH + len(stripped) * CHAR_WIDTH)
        block_height = len(PSEUDOCODE) * PSEUDO_LINE_HEIGHT

        gap_top = row_y(1) + row_h
        gap_bottom = row_y(2)
        # This is pulled in by the card's own backdrop padding plus its glow
        # spread, so that the glow's outer edge lines up with box.x, the
        # same left padding the row list already uses, instead of bleeding
        # past it into the accent frame.
        block_x = box.x + BACKDROP_PADDING + GLOW_MAX_SPREAD
        block_y = gap_top + (gap_bottom - gap_top - block_height) / 2

        card_x, card_y = block_x - BACKDROP_PADDING, block_y - BACKDROP_PADDING
        card_width = block_width + 2 * BACKDROP_PADDING
        card_height = block_height + 2 * BACKDROP_PADDING

        for i in range(GLOW_LAYERS, 0, -1):
            spread = GLOW_MAX_SPREAD * i / GLOW_LAYERS
            dwg.add(
                dwg.rect(
                    insert=(card_x - spread, card_y - spread),
                    size=(card_width + 2 * spread, card_height + 2 * spread),
                    fill=ctx.theme.accent,
                    opacity=GLOW_MAX_OPACITY * (1 - (i - 1) / GLOW_LAYERS),
                    rx=8 + spread * 0.4,
                )
            )

        dwg.add(
            dwg.rect(
                insert=(card_x, card_y),
                size=(card_width, card_height),
                fill=ctx.theme.background,
                opacity=0.92,
                rx=8,
            )
        )

        palette = _SYNTAX_COLORS[ctx.theme.name]
        for i, line in enumerate(PSEUDOCODE):
            stripped = line.lstrip(" ")
            indent = len(line) - len(stripped)
            text_el = dwg.text(
                "",
                insert=(block_x + indent * CHAR_WIDTH, block_y + PSEUDO_FONT_SIZE + i * PSEUDO_LINE_HEIGHT),
                font_family=ctx.theme.font_family,
                font_size=PSEUDO_FONT_SIZE,
            )
            for token_text, color in _tokenize_line(stripped, palette):
                text_el.add(dwg.tspan(token_text, fill=color))
            dwg.add(text_el)

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="binary-search",
    title=TITLE,
    tagline=TAGLINE,
    category=AlgorithmCategory.SEARCH,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#FF8A3D",
    author="Andrei Rukavina",
    date="2026-08-29",
)
