from ascii_weather.art import DEFAULT, get_art


def test_known_condition_returns_its_scene():
    assert get_art("rain").strip() != ""
    assert get_art("rain") != DEFAULT


def test_unknown_condition_falls_back_to_default():
    assert get_art("blizzard-of-doom") == DEFAULT
