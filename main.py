import argparse
import colorsys
import logging
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

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
HEX_COLORS = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF"]
OUTPUT_FILE = "color_wheel_with_legend.png"

# ==========================
# HELPERS
# ==========================


def hex_to_rgb(hex_color):
    """
    Convert a hex color string (e.g., '#RRGGBB') to an RGB tuple.
    Wikipeda: https://en.wikipedia.org/wiki/Web_colors#Hex_triplet
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hsv(rgb):
    """
    Convert an RGB tuple (0-255) to HSV components scaled [0,1].
    See: https://en.wikipedia.org/wiki/HSL_and_HSV#From_RGB
    """
    r, g, b = [x / 255.0 for x in rgb]
    return colorsys.rgb_to_hsv(r, g, b)


def hsv_to_xy(h, s):
    """
    Map hue (angle) and saturation (radius fraction) to (x,y) coordinates on the wheel.
    Uses polar-to-Cartesian conversion:
    https://en.wikipedia.org/wiki/Polar_coordinate_system
    h: hue fraction [0,1], s: saturation fraction [0,1]
    """
    angle = 2 * math.pi * h
    r = s * RADIUS
    x = CENTER[0] + r * math.cos(angle)
    y = CENTER[1] + r * math.sin(angle)
    return int(x), int(y)


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


def main():
    args = parse_args()
    setup_logging(args.verbose)
    logging.debug(f"Arguments: {args}")
    # determine marker colors
    if args.use_data:
        logging.info(f"Loading colors from data file: {args.data_file}")
        reader = DataReader(args.data_file)
        # setups = reader.load_setups()
        # REVISIT
        marker_colors = [ink.color_rgb_hex for ink in reader.inks]
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

    pixels = img.load()

    # ==========================
    # DRAW COLOR WHEEL
    # ==========================
    for y in range(WHEEL_SIZE):
        for x in range(WHEEL_SIZE):
            dx = x - CENTER[0]
            dy = y - CENTER[1]
            distance = math.sqrt(dx * dx + dy * dy)

            if distance <= RADIUS:
                saturation = distance / RADIUS
                hue = (math.atan2(dy, dx) / (2 * math.pi)) % 1.0
                r, g, b = colorsys.hsv_to_rgb(hue, saturation, 1.0)
                pixels[x, y] = (int(r * 255), int(g * 255), int(b * 255))

    # ==========================
    # DRAW MARKERS + NUMBERS
    # ==========================
    marker_positions = []

    # get a proper unique identifier, rather then the place in a list
    for idx, hex_color in enumerate(marker_colors, start=1):
        rgb = hex_to_rgb(hex_color)
        h, s, _ = rgb_to_hsv(rgb)
        x, y = hsv_to_xy(h, s)

        marker_positions.append((idx, hex_color, rgb, x, y))

        # Marker circle
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

        # Number label near marker
        draw.text(
            (x + MARKER_RADIUS + 4, y - MARKER_RADIUS - 4),
            str(idx),
            fill="black",
            font=font_bold,
        )

    # ==========================
    # DRAW LEGEND
    # ==========================
    legend_x = WHEEL_SIZE + 20
    legend_y = 30
    line_height = 30

    draw.text((legend_x, legend_y - 25), "Ink Names", fill="black", font=font_bold)

    for i, hex_color, rgb, _, _ in marker_positions:
        y_pos = legend_y + (i - 1) * line_height

        # Color swatch
        draw.rectangle(
            (legend_x, y_pos, legend_x + 20, y_pos + 20), fill=rgb, outline="black"
        )

        # Legend text
        draw.text(
            (legend_x + 30, y_pos),
            # REVISIT, don't depend on the idx being the same as the place in a list.
            f"{i} : {reader.inks[i - 1].name}",
            fill="black",
            font=font,
        )

        # ... existing drawing code here ...
        # ==========================
        # SAVE
        # ==========================
        out_path = Path(args.output)
        img.save(out_path)
        logging.info(f"Saved image to {out_path}")


if __name__ == "__main__":
    main()
