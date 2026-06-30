"""Command-line entrypoint for ASCII Weather."""

import argparse
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


def render(location, conditions, units: str = "metric") -> str:
    art = get_art(conditions.condition)
    color = CONDITION_COLOR.get(conditions.condition, "bright_white")
    lines = [colorize(art, color)]
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="weather", description="Current conditions for any city, in ASCII art."
    )
    parser.add_argument("city", help="City name, e.g. 'Lisbon' or 'San Francisco'")
    parser.add_argument(
        "--units",
        choices=["metric", "imperial"],
        default="metric",
        help="Display units: metric (°C, km/h) or imperial (°F, mph)",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        location = geocode_city(args.city)
        conditions = fetch_current_conditions(location)
    except CityNotFoundError as exc:
        print(f"weather: {exc}", file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(f"weather: network error: {exc}", file=sys.stderr)
        return 2

    print(render(location, conditions, units=args.units))
    return 0


if __name__ == "__main__":
    sys.exit(main())
