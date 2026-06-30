# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-30

First stable release.

### Added

- `weather <city>` command that fetches current conditions from the free
  [Open-Meteo](https://open-meteo.com/) API (no key required) and renders them
  as colorful ASCII art beside the key stats.
- Distinct ASCII scenes for every major condition — clear, partly cloudy,
  overcast, windy, light/normal/heavy rain and snow, thunderstorm, and fog —
  with moon/stars variants and a dimmer palette at night.
- `--units metric|imperial` for °C/km/h or °F/mph.
- `--json` output for scripting and `-v/--verbose` for inspecting the resolved
  coordinates and raw API response.
- `--no-color` flag, plus automatic color suppression for non-TTY output and
  when `NO_COLOR` is set (per the [NO_COLOR](https://no-color.org/) spec).
- A default city via the `ASCII_WEATHER_CITY` environment variable.
- City disambiguation: a `"City, State"` / `"City, Country"` form and a
  candidate list when a bare name matches several comparable places.
- Automatic retries with backoff on transient network failures, and clear
  one-line error messages (never a raw traceback) for unknown cities,
  malformed responses, and unreachable services.

[1.0.0]: https://github.com/ctkrug/ascii-weather/releases/tag/v1.0.0
