from ascii_weather.weather import condition_for_code


def test_clear_sky_code():
    assert condition_for_code(0) == ("clear", "Clear sky")


def test_thunderstorm_code():
    condition, description = condition_for_code(95)
    assert condition == "thunderstorm"
    assert "Thunderstorm" in description


def test_unknown_code_falls_back():
    condition, description = condition_for_code(-1)
    assert condition == "unknown"
