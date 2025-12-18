import filecmp
import json
from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

from main import generate_wheel_from_db
from orm import FountainPen, Ink, PenSetup, load_data_from_ods


@pytest.fixture(scope="module")
def golden_json_data():
    """Load the golden JSON fixture for pens, inks, setups."""
    path = Path("data/golden.json")
    assert path.exists(), f"Golden JSON {path} not found"
    return json.loads(path.read_text(encoding="utf-8"))


def test_ods_to_db(tmp_path, golden_json_data):
    """Convert ODS to SQL DB and verify row counts match golden JSON."""
    db_file = tmp_path / "tmp.db"
    # Load data from ODS into fresh DB
    engine = load_data_from_ods("data/golden.ods", str(db_file))
    Session = sessionmaker(bind=engine)
    session = Session()
    # Compare counts
    assert session.query(FountainPen).count() == len(golden_json_data["pens"])
    assert session.query(Ink).count() == len(golden_json_data["inks"])
    assert session.query(PenSetup).count() == len(golden_json_data["setups"])
    session.close()


def test_ods_to_png(tmp_path):
    """Convert ODS to PNG via DB and compare to golden PNG."""
    db_file = tmp_path / "tmp.db"
    # Load data and generate wheel
    engine = load_data_from_ods("data/golden.ods", str(db_file))
    out_png = tmp_path / "tmp.png"
    # Use database file path with sqlite URI
    db_uri = f"sqlite:///{db_file}"
    generate_wheel_from_db(db_uri, str(out_png))
    assert out_png.exists(), "Output PNG was not created"
    # Compare binary content
    assert filecmp.cmp(out_png, "data/golden.png", shallow=False), "PNG output differs"


# Mapping of tested conversions:
# Input Format -> Output Format : Test Name
# ODS -> DB   : test_ods_to_db
# ODS -> JSON : test_export_json_from_ods_direct (in test_export_json.py)
# ODS -> PNG  : test_ods_to_png
# DB  -> JSON : test_export_json_from_db (in test_export_json.py)
# DB  -> PNG  : test_db_to_png_conversion (in test_ui_conversion.py)
