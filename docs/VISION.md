# Vision

## The problem

Checking the weather is a two-second need that almost always turns into a
context switch: open a browser, find a tab, sit through a layout full of ads
and a 10-day forecast you didn't ask for, then go back to what you were
doing. For anyone who lives in a terminal, that's a disproportionate amount
of friction for "is it raining right now?"

## Who it's for

Developers and terminal-dwellers who want a fast, no-nonsense answer to
"what's it like outside" without leaving their shell — and who'll appreciate
a tool that's a little bit delightful to look at, not just functional.

## The core idea

One command, one city, one answer:

```
$ weather Lisbon
```

renders the current conditions as a small ASCII scene — sun, clouds, rain,
snow, fog, a storm — colored to match, with the essential numbers
(temperature, feels-like, humidity, wind) underneath. No forecast, no
clutter, no account, no API key to manage. Run it, glance at it, move on.

## Key design decisions

- **No API key required.** The tool calls a free public weather API
  (Open-Meteo) for geocoding and current conditions, so there's zero setup
  between `pip install` and a working command.
- **Current conditions only, not a forecast.** A forecast view is a
  different (denser, busier) product. v1 stays narrow: "right now," rendered
  well, is the whole job.
- **Art and color carry meaning, not decoration.** Each weather condition
  maps to a distinct scene and a distinct color so the *shape* of the output
  tells you the weather before you've read a word.
- **Small, deliberate dependency footprint.** `requests` for HTTP, the
  standard library for everything else. No heavyweight CLI or terminal-UI
  framework — argparse and plain ANSI codes are enough for what this tool
  does.
- **Fail loud, fail simple.** An unknown city or a network error produces a
  clear one-line message on stderr and a non-zero exit code — never a stack
  trace, never a silent wrong answer.
- **Pure rendering logic, network at the edges.** Art selection, coloring,
  and text formatting are pure functions that take already-fetched data, so
  they're trivially testable without mocking the network for every test.

## What "v1 done" looks like

- `pip install ascii-weather` (or `pipx install`) gives you a working
  `weather <city>` command with no further setup.
- Every major weather family (clear, partly cloudy, overcast, rain,
  thunderstorm, snow, fog) has its own ASCII scene and color treatment.
- City lookups that fail (typo, nonexistent place) and network failures both
  produce a clear, friendly error — never a raw traceback.
- The core logic (weather-code → condition mapping, art selection,
  rendering) is unit tested without hitting the network; CI runs lint +
  tests on every push.
- README has install instructions and a real example, and the tool feels
  good to actually use — fast, clear, a little bit fun.
