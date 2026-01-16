"""
.. module:: utils.color_utils
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
import os
import pickle

from apis.color_name_api import get_color_name_from_api

# Minimal curated set of color names, used for readable labels.
# Includes common CSS names plus selected custom entries (e.g., "Candy Green").
CSS_COLOR_NAMES: dict[str, str] = {
    "#ff0000": "Red",
    "#00ff00": "Lime",
    "#0000ff": "Blue",
    "#ffff00": "Yellow",
    "#00ffff": "Aqua",
    "#ff00ff": "Magenta",
    "#ffffff": "White",
    "#000000": "Black",
    "#808080": "Gray",
    "#800000": "Maroon",
    "#808000": "Olive",
    "#008000": "Green",
    "#800080": "Purple",
    "#008080": "Teal",
    "#000080": "Navy",
    "#ffa500": "Orange",
    "#ffc0cb": "Pink",
    "#a52a2a": "Brown",
}
COLOR_NAME_CACHE: dict[str, str] = {}


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


def hex_to_color_name(hex_color: str) -> str:
    """
    Map a hex color to a human-readable name.

    The lookup prefers the Color.pizza API for accurate names. If the API
    raises an error, a curated local palette is used as a fallback.

    Exact matches return the canonical name from ``CSS_COLOR_NAMES``. If no exact
    match exists, the closest named color by Euclidean RGB distance is returned.

    :param hex_color: Hex code in ``#RRGGBB`` format.
    :type hex_color: str
    :returns: Human-readable color name (best effort).
    :rtype: str
    """
    normalized = rgb_to_hex(hex_to_rgbf(hex_color)).lower()
    if normalized in COLOR_NAME_CACHE:
        return COLOR_NAME_CACHE[normalized]
    try:
        name = get_color_name_from_api(normalized)
        COLOR_NAME_CACHE[normalized] = name
        return name
    except Exception:
        pass
    if normalized in CSS_COLOR_NAMES:
        COLOR_NAME_CACHE[normalized] = CSS_COLOR_NAMES[normalized]
        return CSS_COLOR_NAMES[normalized]
    target = hex_to_rgbf(normalized)

    def dist(rgb_a, rgb_b):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(rgb_a, rgb_b)))

    best_name = "Unnamed color"
    best_dist = float("inf")
    for hex_key, name in CSS_COLOR_NAMES.items():
        candidate = hex_to_rgbf(hex_key)
        d = dist(target, candidate)
        if d < best_dist:
            best_dist = d
            best_name = name
    return best_name


def format_hex_with_name(hex_color: str) -> str:
    """
    Format a hex color with its human-readable name.

    :param hex_color: Hex code in ``#RRGGBB`` format.
    :type hex_color: str
    :returns: String in the form ``#rrggbb (Color Name)``.
    :rtype: str
    """
    normalized = rgb_to_hex(hex_to_rgbf(hex_color))
    name = hex_to_color_name(normalized)
    return f"{normalized} ({name})"


def load_color_name_cache(path: str) -> bool:
    """
    Load cached color names from a pickle file into ``COLOR_NAME_CACHE``.

    :param path: Path to a pickle file containing a dict of hex->name.
    :type path: str
    :returns: True if cache loaded, False otherwise.
    :rtype: bool
    """
    if not os.path.exists(path):
        return False
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
        if isinstance(data, dict):
            COLOR_NAME_CACHE.update({k.lower(): v for k, v in data.items()})
            return True
    except Exception:
        return False
    return False


def save_color_name_cache(path: str) -> None:
    """
    Persist the current ``COLOR_NAME_CACHE`` to a pickle file.

    :param path: Destination path for the pickle file.
    :type path: str
    """
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(COLOR_NAME_CACHE, f)
    except Exception:
        # Ignore persistence failures to avoid crashing the UI/CLI.
        return
