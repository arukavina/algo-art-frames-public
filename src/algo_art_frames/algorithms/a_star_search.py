"""A* search: explore a grid, guided by the cost so far plus a heuristic.

The pseudocode sits right in the middle of the poster and acts as a wall:
A* (the real algorithm below, never a hardcoded route) actually has to
search around it to get from a labeled start (A) to a labeled goal (B), and
a second candidate route that almost won is drawn faintly alongside the
winner. With the pseudocode turned off, there is no wall in the way anymore,
so the route becomes simply the direct staircase.
"""

import heapq

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import ContentBox, RenderContext, new_canvas
from algo_art_frames.render.syntax import SYNTAX_COLORS, tokenize_line

PSEUDOCODE = [
    "f(n) = g(n) + h(n)",
    "g(n) = cost from start",
    "h(n) = heuristic to goal",
    "open = {start}, closed = {}",
    "while open is not empty:",
    "    n = lowest f(n) in open",
    "    if n == goal: return path",
    "    move n from open to closed",
    "    for each neighbor of n:",
    "        update g, h, f; add to open",
]

COLS = 12
ROWS = 8
START = (0, 6)
GOAL = (COLS - 1, 0)

START_COLOR = "#5EC8F8"  # a cool "cost from start" hue, kept distinct from the goal's warm accent
PSEUDO_FONT_SIZE = 16  # bigger than the standard pseudocode block, since this one needs to read as a wall
PSEUDO_LINE_HEIGHT = 24
CHAR_WIDTH = PSEUDO_FONT_SIZE * 0.6  # approximate width of one monospace glyph
BACKDROP_PADDING = 14  # a clean margin between the text and its background card
GLOW_LAYERS = 5  # stacked rects that approximate a soft, blurred shadow
GLOW_MAX_SPREAD = 30  # how many px the outermost glow layer extends past the card
GLOW_MAX_OPACITY = 0.18  # opacity of the innermost glow layer, the one closest to the card

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


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _neighbors(cell: tuple[int, int]):
    c, r = cell
    for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nc, nr = c + dc, r + dr
        if 0 <= nc < COLS and 0 <= nr < ROWS:
            yield (nc, nr)


def _a_star(
    start: tuple[int, int], goal: tuple[int, int], blocked: set[tuple[int, int]]
) -> list[tuple[int, int]] | None:
    """This is the textbook algorithm the poster illustrates, and it is used
    here to genuinely route the drawn path around whatever cells happen to
    be walled off.

    On an open grid, many detours share the same Manhattan length, so the
    heuristic is given a tiny tie-breaking nudge (a standard A* trick)
    toward cells closer to the straight start-to-goal line. Without that
    nudge, ties would resolve arbitrarily, and the "shortest" path would end
    up hugging the grid's edges instead of reading as a deliberate route
    around the wall.
    """
    dx_line, dy_line = start[0] - goal[0], start[1] - goal[1]

    def heuristic(cell: tuple[int, int]) -> float:
        dx, dy = cell[0] - goal[0], cell[1] - goal[1]
        cross = abs(dx * dy_line - dx_line * dy)
        return _manhattan(cell, goal) + cross * 0.001

    frontier: list[tuple[float, int, tuple[int, int]]] = [(heuristic(start), 0, start)]
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    best_g = {start: 0}
    visited: set[tuple[int, int]] = set()

    while frontier:
        _, g, current = heapq.heappop(frontier)
        if current in visited:
            continue
        visited.add(current)
        if current == goal:
            path = [current]
            while path[-1] != start:
                path.append(came_from[path[-1]])
            path.reverse()
            return path
        for neighbor in _neighbors(current):
            if neighbor in blocked:
                continue
            tentative_g = g + 1
            if tentative_g < best_g.get(neighbor, float("inf")):
                best_g[neighbor] = tentative_g
                came_from[neighbor] = current
                heapq.heappush(frontier, (tentative_g + heuristic(neighbor), tentative_g, neighbor))
    return None


def _pseudocode_block(box: ContentBox) -> tuple[float, float, float, float]:
    """Bounding box (x, y, width, height) of the pseudocode text, which is
    centered in the content area."""
    block_width = 0.0
    for line in PSEUDOCODE:
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        block_width = max(block_width, indent * CHAR_WIDTH + len(stripped) * CHAR_WIDTH)
    block_height = len(PSEUDOCODE) * PSEUDO_LINE_HEIGHT
    block_x = box.x + (box.width - block_width) / 2
    block_y = box.y + (box.height - block_height) / 2
    return block_x, block_y, block_width, block_height


def draw(ctx: RenderContext) -> str:
    # The pseudocode is drawn manually below, centered in the grid, instead
    # of relying on new_canvas's usual bottom-of-poster block.
    dwg, box = new_canvas(
        ctx,
        title="A* Search",
        tagline="The best path is found by looking ahead.",
        pseudocode=[],
    )

    # The grid is inset a bit further than the poster's usual margin, since
    # wall circles are wider than the grid pitch, and without this the cells
    # right at the edge (col 0/COLS-1, row 0/ROWS-1) would render half off-canvas.
    outer_spacing_x = box.width / (COLS - 1)
    outer_spacing_y = box.height / (ROWS - 1)
    grid_margin = min(outer_spacing_x, outer_spacing_y) * 0.58 + 6
    grid_box = ContentBox(
        x=box.x + grid_margin,
        y=box.y + grid_margin,
        width=box.width - 2 * grid_margin,
        height=box.height - 2 * grid_margin,
    )

    def grid_x(c: int) -> float:
        return grid_box.x + c * (grid_box.width / (COLS - 1))

    def grid_y(r: int) -> float:
        return grid_box.y + r * (grid_box.height / (ROWS - 1))

    spacing_x = grid_box.width / (COLS - 1)
    spacing_y = grid_box.height / (ROWS - 1)
    wall_r = min(spacing_x, spacing_y) * 0.58  # a touch bigger than the grid pitch, so neighboring circles overlap

    blocked: set[tuple[int, int]] = set()
    block_rect = None
    if ctx.show_pseudocode:
        block_x, block_y, block_width, block_height = _pseudocode_block(box)
        block_rect = (block_x, block_y, block_width, block_height)
        side_pad = max(spacing_x, spacing_y) * 0.7
        # There is more padding below the block than above it: going over the
        # top is a short hop past the wall, while going under means clearing
        # a much wider margin first. It is the same wall, but one detour is
        # deliberately made the losing option.
        left, top = block_x - side_pad, block_y - side_pad
        right, bottom = block_x + block_width + side_pad, block_y + block_height + side_pad * 2.6
        for r in range(ROWS):
            for c in range(COLS):
                x, y = grid_x(c), grid_y(r)
                if left <= x <= right and top <= y <= bottom:
                    blocked.add((c, r))

        blocked |= {(3, 6), (5, 7), (7, 6), (8, 6), (11, 4), (11, 5), (11, 6), (11, 7), (10, 2), (9, 6), (10, 4), (4, 0), (5, 0), (6, 0), (7, 0), (3, 0)}

        blocked.discard(START)
        blocked.discard(GOAL)

    primary = _a_star(START, GOAL, blocked)
    alternates: list[list[tuple[int, int]]] = []
    # It is only worth showing a second candidate route when there is
    # actually a wall to route around, since with nothing in the way there
    # is just the one direct path anyway.
    if primary and ctx.show_pseudocode:
        blocked_for_alt = blocked | set(primary[1:-1])
        alt = _a_star(START, GOAL, blocked_for_alt)
        if alt and alt != primary:
            alternates.append(alt)

    drawn_cells = set(primary or []) | {cell for alt in alternates for cell in alt}

    # These are purely decorative wall circles hugging the winning path
    # itself, using the same blue-to-gold treatment as the pseudocode's
    # wall. They are never fed back into the pathfinding, so they are
    # filtered out to make sure they never land on a drawn route.
    flanking: set[tuple[int, int]] = set()
    if primary:
        for cell in primary[1:-1]:
            for n in _neighbors(cell):
                if n not in drawn_cells and n not in blocked and n != START and n != GOAL:
                    flanking.add(n)

    # The backdrop card, drawn later on top of everything, fully hides any
    # wall circle centered underneath it, so those get skipped instead of
    # drawing circles that no one would ever see anyway.
    card_left = card_right = card_top = card_bottom = None
    if block_rect:
        block_x, block_y, block_width, block_height = block_rect
        card_left, card_top = block_x - BACKDROP_PADDING, block_y - BACKDROP_PADDING
        card_right, card_bottom = block_x + block_width + BACKDROP_PADDING, block_y + block_height + BACKDROP_PADDING

    # Background grid: plain walkable dots everywhere, except where the
    # pseudocode wall (or the path-hugging decoration above) blocks the way.
    # Those particular cells glow blue-to-gold, from the start side to the
    # goal side, instead of just showing open space.
    for r in range(ROWS):
        for c in range(COLS):
            if (c, r) in drawn_cells:
                continue
            if (c, r) in blocked or (c, r) in flanking:
                x, y = grid_x(c), grid_y(r)
                if card_left is not None and card_left <= x <= card_right and card_top <= y <= card_bottom:
                    continue
                t = c / (COLS - 1)
                dwg.add(
                    dwg.circle(
                        center=(x, y),
                        r=wall_r,
                        fill=_lerp_color(START_COLOR, ctx.theme.accent, t),
                        opacity=0.55,
                    )
                )
            else:
                dwg.add(dwg.circle(center=(grid_x(c), grid_y(r)), r=2.5, fill=ctx.theme.muted))

    # The route(s) that almost won are drawn faint and thin, underneath the
    # winning path, ideally showing that more than one path was possible.
    for alt in alternates:
        points = [(grid_x(c), grid_y(r)) for c, r in alt]
        dwg.add(
            dwg.polyline(
                points=points,
                fill="none",
                stroke=ctx.theme.muted,
                stroke_width=1.5,
                stroke_dasharray="4,4",
            )
        )
        for x, y in points:
            dwg.add(dwg.circle(center=(x, y), r=4.5, fill=ctx.theme.muted))

    if primary:
        points = [(grid_x(c), grid_y(r)) for c, r in primary]
        dwg.add(dwg.polyline(points=points, fill="none", stroke=ctx.theme.accent, stroke_width=2.5))
        for x, y in points:
            dwg.add(dwg.circle(center=(x, y), r=4.5, fill=ctx.theme.accent))

        def endpoint_marker(x: float, y: float, label: str, color: str) -> None:
            # This is a filled badge, not just an outline, so that it reads
            # clearly over the grid, and it is colored to match its role:
            # cool for the start, warm for the goal.
            dwg.add(
                dwg.circle(center=(x, y), r=15, fill=ctx.theme.background, stroke=color, stroke_width=2.5)
            )
            dwg.add(
                dwg.text(
                    label,
                    insert=(x, y + 5),
                    fill=color,
                    font_family=ctx.theme.font_family,
                    font_size=15,
                    font_weight="bold",
                    text_anchor="middle",
                )
            )

        start_x, start_y = points[0]
        goal_x, goal_y = points[-1]
        endpoint_marker(start_x, start_y, "A", START_COLOR)
        endpoint_marker(goal_x, goal_y, "B", ctx.theme.accent)

    if ctx.show_pseudocode and block_rect:
        block_x, block_y, block_width, block_height = block_rect
        card_x, card_y = block_x - BACKDROP_PADDING, block_y - BACKDROP_PADDING
        card_width, card_height = block_width + 2 * BACKDROP_PADDING, block_height + 2 * BACKDROP_PADDING

        # This is a soft, accent-colored glow behind the card, the same
        # "this section is elevated" treatment that the site's own
        # cards/buttons use on hover (an accent-tinted shadow). It is
        # approximated here with stacked, growing, fading rects, since this
        # renderer does not have access to real SVG blur filters.
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
        palette = SYNTAX_COLORS[ctx.theme.name]
        for i, line in enumerate(PSEUDOCODE):
            stripped = line.lstrip(" ")
            indent = len(line) - len(stripped)
            text_el = dwg.text(
                "",
                insert=(block_x + indent * CHAR_WIDTH, block_y + PSEUDO_FONT_SIZE + i * PSEUDO_LINE_HEIGHT),
                font_family=ctx.theme.font_family,
                font_size=PSEUDO_FONT_SIZE,
            )
            for token_text, color in tokenize_line(stripped, palette):
                text_el.add(dwg.tspan(token_text, fill=color))
            dwg.add(text_el)

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="a-star-search",
    title="A* Search",
    tagline="The best path is found by looking ahead.",
    category=AlgorithmCategory.SEARCH,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#F2C14E",
    author="Andrei Rukavina",
    date="2026-08-26",
)
