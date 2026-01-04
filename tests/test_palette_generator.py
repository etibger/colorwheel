import pytest

import palette_generator as pg


def test_hex_rgb_roundtrip():
    hex_color = "#1a2b3c"
    rgb = pg.hex_to_rgb(hex_color)
    assert isinstance(rgb, tuple) and len(rgb) == 3
    hex_out = pg.rgb_to_hex(rgb)
    # hex_to_rgb and rgb_to_hex should round-trip to same normalized hex
    assert hex_out.lower() == hex_color


def test_hsl_rgb_roundtrip():
    rgb = (0.2, 0.6, 0.4)
    hsl = pg.rgb_to_hsl(rgb)
    rgb_out = pg.hsl_to_rgb(hsl)
    # Values should match approximately
    for a, b in zip(rgb, rgb_out):
        assert pytest.approx(a, rel=1e-3, abs=1e-3) == b


def test_tetradic_red():
    # Tetradic of red should include red, yellow, cyan, blue
    palette = pg.tetradic("#ff0000")
    expected = ["#ff0000", "#ffff00", "#00ffff", "#0000ff"]
    assert palette == expected


def test_two_warm_two_cool():
    colors = ["#ff0000", "#ffff00", "#0000ff", "#00ffff", "#00ff00"]
    result = pg.two_warm_two_cool(colors)
    # two warms first, two cools next
    assert result == ["#ff0000", "#ffff00", "#0000ff", "#00ffff"]


def test_dominant_temperature_contrast():
    # More warm than cool
    colors = ["#ff0000", "#ffff00", "#00ff00", "#0000ff"]
    result = pg.dominant_temperature_contrast(colors)
    # warm are ['#ff0000','#ffff00','#00ff00'] -> dominant
    assert result[:2] == ["#ff0000", "#ffff00"]
    assert result[2:] == ["#0000ff", "#00ff00"] or result[2:] == ["#0000ff", "#00ff00"]


def test_value_ladder_accent_greys():
    # Four greys with increasing lightness
    colors = ["#000000", "#555555", "#aaaaaa", "#ffffff"]
    palette = pg.value_ladder_accent(colors)
    assert palette == ["#000000", "#555555", "#aaaaaa", "#ffffff"]


def test_oklab_roundtrip():
    rgb = (0.5, 0.2, 0.7)
    oklab = pg.rgb_to_oklab(rgb)
    rgb_out = pg.oklab_to_rgb(oklab)
    # round-trip within tolerance
    for a, b in zip(rgb, rgb_out):
        assert pytest.approx(a, rel=1e-3, abs=1e-3) == b


def test_oklch_sampling_length_unique():
    palette = pg.oklch_sampling("#ff0000")
    assert isinstance(palette, list) and len(palette) == 4
    # All entries should be distinct hex strings
    assert len(set(palette)) == 4


def test_split_complementary_accent_properties():
    palette = pg.split_complementary_accent("#00ff00")
    assert isinstance(palette, list) and len(palette) == 4
    # base color should be first
    assert palette[0] == "#00ff00"


def test_square_scheme_properties():
    palette = pg.square_scheme("#0000ff")
    assert isinstance(palette, list) and len(palette) == 4
    assert palette[0] == "#0000ff"
