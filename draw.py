"""
.. module:: draw
   :noindex:
   :synopsis: Draw color wheel, markers, and legend.

This module provides functions to render a color wheel, annotate markers,
and create a legend in the generated image.
"""

import colorsys
import math
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

from color_utils import hex_to_rgb, hsv_to_xy, rgb_to_hsv
from config_loader import load_config

CONFIG = load_config()
# Configuration constants loaded from config
WHEEL_SIZE: int = int(CONFIG["wheel_size"])
LEGEND_WIDTH: int = int(CONFIG["legend_width"])
IMAGE_SIZE: Tuple[int, int] = (WHEEL_SIZE + LEGEND_WIDTH, WHEEL_SIZE)
RADIUS: int = WHEEL_SIZE // 2
CENTER: Tuple[int, int] = (RADIUS, RADIUS)
MARKER_RADIUS: int = int(CONFIG["marker_radius"])
HEX_COLORS: List[Tuple[str, str]] = [
    ("Red", "#FF0000"),
    ("Green", "#00FF00"),
    ("Blue", "#0000FF"),
    ("Yellow", "#FFFF00"),
    ("Magenta", "#FF00FF"),
    ("Cyan", "#00FFFF"),
]


def draw_color_wheel(img: Image.Image) -> None:
    """
    Draw the color wheel background on the provided image.

    :param img: PIL Image instance (mode 'RGB') to render the wheel onto.
    :type img: PIL.Image.Image
    :returns: None
    """
    pixels = img.load()
    for y in range(WHEEL_SIZE):
        for x in range(WHEEL_SIZE):
            dx = x - CENTER[0]
            dy = y - CENTER[1]
            distance = math.hypot(dx, dy)

            if distance <= RADIUS:
                saturation = distance / RADIUS
                hue = (math.atan2(dy, dx) / (2 * math.pi)) % 1.0
                r, g, b = colorsys.hsv_to_rgb(hue, saturation, 1.0)
                pixels[x, y] = (int(r * 255), int(g * 255), int(b * 255))


def draw_markers(
    draw: ImageDraw.ImageDraw,
    marker_colors: List[Tuple[str, str]],
    font_bold: ImageFont.ImageFont,
) -> List[Tuple[int, str, str, Tuple[int, int, int], int, int]]:
    """
    Draw numbered markers on the color wheel and return their data.

    :param draw: Pillow ImageDraw object used to draw shapes and text.
    :type draw: PIL.ImageDraw.ImageDraw
    :param marker_colors: List of (name, hex_color) tuples for each marker.
    :type marker_colors: list[tuple[str, str]]
    :param font_bold: PIL ImageFont for drawing bold labels.
    :type font_bold: PIL.ImageFont.ImageFont
    :returns: List of tuples (index, name, hex_color, rgb_tuple, x, y).
    :rtype: list[tuple[int, str, str, tuple[int,int,int], int, int]]
    """
    marker_positions: List[Tuple[int, str, str, Tuple[int, int, int], int, int]] = []
    for idx, (name, hex_color) in enumerate(marker_colors, start=1):
        rgb = hex_to_rgb(hex_color)
        h, s, _ = rgb_to_hsv(rgb)
        x, y = hsv_to_xy(h, s, RADIUS, CENTER)
        marker_positions.append((idx, name, hex_color, rgb, x, y))

        draw.ellipse(
            (
                x - MARKER_RADIUS,
                y - MARKER_RADIUS,
                x + MARKER_RADIUS,
                y + MARKER_RADIUS,
            ),
            outline="black",
            width=2,
        )
        draw.text(
            (x + MARKER_RADIUS + 4, y - MARKER_RADIUS - 4),
            str(idx),
            fill="black",
            font=font_bold,
        )
    return marker_positions


def draw_legend(
    draw: ImageDraw.ImageDraw,
    marker_positions: List[Tuple[int, str, str, Tuple[int, int, int], int, int]],
    font: ImageFont.ImageFont,
    font_bold: ImageFont.ImageFont,
) -> None:
    """
    Draw a legend panel showing marker swatches and labels.

    :param draw: Pillow ImageDraw object used to draw shapes and text.
    :type draw: PIL.ImageDraw.ImageDraw
    :param marker_positions: List of marker data from draw_markers.
    :type marker_positions: list[tuple[int, str, str, tuple[int,int,int], int, int]]
    :param font: PIL ImageFont for regular text.
    :type font: PIL.ImageFont.ImageFont
    :param font_bold: PIL ImageFont for bold headings.
    :type font_bold: PIL.ImageFont.ImageFont
    :returns: None
    """
    legend_x = WHEEL_SIZE + 20
    legend_y = 30
    line_height = 30

    draw.text((legend_x, legend_y - 25), "Ink Names", fill="black", font=font_bold)
    for i, name, _, rgb, _, _ in marker_positions:
        y_pos = legend_y + (i - 1) * line_height

        draw.rectangle(
            (legend_x, y_pos, legend_x + 20, y_pos + 20), fill=rgb, outline="black"
        )
        draw.text(
            (legend_x + 30, y_pos),
            f"{i} : {name}",
            fill="black",
            font=font,
        )
