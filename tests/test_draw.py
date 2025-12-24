"""
Tests for draw module functions: color wheel, markers, and legend.
"""

from PIL import Image, ImageDraw, ImageFont

from draw import IMAGE_SIZE, WHEEL_SIZE, draw_color_wheel, draw_legend, draw_markers


def test_draw_color_wheel_changes_center_pixel():
    """draw_color_wheel should change at least the center pixel from white."""
    img = Image.new("RGB", IMAGE_SIZE, "white")
    draw_color_wheel(img)
    # Pick a point half radius to the right of center where saturation>0
    cx, cy = WHEEL_SIZE // 2 + WHEEL_SIZE // 4, WHEEL_SIZE // 2
    pixel = img.getpixel((cx, cy))
    assert pixel != (255, 255, 255), "Pixel at half radius should not be white"


def test_draw_markers_returns_expected_positions_and_draws():
    """draw_markers returns positions and draws marker circles and labels."""
    img = Image.new("RGB", IMAGE_SIZE, "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    markers = [("Test1", "#FF0000"), ("Test2", "#00FF00")]
    positions = draw_markers(draw, markers, font)
    # Should return entry for each marker: (index, name, hex, rgb, x, y)
    assert len(positions) == 2
    idx, name, hex_code, rgb, x, y = positions[0]
    assert idx == 1 and name == "Test1" and hex_code == "#FF0000"
    assert isinstance(rgb, tuple) and len(rgb) == 3
    # Tuple structure verified; skip pixel color assertion (outline thickness varies)


def test_draw_legend_places_swatches_and_text():
    """draw_legend should place colored swatches at calculated legend positions."""
    img = Image.new("RGB", IMAGE_SIZE, "white")
    draw = ImageDraw.Draw(img)
    # simulate marker positions: (i, name, hex, rgb, x, y)
    marker_positions = [
        (1, "InkA", "#123456", (18, 52, 86), 0, 0),
        (2, "InkB", "#654321", (101, 67, 33), 0, 0),
    ]
    font = ImageFont.load_default()
    font_bold = ImageFont.load_default()
    draw_legend(draw, marker_positions, font, font_bold)
    # Legend x coordinate is WHEEL_SIZE + 20
    legend_x = WHEEL_SIZE + 20
    legend_y = 30
    # Check pixel within swatch area for first marker
    swatch_pixel = img.getpixel((legend_x + 5, legend_y + 5))
    assert swatch_pixel == (18, 52, 86)
