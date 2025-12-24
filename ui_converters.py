"""
Conversion functions extracted from UI logic.
Each function handles a specific input/output format pair.
"""

import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from draw import IMAGE_SIZE, draw_color_wheel, draw_legend, draw_markers
from orm import init_db


def sql_to_png(in_path: str, out_path: str):
    """Convert SQL DB file to PNG via wheel generator."""
    from main import generate_wheel_from_db

    generate_wheel_from_db(in_path, out_path)


def ods_to_json(in_path: str, out_path: str):
    """Read ODS spreadsheet and export data to JSON file."""
    from data_reader import DataReader

    reader = DataReader(in_path)
    data = {
        "pens": [vars(p) for p in reader.pens.values()],
        "inks": [
            {
                **vars(i),
                "srgb_h": i.color_srgb[0],
                "srgb_s": i.color_srgb[1],
                "srgb_v": i.color_srgb[2],
            }
            for i in reader.inks.values()
        ],
        "setups": [vars(s) for s in reader.setups.values()],
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def ods_to_db(in_path: str, out_path: str):
    """Load ODS data into a fresh SQL DB file."""
    from orm import load_data_from_ods

    load_data_from_ods(in_path, out_path)


def ods_to_png(in_path: str, out_path: str):
    """Convert ODS file directly to PNG by staging a temp DB."""
    from orm import load_data_from_ods

    temp = Path(out_path).with_suffix(".sqlite")
    load_data_from_ods(in_path, str(temp))
    sql_to_png(str(temp), out_path)


def db_to_json(in_path: str, out_path: str):
    """Export database tables to JSON structure file."""
    from orm import FountainPen, Ink, PenSetup

    engine = create_engine(f"sqlite:///{in_path}")
    Session = sessionmaker(bind=engine)
    session = Session()
    pens = [
        {k: getattr(p, k) for k in vars(p) if not k.startswith("_")}
        for p in session.query(FountainPen).all()
    ]
    inks = [
        {
            **{k: getattr(i, k) for k in vars(i) if not k.startswith("_")},
            "srgb_h": i.srgb_h,
            "srgb_s": i.srgb_s,
            "srgb_v": i.srgb_v,
        }
        for i in session.query(Ink).all()
    ]
    setups = [
        {k: getattr(s, k) for k in vars(s) if not k.startswith("_")}
        for s in session.query(PenSetup).all()
    ]
    session.close()
    # Dispose engine to close DB connections
    engine.dispose()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"pens": pens, "inks": inks, "setups": setups}, f, indent=2)


def db_to_ods(in_path: str, out_path: str):
    """Save SQL DB file as ODS placeholder (noop copy)."""
    shutil.copyfile(in_path, out_path)


def json_to_db(in_path: str, out_path: str):
    """Import JSON data to a fresh SQL DB file."""
    data = json.loads(open(in_path, encoding="utf-8").read())
    # Convert numeric IDs to zero-padded hex strings for DB storage
    for p in data.get("pens", []):
        p_id = p.get("id")
        p["id"] = f"{int(p_id):064x}"
    # Normalize ink fields: convert IDs and parse srgb values
    for i in data.get("inks", []):
        ink_id = i.get("id")
        i["id"] = f"{int(ink_id):064x}"
        # srgb_* may be locale strings like '286,7'
        for key in ("srgb_h", "srgb_s", "srgb_v"):
            val = i.get(key)
            try:
                i[key] = float(val.replace(",", "."))
            except Exception:
                i[key] = None
    # Pen setup IDs
    for s in data.get("setups", []):
        # Convert setup id, pen_id, ink_id to hex strings
        s_id = s.get("id")
        s["id"] = f"{int(s_id):064x}"
        # foreign keys
        pen_id = s.get("pen_id")
        ink_id = s.get("ink_id")
        s["pen_id"] = f"{int(pen_id):064x}"
        s["ink_id"] = f"{int(ink_id):064x}"
    engine = init_db(f"sqlite:///{out_path}")
    Session = sessionmaker(bind=engine)
    session = Session()
    from orm import FountainPen, Ink, PenSetup

    for p in data.get("pens", []):
        session.add(FountainPen(**p))
    for i in data.get("inks", []):
        session.add(Ink(**i))
    for s in data.get("setups", []):
        session.add(PenSetup(**s))
    session.commit()
    session.close()
    # Dispose engine to close DB connections
    engine.dispose()


def json_to_png(in_path: str, out_path: str):
    """Render PNG from JSON ink list directly (no DB)."""
    data = json.loads(open(in_path, encoding="utf-8").read())
    markers = [(ink.get("name"), ink.get("rgb_hex")) for ink in data.get("inks", [])]
    img = Image.new("RGB", IMAGE_SIZE, "white")
    dr = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 16)
        font_bold = ImageFont.truetype("DejaVuSans.ttf", 18)
    except IOError:
        font = font_bold = ImageFont.load_default()
    draw_color_wheel(img)
    pos = draw_markers(dr, markers, font_bold)
    draw_legend(dr, pos, font, font_bold)
    img.save(out_path)


def json_to_ods(in_path: str, out_path: str):
    """Save JSON file as ODS placeholder (noop copy)."""
    shutil.copyfile(in_path, out_path)


def handle_conversion(in_fmt: str, out_fmt: str, in_path: str, out_path: str) -> None:
    """Lookup and invoke the appropriate conversion handler."""
    handlers = {
        ("SQL DB", "PNG"): sql_to_png,
        ("ODS", "JSON"): ods_to_json,
        ("ODS", "SQL DB"): ods_to_db,
        ("ODS", "PNG"): ods_to_png,
        ("SQL DB", "JSON"): db_to_json,
        ("SQL DB", "ODS"): db_to_ods,
        ("JSON", "SQL DB"): json_to_db,
        ("JSON", "PNG"): json_to_png,
        ("JSON", "ODS"): json_to_ods,
    }
    handler = handlers.get((in_fmt, out_fmt))
    if not handler:
        raise ValueError(f"No handler for {in_fmt}->{out_fmt}")
    handler(in_path, out_path)
