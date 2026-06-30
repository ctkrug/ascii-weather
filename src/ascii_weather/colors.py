"""Minimal ANSI color helpers for terminal rendering."""

_CODES = {
    "reset": "0",
    "bold": "1",
    "yellow": "33",
    "bright_yellow": "93",
    "white": "37",
    "bright_white": "97",
    "blue": "34",
    "bright_blue": "94",
    "cyan": "36",
    "bright_cyan": "96",
    "grey": "90",
}

# Color used to render each weather condition's ASCII scene.
CONDITION_COLOR = {
    "clear": "bright_yellow",
    "partly_cloudy": "bright_white",
    "cloudy": "white",
    "rain": "bright_blue",
    "thunderstorm": "yellow",
    "snow": "bright_cyan",
    "fog": "grey",
}


def colorize(text: str, color: str) -> str:
    """Wrap text in ANSI escape codes for the given named color."""
    code = _CODES.get(color)
    if code is None:
        return text
    return f"\033[{code}m{text}\033[{_CODES['reset']}m"
