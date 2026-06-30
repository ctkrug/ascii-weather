from ascii_weather.weather import celsius_to_fahrenheit, condition_for_code, kph_to_mph


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
