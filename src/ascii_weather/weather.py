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


def geocode_city(city: str, timeout: float = 10.0) -> Location:
    """Resolve a city name to a Location via the Open-Meteo geocoding API."""
    response = _get_with_retry(GEOCODE_URL, {"name": city, "count": 1}, timeout)
    results = response.json().get("results") or []
    if not results:
        raise CityNotFoundError(f"No location found for {city!r}")
    top = results[0]
    return Location(
        name=top["name"],
        country=top.get("country_code", ""),
        latitude=top["latitude"],
        longitude=top["longitude"],
    )


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
    current = response.json()["current"]
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
