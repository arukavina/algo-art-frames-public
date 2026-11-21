"""Theme tokens that every algorithm's draw() function shares, so the whole catalog stays visually consistent."""

from pydantic import BaseModel


class Theme(BaseModel):
    name: str
    background: str
    foreground: str
    accent: str
    muted: str
    font_family: str = "'JetBrains Mono', 'Courier New', monospace"


DARK = Theme(
    name="dark",
    background="#0b0e14",
    foreground="#e6e6e6",
    accent="#5ec8f8",
    muted="#5a6472",
)

LIGHT = Theme(
    name="light",
    background="#f7f7f5",
    foreground="#14161a",
    accent="#1866db",
    muted="#8a8f98",
)

PRESETS: dict[str, Theme] = {DARK.name: DARK, LIGHT.name: LIGHT}


def resolve_theme(name: str, accent: str | None = None) -> Theme:
    """Look up a theme preset by name, and, if given, override its accent color."""
    try:
        base = PRESETS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown theme '{name}'. Options: {list(PRESETS)}") from exc
    return base.model_copy(update={"accent": accent}) if accent else base
