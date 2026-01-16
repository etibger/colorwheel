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
from textual.widgets import Input, OptionList, RadioButton

from ui.ui_color_palett_app import LOG_FILE, PaletteApp, init_cli

LOG_PATH = Path(LOG_FILE)
NAME_FMT = "Name({})"


def fmt_hex(hex_color: str) -> str:
    normalized = hex_color.lower()
    return f"{normalized} ({NAME_FMT.format(normalized)})"


@pytest.fixture(autouse=True)
def clean_palette_log():
    """Ensure the palette UI log file is isolated per test run."""
    LOG_PATH.unlink(missing_ok=True)
    yield
    LOG_PATH.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def mock_color_names(monkeypatch):
    """Avoid external API calls; provide deterministic names."""
    monkeypatch.setattr(
        "utils.color_utils.hex_to_color_name", lambda hx: NAME_FMT.format(hx.lower())
    )


@pytest.fixture(autouse=True)
def sandbox_color_cache(monkeypatch, tmp_path):
    """Prevent tests from reading/writing the real color name cache file."""
    temp_cache = tmp_path / "color_names.pickle"
    monkeypatch.setattr("ui.ui_color_palett_app.CACHE_FILE", str(temp_cache))
    monkeypatch.setattr(
        "ui.ui_color_palett_app.save_color_name_cache", lambda path: None
    )
    monkeypatch.setattr(
        "ui.ui_color_palett_app.load_color_name_cache", lambda path: False
    )
    monkeypatch.setattr(
        "ui.ui_color_palett_app.PREVIEW_FILE",
        str(tmp_path / "generated_palette_color_wheel.png"),
    )


@pytest.fixture(autouse=True)
def sandbox_palette_log(monkeypatch, tmp_path):
    """Isolate log file per worker/process when running in parallel."""
    log_path = tmp_path / "colorwheel_palett_ui.log"
    monkeypatch.setattr("ui.ui_color_palett_app.LOG_FILE", str(log_path))
    globals()["LOG_PATH"] = log_path


@pytest.mark.parametrize(
    "argv, expected_level",
    [
        (["ui_color_palett_app.py", "-v"], logging.WARNING),
        (["ui_color_palett_app.py", "-vv"], logging.INFO),
        (["ui_color_palett_app.py", "-vvv"], logging.DEBUG),
    ],
)
def test_palette_init_cli_verbosity(monkeypatch, argv, expected_level):
    """init_cli sets logger level based on verbosity flags."""
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setattr(sys, "argv", argv)
    logger = init_cli()
    try:
        # File handler should reflect requested level; logger stays at DEBUG
        file_levels = [
            h.level for h in logger.handlers if isinstance(h, logging.FileHandler)
        ]
        assert expected_level in file_levels
        assert logger.level == logging.DEBUG
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
        f"{fmt_hex('#ff0000')} -> closest available {
            fmt_hex('#eb4836')
        } (Pilot - fuyu-gaki)",
        f"{fmt_hex('#ffff00')} -> closest available {
            fmt_hex('#da8730')
        } (Kaweco - Sunrise Orange)",
        f"{fmt_hex('#00ffff')} -> closest available {
            fmt_hex('#00c49f')
        } (Faber-Castell - Türkis Turquoise)",
        f"{fmt_hex('#0000ff')} -> closest available {
            fmt_hex('#4c58e0')
        } (Kaweco - Royal Blue)",
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
        f"Generating palette with tetradic using {fmt_hex(base_color)} "
        "(ODS source: data/golden.ods)" in log_lines
    )
    palette_lines = [line for line in log_lines if "-> closest available" in line]
    assert palette_lines == expected_palette_lines


def test_palette_ui_log_event_visible():
    """Ensure log_event writes to the on-screen Log widget."""

    async def run_case():
        async with PaletteApp().run_test(size=TEST_SIZE) as pilot:
            await pilot.pause(0.2)
            pilot.app.log_event("hello-log")
            await pilot.pause(0.1)
            lines = pilot.app.log_widget.lines
        return lines

    lines = asyncio.run(run_case())
    assert any(
        ("hello-log" in line.plain)
        if hasattr(line, "plain")
        else ("hello-log" in str(line))
        for line in lines
    )


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
        line.split(" -> closest available ")[1].split()[0] for line in palette_lines
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
            pilot.app.query_one("#use_selected").press()
            await pilot.pause(0.2)
            base_value = pilot.app.query_one("#base_input", Input).value
        return expected_hex, base_value

    expected_hex, base_value = asyncio.run(run_case())
    log_lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    assert base_value == expected_hex
    assert any(
        line.startswith(f"Using highlighted ink: {fmt_hex(expected_hex)}")
        for line in log_lines
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
        line.startswith(f"Selected base color from inks: {fmt_hex(expected_hex)}")
        for line in log_lines
    ), "Option selection was not logged"


async def _press_key(pilot, key: str):
    """Helper to send key presses in headless tests."""
    await pilot.press(key)
    await pilot.pause(0.1)


def test_palette_ui_jk_navigation():
    """j/k keys move within available inks and strategy radios."""

    async def run_case():
        async with PaletteApp().run_test(size=TEST_SIZE) as pilot:
            await pilot.pause(0.3)
            option_list = pilot.app.query_one("#available_colors", OptionList)
            option_list.focus()
            await _press_key(pilot, "j")
            assert option_list.highlighted == 1
            await _press_key(pilot, "k")
            assert option_list.highlighted == 0
            # move to strategies and test radio movement
            await pilot.click("#strategy_square_scheme")
            await _press_key(pilot, "j")
            selected = [
                btn
                for btn in pilot.app.query("#strategies RadioButton")
                if btn.value is True
            ]
            assert selected, "No strategy selected after navigation"
            names = [btn.id for btn in pilot.app.query("#strategies RadioButton")]
            selected_idx = names.index(selected[0].id)
            assert selected_idx >= names.index("strategy_square_scheme")

    asyncio.run(run_case())


def test_palette_ui_random_base(monkeypatch):
    """Random base should pick a random available color and log its label."""

    async def run_case():
        async with PaletteApp().run_test(size=TEST_SIZE) as pilot:
            await pilot.pause(0.3)
            target = pilot.app.available_colors[-1]
            monkeypatch.setattr(
                "ui.ui_color_palett_app.random.choice", lambda seq: target
            )
            pilot.app.query_one("#random_base").press()
            await pilot.pause(0.2)
            base_val = pilot.app.query_one("#base_input", Input).value
        return target, base_val

    target, base_val = asyncio.run(run_case())
    expected_hex, expected_label = target
    log_lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    assert base_val == expected_hex
    assert any(
        line == f"Random base color: {fmt_hex(expected_hex)} ({expected_label})"
        for line in log_lines
    ), "Random base selection not logged with label"


def test_palette_ui_combined_navigation():
    """Tab, arrows, and j/k should work together to move selection and focus."""

    def _selected_strategy(app):
        buttons = list(app.query("#strategies RadioButton"))
        return next(btn.id for btn in buttons if btn.value)

    async def run_case():
        async with PaletteApp().run_test(size=TEST_SIZE) as pilot:
            await pilot.pause(0.3)
            option_list = pilot.app.query_one("#available_colors", OptionList)
            option_list.focus()
            # arrows and j/k advance/reverse the option list
            await pilot.press("down")
            await pilot.press("j")
            assert option_list.highlighted == 2
            await pilot.press("up")
            await pilot.press("k")
            assert option_list.highlighted == 0
            # tab into strategies, then j moves selection down
            await pilot.press("tab")
            focused = pilot.app.focused
            assert getattr(focused, "id", "") == "strategies" or isinstance(
                focused, RadioButton
            )
            initial = _selected_strategy(pilot.app)
            await pilot.press("j")
            moved = _selected_strategy(pilot.app)
            assert moved != initial

    asyncio.run(run_case())


def test_palette_ui_generates_preview_file(monkeypatch, tmp_path):
    """Palette generation should render a preview PNG via draw helpers."""
    preview_path = tmp_path / "preview.png"
    monkeypatch.setattr("ui.ui_color_palett_app.PREVIEW_FILE", str(preview_path))

    async def run_case():
        async with PaletteApp().run_test(size=TEST_SIZE) as pilot:
            await pilot.pause(0.3)
            pilot.app.query_one("#base_input", Input).value = "#ff0000"
            await pilot.click("#strategy_tetradic")
            await pilot.click("#run")
            await pilot.pause(0.3)

    asyncio.run(run_case())
    assert preview_path.exists(), "Preview PNG was not created"


def test_palette_ui_update_preview_hint():
    """_update_preview_hint should change the preview Static text."""

    async def run_case():
        async with PaletteApp().run_test(size=TEST_SIZE) as pilot:
            await pilot.pause(0.2)
            pilot.app._update_preview_hint("Updated preview text")
            await pilot.pause(0.1)
            preview = pilot.app.query_one("#palette_preview")
            rendered = preview._render()
            if isinstance(rendered, str):
                content = rendered
            else:
                content = "".join(str(r) for r in rendered)
        return content

    content = asyncio.run(run_case())
    assert "Updated preview text" in str(content)


TEST_SIZE = (220, 160)
