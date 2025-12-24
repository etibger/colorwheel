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
