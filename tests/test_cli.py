import json
import re

import pytest
import requests

from ascii_weather.cli import (
    _config_units,
    _normalize_units,
    _resolve_units,
    build_parser,
    main,
    render,
    render_ambiguous_city_error,
    render_json,
    should_use_color,
)
from ascii_weather.weather import (
    AmbiguousCityError,
    CityCandidate,
    CityNotFoundError,
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


def test_render_ambiguous_city_error_skips_empty_fields():
    exc = AmbiguousCityError(
        "Test",
        [CityCandidate(name="Test", country="", country_code="XX", admin1="")],
    )
    output = render_ambiguous_city_error(exc)
    assert "- Test, XX" in output
    assert ", ," not in output


def test_main_prints_friendly_message_on_city_not_found(monkeypatch, capsys):
    def fake_geocode(city):
        raise CityNotFoundError("No location found for 'Nowhereville'")

    monkeypatch.setattr("ascii_weather.cli.geocode_city", fake_geocode)

    assert main(["Nowhereville"]) == 1
    err = capsys.readouterr().err
    assert "No location found for 'Nowhereville'" in err


def test_main_prints_network_error_on_request_exception(monkeypatch, capsys):
    def fake_geocode(city):
        raise requests.ConnectionError("DNS lookup failed")

    monkeypatch.setattr("ascii_weather.cli.geocode_city", fake_geocode)

    assert main(["Lisbon"]) == 2
    err = capsys.readouterr().err
    assert "network error" in err
    assert "DNS lookup failed" in err


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


def test_main_json_flag_prints_machine_readable_output(monkeypatch, capsys):
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    conditions = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=21.0,
        feels_like_c=22.0,
        humidity_pct=58,
        wind_kph=11,
    )
    monkeypatch.setattr("ascii_weather.cli.geocode_city", lambda city: location)
    monkeypatch.setattr("ascii_weather.cli.fetch_current_conditions", lambda loc: conditions)

    assert main(["Lisbon", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["location"]["name"] == "Lisbon"
    assert out["condition"] == "clear"


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


def test_render_places_art_and_stats_side_by_side():
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
    lines = output.splitlines()
    place_line = next(line for line in lines if "Lisbon, PT" in line)
    # The art column should appear before the info column on the same line.
    assert place_line.index("Lisbon, PT") > 0


def test_render_aligns_info_column_across_rows():
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
    info_texts = ["Lisbon, PT", "Clear sky", "21°C feels like 22°C", "Humidity 58%  Wind 11 km/h"]
    columns = {line.index(text) for line, text in zip(output.splitlines(), info_texts)}
    assert len(columns) == 1


def test_render_color_does_not_break_info_column_alignment():
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    conditions = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=21.0,
        feels_like_c=22.0,
        humidity_pct=58,
        wind_kph=11,
    )
    plain = render(location, conditions, use_color=False)
    colored = render(location, conditions, use_color=True)
    stripped = re.sub(r"\033\[\d+m", "", colored)
    assert stripped == plain


def test_render_taller_art_has_no_trailing_whitespace_past_info():
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    conditions = CurrentConditions(
        condition="snow_heavy",
        description="Heavy snow",
        temperature_c=-2.0,
        feels_like_c=-5.0,
        humidity_pct=80,
        wind_kph=11,
    )
    output = render(location, conditions, use_color=False)
    lines = output.splitlines()
    # snow_heavy's art has more rows than the 4 info lines; the extra
    # art-only rows should be plain art text, not padded with trailing spaces.
    assert len(lines) > 4
    for line in lines[4:]:
        assert line == line.rstrip()


def test_render_avoids_negative_zero_temperature():
    location = Location(name="Reykjavik", country="IS", latitude=64.1, longitude=-21.9)
    conditions = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=-0.4,
        feels_like_c=-0.2,
        humidity_pct=58,
        wind_kph=11,
    )
    output = render(location, conditions, use_color=False)
    assert "-0°C" not in output
    assert "0°C feels like 0°C" in output


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


def test_should_use_color_respects_no_color_set_to_empty_string(monkeypatch):
    # Per the NO_COLOR spec, presence of the variable disables color
    # regardless of its value, including an empty string.
    monkeypatch.setenv("NO_COLOR", "")
    assert should_use_color(no_color_flag=False) is False


def test_render_json_avoids_negative_zero_temperature():
    location = Location(name="Reykjavik", country="IS", latitude=64.1, longitude=-21.9)
    conditions = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=-0.04,
        feels_like_c=-0.02,
        humidity_pct=58,
        wind_kph=11,
    )
    output = render_json(location, conditions)
    assert "-0.0" not in output
    payload = json.loads(output)
    assert payload["temperature"] == 0.0
    assert str(payload["temperature"]) == "0.0"


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


# ---------------------------------------------------------------------------
# -f / -c shorthand flags
# ---------------------------------------------------------------------------

def test_parser_fahrenheit_short_flag():
    args = build_parser().parse_args(["Lisbon", "-f"])
    assert args.fahrenheit is True
    assert args.celsius is False
    assert args.units is None


def test_parser_fahrenheit_long_flag():
    args = build_parser().parse_args(["Lisbon", "--fahrenheit"])
    assert args.fahrenheit is True


def test_parser_celsius_short_flag():
    args = build_parser().parse_args(["Lisbon", "-c"])
    assert args.celsius is True
    assert args.fahrenheit is False
    assert args.units is None


def test_parser_celsius_long_flag():
    args = build_parser().parse_args(["Lisbon", "--celsius"])
    assert args.celsius is True


def test_parser_rejects_f_and_c_together():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["Lisbon", "-f", "-c"])


def test_parser_rejects_fahrenheit_and_units_together():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["Lisbon", "-f", "--units", "metric"])


def test_parser_rejects_celsius_and_units_together():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["Lisbon", "-c", "--units", "imperial"])


# ---------------------------------------------------------------------------
# _normalize_units
# ---------------------------------------------------------------------------

def test_normalize_units_metric_aliases():
    for val in ("metric", "c", "celsius", "C", "Celsius", "METRIC"):
        assert _normalize_units(val) == "metric", val


def test_normalize_units_imperial_aliases():
    for val in ("imperial", "f", "fahrenheit", "F", "Fahrenheit", "IMPERIAL"):
        assert _normalize_units(val) == "imperial", val


def test_normalize_units_returns_none_for_unknown():
    assert _normalize_units("kelvin") is None
    assert _normalize_units("") is None
    assert _normalize_units("banana") is None


# ---------------------------------------------------------------------------
# _config_units
# ---------------------------------------------------------------------------

def test_config_units_reads_metric_aliases(tmp_path):
    for alias in ("c", "celsius", "metric"):
        cfg = tmp_path / "config"
        cfg.write_text(f"[defaults]\nunits = {alias}\n")
        assert _config_units(cfg) == "metric", alias


def test_config_units_reads_imperial_aliases(tmp_path):
    for alias in ("f", "fahrenheit", "imperial"):
        cfg = tmp_path / "config"
        cfg.write_text(f"[defaults]\nunits = {alias}\n")
        assert _config_units(cfg) == "imperial", alias


def test_config_units_returns_none_for_missing_file(tmp_path):
    assert _config_units(tmp_path / "nonexistent") is None


def test_config_units_returns_none_for_unrecognized_value(tmp_path):
    cfg = tmp_path / "config"
    cfg.write_text("[defaults]\nunits = kelvin\n")
    assert _config_units(cfg) is None


def test_config_units_returns_none_when_key_absent(tmp_path):
    cfg = tmp_path / "config"
    cfg.write_text("[defaults]\n")
    assert _config_units(cfg) is None


# ---------------------------------------------------------------------------
# _resolve_units — priority stack
# ---------------------------------------------------------------------------

def test_resolve_units_fahrenheit_flag_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("ASCII_WEATHER_UNITS", "c")
    args = build_parser().parse_args(["Lisbon", "-f"])
    assert _resolve_units(args, tmp_path / "none") == "imperial"


def test_resolve_units_celsius_flag_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("ASCII_WEATHER_UNITS", "f")
    args = build_parser().parse_args(["Lisbon", "-c"])
    assert _resolve_units(args, tmp_path / "none") == "metric"


def test_resolve_units_units_flag_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("ASCII_WEATHER_UNITS", "c")
    args = build_parser().parse_args(["Lisbon", "--units", "imperial"])
    assert _resolve_units(args, tmp_path / "none") == "imperial"


def test_resolve_units_env_var_metric(monkeypatch, tmp_path):
    monkeypatch.setenv("ASCII_WEATHER_UNITS", "celsius")
    args = build_parser().parse_args(["Lisbon"])
    assert _resolve_units(args, tmp_path / "none") == "metric"


def test_resolve_units_env_var_imperial(monkeypatch, tmp_path):
    monkeypatch.setenv("ASCII_WEATHER_UNITS", "fahrenheit")
    args = build_parser().parse_args(["Lisbon"])
    assert _resolve_units(args, tmp_path / "none") == "imperial"


def test_resolve_units_env_var_short_f(monkeypatch, tmp_path):
    monkeypatch.setenv("ASCII_WEATHER_UNITS", "f")
    args = build_parser().parse_args(["Lisbon"])
    assert _resolve_units(args, tmp_path / "none") == "imperial"


def test_resolve_units_env_var_ignores_unknown_falls_to_default(monkeypatch, tmp_path):
    monkeypatch.setenv("ASCII_WEATHER_UNITS", "kelvin")
    args = build_parser().parse_args(["Lisbon"])
    assert _resolve_units(args, tmp_path / "none") == "metric"


def test_resolve_units_config_file(monkeypatch, tmp_path):
    monkeypatch.delenv("ASCII_WEATHER_UNITS", raising=False)
    cfg = tmp_path / "config"
    cfg.write_text("[defaults]\nunits = f\n")
    args = build_parser().parse_args(["Lisbon"])
    assert _resolve_units(args, cfg) == "imperial"


def test_resolve_units_flag_beats_config_file(monkeypatch, tmp_path):
    monkeypatch.delenv("ASCII_WEATHER_UNITS", raising=False)
    cfg = tmp_path / "config"
    cfg.write_text("[defaults]\nunits = f\n")
    args = build_parser().parse_args(["Lisbon", "-c"])
    assert _resolve_units(args, cfg) == "metric"


def test_resolve_units_env_beats_config_file(monkeypatch, tmp_path):
    monkeypatch.setenv("ASCII_WEATHER_UNITS", "c")
    cfg = tmp_path / "config"
    cfg.write_text("[defaults]\nunits = f\n")
    args = build_parser().parse_args(["Lisbon"])
    assert _resolve_units(args, cfg) == "metric"


def test_resolve_units_default_is_metric(monkeypatch, tmp_path):
    monkeypatch.delenv("ASCII_WEATHER_UNITS", raising=False)
    args = build_parser().parse_args(["Lisbon"])
    assert _resolve_units(args, tmp_path / "none") == "metric"


# ---------------------------------------------------------------------------
# main() integration with -f / -c
# ---------------------------------------------------------------------------

def _stub(location, conditions):
    """Helper: patch geocode + fetch so main() doesn't hit the network."""
    return location, conditions


def test_main_fahrenheit_flag_renders_imperial(monkeypatch, capsys):
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    conditions = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=0.0,
        feels_like_c=0.0,
        humidity_pct=58,
        wind_kph=100,
    )
    monkeypatch.setattr("ascii_weather.cli.geocode_city", lambda city: location)
    monkeypatch.setattr("ascii_weather.cli.fetch_current_conditions", lambda loc: conditions)
    assert main(["Lisbon", "-f"]) == 0
    out = capsys.readouterr().out
    assert "32°F" in out
    assert "mph" in out
    assert "°C" not in out


def test_main_celsius_flag_renders_metric(monkeypatch, capsys):
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    conditions = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=21.0,
        feels_like_c=22.0,
        humidity_pct=58,
        wind_kph=11,
    )
    monkeypatch.setattr("ascii_weather.cli.geocode_city", lambda city: location)
    monkeypatch.setattr("ascii_weather.cli.fetch_current_conditions", lambda loc: conditions)
    assert main(["Lisbon", "-c"]) == 0
    out = capsys.readouterr().out
    assert "°C" in out
    assert "km/h" in out
    assert "°F" not in out


def test_main_json_uses_fahrenheit_flag(monkeypatch, capsys):
    location = Location(name="Lisbon", country="PT", latitude=38.7, longitude=-9.1)
    conditions = CurrentConditions(
        condition="clear",
        description="Clear sky",
        temperature_c=0.0,
        feels_like_c=0.0,
        humidity_pct=58,
        wind_kph=100,
    )
    monkeypatch.setattr("ascii_weather.cli.geocode_city", lambda city: location)
    monkeypatch.setattr("ascii_weather.cli.fetch_current_conditions", lambda loc: conditions)
    assert main(["Lisbon", "-f", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["units"] == "imperial"
    assert payload["temperature"] == 32.0
