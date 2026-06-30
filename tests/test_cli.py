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
