import requests

from ascii_weather.weather import (
    WeatherServiceError,
    _get_with_retry,
    celsius_to_fahrenheit,
    condition_for_code,
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


def test_celsius_to_fahrenheit():
    assert celsius_to_fahrenheit(0) == 32
    assert celsius_to_fahrenheit(100) == 212


def test_kph_to_mph():
    assert round(kph_to_mph(100), 2) == 62.14


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
