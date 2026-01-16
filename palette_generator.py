"""
.. module:: palette_generator
   :noindex:
   :synopsis: Generate 4-color palettes using various strategies.

Provides functions to generate 4-color palettes using various strategies:
1) Color-wheel-based: Tetradic, Square Scheme, Split-Complementary + Accent
2) Color Temperature: 2 Warm + 2 Cool, Dominant Temperature + Contrast Pair
3) Value-Driven: Value Ladder + Accent
4) Perceptual Modern: OKLCH/LAB space sampling
"""

import math

from color_utils import (
    hex_to_rgbf as hex_to_rgb,
)
from color_utils import (
    hsl_to_rgb,
    oklab_to_rgb,
    rgb_to_hex,
    rgb_to_hsl,
    rgb_to_oklab,
)


def _adjust_hue(h, angle):
    """
    Adjust a hue value by a given angle, wrapping around 360 degrees.

    :param h: Original hue in degrees.
    :type h: float
    :param angle: Angle to adjust the hue by in degrees.
    :type angle: float
    :return: New hue in degrees modulo 360.
    :rtype: float
    """
    return (h + angle) % 360


# 1) Color-Wheel-Based Algorithms


def tetradic(base_hex):
    """
    Generate a tetradic (double complementary) color palette from a base color.

    :param base_hex: Base color in #RRGGBB format.
    :type base_hex: str
    :return: List of four hex color strings forming a tetradic palette.
    :rtype: list
    """
    rgb = hex_to_rgb(base_hex)
    h, s, _l = rgb_to_hsl(rgb)
    hues = [h, _adjust_hue(h, 60), _adjust_hue(h, 180), _adjust_hue(h, 240)]
    return [rgb_to_hex(hsl_to_rgb((hh, s, _l))) for hh in hues]


def square_scheme(base_hex):
    """
    Generate a square color scheme from a base color.

    :param base_hex: Base color in #RRGGBB format.
    :type base_hex: str
    :return: List of four hex color strings forming a square scheme.
    :rtype: list
    """
    rgb = hex_to_rgb(base_hex)
    h, s, _l = rgb_to_hsl(rgb)
    return [rgb_to_hex(hsl_to_rgb((_adjust_hue(h, i * 90), s, _l))) for i in range(4)]


def split_complementary_accent(base_hex):
    """
    Generate a split-complementary palette with an accent color.

    :param base_hex: Base color in #RRGGBB format.
    :type base_hex: str
    :return: List of four hex color strings (base, two splits, accent).
    :rtype: list
    """
    rgb = hex_to_rgb(base_hex)
    h, s, _l = rgb_to_hsl(rgb)
    split1 = _adjust_hue(h, 150)
    split2 = _adjust_hue(h, 210)
    accent = _adjust_hue(h, 180)
    hues = [h, split1, split2, accent]
    return [rgb_to_hex(hsl_to_rgb((hh, s, _l))) for hh in hues]


# 2) Color Temperature-Based Strategies


def _hue_to_temperature(h):
    """
    Classify a hue angle as 'warm' or 'cool'.

    :param h: Hue angle in degrees.
    :type h: float
    :return: 'warm' if hue is warm-toned, otherwise 'cool'.
    :rtype: str
    """
    h = h % 360
    return "warm" if h < 90 or h > 330 else "cool"


def two_warm_two_cool(colors):
    """
    Select two warm and two cool colors from a list of hex colors.

    :param colors: List of color strings in #RRGGBB format.
    :type colors: list
    :return: Four selected color strings (two warm, two cool).
    :rtype: list
    :raises ValueError: If fewer than two warm or two cool colors available.
    """
    warm, cool = [], []
    for c in colors:
        h, s, _l = rgb_to_hsl(hex_to_rgb(c))
        (_ := warm if _hue_to_temperature(h) == "warm" else cool).append(c)
    if len(warm) < 2 or len(cool) < 2:
        raise ValueError("Need at least 2 warm and 2 cool colors")
    return warm[:2] + cool[:2]


def dominant_temperature_contrast(colors):
    """
    Select two colors from the dominant temperature category and two from the opposite.

    :param colors: List of color strings in #RRGGBB format.
    :type colors: list
    :return: Four selected color strings (two dominant, two contrast).
    :rtype: list
    :raises ValueError: If not enough colors in either category.
    """
    warm, cool = [], []
    for c in colors:
        h, s, _l = rgb_to_hsl(hex_to_rgb(c))
        (_ := warm if _hue_to_temperature(h) == "warm" else cool).append(c)
    dominant, other = (warm, cool) if len(warm) >= len(cool) else (cool, warm)
    if len(dominant) < 2 or len(other) < 2:
        raise ValueError("Not enough colors in categories")
    # select two dominant colors in input order
    dom_sel = dominant[:2]
    # for contrast, sort other by hue descending for consistency

    def _hue(c):
        return rgb_to_hsl(hex_to_rgb(c))[0]

    other_sorted = sorted(other, key=_hue, reverse=True)
    return dom_sel + other_sorted[:2]


# 3) Value-Driven (Lightness First) Palettes


def value_ladder_accent(colors):
    """
    Create a palette by selecting three colors with evenly spaced lightness and one accent by highest saturation.

    :param colors: List of color strings in #RRGGBB format.
    :type colors: list
    :return: Four selected color strings (three ladder, one accent).
    :rtype: list
    :raises ValueError: If fewer than four colors provided.
    """
    # compute lightness and saturation
    info = []
    for c in colors:
        h, s, _l = rgb_to_hsl(hex_to_rgb(c))
        info.append({"hex": c, "l": _l, "s": s})
    info.sort(key=lambda x: x["l"])
    n = len(info)
    if n < 4:
        raise ValueError("Need at least 4 colors")
    # pick ladder
    idxs = [0, n // 3, 2 * n // 3]
    ladder = [info[i]["hex"] for i in idxs]
    # pick accent by highest saturation not in ladder
    accent = max([i for i in info if i["hex"] not in ladder], key=lambda x: x["s"])[
        "hex"
    ]
    return ladder + [accent]


# 4) Perceptual and Modern Algorithms (OKLCH/LAB Sampling)


def oklch_sampling(base_hex):
    """
    Generate a 4-color palette by sampling equal hue intervals in OKLCH space.

    :param base_hex: Base color in #RRGGBB format.
    :type base_hex: str
    :return: List of four hex color strings sampled in OKLCH space.
    :rtype: list
    """
    rgb = hex_to_rgb(base_hex)
    _l, a, b = rgb_to_oklab(rgb)
    # compute chroma and hue
    c = math.hypot(a, b)
    h = math.degrees(math.atan2(b, a))
    # sample 4 hues
    hues = [(h + i * 90) % 360 for i in range(4)]
    palette = []
    for hh in hues:
        rad = math.radians(hh)
        a2 = c * math.cos(rad)
        b2 = c * math.sin(rad)
        rgb2 = oklab_to_rgb((_l, a2, b2))
        palette.append(rgb_to_hex(rgb2))
    return palette
