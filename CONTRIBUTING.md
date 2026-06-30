# Contributing

## Dev setup

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running checks

```sh
ruff check .
pytest -q
```

Both run in CI on every push and pull request — see
[`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Project layout

- `src/ascii_weather/` — the package: CLI (`cli.py`), weather data
  (`weather.py`), ASCII scenes (`art.py`), terminal color helpers
  (`colors.py`)
- `tests/` — unit tests for the pure logic (no live network calls)
- `docs/VISION.md` — what this project is and why
- `docs/BACKLOG.md` — planned epics/stories
