import json

import pytest

from ascii_weather.cli import build_parser, main, render, render_json, should_use_color
from ascii_weather.weather import (
    AmbiguousCityError,
    CityCandidate,
    CurrentConditions,
    Location,
    WeatherServiceError,
)


def test_parser_requires_city():
    parser = build_parser()
    args = parser.parse_args(["Lisbon"])
    assert args.city == "Lisbon"


def test_parser_allows_omitted_city():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.city is None


def test_main_errors_without_city_or_env_var(monkeypatch, capsys):
    monkeypatch.delenv("ASCII_WEATHER_CITY", raising=False)
    with pytest.raises(SystemExit):
        main([])
    assert "ASCII_WEATHER_CITY" in capsys.readouterr().err


def test_main_prints_friendly_message_on_weather_service_error(monkeypatch, capsys):
    def fake_geocode(city):
        raise WeatherServiceError("could not reach the weather service after 3 attempts: boom")

    monkeypatch.setattr("ascii_weather.cli.geocode_city", fake_geocode)

    assert main(["Lisbon"]) == 2
    err = capsys.readouterr().err
    assert "couldn't reach the weather service" in err


def test_main_prints_disambiguation_prompt_on_ambiguous_city(monkeypatch, capsys):
    def fake_geocode(city):
        raise AmbiguousCityError(
            "Springfield",
            [
                CityCandidate(name="Springfield", country="United States", country_code="US",
                               admin1="Missouri"),
                CityCandidate(name="Springfield", country="United States", country_code="US",
                               admin1="Illinois"),
            ],
        )

    monkeypatch.setattr("ascii_weather.cli.geocode_city", fake_geocode)

    assert main(["Springfield"]) == 1
    err = capsys.readouterr().err
    assert "multiple locations" in err
    assert "Missouri" in err
    assert "Illinois" in err


def test_main_verbose_prints_coordinates_and_raw_response(monkeypatch, capsys):
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    conditions = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=21.0,
        feels_like_c=22.0,
        humidity_pct=58,
        wind_kph=11,
        raw={"weather_code": 0},
    )
    monkeypatch.setattr("ascii_weather.cli.geocode_city", lambda city: location)
    monkeypatch.setattr("ascii_weather.cli.fetch_current_conditions", lambda loc: conditions)

    assert main(["Lisbon", "-v"]) == 0
    err = capsys.readouterr().err
    assert "38.7" in err
    assert "weather_code" in err


def test_main_uses_env_var_city_when_omitted(monkeypatch):
    monkeypatch.setenv("ASCII_WEATHER_CITY", "Lisbon")

    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    conditions = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=21.0,
        feels_like_c=22.0,
        humidity_pct=58,
        wind_kph=11,
    )
    seen_city = {}

    def fake_geocode(city):
        seen_city["city"] = city
        return location

    monkeypatch.setattr("ascii_weather.cli.geocode_city", fake_geocode)
    monkeypatch.setattr("ascii_weather.cli.fetch_current_conditions", lambda loc: conditions)

    assert main([]) == 0
    assert seen_city["city"] == "Lisbon"


def test_render_includes_place_and_temperature():
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    conditions = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=21.0,
        feels_like_c=22.0,
        humidity_pct=58,
        wind_kph=11,
    )
    output = render(location, conditions)
    assert "Lisbon, PT" in output
    assert "Clear sky" in output
    assert "21°C" in output


def test_render_imperial_units_converts_temperature_and_wind():
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    conditions = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=0.0,
        feels_like_c=0.0,
        humidity_pct=58,
        wind_kph=100,
    )
    output = render(location, conditions, units="imperial")
    assert "32°F" in output
    assert "62 mph" in output
    assert "°C" not in output


def test_parser_accepts_units_flag():
    parser = build_parser()
    args = parser.parse_args(["Lisbon", "--units", "imperial"])
    assert args.units == "imperial"


def test_render_without_color_has_no_ansi_codes():
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    conditions = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=21.0,
        feels_like_c=22.0,
        humidity_pct=58,
        wind_kph=11,
    )
    output = render(location, conditions, use_color=False)
    assert "\033[" not in output


def test_should_use_color_respects_no_color_flag(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert should_use_color(no_color_flag=True) is False


def test_should_use_color_respects_no_color_env_var(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    assert should_use_color(no_color_flag=False) is False


def test_render_json_produces_parseable_payload():
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    conditions = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=21.0,
        feels_like_c=22.0,
        humidity_pct=58,
        wind_kph=11,
    )
    payload = json.loads(render_json(location, conditions))
    assert payload["location"]["name"] == "Lisbon"
    assert payload["condition"] == "clear"
    assert payload["temperature"] == 21.0


def test_render_uses_windy_scene_above_threshold():
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    calm = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=21.0,
        feels_like_c=22.0,
        humidity_pct=58,
        wind_kph=11,
    )
    gusty = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=21.0,
        feels_like_c=22.0,
        humidity_pct=58,
        wind_kph=45,
    )
    assert render(location, calm, use_color=False) != render(location, gusty, use_color=False)


def test_render_uses_night_art_when_not_daytime():
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    day = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=21.0,
        feels_like_c=22.0,
        humidity_pct=58,
        wind_kph=11,
        is_day=True,
    )
    night = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=21.0,
        feels_like_c=22.0,
        humidity_pct=58,
        wind_kph=11,
        is_day=False,
    )
    assert render(location, day, use_color=False) != render(location, night, use_color=False)


def test_render_json_includes_is_day_and_windy():
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    conditions = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=21.0,
        feels_like_c=22.0,
        humidity_pct=58,
        wind_kph=45,
        is_day=False,
    )
    payload = json.loads(render_json(location, conditions))
    assert payload["is_day"] is False
    assert payload["windy"] is True


def test_render_json_converts_units_when_imperial():
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    conditions = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=0.0,
        feels_like_c=0.0,
        humidity_pct=58,
        wind_kph=100,
    )
    payload = json.loads(render_json(location, conditions, units="imperial"))
    assert payload["temperature"] == 32.0
    assert payload["units"] == "imperial"
