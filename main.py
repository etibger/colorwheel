import argparse
import logging
from pathlib import Path
import json

from PIL import Image, ImageDraw, ImageFont

from data_reader import DataReader
from draw import HEX_COLORS, IMAGE_SIZE, draw_color_wheel, draw_legend, draw_markers
from orm import load_data_from_ods, FountainPen, Ink, PenSetup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ==========================
# CONFIGURATION & ARGPARSE
# ==========================
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
    parser.add_argument(
        "--db-url",
        dest="db_url",
        help="SQLAlchemy database URL to save pens, inks, and setups",
        default=None,
    )
    parser.add_argument(
        "--export-json",
        dest="export_json",
        help="Path to JSON file to export pens, inks, and setups",
        default=None,
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
    # Export existing DB data to JSON if requested
    if args.export_json:
        if not args.db_url:
            logging.error("--db-url is required with --export-json")
            return
        # Initialize and populate the database from ODS
        engine = load_data_from_ods(args.data_file, args.db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        pens = [
            {"id": p.id, "brand": p.brand, "name": p.name, "nib_size": p.nib_size, "body_color": p.body_color}
            for p in session.query(FountainPen).all()
        ]
        inks = [
            {"id": i.id, "brand": i.brand, "name": i.name, "srgb_h": i.srgb_h, "srgb_s": i.srgb_s, "srgb_v": i.srgb_v, "rgb_hex": i.rgb_hex}
            for i in session.query(Ink).all()
        ]
        setups = [
            {"id": s.id, "pen_id": s.pen_id, "ink_id": s.ink_id}
            for s in session.query(PenSetup).all()
        ]
        data = {"pens": pens, "inks": inks, "setups": setups}
        out_path = Path(args.export_json)
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        logging.info(f"Exported data to {out_path}")
        return
    # if requested, load data to SQL DB and exit
    if args.db_url:
        logging.info(f"Loading data from ODS to database at {args.db_url}")
        load_data_from_ods(args.data_file, args.db_url)
        logging.info("Database load complete.")
        return
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
