"""TODO: a one-line description of the algorithm this module visualizes.

TODO: a short paragraph explaining what the diagram depicts and why it is
drawn this particular way (for example, "as a funnel of narrowing rows" for
binary search). Take a look at binary_search.py or quicksort.py for a
filled-in reference, it helps a lot to see a finished example first.

Note that this file is never imported by algorithms/__init__.py, so on
its own it has no effect on the registry or the test suite. It only starts
to matter once you copy it, rename it, and register it (see
CONTRIBUTING.md).
"""

from algo_art_frames.algorithms.base import AlgorithmCategory, AlgorithmPlugin
from algo_art_frames.render.canvas import RenderContext, new_canvas

PSEUDOCODE = [
    "TODO: step 1",
    "TODO: step 2",
    "TODO: step 3",
]


def draw(ctx: RenderContext) -> str:
    dwg, _box = new_canvas(
        ctx,
        title="TODO Title",
        tagline="TODO one-line tagline.",
        pseudocode=PSEUDOCODE,
    )

    # TODO: draw the diagram into `_box` (a ContentBox, with _box.x, _box.y,
    # _box.width, _box.height) using dwg.rect/text/line/circle/path. Colors
    # should come from ctx.theme.accent (for the highlight), ctx.theme.foreground
    # (the default ink), and ctx.theme.muted (for anything de-emphasized), that
    # way the diagram respects both the dark and the light theme.

    return dwg.tostring()


PLUGIN = AlgorithmPlugin(
    slug="TODO-kebab-case-slug",
    title="TODO Title",
    tagline="TODO one-line tagline.",
    # TODO: pick whichever category fits best from AlgorithmCategory (base.py),
    # for instance AlgorithmCategory.SEARCH, .SORTING, .GRAPH,
    # .MACHINE_LEARNING, .GRAPHICS, and so on.
    category=AlgorithmCategory.SEARCH,
    pseudocode=PSEUDOCODE,
    draw=draw,
    accent="#TODO00",
    author="TODO Your Name",  # optional, feel free to omit both and render no attribution at all
    date="TODO YYYY-MM-DD",
)
