"""
tests/test_ui_app.py

UI tests for ConverterApp CLI application.

This module exercises the Textual-based GUI:
  - Launching the app in headless/test mode
  - Interacting with buttons and inputs
  - Verifying conversion output files

It uses pytest fixtures and decorators to parameterize
test cases and manage asynchronous I/O.
"""

import asyncio  # Standard library for asynchronous event loop management
import filecmp  # File comparison utility to validate generated outputs

import pytest  # Pytest framework for writing and running tests
from textual.widgets import Input  # Textual widget for simulating user text input

from ui import ConverterApp  # Main application class under test (Textual-based GUI)


def test_ui_click_run_no_error():
    # Verify that launching ConverterApp and clicking 'Run' completes without error
    # Uses ConverterApp.run_test() to start the app in a headless test harness
    # Async I/O (asyncio.run) is required because the Textual app operates on
    # an event loop
    """Start the app headless, click the Run button, and ensure no exceptions."""

    async def run_smoke():
        async with ConverterApp().run_test() as pilot:
            # Allow UI to initialize
            await pilot.pause(0.1)
            # Click the Run button (with default selections)
            await pilot.click("#run")
            # Allow any handlers to execute
            await pilot.pause(0.1)

    # Execute the async smoke run in an event loop;
    # test passes if no exception is raised
    asyncio.run(run_smoke())


def test_ui_all_features(tmp_path):
    # Test full conversion flow for SQL DB -> PNG via GUI interactions
    # tmp_path fixture provides an isolated temp directory for output files
    """Test all implemented conversion paths via GUI."""

    async def run_features():
        # Launch the app and perform SQL DB -> PNG conversion via GUI steps
        async with ConverterApp().run_test() as pilot:
            # Allow UI to initialize
            await pilot.pause(0.5)
            # Select SQL DB input and PNG output
            await pilot.click("#sql_in")
            await pilot.click("#png_out")
            # Set file paths
            db_widget = pilot.app.query_one("#input_path", Input)
            db_widget.value = "data/golden.db"
            # Define output file in temporary directory
            out_path = tmp_path / "wheel.png"
            png_widget = pilot.app.query_one("#output_path", Input)
            png_widget.value = str(out_path)
            # Run conversion and wait
            await pilot.pause(0.5)
            await pilot.click("#run")
            # Give time for conversion to finish
            await pilot.pause(0.5)
            # Verify PNG was generated
            assert out_path.exists(), f"PNG not created: {out_path}"
        # After app exit, compare to reference
        assert filecmp.cmp(out_path, "data/golden.png", shallow=False), (
            "Generated PNG differs from golden"
        )

    # Run the async feature test; ensures file created and matches golden reference
    asyncio.run(run_features())


@pytest.mark.parametrize(
    # @pytest.mark.parametrize: run test with multiple scenarios
    # in_lbl/out_lbl: human-readable labels for input/output formats
    # in_file: source test asset; out_name: generated file name
    # expected: whether conversion should succeed (file exists)
    "in_lbl,out_lbl,in_file,out_name,expected",
    [
        ("ODS", "SQL DB", "data/golden.ods", "to_db.sqlite", True),
        ("ODS", "JSON", "data/golden.ods", "to_json.json", True),
        ("ODS", "PNG", "data/golden.ods", "to_png.png", True),
        ("SQL DB", "ODS", "data/golden.db", "to_ods.ods", True),
        ("SQL DB", "JSON", "data/golden.db", "to_json.json", True),
        ("SQL DB", "PNG", "data/golden.db", "to_png.png", True),
        ("JSON", "ODS", "data/golden.json", "to_ods.ods", True),
        ("JSON", "SQL DB", "data/golden.json", "to_db.sqlite", True),
        ("JSON", "PNG", "data/golden.json", "to_png.png", True),
    ],
)
def test_ui_conversion_matrix(tmp_path, in_lbl, out_lbl, in_file, out_name, expected):
    # This test iterates over all format combinations to verify
    # whether the GUI conversion path is supported or disabled
    # tmp_path fixture isolates outputs per scenario
    """Verify UI conversion availability for all in->out combos."""
    in_map = {"ODS": "ods_in", "SQL DB": "sql_in", "JSON": "json_in"}
    out_map = {
        "ODS": "ods_out",
        "SQL DB": "sql_out",
        "JSON": "json_out",
        "PNG": "png_out",
    }

    async def run_case():
        async with ConverterApp().run_test() as pilot:
            # Initialize
            await pilot.pause(0.3)
            # Select formats
            await pilot.click(f"#{in_map[in_lbl]}")
            await pilot.click(f"#{out_map[out_lbl]}")
            # Set paths
            inp = pilot.app.query_one("#input_path", Input)
            inp.value = in_file
            out_path = tmp_path / out_name
            outw = pilot.app.query_one("#output_path", Input)
            outw.value = str(out_path)
            # Run and wait
            await pilot.pause(0.3)
            await pilot.click("#run")
            await pilot.pause(0.5)
        # Return output path
        return out_path

    # Execute the async case and get its output file path
    out_path = asyncio.run(run_case())
    # Confirm file existence matches the supported-flag
    exists = out_path.exists()
    assert exists == expected, (
        f"Conversion {in_lbl}->{out_lbl} existence {exists}, expected {expected}"
    )
    # For supported JSON/PNG, verify content
    # For successful JSON output, verify correct JSON schema
    if expected and out_name.endswith(".json"):
        import json  # Built-in JSON library for content validation

        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert set(data.keys()) == {"pens", "inks", "setups"}, (
            "JSON schema keys mismatch"
        )
    # For successful PNG output, compare to golden reference image
    if expected and out_name.endswith(".png"):
        assert filecmp.cmp(out_path, "data/golden.png", shallow=False), (
            "Generated PNG differs from golden reference"
        )
