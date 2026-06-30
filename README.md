# ASCII Weather

A command-line tool that fetches the current weather for any city and renders
it as colorful ASCII art right in your terminal. No API key required, no
browser tab, no clutter — just the sky, drawn in text.

```
$ weather Lisbon

      .--.      Lisbon, PT
   .-(    ).    Partly Cloudy
  (___.__)__)   21°C  feels like 22°C
                Humidity 58%  Wind 11 km/h
```

## Usage

```
$ weather Lisbon                     # current conditions for a city
$ weather Lisbon --units imperial    # °F and mph instead of °C and km/h
$ weather Lisbon --json              # machine-readable output for scripting
$ weather Lisbon --no-color          # plain text, no ANSI color
$ weather Lisbon -v                  # also print resolved coordinates + raw API response
$ ASCII_WEATHER_CITY=Lisbon weather  # omit the city arg, fall back to an env var
```

Color is also automatically disabled when stdout isn't a terminal (e.g. piping
to a file) or when the `NO_COLOR` environment variable is set.

## Why

Checking the weather shouldn't require leaving the terminal. ASCII Weather
turns a single command into a small, pleasant moment: a quick glance at
real conditions, rendered with color and a bit of character, and nothing
else competing for your attention.

## Features

Planned for v1 (see [`docs/VISION.md`](docs/VISION.md) and
[`docs/BACKLOG.md`](docs/BACKLOG.md) for the full breakdown):

- Look up current conditions for any city by name
- Distinct ASCII art scenes for the major weather conditions (clear, cloudy,
  rain, snow, thunderstorm, fog, etc.)
- Terminal color rendering that adapts to the condition, with `--no-color`
  and `NO_COLOR` support for piping into other tools
- Key stats at a glance: temperature, feels-like, humidity, wind, with
  `--units metric|imperial`
- `--json` output for scripting, `-v/--verbose` for debugging lookups
- A default city via the `ASCII_WEATHER_CITY` environment variable
- Sensible fallbacks when a city can't be found or the network is down,
  including automatic retries on transient failures
- Fast: a single command, a single API round-trip, no setup beyond install

## Stack

- **Python 3.10+**, distributed as a standard `pyproject.toml` package
- Public weather API for live conditions (no key required)
- Standard library + a small, deliberate set of dependencies for HTTP and
  terminal color output
- `pytest` for tests, run on every push via GitHub Actions

## Status

Early scaffold — see [`docs/VISION.md`](docs/VISION.md) for where this is
headed and [`docs/BACKLOG.md`](docs/BACKLOG.md) for the planned work.

## License

MIT — see [`LICENSE`](LICENSE).
