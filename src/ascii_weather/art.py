"""ASCII art scenes for weather conditions."""

CLEAR = r"""
    \   /
     .-.
  ― (   ) ―
     `-'
    /   \
"""

CLEAR_NIGHT = r"""
       *  .
   .  *  .--.
      *  (    )
   .    `----'
        *   .
"""

PARTLY_CLOUDY = r"""
   \  /
 _ /"".-.
   \_(   ).
   /(___(__)
"""

PARTLY_CLOUDY_NIGHT = r"""
   .  *
 _ /---.-.
   \_(   ).
   /(___(__)
"""

CLOUDY = r"""
     .--.
  .-(    ).
 (___.__)__)
"""

WINDY = r"""
  ~~  ~~~  ~~
 ~~~ .--. ~~~
  .-(    ).~~
 (___.__)__)
  ~~~  ~~  ~~
"""

RAIN_LIGHT = r"""
     .--.
  .-(    ).
 (___.__)__)
   '   '
"""

RAIN = r"""
     .--.
  .-(    ).
 (___.__)__)
  ' ' ' ' '
 ' ' ' ' '
"""

RAIN_HEAVY = r"""
     .--.
  .-(    ).
 (___.__)__)
 ' ' ' ' ' '
' ' ' ' ' ' '
 ' ' ' ' ' '
"""

THUNDERSTORM = r"""
     .--.
  .-(    ).
 (___.__)__)
   ⚡'  ⚡'
"""

SNOW_LIGHT = r"""
     .--.
  .-(    ).
 (___.__)__)
    *   *
"""

SNOW = r"""
     .--.
  .-(    ).
 (___.__)__)
  *  *  *
 *  *  *
"""

SNOW_HEAVY = r"""
     .--.
  .-(    ).
 (___.__)__)
 *  *  *  *
* *  *  *  *
 *  *  *  *
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

# Conditions whose art swaps in a moon/stars variant at night instead of the
# day scene. Everything else (rain, snow, fog, storms...) looks the same
# regardless of time of day — only the color treatment changes for those.
_NIGHT_SCENES = {
    "clear": CLEAR_NIGHT,
    "partly_cloudy": PARTLY_CLOUDY_NIGHT,
}

# Conditions whose scene is swapped out entirely for the windy overlay when
# wind speed crosses the windy threshold. Rain/snow/storm/fog scenes already
# carry the conditions that matter most, so wind doesn't override those.
_WINDY_OVERRIDE_CONDITIONS = {"clear", "partly_cloudy", "cloudy"}

_SCENES = {
    "clear": CLEAR,
    "partly_cloudy": PARTLY_CLOUDY,
    "cloudy": CLOUDY,
    "windy": WINDY,
    "rain_light": RAIN_LIGHT,
    "rain": RAIN,
    "rain_heavy": RAIN_HEAVY,
    "thunderstorm": THUNDERSTORM,
    "snow_light": SNOW_LIGHT,
    "snow": SNOW,
    "snow_heavy": SNOW_HEAVY,
    "fog": FOG,
}


def get_art(condition: str, is_day: bool = True, windy: bool = False) -> str:
    """Return the ASCII art scene for a condition, falling back to a default.

    ``is_day`` swaps in a moon/stars variant for conditions that have one.
    ``windy`` overrides clear/partly_cloudy/cloudy scenes with a windy scene,
    since wind doesn't otherwise show up in the WMO condition code.
    """
    if windy and condition in _WINDY_OVERRIDE_CONDITIONS:
        return WINDY
    if not is_day and condition in _NIGHT_SCENES:
        return _NIGHT_SCENES[condition]
    return _SCENES.get(condition, DEFAULT)
