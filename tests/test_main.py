"""
Unit tests for main.py CLI and functionality.
"""

import json
import logging
import sqlite3
import sys

import pytest

import main


@pytest.fixture
def sample_ods(tmp_path):
    # Reuse sample_ods from data_reader tests
    from tests.conftest import SAMPLE_CONTENT

    ods_path = tmp_path / "sample.ods"
    with open(ods_path, "wb") as f:
        import zipfile

        with zipfile.ZipFile(f, mode="w") as zf:
            zf.writestr("content.xml", SAMPLE_CONTENT)
    return str(ods_path)


def test_parse_args_defaults(monkeypatch):
    # Ensure default args are set when no flags provided
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    # Override sys.argv for parse_args
    monkeypatch.setattr(sys, "argv", ["main.py"])
    args = main.parse_args()
    # Default output file and flags
    assert args.output == main.OUTPUT_FILE
    assert not args.verbose
    assert not args.use_data
    assert args.data_file == "data/golden.ods"
    assert args.db_url is None
    assert args.export_json is None


def test_setup_logging_levels(tmp_path):
    # verbose=False should configure INFO level
    log_file = tmp_path / "log.txt"
    logger = main.setup_logging(False, logfile=str(log_file))
    assert logger.level == logging.INFO
    # verbose=True should configure DEBUG level
    logger2 = main.setup_logging(True, logfile=str(log_file))
    assert logger2.level == logging.DEBUG


@pytest.mark.usefixtures("sample_ods")
def test_export_json_from_ods_cli(tmp_path, sample_ods, monkeypatch):
    # Test CLI export to JSON from ODS
    out_json = tmp_path / "export.json"
    args = ["main.py", "--export-json", str(out_json), "--data-file", sample_ods]
    monkeypatch.setattr(sys, "argv", args)
    main.main()
    assert out_json.exists(), "JSON not created by CLI export"
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert set(data.keys()) == {"pens", "inks", "setups"}


@pytest.mark.usefixtures("sample_ods")
def test_load_db_cli(tmp_path, sample_ods, monkeypatch):
    # Test CLI load data from ODS to DB
    out_db = tmp_path / "out.db"
    monkeypatch.setattr(
        sys, "argv", ["main.py", "--db-url", str(out_db), "--data-file", sample_ods]
    )
    main.main()
    conn = sqlite3.connect(str(out_db))
    tbls = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    conn.close()
    assert "fountain_pens" in tbls and "inks" in tbls


@pytest.mark.usefixtures("sample_ods")
def test_default_generate_image(tmp_path, sample_ods, monkeypatch):
    # Generate image using --use-data option
    tmp_png = tmp_path / main.OUTPUT_FILE
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys, "argv", ["main.py", "--use-data", "--data-file", sample_ods]
    )
    main.main()
    assert tmp_png.exists(), "Default PNG not generated"
    tmp_png.unlink()


def test_load_db_cli_with_url(tmp_path, sample_ods, monkeypatch):
    """Test CLI handling of full SQLite URL for --db-url."""
    # Prepare output DB path
    out_db = tmp_path / "url_load.db"
    # Use full sqlite URL scheme
    db_url = f"sqlite:///{out_db}"
    # Prevent pytest from picking up '-v' flags
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    # Override argv and invoke main
    import sqlite3
    import sys

    monkeypatch.setattr(
        sys, "argv", ["main.py", "--db-url", db_url, "--data-file", sample_ods]
    )
    # Running with URL should create the same out_db file
    import main

    main.main()
    # Check file exists
    assert out_db.exists(), "DB file not created for full URL"
    # Verify tables inside the created DB
    conn = sqlite3.connect(str(out_db))
    tables = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    conn.close()
    assert "fountain_pens" in tables and "inks" in tables


@pytest.mark.usefixtures("sample_ods")
def test_export_json_from_db_cli_with_url(tmp_path, sample_ods, monkeypatch):
    """Test CLI --export-json uses full SQLite URL to export DB to JSON."""
    # First create a DB from ODS
    from orm import load_data_from_ods

    db_path = tmp_path / "db_for_json.db"
    engine = load_data_from_ods(sample_ods, str(db_path))
    engine.dispose()
    # Now export JSON via CLI
    out_json = tmp_path / "export.json"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    import sys

    monkeypatch.setattr(
        sys, "argv", ["main.py", "--export-json", str(out_json), "--db-url", db_url]
    )
    import main

    main.main()
    # Verify JSON file
    assert out_json.exists(), "JSON not created from DB URL"
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert set(data.keys()) == {"pens", "inks", "setups"}
    assert len(data["pens"]) > 0 and len(data["inks"]) > 0


@pytest.mark.usefixtures("sample_ods")
def test_import_json_to_db_cli_with_url(tmp_path, sample_ods, monkeypatch):
    """Test CLI --import-json with full SQLite URL to import JSON data."""
    # Prepare JSON from sample ODS
    from orm import load_data_from_ods

    db0 = tmp_path / "init.db"
    eng0 = load_data_from_ods(sample_ods, str(db0))
    eng0.dispose()
    # Export JSON from that DB
    json_file = tmp_path / "export.json"
    import sqlite3
    import sys

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "--export-json", str(json_file), "--db-url", f"sqlite:///{db0}"],
    )
    import main

    main.main()
    assert json_file.exists(), "JSON not created from DB"
    # Now import back JSON into new DB via CLI
    new_db = tmp_path / "imported.db"
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "--import-json", str(json_file), "--db-url", f"sqlite:///{new_db}"],
    )
    main.main()
    # Verify imported DB has tables
    conn = sqlite3.connect(str(new_db))
    tables = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    conn.close()
    assert "fountain_pens" in tables and "inks" in tables
