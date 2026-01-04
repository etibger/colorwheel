"""
.. module:: color_palett_app
   :noindex:
   :synopsis: Command-line tool to generate 4-color palettes from a base color and strategy.

Available palette strategies:
- tetradic: double complementary hues at 0°,60°,180°,240°
- square_scheme: four hues at 90° intervals
- split_complementary_accent: two splits ±30° and complement accent
- two_warm_two_cool: pick 2 warm and 2 cool colors
- dominant_temperature_contrast: 2 from dominant and 2 from opposite temperature
- value_ladder_accent: three evenly spaced lightness + high-saturation accent
    - oklch_sampling: sample four hues at equal 90° steps in OKLCH space
"""

import argparse
import math

import palette_generator as pg
from color_utils import hex_to_rgbf
from data_reader import DataReader
import logging

def setup_logging(verbose: int) -> logging.Logger:
    """
    Configure a simple logger based on verbosity.

    :param verbose: verbosity count, >=1 for DEBUG.
    :type verbose: int
    :returns: Configured logger.
    :rtype: logging.Logger
    """
    level = logging.DEBUG if verbose and verbose > 0 else logging.INFO
    logger = logging.getLogger('color_palett_app')
    logger.setLevel(level)
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(ch)
    return logger

STRATEGIES = [
    "tetradic",
    "square_scheme",
    "split_complementary_accent",
    "two_warm_two_cool",
    "dominant_temperature_contrast",
    "value_ladder_accent",
    "oklch_sampling",
]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the palette app."""
    parser = argparse.ArgumentParser(
        description="Generate a 4-color palette from a base color and strategy."
    )
    parser.add_argument(
        "base_color", help="Base color in #RRGGBB format (e.g. #ff0000)"
    )
    parser.add_argument(
        "-s",
        "--strategy",
        choices=STRATEGIES,
        required=True,
        help=("Palette strategy. Available: " + ", ".join(STRATEGIES)),
    )
    parser.add_argument(
        "--ods-file",
        default="data/golden.ods",
        help="Path to ODS file for available colors (default: data/golden.ods)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (use -v, -vv)",
    )
    return parser.parse_args()


def find_closest(hex_target: str, candidates: list[str]) -> str:
    """Find the candidate color closest to a target color in RGB space."""
    target_rgb = hex_to_rgbf(hex_target)
    best = None
    best_dist = None
    for cand in candidates:
        rgb = hex_to_rgbf(cand)
        dist = math.sqrt(sum((c - t) ** 2 for c, t in zip(rgb, target_rgb)))
        if best is None or dist < best_dist:
            best = cand
            best_dist = dist
    return best


def main() -> None:
    """Entry point for the color palette application."""
    args = parse_args()
    logger = setup_logging(args.verbose)
    logger.debug(f"Args: {args}")

    # Load available colors from ODS
    reader = DataReader(args.ods_file)
    available = ["#" + i.color_rgb_hex for i in reader.inks.values()]
    logger.info(f"Loaded {len(available)} available colors from {args.ods_file}")

    # Generate palette
    strat = args.strategy
    func = getattr(pg, strat)
    if strat in (
        "tetradic",
        "square_scheme",
        "split_complementary_accent",
        "oklch_sampling",
    ):
        palette = func(args.base_color)
    else:
        palette = func(available)
    print("Generated palette:")
    for color in palette:
        closest = find_closest(color, available)
        print(f"  {color}  -> closest available {closest}")


if __name__ == "__main__":
    main()
