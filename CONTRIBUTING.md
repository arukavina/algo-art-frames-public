# Contributing

The best way to contribute is to add a new algorithm poster. Each algorithm is a self-contained plugin: one Python module that draws an SVG. You never need to touch the renderer, and the website picks up merged posters automatically.

## Set up

```bash
git clone https://github.com/arukavina/algo-art-frames-public.git
cd algo-art-frames-public
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
```

## The plugin contract

Every algorithm module exposes one module-level `PLUGIN`, an instance of `AlgorithmPlugin` (`src/algo_art_frames/algorithms/base.py`):

```python
@dataclass(frozen=True)
class AlgorithmPlugin:
    slug: str                            # kebab-case, e.g. "binary-search"
    title: str                           # e.g. "Binary Search"
    tagline: str                         # one line, e.g. "Halve the search space every step."
    category: AlgorithmCategory          # pick one from the enum below, don't invent a new string
    pseudocode: list[str]                # a few short lines
    draw: Callable[[RenderContext], str] # renders the SVG diagram
    accent: str                          # signature hex color, e.g. "#FF8A3D"
    author: str | None = None            # optional, shown bottom-right when show_author is on
    date: str | None = None              # optional, e.g. "2026-08-26"
```

`category` must be one of `AlgorithmCategory` (also in `base.py`), so the catalog's categories can't fragment into near-duplicates ("ml" vs "machine-learning") as more algorithms get added:

```python
class AlgorithmCategory(str, Enum):
    SEARCH = "search"
    SORTING = "sorting"
    GRAPH = "graph"
    GAME_THEORY = "game-theory"
    CRYPTOGRAPHY = "cryptography"
    COMPRESSION = "compression"
    STREAMING = "streaming"
    RANDOMNESS = "randomness"
    OPTIMIZATION = "optimization"
    MACHINE_LEARNING = "machine-learning"
    SIGNAL_PROCESSING = "signal-processing"
    LINEAR_ALGEBRA = "linear-algebra"
    GRAPHICS = "graphics"
    STRINGS = "strings"
```

Need a category that doesn't fit any of these? Add a new member to the enum in the same PR rather than falling back to a raw string.

`draw(ctx)` gets a `RenderContext` (theme and canvas size) and returns raw SVG markup. Use the shared `new_canvas()` helper (`src/algo_art_frames/render/canvas.py`) to get the title/tagline/pseudocode scaffolding out of the way, plus a `ContentBox` (`box.x`, `box.y`, `box.width`, `box.height`) to draw your diagram into. Color it with `ctx.theme.accent`, `ctx.theme.foreground` and `ctx.theme.muted` so it works in both the dark and light presets (`src/algo_art_frames/render/theme.py`).

## Steps to add a new algorithm

1. Copy the template. The filename is `snake_case` and must match the slug (`dijkstra_shortest_path.py` for the slug `dijkstra-shortest-path`):
   ```bash
   cp src/algo_art_frames/algorithms/_template.py src/algo_art_frames/algorithms/<your_algorithm>.py
   ```
2. Set `TITLE` and `TAGLINE` once at the top, then fill in `PSEUDOCODE`, the `draw()` function and the `PLUGIN` metadata. `binary_search.py` and `quicksort.py` are good references for the level of detail expected.
3. Register it in `src/algo_art_frames/algorithms/__init__.py`: import your module and add it to the `_MODULES` tuple. `REGISTRY` is built from that tuple automatically.
4. Add your new slug to `EXPECTED_SLUGS` in `tests/test_algorithms.py`.
5. Look at it in both themes:
   ```bash
   python -m algo_art_frames.preview <your-slug>
   ```
   This writes `out/<your-slug>-dark.svg` and `out/<your-slug>-light.svg`. Open them in a browser. Viewers can switch the display options, so check that your poster still looks right with each of them:
   ```bash
   python -m algo_art_frames.preview <your-slug> --variations
   ```
   This writes every combination of the frame, pseudocode, tagline and author options in both themes (32 files), named after the options they use, such as `out/<your-slug>-dark-frame-no-pseudocode.svg`. You can also pick options one at a time:

   | Option | Effect |
   |---|---|
   | `--frame` | draws the thin accent frame |
   | `--no-pseudocode` | hides the pseudocode panel |
   | `--no-tagline` | hides the tagline |
   | `--no-author` | hides the author line |
   | `--accent "#ff6b6b"` | replaces your poster's accent color (also works with `--variations`) |
   | `--theme dark` | renders only that theme (repeatable) |
   | `--width 900 --height 1200` | changes the canvas size |

6. Run the checks, then open a pull request from your fork (see [Opening your pull request](#opening-your-pull-request)) with a screenshot of both previews:
   ```bash
   ruff check .
   pytest
   ```

## Opening your pull request

To send your poster you need a **fork**: your own copy of this repo on GitHub. Only maintainers can push branches to this repo, so contributors push their branch to their fork and open a pull request from there. With the [GitHub CLI](https://cli.github.com):

```bash
gh repo fork --remote          # creates your fork; it becomes "origin" and this repo "upstream"
git checkout -b my-poster
git add src/algo_art_frames/algorithms/dijkstra.py src/algo_art_frames/algorithms/__init__.py tests/test_algorithms.py
git commit -m "feat: add dijkstra poster"
git push -u origin my-poster
gh pr create                   # opens the pull request against this repo's main
```

Without the CLI: click **Fork** at the top of this repo's GitHub page, add your fork as a remote with `git remote add fork` followed by your fork's URL, push with `git push -u fork my-poster`, and open the pull request from the banner GitHub shows on your fork.

## What the checks enforce

Merged posters go live automatically, so `tests/test_contract.py` keeps plugin code limited to drawing. A plugin:

- may only import `algo_art_frames.*` and these standard-library modules: `math`, `random`, `itertools`, `heapq`, `re`, `dataclasses`, `collections`, `functools`, `enum`, `typing`, `__future__`;
- may not use `eval`, `exec`, `open`, `__import__`, `getattr`/`setattr` and similar built-ins, or dunder attributes such as `__globals__`;
- must render in under 2 seconds and produce less than 1 MB of SVG, in both themes;
- must use a kebab-case slug matching its filename, a valid hex accent, a real `AlgorithmCategory`, and no leftover `TODO` text;
- must draw the same title and tagline it lists in `PLUGIN` (define `TITLE` and `TAGLINE` once and use them in both places, as `_template.py` does);
- must visibly change when the frame, pseudocode, tagline or author display option is switched (build the poster with `new_canvas` and it is handled for you);
- must never rename or remove an existing slug (published posters are identified by their slug).

For randomness, use a seeded `random.Random(<seed>)` so a poster looks the same on every render.

These checks are a first line of defense, not a sandbox: every PR is also reviewed by a maintainer before it's merged.

## License

By contributing, you agree your changes are licensed under this repo's [MIT license](LICENSE).
