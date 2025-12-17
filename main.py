import argparse
import colorsys
import logging
import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

from color_utils import hex_to_rgb, hsv_to_xy, rgb_to_hsv
from data_reader import DataReader

# ==========================
# CONFIGURATION & ARGPARSE
# ==========================
# default settings
WHEEL_SIZE = 600
LEGEND_WIDTH = 260
IMAGE_SIZE = (WHEEL_SIZE + LEGEND_WIDTH, WHEEL_SIZE)
RADIUS = WHEEL_SIZE // 2
CENTER = (RADIUS, RADIUS)
MARKER_RADIUS = 6
# default list of (color_name, hex) for manual markers
HEX_COLORS = [
    ("Red", "#FF0000"),
    ("Green", "#00FF00"),
    ("Blue", "#0000FF"),
    ("Yellow", "#FFFF00"),
    ("Magenta", "#FF00FF"),
    ("Cyan", "#00FFFF"),
]
OUTPUT_FILE = "color_wheel_with_legend.png"


# ==========================
# IMAGE SETUP
# ==========================
# placeholder for CLI args
def parse_args():
    parser = argparse.ArgumentParser(description="Generate a color wheel image.")
    parser.add_argument(
        "-o",
        "--output",
        default=OUTPUT_FILE,
        help="Output filename for the generated image",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging to console and file",
    )
    parser.add_argument(
        "--use-data",
        action="store_true",
        help="Use colors loaded from the ODS data file instead of default HEX_COLORS",
    )
    parser.add_argument(
        "--data-file",
        default="data/tinta_szinek.ods",
        help="Path to ODS file when using --use-data",
    )
    return parser.parse_args()


def setup_logging(verbose: bool, logfile: str = "colorwheel.log"):
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(
        level=level,
        format=fmt,
        handlers=[logging.StreamHandler(), logging.FileHandler(logfile, mode="w")],
    )


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


def main():
    args = parse_args()
    setup_logging(args.verbose)
    logging.debug(f"Arguments: {args}")
    # determine marker colors
    if args.use_data:
        logging.info(f"Loading colors from data file: {args.data_file}")
        reader = DataReader(args.data_file)
        # prepare ink list to preserve order and include names
        ink_list = list(reader.inks.values())
        # marker colors as (name, hex)
        marker_colors = [(ink.name, ink.color_rgb_hex) for ink in ink_list]
        logging.info(f"Using {len(marker_colors)} colors from data")
    else:
        marker_colors = HEX_COLORS
    # create image
    img = Image.new("RGB", IMAGE_SIZE, "white")
    draw = ImageDraw.Draw(img)

    # Try to load a nicer font, fallback if unavailable
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 16)
        font_bold = ImageFont.truetype("DejaVuSans.ttf", 18)
    except IOError:
        font = font_bold = ImageFont.load_default()

    # Draw the wheel, markers, and legend
    draw_color_wheel(img)
    marker_positions = draw_markers(draw, marker_colors, font_bold)
    draw_legend(draw, marker_positions, font, font_bold)

    # Save output
    out_path = Path(args.output)
    img.save(out_path)
    logging.info(f"Saved image to {out_path}")


if __name__ == "__main__":
    main()
