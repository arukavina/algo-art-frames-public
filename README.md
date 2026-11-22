# Algorithmic Art Frames

**Famous algorithms, drawn as minimalist posters. One Python file each.**

Algorithmic Art Frames is an educational, open source project for people learning data visualization and for anyone who loves making art with computers. Each poster turns a famous algorithm into a print-ready SVG: a title, a one-line tagline, a generative diagram and the pseudocode behind it. Every poster here is published on [pseudocode.art](https://pseudocode.art).

Some examples:

![Example posters: Backpropagation, Linear Congruential Generator, A* Search, Ray Tracing, Monte Carlo and Binary Search](assets/gallery.png)

## Why contribute

This is a passion project. You don't need to be the best programmer or the best designer to add a poster, and nobody is keeping score. In a time when AI can generate almost anything in seconds, a poster here is something you made yourself: an algorithm you care about, drawn the way you see it. Pick one, give it your own style, and share it.

**Ready?** Read [CONTRIBUTING.md](CONTRIBUTING.md). All you need is Python.

## Quick start

```bash
git clone https://github.com/arukavina/algo-art-frames-public.git
cd algo-art-frames-public
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"

pytest                             # run every check
python -m algo_art_frames.preview binary-search   # writes out/binary-search-{dark,light}.svg
python -m algo_art_frames.preview binary-search --variations   # every display option combination
```

Open the SVG files in any browser to see the posters. Run `python -m algo_art_frames.preview --help` for every display option (frame, pseudocode, tagline, author, accent color, theme).

## Layout

```
src/algo_art_frames/
  algorithms/
    base.py           # the plugin contract: AlgorithmPlugin, AlgorithmCategory
    __init__.py       # the registry (REGISTRY) built from the _MODULES tuple
    _template.py      # copy this to start a new algorithm
    <one module per algorithm>.py
  render/
    canvas.py         # new_canvas(): background, title, tagline, pseudocode, layout box
    theme.py          # dark and light theme presets
    syntax.py         # pseudocode syntax highlighting
  preview.py          # renders posters to SVG files for local review
tests/
  test_algorithms.py  # every plugin is registered and renders valid SVG
  test_contract.py    # safety and consistency checks (see CONTRIBUTING.md)
```

## How a merged poster goes live

1. You open a PR here. CI runs the lint, the tests and the safety checks, and uploads rendered SVG previews of every poster as a workflow artifact.
2. A maintainer reviews the poster and approves the PR (when possible)
3. Once it's merged into `main`, your poster is published on pseudocode.art automatically.

## License

[MIT](LICENSE)
