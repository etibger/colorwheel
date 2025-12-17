"""
Module for drawing the color wheel, markers, and legend.
"""

import colorsys
import math
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

from color_utils import hex_to_rgb, hsv_to_xy, rgb_to_hsv

# Configuration constants
WHEEL_SIZE: int = 600
LEGEND_WIDTH: int = 260
IMAGE_SIZE: Tuple[int, int] = (WHEEL_SIZE + LEGEND_WIDTH, WHEEL_SIZE)
RADIUS: int = WHEEL_SIZE // 2
CENTER: Tuple[int, int] = (RADIUS, RADIUS)
MARKER_RADIUS: int = 6
HEX_COLORS: List[Tuple[str, str]] = [
    ("Red", "#FF0000"),
    ("Green", "#00FF00"),
    ("Blue", "#0000FF"),
    ("Yellow", "#FFFF00"),
    ("Magenta", "#FF00FF"),
    ("Cyan", "#00FFFF"),
]


def draw_color_wheel(img: Image.Image) -> None:
    """Draw the color wheel background on the image."""
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
    """Draw markers and number labels, return positions."""
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
    """Draw the legend for the markers."""
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
