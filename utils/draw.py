"""
.. module:: utils.draw
   :noindex:
   :synopsis: Draw color wheel, markers, and legend.

This module provides functions to render a color wheel, annotate markers,
and create a legend in the generated image.
"""

import colorsys
import math
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

from utils.color_utils import hex_to_rgb, hsv_to_xy, rgb_to_hsv
from config.config_loader import load_config

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
    marker_colors: List[Tuple[str, str] | Tuple[str, str, str]],
    font_bold: ImageFont.ImageFont,
) -> List[Tuple[int, str, str, Tuple[int, int, int], int, int, str]]:
    """
    Draw marker glyphs on the wheel and capture their metadata.

    Each entry in ``marker_colors`` may optionally supply a marker type
    (``\"circle\"`` for palette colors or ``\"cross\"`` for alternates). When the
    style is omitted the function renders a circle to remain backward compatible.
    Labels are drawn next to the marker: ``N`` for circles and ``Nx`` for crosses.

    :param draw: Pillow ImageDraw surface used to render markers.
    :type draw: PIL.ImageDraw.ImageDraw
    :param marker_colors: Tuples of ``(name, hex[, marker_type])`` to place on the wheel.
    :type marker_colors: list[tuple[str, str] | tuple[str, str, str]]
    :param font_bold: Bold font used for marker labels.
    :type font_bold: PIL.ImageFont.ImageFont
    :returns: Marker metadata ``(index, name, hex_color, rgb, x, y, marker_type)``.
    :rtype: list[tuple[int, str, str, tuple[int,int,int], int, int, str]]
    """
    marker_positions: List[
        Tuple[int, str, str, Tuple[int, int, int], int, int, str]
    ] = []
    for idx, entry in enumerate(marker_colors, start=1):
        if len(entry) == 3:
            name, hex_color, marker_type = entry
        else:
            name, hex_color = entry
            marker_type = "circle"

        rgb = hex_to_rgb(hex_color)
        h, s, _ = rgb_to_hsv(rgb)
        x, y = hsv_to_xy(h, s, RADIUS, CENTER)
        marker_positions.append((idx, name, hex_color, rgb, x, y, marker_type))

        if marker_type == "cross":
            draw.line(
                (
                    x - MARKER_RADIUS,
                    y - MARKER_RADIUS,
                    x + MARKER_RADIUS,
                    y + MARKER_RADIUS,
                ),
                fill="black",
                width=2,
            )
            draw.line(
                (
                    x - MARKER_RADIUS,
                    y + MARKER_RADIUS,
                    x + MARKER_RADIUS,
                    y - MARKER_RADIUS,
                ),
                fill="black",
                width=2,
            )
            label = f"{idx}x"
        else:
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
            label = str(idx)

        draw.text(
            (x + MARKER_RADIUS + 4, y - MARKER_RADIUS - 4),
            label,
            fill="black",
            font=font_bold,
        )
    return marker_positions


def draw_legend(
    draw: ImageDraw.ImageDraw,
    marker_positions: List[Tuple[int, str, str, Tuple[int, int, int], int, int, str]],
    font: ImageFont.ImageFont,
    font_bold: ImageFont.ImageFont,
) -> None:
    """
    Draw a legend panel showing marker swatches and labels.

    The legend mirrors the marker list and annotates crosses with an ``x`` suffix
    (for closest-ink markers). Ordering and numbering follow the sequence returned
    by :func:`draw_markers`.

    :param draw: Pillow ImageDraw object used to draw shapes and text.
    :type draw: PIL.ImageDraw.ImageDraw
    :param marker_positions: Marker data produced by :func:`draw_markers`.
    :type marker_positions: list[tuple[int, str, str, tuple[int,int,int], int, int, str]]
    :param font: Regular font for legend text.
    :type font: PIL.ImageFont.ImageFont
    :param font_bold: Bold font for headings.
    :type font_bold: PIL.ImageFont.ImageFont
    :returns: None
    """
    legend_x = WHEEL_SIZE + 20
    legend_y = 30
    line_height = 30

    draw.text((legend_x, legend_y - 25), "Ink Names", fill="black", font=font_bold)
    for entry in marker_positions:
        if len(entry) == 7:
            i, name, _, rgb, _, _, marker_type = entry
        else:
            i, name, _, rgb, _, _ = entry
            marker_type = "circle"
        y_pos = legend_y + (i - 1) * line_height
        marker_label = f"{i}x" if marker_type == "cross" else str(i)

        draw.rectangle(
            (legend_x, y_pos, legend_x + 20, y_pos + 20), fill=rgb, outline="black"
        )
        draw.text(
            (legend_x + 30, y_pos),
            f"{marker_label} : {name}",
            fill="black",
            font=font,
        )
