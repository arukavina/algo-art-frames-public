"""Shared pseudocode syntax highlighting: a lightweight, rule-based tokenizer
that colors control-flow keywords, function-style calls, numbers, and
punctuation differently, so pseudocode blocks read as more than a flat wall
of text. This is not real Python, so a proper lexer would misfire on it."""

import re

TOKEN_RE = re.compile(r"(\s+)|([A-Za-z_][A-Za-z0-9_]*)|(\d+)|([^\sA-Za-z0-9_])")
KEYWORDS = {"while", "if", "for", "each", "in", "is", "not", "return", "add", "set"}
OBJECTS = {"viewport", "camera", "pixel", "square"}

SYNTAX_COLORS = {
    "dark": {"keyword": "#F97583", "call": "#79B8FF", "number": "#FFAB70", "punct": "#8B949E", "objects": "#F0BC0F", "default": "#C9D1D9"},
    "light": {"keyword": "#D73A49", "call": "#005CC5", "number": "#B35900", "punct": "#6A737D", "objects": "#A01919", "default": "#24292E"},
}


def tokenize_line(line: str, palette: dict[str, str]) -> list[tuple[str, str]]:
    """Split a pseudocode line into (text, color) runs."""
    runs: list[tuple[str, str]] = []
    for match in TOKEN_RE.finditer(line):
        space, word, number, punct = match.groups()
        if space is not None:
            runs.append((space, palette["default"]))
        elif word is not None:
            if word in KEYWORDS:
                color = palette["keyword"]
            elif word in OBJECTS:
                color = palette["objects"]
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
