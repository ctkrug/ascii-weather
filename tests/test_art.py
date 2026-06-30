from ascii_weather.art import (
    CLEAR,
    CLEAR_NIGHT,
    DEFAULT,
    RAIN,
    RAIN_HEAVY,
    RAIN_LIGHT,
    WINDY,
    get_art,
)


def test_known_condition_returns_its_scene():
    assert get_art("rain").strip() != ""
    assert get_art("rain") != DEFAULT


def test_unknown_condition_falls_back_to_default():
    assert get_art("blizzard-of-doom") == DEFAULT


def test_rain_intensity_has_distinct_scenes():
    assert get_art("rain_light") == RAIN_LIGHT
    assert get_art("rain") == RAIN
    assert get_art("rain_heavy") == RAIN_HEAVY
    assert len({RAIN_LIGHT, RAIN, RAIN_HEAVY}) == 3


def test_clear_uses_night_variant_after_dark():
    assert get_art("clear", is_day=True) == CLEAR
    assert get_art("clear", is_day=False) == CLEAR_NIGHT


def test_rain_has_no_night_variant():
    assert get_art("rain", is_day=False) == RAIN


def test_windy_overrides_clear_scene():
    assert get_art("clear", windy=True) == WINDY


def test_windy_does_not_override_rain_scene():
    assert get_art("rain", windy=True) == RAIN
