"""
Unit tests for ui_converters module functions.
Each test covers one conversion handler with isolated inputs/outputs.
"""

import filecmp
import json
import sqlite3

import pytest

from ui.ui_converters import (
    db_to_json,
    db_to_ods,
    json_to_db,
    json_to_ods,
    json_to_png,
    ods_to_db,
    ods_to_json,
    ods_to_png,
    sql_to_png,
)


@pytest.mark.parametrize("in_db", ["data/golden.db"])
def test_sql_to_png(tmp_path, in_db):
    # Convert DB to PNG and compare with golden image
    out_file = tmp_path / "out_db.png"
    sql_to_png(in_db, str(out_file))
    assert out_file.exists(), "PNG not created from DB"
    assert filecmp.cmp(str(out_file), "data/golden.png", shallow=False), (
        "Generated PNG differs from reference"
    )


@pytest.mark.parametrize("in_ods", ["data/golden.ods"])
def test_ods_to_json(tmp_path, in_ods):
    # Export ODS data to JSON and verify schema keys
    out_file = tmp_path / "out_data.json"
    ods_to_json(in_ods, str(out_file))
    assert out_file.exists(), "JSON not created from ODS"
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert set(data.keys()) == {"pens", "inks", "setups"}


@pytest.mark.parametrize("in_ods", ["data/golden.ods"])
def test_ods_to_db(tmp_path, in_ods):
    # Load ODS into SQLite DB file; check for expected tables
    out_db = tmp_path / "out.db"
    ods_to_db(in_ods, str(out_db))
    conn = sqlite3.connect(str(out_db))
    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    conn.close()
    # Close SQLite connection to avoid unclosed db warning
    assert "fountain_pens" in tables and "inks" in tables


@pytest.mark.parametrize("in_ods", ["data/golden.ods"])
def test_ods_to_png(tmp_path, in_ods):
    # Convert ODS to PNG via temp DB and compare
    out_file = tmp_path / "out_ods.png"
    ods_to_png(in_ods, str(out_file))
    assert out_file.exists(), "PNG not created from ODS"
    assert filecmp.cmp(str(out_file), "data/golden.png", shallow=False)


@pytest.mark.parametrize("in_db", ["data/golden.db"])
def test_db_to_json(tmp_path, in_db):
    # Export DB contents to JSON and verify schema
    out_file = tmp_path / "out_db.json"
    db_to_json(in_db, str(out_file))
    assert out_file.exists(), "JSON not created from DB"
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert set(data.keys()) == {"pens", "inks", "setups"}


@pytest.mark.parametrize("in_db", ["data/golden.db"])
def test_db_to_ods(tmp_path, in_db):
    # Copy DB file to ODS placeholder and ensure match
    out_file = tmp_path / "copied.ods"
    db_to_ods(in_db, str(out_file))
    assert out_file.exists(), "ODS not created from DB"
    assert filecmp.cmp(in_db, str(out_file), shallow=False)


@pytest.mark.parametrize("in_json", ["data/golden.json"])
def test_json_to_db(tmp_path, in_json):
    # Import JSON into DB; check for expected tables
    out_db = tmp_path / "json.db"
    json_to_db(in_json, str(out_db))
    conn = sqlite3.connect(str(out_db))
    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    conn.close()
    # Close SQLite connection to avoid unclosed db warning
    assert "fountain_pens" in tables and "inks" in tables


@pytest.mark.parametrize("in_json", ["data/golden.json"])
def test_json_to_png(tmp_path, in_json):
    # Render PNG from JSON data and compare
    out_file = tmp_path / "json.png"
    json_to_png(in_json, str(out_file))
    assert out_file.exists(), "PNG not created from JSON"
    assert filecmp.cmp(str(out_file), "data/golden.png", shallow=False)


@pytest.mark.parametrize("in_json", ["data/golden.json"])
def test_json_to_ods(tmp_path, in_json):
    # Copy JSON to ODS placeholder; ensure file matches
    out_file = tmp_path / "copied.ods"
    json_to_ods(in_json, str(out_file))
    assert out_file.exists(), "ODS not created from JSON"
    assert filecmp.cmp(in_json, str(out_file), shallow=False)
