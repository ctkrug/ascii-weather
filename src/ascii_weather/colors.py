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

# Color used to render each weather condition's ASCII scene during the day.
CONDITION_COLOR = {
    "clear": "bright_yellow",
    "partly_cloudy": "bright_white",
    "cloudy": "white",
    "windy": "bright_white",
    "rain_light": "bright_blue",
    "rain": "bright_blue",
    "rain_heavy": "bright_blue",
    "thunderstorm": "yellow",
    "snow_light": "bright_cyan",
    "snow": "bright_cyan",
    "snow_heavy": "bright_cyan",
    "fog": "grey",
}

# Dimmer color treatment used at night: the same conditions, but swapped to
# their non-"bright_" counterpart so the scene reads as dimmer after dark.
CONDITION_COLOR_NIGHT = {
    "clear": "white",
    "partly_cloudy": "grey",
    "cloudy": "grey",
    "windy": "grey",
    "rain_light": "blue",
    "rain": "blue",
    "rain_heavy": "blue",
    "thunderstorm": "yellow",
    "snow_light": "cyan",
    "snow": "cyan",
    "snow_heavy": "cyan",
    "fog": "grey",
}


def color_for_condition(condition: str, is_day: bool = True) -> str:
    """Look up the color name for a condition, honoring day/night treatment."""
    palette = CONDITION_COLOR if is_day else CONDITION_COLOR_NIGHT
    return palette.get(condition, "bright_white" if is_day else "grey")


def colorize(text: str, color: str) -> str:
    """Wrap text in ANSI escape codes for the given named color."""
    code = _CODES.get(color)
    if code is None:
        return text
    return f"\033[{code}m{text}\033[{_CODES['reset']}m"
