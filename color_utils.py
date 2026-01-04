"""
.. module:: color_utils
   :noindex:
   :synopsis: Color space conversion utilities.

This module provides utilities for converting between various color representations
and color spaces:

- `sRGB <https://en.wikipedia.org/wiki/SRGB>`_: Standard RGB color space.
- `HSV <https://en.wikipedia.org/wiki/HSL_and_HSV>`_: Hue, Saturation, Value.
- `HSL <https://en.wikipedia.org/wiki/HSL_and_HSV>`_: Hue, Saturation, Lightness.
- `Oklab <https://en.wikipedia.org/wiki/Color_space#Oklab>`_: Perceptual color space.
"""

import colorsys
import math


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """
    Convert a hexadecimal color code to an integer RGB tuple in sRGB space.

    :param hex_color: Hex color code in ``#RRGGBB`` format.
    :type hex_color: str
    :returns: RGB tuple with integer components [0..255].
    :rtype: tuple[int, int, int]
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hsv(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    """
    Convert an integer RGB tuple to HSV (Hue, Saturation, Value) components.

    :param rgb: RGB tuple with integer components [0..255].
    :type rgb: tuple[int, int, int]
    :returns: Tuple ``(h, s, v)`` where hue, saturation, and value are in [0..1].
    :rtype: tuple[float, float, float]
    """
    r, g, b = [x / 255.0 for x in rgb]
    return colorsys.rgb_to_hsv(r, g, b)


def hsv_to_xy(
    h: float, s: float, radius: int, center: tuple[int, int]
) -> tuple[int, int]:
    """
    Map HSV hue and saturation to Cartesian coordinates on a color wheel.

    :param h: Hue fraction in [0..1] (`HSV <https://en.wikipedia.org/wiki/HSL_and_HSV>`_).
    :type h: float
    :param s: Saturation fraction in [0..1].
    :type s: float
    :param radius: Radius of the color wheel in pixels.
    :type radius: int
    :param center: Center coordinates (x0, y0) of the color wheel.
    :type center: tuple[int, int]
    :returns: (x, y) pixel coordinates corresponding to the HSV position.
    :rtype: tuple[int, int]
    """
    angle = 2 * math.pi * h
    r = s * radius
    x = center[0] + r * math.cos(angle)
    y = center[1] + r * math.sin(angle)
    return int(x), int(y)


# Palette generation conversion utilities (normalized floats and perceptual spaces)


def hex_to_rgbf(hex_color: str) -> tuple[float, float, float]:
    """
    Convert a hexadecimal color code to a normalized RGB tuple in [0..1].

    :param hex_color: Hex color code in ``#RRGGBB`` format.
    :type hex_color: str
    :returns: RGB tuple with float components in [0..1].
    :rtype: tuple[float, float, float]
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    """
    Convert a normalized RGB tuple in [0..1] to a hexadecimal color code.

    :param rgb: RGB tuple with float components in [0..1].
    :type rgb: tuple[float, float, float]
    :returns: Hex color code in ``#RRGGBB`` format.
    :rtype: str
    """
    r = int(round(max(0, min(1, rgb[0])) * 255))
    g = int(round(max(0, min(1, rgb[1])) * 255))
    b = int(round(max(0, min(1, rgb[2])) * 255))
    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def rgb_to_hsl(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    """
    Convert a normalized RGB tuple to HSL (Hue, Saturation, Lightness).

    :param rgb: RGB tuple with float components in [0..1].
    :type rgb: tuple[float, float, float]
    :returns: Tuple ``(h, s, l)`` where hue is in degrees [0..360),
              saturation and lightness in [0..1].
    :rtype: tuple[float, float, float]
    """
    h, l, s = colorsys.rgb_to_hls(*rgb)
    return (h * 360.0, s, l)


def hsl_to_rgb(hsl: tuple[float, float, float]) -> tuple[float, float, float]:
    """
    Convert HSL (Hue, Saturation, Lightness) to a normalized RGB tuple.

    :param hsl: Tuple ``(h, s, l)`` where hue is in degrees [0..360),
                saturation and lightness in [0..1].
    :type hsl: tuple[float, float, float]
    :returns: RGB tuple with float components in [0..1].
    :rtype: tuple[float, float, float]
    """
    h, s, l = hsl
    return colorsys.hls_to_rgb(h / 360.0, l, s)


def rgb_to_oklab(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    """
    Convert an sRGB tuple to the Oklab perceptual color space.

    :param rgb: RGB tuple with float components in [0..1] (sRGB).
    :type rgb: tuple[float, float, float]
    :returns: Tuple ``(L, a, b)`` in Oklab space.
    :rtype: tuple[float, float, float]
    """

    def to_linear(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = map(to_linear, rgb)
    l_ = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m_ = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s_ = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    L = (
        0.2104542553 * l_ ** (1 / 3)
        + 0.7936177850 * m_ ** (1 / 3)
        - 0.0040720468 * s_ ** (1 / 3)
    )
    A = (
        1.9779984951 * l_ ** (1 / 3)
        - 2.4285922050 * m_ ** (1 / 3)
        + 0.4505937099 * s_ ** (1 / 3)
    )
    B = (
        0.0259040371 * l_ ** (1 / 3)
        + 0.7827717662 * m_ ** (1 / 3)
        - 0.8086757660 * s_ ** (1 / 3)
    )
    return (L, A, B)


def oklab_to_rgb(oklab: tuple[float, float, float]) -> tuple[float, float, float]:
    """
    Convert from Oklab perceptual color space back to sRGB.

    :param oklab: Tuple ``(L, a, b)`` in Oklab space.
    :type oklab: tuple[float, float, float]
    :returns: RGB tuple with float components in [0..1] (sRGB).
    :rtype: tuple[float, float, float]
    """
    L, A, B = oklab
    l_ = (L + 0.3963377774 * A + 0.2158037573 * B) ** 3
    m_ = (L - 0.1055613458 * A - 0.0638541728 * B) ** 3
    s_ = (L - 0.0894841775 * A - 1.2914855480 * B) ** 3
    r = +4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_
    g = -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_
    b = -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_

    def to_srgb(c: float) -> float:
        return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055

    return (to_srgb(r), to_srgb(g), to_srgb(b))
