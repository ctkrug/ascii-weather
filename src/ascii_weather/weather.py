"""Fetch city coordinates and current conditions from the Open-Meteo public API.

No API key is required: https://open-meteo.com/
"""

from dataclasses import dataclass

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes -> (condition key, human description)
WMO_CODES = {
    0: ("clear", "Clear sky"),
    1: ("clear", "Mainly clear"),
    2: ("partly_cloudy", "Partly cloudy"),
    3: ("cloudy", "Overcast"),
    45: ("fog", "Fog"),
    48: ("fog", "Depositing rime fog"),
    51: ("rain", "Light drizzle"),
    53: ("rain", "Drizzle"),
    55: ("rain", "Dense drizzle"),
    56: ("rain", "Freezing drizzle"),
    57: ("rain", "Dense freezing drizzle"),
    61: ("rain", "Slight rain"),
    63: ("rain", "Rain"),
    65: ("rain", "Heavy rain"),
    66: ("rain", "Freezing rain"),
    67: ("rain", "Heavy freezing rain"),
    71: ("snow", "Slight snow fall"),
    73: ("snow", "Snow fall"),
    75: ("snow", "Heavy snow fall"),
    77: ("snow", "Snow grains"),
    80: ("rain", "Slight rain showers"),
    81: ("rain", "Rain showers"),
    82: ("rain", "Violent rain showers"),
    85: ("snow", "Slight snow showers"),
    86: ("snow", "Heavy snow showers"),
    95: ("thunderstorm", "Thunderstorm"),
    96: ("thunderstorm", "Thunderstorm with hail"),
    99: ("thunderstorm", "Thunderstorm with heavy hail"),
}


class CityNotFoundError(Exception):
    """Raised when the geocoding API has no match for the given city name."""


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


def condition_for_code(code: int) -> tuple[str, str]:
    """Map a WMO weather code to a (condition key, description) pair."""
    return WMO_CODES.get(code, ("unknown", "Unknown"))


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert a Celsius temperature to Fahrenheit."""
    return celsius * 9 / 5 + 32


def kph_to_mph(kph: float) -> float:
    """Convert a speed in kilometers per hour to miles per hour."""
    return kph * 0.621371


def geocode_city(city: str, timeout: float = 10.0) -> Location:
    """Resolve a city name to a Location via the Open-Meteo geocoding API."""
    response = requests.get(
        GEOCODE_URL, params={"name": city, "count": 1}, timeout=timeout
    )
    response.raise_for_status()
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
    response = requests.get(
        FORECAST_URL,
        params={
            "latitude": location.latitude,
            "longitude": location.longitude,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
            "wind_speed_10m,weather_code",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    current = response.json()["current"]
    condition, description = condition_for_code(current["weather_code"])
    return CurrentConditions(
        condition=condition,
        description=description,
        temperature_c=current["temperature_2m"],
        feels_like_c=current["apparent_temperature"],
        humidity_pct=current["relative_humidity_2m"],
        wind_kph=current["wind_speed_10m"],
    )
