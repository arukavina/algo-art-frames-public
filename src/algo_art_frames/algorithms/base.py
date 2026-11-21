"""Algorithm plugin contract.

Each module under algo_art_frames/algorithms/ exposes exactly one module-level `PLUGIN`
instance of AlgorithmPlugin. That is the whole contract: to add a new
algorithm, you add one new module and register it in algorithms/__init__.py,
nothing more. In particular, it should never be necessary to touch the
renderer for that.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from algo_art_frames.render.canvas import RenderContext


class AlgorithmCategory(str, Enum):
    """Canonical category tags. Always pick the closest existing fit instead of
    inventing a new string, otherwise the catalog's categories end up
    fragmenting into near-duplicates ("ml" versus "machine-learning") as more
    algorithms get added over time."""

    SEARCH = "search"
    SORTING = "sorting"
    GRAPH = "graph"
    GAME_THEORY = "game-theory"
    CRYPTOGRAPHY = "cryptography"
    COMPRESSION = "compression"
    STREAMING = "streaming"
    PROBABILITY = "probability"
    OPTIMIZATION = "optimization"
    MACHINE_LEARNING = "machine-learning"
    SIGNAL_PROCESSING = "signal-processing"
    LINEAR_ALGEBRA = "linear-algebra"
    GRAPHICS = "graphics"
    STRINGS = "strings"


@dataclass(frozen=True)
class AlgorithmPlugin:
    slug: str
    title: str
    tagline: str
    category: AlgorithmCategory
    pseudocode: list[str]
    draw: Callable[[RenderContext], str]
    accent: str
    """Signature hex color for this algorithm's diagram. It is used as the
    default render accent and also helps identify the algorithm across the
    collection, matching the varied per-algorithm hues seen across the
    reference poster set."""
    author: str | None = None
    date: str | None = None
    """Optional attribution, drawn in the poster's bottom-right corner when
    show_author is enabled. Both fields are free text (date="2026-08-26", for
    instance), and neither one is actually required: a plugin that leaves
    both unset simply renders no attribution at all."""
