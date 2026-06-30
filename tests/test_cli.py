from ascii_weather.cli import build_parser, render
from ascii_weather.weather import CurrentConditions, Location


def test_parser_requires_city():
    parser = build_parser()
    args = parser.parse_args(["Lisbon"])
    assert args.city == "Lisbon"


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
