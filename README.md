# ASCII Weather

[![CI](https://github.com/ctkrug/ascii-weather/actions/workflows/ci.yml/badge.svg)](https://github.com/ctkrug/ascii-weather/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

**Current weather for any city, rendered as colorful ASCII art in your terminal.**
No API key. No signup. No browser tab. Just the sky, drawn in text.

```
$ weather Tokyo

    \   /     Tokyo, JP
     .-.       Mainly clear
  ― (   ) ―    24°C feels like 26°C
     `-'        Humidity 77%  Wind 3 km/h
    /   \

$ weather London -f

     .--.     London, GB
  .-(    ).   Overcast
 (___.__)__)  59°F feels like 56°F
              Humidity 82%  Wind 14 mph

$ weather Oslo

     .--.     Oslo, NO
  .-(    ).   Light snow
 (___.__)__)  -2°C feels like -6°C
    *   *      Humidity 90%  Wind 8 km/h
```

## Install

```bash
pip install ascii-weather
```

From source:

```bash
git clone https://github.com/ctkrug/ascii-weather.git
cd ascii-weather
pip install -e .
```

Requires Python 3.10+. No API key — weather data comes from the free
[Open-Meteo](https://open-meteo.com/) public API.

## Quick start

```bash
weather "New York"
weather London -f        # Fahrenheit and mph
weather Paris -c         # Celsius and km/h (explicit)
weather Tokyo --json     # machine-readable output
```

## Options

```
weather [CITY] [options]
```

| Flag | Description |
|------|-------------|
| `-f`, `--fahrenheit` | Display in °F and mph |
| `-c`, `--celsius` | Display in °C and km/h |
| `--units metric\|imperial` | Explicit unit system |
| `--no-color` | Plain text, no ANSI colors |
| `--json` | JSON output for scripting and pipelines |
| `-v`, `--verbose` | Print resolved coordinates + raw API response |
| `--version` | Print version and exit |
| `-h`, `--help` | Show this help and full example list |

`-f` and `-c` are mutually exclusive with each other and with `--units`.

## Setting a default unit system

Set it once in your shell profile and never type `-f` or `-c` again.

**Option 1 — environment variable** (add to `~/.zshrc` or `~/.bashrc`):

```bash
export ASCII_WEATHER_UNITS=f
```

**Option 2 — config file** at `~/.config/ascii-weather/config`:

```ini
[defaults]
units = f
```

Both accept: `f` `fahrenheit` `imperial` `c` `celsius` `metric`

Priority order: **command-line flag** > `ASCII_WEATHER_UNITS` > config file > metric

## Default city

Skip the argument entirely with `ASCII_WEATHER_CITY`:

```bash
export ASCII_WEATHER_CITY="San Francisco"
weather           # always checks SF
weather Tokyo     # city argument still overrides it
```

## Disambiguation

When a city name matches several comparably-sized places, `weather` lists
them and asks you to be more specific — it never silently picks wrong:

```
$ weather Springfield

weather: 'Springfield' matches multiple locations, please be more specific:
  - Springfield, Missouri, US
  - Springfield, Illinois, US
  - Springfield, Massachusetts, US
  - Springfield, Ohio, US
weather: try `weather "Springfield, <state or country>"`

$ weather "Springfield, IL"

     .--.     Springfield, US
  .-(    ).   Thunderstorm
 (___.__)__)  34°C feels like 36°C
   ⚡'  ⚡'     Humidity 49%  Wind 24 km/h
```

Pass `"City, State"`, `"City, Country"`, or a country code to pick one.
Open-Meteo already ranks by city population, so major cities (London,
Paris, Tokyo) resolve instantly with no disambiguation step.

## Scripting with `--json`

`--json` emits a compact JSON object to stdout — pipe it anywhere:

```bash
weather Lisbon --json | jq .temperature
weather Lisbon --json | jq -r '.description'
weather Lisbon -f --json | jq '{city: .location.name, temp: .temperature}'
```

Example output:

```json
{
  "location": {"name": "Lisbon", "country": "PT", "latitude": 38.725, "longitude": -9.15},
  "condition": "clear",
  "description": "Clear sky",
  "is_day": true,
  "windy": false,
  "units": "metric",
  "temperature": 21.0,
  "feels_like": 22.0,
  "humidity_pct": 58,
  "wind": 14.7
}
```

Color is automatically disabled when stdout is not a TTY (pipe, redirect,
subshell). Set `NO_COLOR=1` to force it off in all contexts.

## What it draws

Distinct ASCII scenes for every major WMO weather code, with day/night
and wind variants:

| Condition | What you see |
|-----------|--------------|
| Clear sky (day) | Bright sun with rays |
| Clear sky (night) | Moon and scattered stars |
| Partly cloudy (day) | Sun peeking over a cloud |
| Partly cloudy (night) | Moon behind a cloud |
| Overcast | Flat, heavy cloud |
| Windy | Cloud with motion lines |
| Light / normal / heavy rain | Dripping cloud, more drops = more rain |
| Thunderstorm | Cloud with ⚡ lightning |
| Light / normal / heavy snow | Cloud with ❄ snowflakes |
| Fog | Layered dashes |

Colors adapt to condition and time of day — vivid palette in daylight,
dimmer treatment after dark. Use `--no-color` or set `NO_COLOR` to disable.

## Debugging with `-v`

```bash
$ weather Lisbon -v

weather: resolved 'Lisbon' to Lisbon, PT (38.72509, -9.1498)
weather: raw response: {"time": "...", "temperature_2m": 20.6, "weather_code": 0, ...}
       *  .      Lisbon, PT
   .  *  .--.    Clear sky
      *  (    )  21°C feels like 20°C
   .    `----'   Humidity 71%  Wind 15 km/h
        *   .
```

`-v` prints the resolved city coordinates and the full raw API response to
stderr, leaving stdout clean for piping.

## Resilience

- **Retries**: transient network failures are retried twice with exponential
  backoff before giving up.
- **Graceful errors**: bad city names, ambiguous matches, and network
  timeouts all produce clear, actionable messages to stderr and a non-zero
  exit code.
- **No negative-zero**: temperatures that round to `0°` never print as
  `-0°` — a subtle but real annoyance, fixed.

## Why

Checking the weather shouldn't require leaving the terminal. ASCII Weather
turns a single command into a small, pleasant moment: real conditions for
the city you asked about, rendered with color and a bit of character, and
nothing else competing for your attention.

It's deliberately small and fast — one command, one API round-trip, no
configuration required to get started.

## Stack

- **Python 3.10+**, packaged via `pyproject.toml` (pip-installable)
- **[Open-Meteo](https://open-meteo.com/)** — free public weather and
  geocoding APIs, no key required
- **`requests`** for HTTP; everything else is stdlib
- **`pytest`** test suite (96 tests), **`ruff`** linting, GitHub Actions CI

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and PRs welcome.

## License

MIT — see [LICENSE](LICENSE).
