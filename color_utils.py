"""
Module for color conversion utilities.
"""

import colorsys
import math


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """
    Convert a hex color string (e.g., '#RRGGBB') to an RGB tuple.
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hsv(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    """
    Convert an RGB tuple (0-255) to HSV components scaled [0,1].
    """
    r, g, b = [x / 255.0 for x in rgb]
    return colorsys.rgb_to_hsv(r, g, b)


def hsv_to_xy(
    h: float, s: float, radius: int, center: tuple[int, int]
) -> tuple[int, int]:
    """
    Map hue (angle) and saturation (radius fraction) to (x,y) coordinates on the wheel.
    h: hue fraction [0,1], s: saturation fraction [0,1],
    radius: wheel radius, center: (x0, y0)
    """
    angle = 2 * math.pi * h
    r = s * radius
    x = center[0] + r * math.cos(angle)
    y = center[1] + r * math.sin(angle)
    return int(x), int(y)
