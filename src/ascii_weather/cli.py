"""Command-line entrypoint for ASCII Weather."""

import argparse
import json
import os
import sys

import requests

from ascii_weather import __version__
from ascii_weather.art import get_art
from ascii_weather.colors import color_for_condition, colorize
from ascii_weather.weather import (
    AmbiguousCityError,
    CityNotFoundError,
    WeatherServiceError,
    celsius_to_fahrenheit,
    fetch_current_conditions,
    geocode_city,
    is_windy,
    kph_to_mph,
)


def render_ambiguous_city_error(exc: AmbiguousCityError) -> str:
    lines = [f"weather: {exc.query!r} matches multiple locations, please be more specific:"]
    for candidate in exc.candidates:
        place = candidate.admin1 or candidate.country
        parts = [part for part in (candidate.name, place, candidate.country_code) if part]
        lines.append(f"  - {', '.join(parts)}")
    lines.append(f'weather: try `weather "{exc.query}, <state or country>"`')
    return "\n".join(lines)


def _round_temp(value: float) -> int:
    """Round a temperature to the nearest whole degree without a "-0" result.

    round() with no ndigits returns an int, which has no negative-zero
    representation, so a value like -0.4 correctly becomes 0 instead of
    the "-0" a naive f"{value:.0f}" format would print.
    """
    return round(value)


def _align_art_and_info(art: str, info_lines: list[str], color: str | None) -> str:
    """Lay out ASCII art and info text side by side, art on the left.

    Padding is computed from the plain (uncolored) art so ANSI escape
    codes never throw off column alignment.
    """
    art_lines = art.strip("\n").splitlines()
    width = max((len(line) for line in art_lines), default=0)

    rows = []
    for i in range(max(len(art_lines), len(info_lines))):
        art_line = art_lines[i] if i < len(art_lines) else ""
        info_line = info_lines[i] if i < len(info_lines) else ""
        if info_line:
            padded = art_line.ljust(width)
            styled = colorize(padded, color) if color else padded
            rows.append(f"{styled}  {info_line}")
        else:
            rows.append(colorize(art_line, color) if color else art_line)
    return "\n".join(rows)


def render(location, conditions, units: str = "metric", use_color: bool = True) -> str:
    windy = is_windy(conditions.wind_kph)
    art = get_art(conditions.condition, is_day=conditions.is_day, windy=windy)
    color = color_for_condition(conditions.condition, is_day=conditions.is_day) if use_color else None

    place = location.name
    if location.country:
        place = f"{location.name}, {location.country}"
    info_lines = [place, conditions.description]

    if units == "imperial":
        temp = celsius_to_fahrenheit(conditions.temperature_c)
        feels_like = celsius_to_fahrenheit(conditions.feels_like_c)
        wind = kph_to_mph(conditions.wind_kph)
        info_lines.append(f"{_round_temp(temp)}°F feels like {_round_temp(feels_like)}°F")
        info_lines.append(f"Humidity {conditions.humidity_pct:.0f}%  Wind {wind:.0f} mph")
    else:
        info_lines.append(
            f"{_round_temp(conditions.temperature_c)}°C "
            f"feels like {_round_temp(conditions.feels_like_c)}°C"
        )
        info_lines.append(
            f"Humidity {conditions.humidity_pct:.0f}%  Wind {conditions.wind_kph:.0f} km/h"
        )
    return _align_art_and_info(art, info_lines, color)


def render_json(location, conditions, units: str = "metric") -> str:
    if units == "imperial":
        temperature = celsius_to_fahrenheit(conditions.temperature_c)
        feels_like = celsius_to_fahrenheit(conditions.feels_like_c)
        wind = kph_to_mph(conditions.wind_kph)
    else:
        temperature = conditions.temperature_c
        feels_like = conditions.feels_like_c
        wind = conditions.wind_kph

    payload = {
        "location": {
            "name": location.name,
            "country": location.country,
            "latitude": location.latitude,
            "longitude": location.longitude,
        },
        "condition": conditions.condition,
        "description": conditions.description,
        "is_day": conditions.is_day,
        "windy": is_windy(conditions.wind_kph),
        "units": units,
        "temperature": round(temperature, 1),
        "feels_like": round(feels_like, 1),
        "humidity_pct": conditions.humidity_pct,
        "wind": round(wind, 1),
    }
    return json.dumps(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="weather", description="Current conditions for any city, in ASCII art."
    )
    parser.add_argument(
        "city",
        nargs="?",
        default=None,
        help="City name, e.g. 'Lisbon' or 'San Francisco'. "
        "Falls back to the ASCII_WEATHER_CITY environment variable if omitted.",
    )
    parser.add_argument(
        "--units",
        choices=["metric", "imperial"],
        default="metric",
        help="Display units: metric (°C, km/h) or imperial (°F, mph)",
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable ANSI color output"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output current conditions as JSON"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show resolved coordinates and the raw API response on stderr",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


def should_use_color(no_color_flag: bool) -> bool:
    """Decide whether to emit ANSI color, honoring --no-color, NO_COLOR, and non-TTY output."""
    if no_color_flag or "NO_COLOR" in os.environ:
        return False
    return sys.stdout.isatty()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    city = args.city or os.environ.get("ASCII_WEATHER_CITY")
    if not city:
        parser.error(
            "city is required (pass it as an argument or set ASCII_WEATHER_CITY)"
        )

    try:
        location = geocode_city(city)
        conditions = fetch_current_conditions(location)
    except CityNotFoundError as exc:
        print(f"weather: {exc}", file=sys.stderr)
        return 1
    except AmbiguousCityError as exc:
        print(render_ambiguous_city_error(exc), file=sys.stderr)
        return 1
    except WeatherServiceError:
        print(
            "weather: couldn't reach the weather service, please try again later",
            file=sys.stderr,
        )
        return 2
    except requests.RequestException as exc:
        print(f"weather: network error: {exc}", file=sys.stderr)
        return 2

    if args.verbose:
        print(
            f"weather: resolved {city!r} to {location.name}, {location.country} "
            f"({location.latitude}, {location.longitude})",
            file=sys.stderr,
        )
        print(f"weather: raw response: {json.dumps(conditions.raw)}", file=sys.stderr)

    if args.json:
        print(render_json(location, conditions, units=args.units))
        return 0

    use_color = should_use_color(args.no_color)
    print(render(location, conditions, units=args.units, use_color=use_color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
