"""
UI tests for ``ui_color_palett_app.PaletteApp``.

This suite exercises the Textual UI in headless mode to verify:

* Smoke launch and Run button handling
* Palette generation and closest-ink logging for each strategy
* Option list selection flows (highlighted ink usage)
"""

import asyncio
import logging
import sys
from pathlib import Path

import pytest
from textual.widgets import Input, OptionList

from ui_color_palett_app import LOG_FILE, PaletteApp, init_cli

LOG_PATH = Path(LOG_FILE)


@pytest.fixture(autouse=True)
def clean_palette_log():
    """Ensure the palette UI log file is isolated per test run."""
    LOG_PATH.unlink(missing_ok=True)
    yield
    LOG_PATH.unlink(missing_ok=True)


@pytest.mark.parametrize(
    "argv, expected_level",
    [
        (["ui_color_palett_app.py", "-v"], logging.WARNING),
        (["ui_color_palett_app.py", "-vv"], logging.INFO),
    ],
)
def test_palette_init_cli_verbosity(monkeypatch, argv, expected_level):
    """init_cli sets logger level based on verbosity flags."""
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setattr(sys, "argv", argv)
    logger = init_cli()
    try:
        assert logger.level == expected_level
    finally:
        logger.handlers.clear()


def test_palette_ui_click_run_no_error():
    """Launch PaletteApp headless and click Run without errors."""

    async def run_smoke():
        async with PaletteApp().run_test(size=TEST_SIZE) as pilot:
            await pilot.pause(0.2)
            await pilot.click("#run")
            await pilot.pause(0.2)

    asyncio.run(run_smoke())


def test_palette_ui_generates_expected_palette():
    """Set a base color, run tetradic strategy, and verify logged palette."""
    base_color = "#ff0000"
    expected_palette_lines = [
        "#ff0000 -> closest available #eb4836 (Pilot - fuyu-gaki)",
        "#ffff00 -> closest available #da8730 (Kaweco - Sunrise Orange)",
        "#00ffff -> closest available #00c49f (Faber-Castell - Türkis Turquoise)",
        "#0000ff -> closest available #4c58e0 (Kaweco - Royal Blue)",
    ]

    async def run_app():
        async with PaletteApp().run_test(size=TEST_SIZE) as pilot:
            await pilot.pause(0.3)
            pilot.app.query_one("#base_input", Input).value = base_color
            await pilot.click("#strategy_tetradic")
            await pilot.click("#run")
            await pilot.pause(0.3)

    asyncio.run(run_app())
    log_lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    assert (
        f"Generating palette with tetradic using {base_color} "
        "(ODS source: data/golden.ods)" in log_lines
    )
    palette_lines = [line for line in log_lines if "-> closest available" in line]
    assert palette_lines == expected_palette_lines


@pytest.mark.parametrize(
    "strategy,base_color,expected_closest",
    [
        ("tetradic", "#ff0000", ["#eb4836", "#da8730", "#00c49f", "#4c58e0"]),
        ("square_scheme", "#ff0000", ["#eb4836", "#da8730", "#00c49f", "#4c58e0"]),
        (
            "split_complementary_accent",
            "#ff0000",
            ["#eb4836", "#00c49f", "#4c58e0", "#00c49f"],
        ),
        (
            "two_warm_two_cool",
            "#ff0000",
            ["#f0668c", "#da8730", "#643a70", "#5673ae"],
        ),
        (
            "dominant_temperature_contrast",
            "#ff0000",
            ["#643a70", "#5673ae", "#341c22", "#f0668c"],
        ),
        (
            "value_ladder_accent",
            "#ff0000",
            ["#341c22", "#238b73", "#da8730", "#00c49f"],
        ),
        ("oklch_sampling", "#ff0000", ["#eb4836", "#da8730", "#00c49f", "#4c58e0"]),
    ],
)
def test_palette_ui_strategy_matrix(strategy, base_color, expected_closest):
    """Verify each palette strategy produces 4 logged entries with expected matches."""

    async def run_case():
        async with PaletteApp().run_test(size=TEST_SIZE) as pilot:
            await pilot.pause(0.3)
            pilot.app.query_one("#base_input", Input).value = base_color
            await pilot.click(f"#strategy_{strategy}")
            await pilot.click("#run")
            await pilot.pause(0.3)

    asyncio.run(run_case())
    log_lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    palette_lines = [line for line in log_lines if "-> closest available" in line]
    assert len(palette_lines) == 4, f"{strategy} did not log 4 palette entries"
    closests = [
        line.split(" -> closest available ")[1].split(" (", 1)[0]
        for line in palette_lines
    ]
    assert closests == expected_closest


def test_palette_ui_use_selected_highlight_flow():
    """Ensure 'Use highlighted ink' reads Option from index and updates input/log."""

    async def run_case():
        async with PaletteApp().run_test(size=TEST_SIZE) as pilot:
            await pilot.pause(0.3)
            option_list = pilot.app.query_one("#available_colors", OptionList)
            option_list.highlighted = 0
            option = option_list.get_option_at_index(option_list.highlighted)
            expected_hex = option.id or option.prompt
            await pilot.click("#use_selected")
            await pilot.pause(0.2)
            base_value = pilot.app.query_one("#base_input", Input).value
        return expected_hex, base_value

    expected_hex, base_value = asyncio.run(run_case())
    log_lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    assert base_value == expected_hex
    assert any(
        line.startswith(f"Using highlighted ink: {expected_hex}") for line in log_lines
    ), "Highlighted ink usage was not logged"


def test_palette_ui_option_selected_event():
    """OptionSelected should populate base input and log the selection."""

    async def run_case():
        async with PaletteApp().run_test(size=TEST_SIZE) as pilot:
            await pilot.pause(0.3)
            option_list = pilot.app.query_one("#available_colors", OptionList)
            option = option_list.get_option_at_index(0)
            event = OptionList.OptionSelected(option_list, option, 0)
            pilot.app.on_option_list_option_selected(event)
            await pilot.pause(0.1)
            base_val = pilot.app.query_one("#base_input", Input).value
        return option, base_val

    option, base_val = asyncio.run(run_case())
    expected_hex = option.id or option.prompt
    log_lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    assert base_val == expected_hex
    assert any(
        line.startswith(f"Selected base color from inks: {expected_hex}")
        for line in log_lines
    ), "Option selection was not logged"


def test_palette_ui_random_base(monkeypatch):
    """Random base should pick a random available color and log its label."""

    async def run_case():
        async with PaletteApp().run_test(size=TEST_SIZE) as pilot:
            await pilot.pause(0.3)
            target = pilot.app.available_colors[-1]
            monkeypatch.setattr("ui_color_palett_app.random.choice", lambda seq: target)
            await pilot.click("#random_base")
            await pilot.pause(0.2)
            base_val = pilot.app.query_one("#base_input", Input).value
        return target, base_val

    target, base_val = asyncio.run(run_case())
    expected_hex, expected_label = target
    log_lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    assert base_val == expected_hex
    assert any(
        line == f"Random base color: {expected_label}" for line in log_lines
    ), "Random base selection not logged with label"


TEST_SIZE = (120, 80)
