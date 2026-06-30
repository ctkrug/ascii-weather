from ascii_weather.colors import color_for_condition, colorize


def test_color_for_condition_day_uses_bright_palette():
    assert color_for_condition("clear", is_day=True) == "bright_yellow"


def test_color_for_condition_night_uses_dimmer_palette():
    assert color_for_condition("clear", is_day=False) == "white"
    assert color_for_condition("clear", is_day=True) != color_for_condition(
        "clear", is_day=False
    )


def test_color_for_unknown_condition_falls_back():
    assert color_for_condition("blizzard-of-doom", is_day=True) == "bright_white"
    assert color_for_condition("blizzard-of-doom", is_day=False) == "grey"


def test_colorize_wraps_text_in_ansi_codes():
    result = colorize("hi", "bright_yellow")
    assert result.startswith("\033[93m")
    assert result.endswith("\033[0m")


def test_colorize_unknown_color_returns_text_unchanged():
    assert colorize("hi", "not-a-color") == "hi"
