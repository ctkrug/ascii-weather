import requests

from ascii_weather.weather import (
    AmbiguousCityError,
    CityNotFoundError,
    Location,
    WeatherServiceError,
    _get_with_retry,
    celsius_to_fahrenheit,
    condition_for_code,
    fetch_current_conditions,
    geocode_city,
    is_windy,
    kph_to_mph,
)


def test_clear_sky_code():
    assert condition_for_code(0) == ("clear", "Clear sky")


def test_thunderstorm_code():
    condition, description = condition_for_code(95)
    assert condition == "thunderstorm"
    assert "Thunderstorm" in description


def test_unknown_code_falls_back():
    condition, description = condition_for_code(-1)
    assert condition == "unknown"


def test_rain_intensity_distinguishes_light_normal_heavy():
    assert condition_for_code(51)[0] == "rain_light"
    assert condition_for_code(63)[0] == "rain"
    assert condition_for_code(65)[0] == "rain_heavy"


def test_snow_intensity_distinguishes_light_normal_heavy():
    assert condition_for_code(71)[0] == "snow_light"
    assert condition_for_code(73)[0] == "snow"
    assert condition_for_code(75)[0] == "snow_heavy"


def test_celsius_to_fahrenheit():
    assert celsius_to_fahrenheit(0) == 32
    assert celsius_to_fahrenheit(100) == 212


def test_kph_to_mph():
    assert round(kph_to_mph(100), 2) == 62.14


def test_is_windy_below_threshold():
    assert is_windy(10.0) is False


def test_is_windy_above_threshold():
    assert is_windy(45.0) is True


class _FakeResponse:
    def raise_for_status(self):
        pass


def test_get_with_retry_succeeds_after_transient_failures(monkeypatch):
    monkeypatch.setattr("ascii_weather.weather.time.sleep", lambda _: None)
    calls = {"count": 0}

    def fake_get(url, params, timeout):
        calls["count"] += 1
        if calls["count"] < 3:
            raise requests.ConnectionError("boom")
        return _FakeResponse()

    monkeypatch.setattr("ascii_weather.weather.requests.get", fake_get)
    response = _get_with_retry("http://example.com", {}, 10.0, retries=2)
    assert isinstance(response, _FakeResponse)
    assert calls["count"] == 3


def test_get_with_retry_raises_friendly_error_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr("ascii_weather.weather.time.sleep", lambda _: None)

    def always_fails(url, params, timeout):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr("ascii_weather.weather.requests.get", always_fails)
    try:
        _get_with_retry("http://example.com", {}, 10.0, retries=2)
        assert False, "expected WeatherServiceError"
    except WeatherServiceError as exc:
        assert "3 attempts" in str(exc)


class _FakeForecastResponse:
    def __init__(self, is_day):
        self._is_day = is_day

    def raise_for_status(self):
        pass

    def json(self):
        return {
            "current": {
                "temperature_2m": 10.0,
                "apparent_temperature": 8.0,
                "relative_humidity_2m": 50,
                "wind_speed_10m": 5.0,
                "weather_code": 0,
                "is_day": self._is_day,
            }
        }


def test_fetch_current_conditions_parses_is_day_true(monkeypatch):
    monkeypatch.setattr(
        "ascii_weather.weather.requests.get",
        lambda url, params, timeout: _FakeForecastResponse(1),
    )
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    conditions = fetch_current_conditions(location)
    assert conditions.is_day is True


def test_fetch_current_conditions_parses_is_day_false(monkeypatch):
    monkeypatch.setattr(
        "ascii_weather.weather.requests.get",
        lambda url, params, timeout: _FakeForecastResponse(0),
    )
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    conditions = fetch_current_conditions(location)
    assert conditions.is_day is False


class _FakeGeocodeResponse:
    def __init__(self, results):
        self._results = results

    def raise_for_status(self):
        pass

    def json(self):
        return {"results": self._results}


def _geocode_result(name, country, country_code, admin1, population, lat=0.0, lon=0.0):
    return {
        "name": name,
        "country": country,
        "country_code": country_code,
        "admin1": admin1,
        "population": population,
        "latitude": lat,
        "longitude": lon,
    }


def test_geocode_city_picks_dominant_result_unambiguously(monkeypatch):
    results = [
        _geocode_result("Lisbon", "Portugal", "PT", "Lisbon District", 517802),
        _geocode_result("Lisbon", "United States", "US", "Ohio", 2727),
    ]
    monkeypatch.setattr(
        "ascii_weather.weather.requests.get",
        lambda url, params, timeout: _FakeGeocodeResponse(results),
    )
    location = geocode_city("Lisbon")
    assert location.country == "PT"


def test_geocode_city_raises_ambiguous_for_comparable_results(monkeypatch):
    results = [
        _geocode_result("Springfield", "United States", "US", "Missouri", 170188),
        _geocode_result("Springfield", "United States", "US", "Illinois", 114394),
    ]
    monkeypatch.setattr(
        "ascii_weather.weather.requests.get",
        lambda url, params, timeout: _FakeGeocodeResponse(results),
    )
    try:
        geocode_city("Springfield")
        assert False, "expected AmbiguousCityError"
    except AmbiguousCityError as exc:
        admin1s = {c.admin1 for c in exc.candidates}
        assert admin1s == {"Missouri", "Illinois"}


def test_geocode_city_region_suffix_disambiguates(monkeypatch):
    results = [
        _geocode_result("Springfield", "United States", "US", "Missouri", 170188),
        _geocode_result("Springfield", "United States", "US", "Illinois", 114394),
    ]
    monkeypatch.setattr(
        "ascii_weather.weather.requests.get",
        lambda url, params, timeout: _FakeGeocodeResponse(results),
    )
    location = geocode_city("Springfield, Illinois")
    assert location.country == "US"


def test_geocode_city_region_suffix_with_no_match_raises_not_found(monkeypatch):
    results = [
        _geocode_result("Springfield", "United States", "US", "Missouri", 170188),
    ]
    monkeypatch.setattr(
        "ascii_weather.weather.requests.get",
        lambda url, params, timeout: _FakeGeocodeResponse(results),
    )
    try:
        geocode_city("Springfield, Germany")
        assert False, "expected CityNotFoundError"
    except CityNotFoundError:
        pass


def test_geocode_city_raises_not_found_when_no_results(monkeypatch):
    monkeypatch.setattr(
        "ascii_weather.weather.requests.get",
        lambda url, params, timeout: _FakeGeocodeResponse([]),
    )
    try:
        geocode_city("Nowhereville")
        assert False, "expected CityNotFoundError"
    except CityNotFoundError:
        pass
