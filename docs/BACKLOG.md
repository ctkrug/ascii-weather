# Backlog

High-level epic/story breakdown to guide the build phase. Stories are
intentionally coarse — they'll be refined as they're picked up.

## Epic 1 — Core weather pipeline

- [ ] Add retry/timeout handling around the Open-Meteo geocoding and forecast
      requests, with a friendly message on repeated failure
- [ ] Support disambiguating cities with the same name (e.g. multiple
      "Springfield" results) instead of silently taking the first match
- [ ] Add a small on-disk cache (short TTL) so repeated lookups of the same
      city don't always hit the network
- [x] Support `--units` for metric/imperial (°C/km/h vs °F/mph)

## Epic 2 — ASCII art & rendering

- [ ] Expand art coverage: distinct scenes for windy conditions, heavy vs.
      light rain/snow, and night-time variants
- [ ] Add a day/night color treatment (e.g. dimmer palette, moon instead of
      sun) based on local time at the queried location
- [ ] Polish layout/alignment so art and stats line up cleanly across
      terminal widths
- [x] Add a `--no-color` flag (and respect `NO_COLOR`/non-TTY output) for
      piping into other tools or scripts

## Epic 3 — CLI polish & UX

- [x] Add `--json` output mode for scripting/piping into other tools
- [ ] Support reading a default city from an env var or config file so
      `weather` with no arguments still works
- [ ] Improve error messages for ambiguous/misspelled city names (e.g. "did
      you mean...")
- [ ] Add `-v/--verbose` to show the resolved coordinates and raw API
      response for debugging

## Epic 4 — Packaging & distribution

- [ ] Publish to PyPI as `ascii-weather` with a working `pipx install`
      story
- [ ] Add a richer test suite covering the CLI end-to-end with a mocked
      HTTP layer (no live network calls in CI)
- [ ] Expand README with install badges, more usage examples, and a GIF/
      screenshot of real output
