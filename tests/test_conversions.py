import filecmp
import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from data_reader import DataReader
from main import generate_wheel_from_db
from orm import FountainPen, Ink, PenSetup, load_data_from_ods


@pytest.fixture(scope="module")
def golden_json_data():
    """Load the golden JSON fixture for pens, inks, setups."""
    path = Path("data/golden.json")
    assert path.exists(), f"Golden JSON {path} not found"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("ods_file", ["data/golden.ods"])
def test_ods_to_db(tmp_path, ods_file, golden_json_data):
    """Convert ODS to DB and verify JSON counts."""
    db_file = tmp_path / "tmp.db"
    engine = load_data_from_ods(ods_file, str(db_file))
    Session = sessionmaker(bind=engine)
    session = Session()
    assert session.query(FountainPen).count() == len(golden_json_data["pens"])
    assert session.query(Ink).count() == len(golden_json_data["inks"])
    assert session.query(PenSetup).count() == len(golden_json_data["setups"])
    session.close()
    # Dispose engine to close DB connections and prevent ResourceWarning
    engine.dispose()
    # Dispose SQLAlchemy engine to close DB connections
    engine.dispose()


@pytest.mark.parametrize("ods_file", ["data/golden.ods"])
def test_ods_to_png(tmp_path, ods_file):
    """Convert ODS to PNG and compare to golden image."""
    db_file = tmp_path / "tmp.db"
    # Load data into a temporary DB and capture the engine
    engine = load_data_from_ods(ods_file, str(db_file))
    out_png = tmp_path / "tmp.png"
    db_uri = f"sqlite:///{db_file}"
    # Use explicit engine to ensure connections are closed
    from sqlalchemy import create_engine

    engine = create_engine(db_uri)
    generate_wheel_from_db(db_uri, str(out_png))
    engine.dispose()
    assert out_png.exists(), "Output PNG was not created"
    assert filecmp.cmp(out_png, "data/golden.png", shallow=False), "PNG output differs"
    # Dispose engine to avoid resource warnings
    engine.dispose()


@pytest.mark.parametrize("ods_file", ["data/golden.ods"])
def test_export_json_from_ods_direct(tmp_path, ods_file):
    """Export pens, inks, setups directly from ODS to JSON."""
    ods_path = Path(ods_file)
    assert ods_path.exists(), f"ODS file {ods_file} not found"
    reader = DataReader(str(ods_path))
    pens = [
        {
            "id": p.id,
            "brand": p.brand,
            "name": p.name,
            "nib_size": p.nib_size,
            "body_color": p.body_color,
        }
        for p in reader.pens.values()
    ]
    inks = [
        {
            "id": i.id,
            "brand": i.brand,
            "name": i.name,
            "srgb_h": i.color_srgb[0],
            "srgb_s": i.color_srgb[1],
            "srgb_v": i.color_srgb[2],
            "rgb_hex": i.color_rgb_hex,
        }
        for i in reader.inks.values()
    ]
    setups = [
        {"id": s.id, "pen_id": s.pen_id, "ink_id": s.ink_id}
        for s in reader.setups.values()
    ]
    data = {"pens": pens, "inks": inks, "setups": setups}
    out_file = tmp_path / "export_from_ods.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    assert out_file.exists(), "Export JSON file was not created"
    loaded = json.loads(out_file.read_text(encoding="utf-8"))
    assert set(loaded.keys()) == {"pens", "inks", "setups"}
    assert len(loaded["pens"]) == len(pens)
    assert len(loaded["inks"]) == len(inks)
    assert len(loaded["setups"]) == len(setups)


@pytest.mark.parametrize("db_file", ["data/golden.db"])
def test_export_json_from_db(tmp_path, db_file):
    """Export DB tables to JSON and verify content."""
    db_path = Path(db_file)
    assert db_path.exists(), f"Database file {db_file} not found"
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()
    pens = [
        {
            "id": p.id,
            "brand": p.brand,
            "name": p.name,
            "nib_size": p.nib_size,
            "body_color": p.body_color,
        }
        for p in session.query(FountainPen).all()
    ]
    inks = [
        {
            "id": i.id,
            "brand": i.brand,
            "name": i.name,
            "srgb_h": i.srgb_h,
            "srgb_s": i.srgb_s,
            "srgb_v": i.srgb_v,
            "rgb_hex": i.rgb_hex,
        }
        for i in session.query(Ink).all()
    ]
    setups = [
        {"id": s.id, "pen_id": s.pen_id, "ink_id": s.ink_id}
        for s in session.query(PenSetup).all()
    ]
    session.close()
    # Dispose engine to close DB connections and prevent ResourceWarning
    engine.dispose()
    # Dispose SQLAlchemy engine to close DB connections
    engine.dispose()
    out_file = tmp_path / "export.json"
    data = {"pens": pens, "inks": inks, "setups": setups}
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    assert out_file.exists(), "JSON export file was not created"
    loaded = json.loads(out_file.read_text(encoding="utf-8"))
    assert set(loaded.keys()) == {"pens", "inks", "setups"}
    assert len(loaded["pens"]) == len(pens)
    assert len(loaded["inks"]) == len(inks)
    assert len(loaded["setups"]) == len(setups)


@pytest.mark.parametrize(
    "db_file, output_png, expected_png",
    [("data/golden.db", "tmp_wheel.png", "data/golden.png")],
)
def test_db_to_png_conversion(tmp_path, db_file, output_png, expected_png):
    """Generate PNG from DB and compare to reference image."""
    db_path = Path(db_file)
    assert db_path.exists(), f"DB file {db_file} not found"
    out_path = tmp_path / output_png
    # Create SQLAlchemy engine to dispose after use and avoid ResourceWarning
    from sqlalchemy import create_engine

    engine = create_engine(f"sqlite:///{db_path}")
    result = generate_wheel_from_db(str(db_path), str(out_path))
    assert result.exists(), "Output PNG was not created"
    expected = Path(expected_png)
    assert expected.exists(), f"Expected image {expected_png} not found"
    assert filecmp.cmp(result, expected, shallow=False), (
        "Generated PNG differs from reference"
    )
    # Dispose engine to close DB connections
    engine.dispose()
