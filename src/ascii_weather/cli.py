"""Command-line entrypoint for ASCII Weather."""

import argparse
import json
import os
import sys

import requests

from ascii_weather import __version__
from ascii_weather.art import get_art
from ascii_weather.colors import CONDITION_COLOR, colorize
from ascii_weather.weather import (
    CityNotFoundError,
    celsius_to_fahrenheit,
    fetch_current_conditions,
    geocode_city,
    kph_to_mph,
)


def render(location, conditions, units: str = "metric", use_color: bool = True) -> str:
    art = get_art(conditions.condition)
    if use_color:
        color = CONDITION_COLOR.get(conditions.condition, "bright_white")
        art = colorize(art, color)
    lines = [art]
    place = location.name
    if location.country:
        place = f"{location.name}, {location.country}"
    lines.append(place)
    lines.append(conditions.description)

    if units == "imperial":
        temp = celsius_to_fahrenheit(conditions.temperature_c)
        feels_like = celsius_to_fahrenheit(conditions.feels_like_c)
        wind = kph_to_mph(conditions.wind_kph)
        lines.append(f"{temp:.0f}°F feels like {feels_like:.0f}°F")
        lines.append(f"Humidity {conditions.humidity_pct:.0f}%  Wind {wind:.0f} mph")
    else:
        lines.append(
            f"{conditions.temperature_c:.0f}°C "
            f"feels like {conditions.feels_like_c:.0f}°C"
        )
        lines.append(
            f"Humidity {conditions.humidity_pct:.0f}%  Wind {conditions.wind_kph:.0f} km/h"
        )
    return "\n".join(lines)


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
    if no_color_flag or os.environ.get("NO_COLOR"):
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
