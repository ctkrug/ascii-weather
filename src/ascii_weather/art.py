"""ASCII art scenes for weather conditions."""

CLEAR = r"""
    \   /
     .-.
  ― (   ) ―
     `-'
    /   \
"""

PARTLY_CLOUDY = r"""
   \  /
 _ /"".-.
   \_(   ).
   /(___(__)
"""

CLOUDY = r"""
     .--.
  .-(    ).
 (___.__)__)
"""

RAIN = r"""
     .--.
  .-(    ).
 (___.__)__)
  ' ' ' ' '
 ' ' ' ' '
"""

THUNDERSTORM = r"""
     .--.
  .-(    ).
 (___.__)__)
   ⚡'  ⚡'
"""

SNOW = r"""
     .--.
  .-(    ).
 (___.__)__)
  *  *  *
 *  *  *
"""

FOG = r"""
 _ - _ - _ -
  _ - _ - _
 _ - _ - _ -
"""

DEFAULT = r"""
     .-.
    (   )
     `-'
"""

_SCENES = {
    "clear": CLEAR,
    "partly_cloudy": PARTLY_CLOUDY,
    "cloudy": CLOUDY,
    "rain": RAIN,
    "thunderstorm": THUNDERSTORM,
    "snow": SNOW,
    "fog": FOG,
}


def get_art(condition: str) -> str:
    """Return the ASCII art scene for a condition name, falling back to a default."""
    return _SCENES.get(condition, DEFAULT)
