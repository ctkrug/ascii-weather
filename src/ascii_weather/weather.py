"""Fetch city coordinates and current conditions from the Open-Meteo public API.

No API key is required: https://open-meteo.com/
"""

import time
from dataclasses import dataclass

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes -> (condition key, human description)
# Rain and snow distinguish light/normal/heavy intensity so the art and
# color treatment can reflect how bad it actually is.
WMO_CODES = {
    0: ("clear", "Clear sky"),
    1: ("clear", "Mainly clear"),
    2: ("partly_cloudy", "Partly cloudy"),
    3: ("cloudy", "Overcast"),
    45: ("fog", "Fog"),
    48: ("fog", "Depositing rime fog"),
    51: ("rain_light", "Light drizzle"),
    53: ("rain", "Drizzle"),
    55: ("rain_heavy", "Dense drizzle"),
    56: ("rain_light", "Freezing drizzle"),
    57: ("rain_heavy", "Dense freezing drizzle"),
    61: ("rain_light", "Slight rain"),
    63: ("rain", "Rain"),
    65: ("rain_heavy", "Heavy rain"),
    66: ("rain", "Freezing rain"),
    67: ("rain_heavy", "Heavy freezing rain"),
    71: ("snow_light", "Slight snow fall"),
    73: ("snow", "Snow fall"),
    75: ("snow_heavy", "Heavy snow fall"),
    77: ("snow_light", "Snow grains"),
    80: ("rain_light", "Slight rain showers"),
    81: ("rain", "Rain showers"),
    82: ("rain_heavy", "Violent rain showers"),
    85: ("snow_light", "Slight snow showers"),
    86: ("snow_heavy", "Heavy snow showers"),
    95: ("thunderstorm", "Thunderstorm"),
    96: ("thunderstorm", "Thunderstorm with hail"),
    99: ("thunderstorm", "Thunderstorm with heavy hail"),
}


# Wind speed (km/h) above which conditions are considered windy enough to
# show a dedicated scene instead of the plain clear/cloudy art.
WINDY_THRESHOLD_KPH = 30.0


class CityNotFoundError(Exception):
    """Raised when the geocoding API has no match for the given city name."""


@dataclass
class CityCandidate:
    name: str
    country: str
    country_code: str
    admin1: str


class AmbiguousCityError(Exception):
    """Raised when a city name matches multiple comparably significant places."""

    def __init__(self, query: str, candidates: list[CityCandidate]):
        self.query = query
        self.candidates = candidates
        super().__init__(f"{query!r} matches multiple locations")


class WeatherServiceError(Exception):
    """Raised when the weather service can't be reached after retrying."""


def _get_with_retry(
    url: str, params: dict, timeout: float, retries: int = 2, backoff: float = 0.5
) -> requests.Response:
    """GET a URL, retrying transient failures with exponential backoff."""
    last_exc: requests.RequestException | None = None
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(backoff * (2**attempt))
    raise WeatherServiceError(
        f"could not reach the weather service after {retries + 1} attempts: {last_exc}"
    ) from last_exc


def _parse_json(response: requests.Response) -> dict:
    """Parse a response body as JSON, raising a friendly error on malformed output."""
    try:
        return response.json()
    except ValueError as exc:
        raise WeatherServiceError(f"the weather service returned an invalid response: {exc}") from exc


@dataclass
class Location:
    name: str
    country: str
    latitude: float
    longitude: float


@dataclass
class CurrentConditions:
    condition: str
    description: str
    temperature_c: float
    feels_like_c: float
    humidity_pct: float
    wind_kph: float
    is_day: bool = True
    raw: dict | None = None


def condition_for_code(code: int) -> tuple[str, str]:
    """Map a WMO weather code to a (condition key, description) pair."""
    return WMO_CODES.get(code, ("unknown", "Unknown"))


def is_windy(wind_kph: float) -> bool:
    """Return True when wind speed is high enough to warrant the windy scene."""
    return wind_kph >= WINDY_THRESHOLD_KPH


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert a Celsius temperature to Fahrenheit."""
    return celsius * 9 / 5 + 32


def kph_to_mph(kph: float) -> float:
    """Convert a speed in kilometers per hour to miles per hour."""
    return kph * 0.621371


# A second result only counts as a real rival to the top match when its
# population is at least this fraction of the top match's population...
DISAMBIGUATION_DOMINANCE_RATIO = 3.0
# ...and is itself a place big enough to plausibly be what someone meant.
DISAMBIGUATION_POPULATION_FLOOR = 10_000


def _matches_region(result: dict, region: str) -> bool:
    region = region.strip().lower()
    return (
        (result.get("country_code") or "").lower() == region
        or region in (result.get("country") or "").lower()
        or region in (result.get("admin1") or "").lower()
    )


def _to_candidate(result: dict) -> CityCandidate:
    return CityCandidate(
        name=result["name"],
        country=result.get("country", ""),
        country_code=result.get("country_code", ""),
        admin1=result.get("admin1", ""),
    )


def _pick_unambiguous(results: list[dict]) -> tuple[dict | None, list[dict]]:
    """Pick the clear best match, or report the results it's ambiguous against.

    Open-Meteo already returns results in relevance order, so the top result
    is usually correct (e.g. Lisbon, Portugal beats Lisbon, Ohio). Only when
    another result is both populous and comparable in size to the top result
    do we treat the query as genuinely ambiguous, rather than silently
    picking the first match.
    """
    top = results[0]
    if len(results) == 1:
        return top, []
    top_population = top.get("population") or 0
    rivals = [top]
    for result in results[1:]:
        population = result.get("population") or 0
        if population < DISAMBIGUATION_POPULATION_FLOOR:
            continue
        if top_population and population < top_population / DISAMBIGUATION_DOMINANCE_RATIO:
            continue
        rivals.append(result)
    if len(rivals) > 1:
        return None, rivals
    return top, []


def geocode_city(city: str, timeout: float = 10.0) -> Location:
    """Resolve a city name to a Location via the Open-Meteo geocoding API.

    Accepts an optional ``"City, Region"`` form (region matching country
    code, country name, or admin1/state name) to disambiguate cities that
    share a name, e.g. ``geocode_city("Springfield, IL")``.
    """
    name, _, region = city.partition(",")
    name = name.strip()
    region = region.strip()
    if not name:
        raise CityNotFoundError(f"No location found for {city!r}")

    response = _get_with_retry(GEOCODE_URL, {"name": name, "count": 10}, timeout)
    results = _parse_json(response).get("results") or []
    if not results:
        raise CityNotFoundError(f"No location found for {city!r}")

    if region:
        results = [r for r in results if _matches_region(r, region)]
        if not results:
            raise CityNotFoundError(f"No location found for {city!r}")

    top, rivals = _pick_unambiguous(results)
    if top is None:
        raise AmbiguousCityError(name, [_to_candidate(r) for r in rivals])

    try:
        return Location(
            name=top["name"],
            country=top.get("country_code", ""),
            latitude=top["latitude"],
            longitude=top["longitude"],
        )
    except KeyError as exc:
        raise WeatherServiceError(
            f"the weather service returned an incomplete location: missing {exc}"
        ) from exc


def fetch_current_conditions(location: Location, timeout: float = 10.0) -> CurrentConditions:
    """Fetch current weather conditions for a Location via the Open-Meteo forecast API."""
    response = _get_with_retry(
        FORECAST_URL,
        {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
            "wind_speed_10m,weather_code,is_day",
        },
        timeout,
    )
    try:
        current = _parse_json(response)["current"]
        condition, description = condition_for_code(current["weather_code"])
        return CurrentConditions(
            condition=condition,
            description=description,
            temperature_c=current["temperature_2m"],
            feels_like_c=current["apparent_temperature"],
            humidity_pct=current["relative_humidity_2m"],
            wind_kph=current["wind_speed_10m"],
            is_day=bool(current.get("is_day", 1)),
            raw=current,
        )
    except KeyError as exc:
        raise WeatherServiceError(
            f"the weather service returned incomplete conditions: missing {exc}"
        ) from exc
