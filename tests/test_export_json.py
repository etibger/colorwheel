import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from orm import FountainPen, Ink, PenSetup


@pytest.mark.parametrize("db_file", ["data/golden.db"])
def test_export_json_from_db(tmp_path, db_file):
    """
    Connect to an existing SQLite database and export its tables to JSON.
    """
    # Prepare paths
    db_path = Path(db_file)
    assert db_path.exists(), f"Database file {db_file} not found"

    # Connect to the database
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    # Query all records
    pens = [
        {"id": p.id, "brand": p.brand, "name": p.name,
         "nib_size": p.nib_size, "body_color": p.body_color}
        for p in session.query(FountainPen).all()
    ]
    inks = [
        {"id": i.id, "brand": i.brand, "name": i.name,
         "srgb_h": i.srgb_h, "srgb_s": i.srgb_s, "srgb_v": i.srgb_v,
         "rgb_hex": i.rgb_hex}
        for i in session.query(Ink).all()
    ]
    setups = [
        {"id": s.id, "pen_id": s.pen_id, "ink_id": s.ink_id}
        for s in session.query(PenSetup).all()
    ]
    session.close()

    # Basic sanity checks
    assert isinstance(pens, list) and len(pens) > 0
    assert isinstance(inks, list) and len(inks) > 0
    assert isinstance(setups, list) and len(setups) > 0

    # Export to JSON file
    out_file = tmp_path / "export.json"
    data = {"pens": pens, "inks": inks, "setups": setups}
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Verify JSON content
    assert out_file.exists()
    loaded = json.loads(out_file.read_text(encoding="utf-8"))
    assert set(loaded.keys()) == {"pens", "inks", "setups"}
    assert len(loaded["pens"]) == len(pens)
    assert len(loaded["inks"]) == len(inks)
    assert len(loaded["setups"]) == len(setups)

@pytest.mark.parametrize("ods_file", ["data/golden.ods"])
def test_export_json_from_ods_direct(tmp_path, ods_file):
    """
    Test exporting pens, inks, and setups directly from an ODS file to JSON.
    """
    from data_reader import DataReader

    ods_path = Path(ods_file)
    assert ods_path.exists(), f"ODS file {ods_file} not found"
    # Read data
    reader = DataReader(str(ods_path))
    # Prepare JSON data
    pens = [
        {"id": p.id, "brand": p.brand, "name": p.name,
         "nib_size": p.nib_size, "body_color": p.body_color}
        for p in reader.pens.values()
    ]
    inks = [
        {"id": i.id, "brand": i.brand, "name": i.name,
         "srgb_h": i.color_srgb[0], "srgb_s": i.color_srgb[1],
         "srgb_v": i.color_srgb[2], "rgb_hex": i.color_rgb_hex}
        for i in reader.inks.values()
    ]
    setups = [
        {"id": s.id, "pen_id": s.pen_id, "ink_id": s.ink_id}
        for s in reader.setups.values()
    ]
    data = {"pens": pens, "inks": inks, "setups": setups}
    # Write to file
    out_file = tmp_path / "export_from_ods.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    # Validate output
    assert out_file.exists(), "Export JSON file was not created"
    loaded = json.loads(out_file.read_text(encoding="utf-8"))
    assert set(loaded.keys()) == {"pens", "inks", "setups"}
    assert len(loaded["pens"]) == len(pens)
    assert len(loaded["inks"]) == len(inks)
    assert len(loaded["setups"]) == len(setups)
