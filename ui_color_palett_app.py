"""
Textual-based interface to run :mod:`color_palett_app` with a chosen base color and strategy.

Overview
--------
This UI lists available inks from an ODS file, allows picking a palette strategy,
and logs the generated palette alongside the closest available inks (brand and name).

Usage
-----
Run ``python ui_color_palett_app.py`` for the interactive interface, or
use ``PaletteApp().run_test()`` in tests for headless execution.
"""

import argparse
import logging
import os
import random
import subprocess
import sys
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont
from textual import events
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Log,
    OptionList,
    RadioButton,
    RadioSet,
    Static,
)
from textual.widgets.option_list import Option

import palette_generator as pg
from color_palett_app import STRATEGIES, find_closest
from color_utils import (
    format_hex_with_name,
    load_color_name_cache,
    save_color_name_cache,
)
from config_loader import load_config
from data_reader import DataReader
from draw import IMAGE_SIZE, draw_color_wheel, draw_legend, draw_markers

CONFIG = load_config()
ODS_PATH = CONFIG["ods_path"]
LOG_FILE = CONFIG["palette_log_file"]
CACHE_FILE = CONFIG["color_name_cache"]
PREVIEW_FILE = CONFIG["palette_preview_file"]


def verbosity_to_loglevel(verbosity: int) -> int:
    """
    Map verbosity count to logging levels.

    * 0 -> ERROR
    * 1 -> WARNING
    * 2 -> INFO
    * >=3 -> DEBUG
    """
    if verbosity <= 0:
        return logging.ERROR
    if verbosity == 1:
        return logging.WARNING
    if verbosity == 2:
        return logging.INFO
    return logging.DEBUG


def setup_logging(verbose: int) -> logging.Logger:
    """
    Configure and return a logger based on verbosity count.

    :param verbose: Count of ``-v`` flags.
    :returns: Configured logger instance.
    """
    level = verbosity_to_loglevel(verbose)
    logger = logging.getLogger("color_palett_ui")
    # Allow handlers to filter; keep logger open at DEBUG so UI events are visible.
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(level)
    fh.setFormatter(
        logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
    )
    logger.addHandler(fh)
    logger.debug("Logging initialized at level %s", logging.getLevelName(level))
    return logger


def init_cli() -> logging.Logger:
    """
    Parse CLI args and configure logger.

    :returns: Logger configured according to CLI flags.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (use -v, -vv)",
    )
    args, _ = parser.parse_known_args()
    logger = setup_logging(args.verbose)
    logger.debug("ui_color_palett_app.py execution begins (verbosity=%d)", args.verbose)
    logger.debug("attempting to import textual modules")
    return logger


logger = init_cli()
# Load cached color names at startup
load_color_name_cache(CACHE_FILE)
try:
    from textual.app import App, ComposeResult

    logger.debug("Imported textual modules successfully")
except ImportError:
    logger.error("'textual' library not found - install with 'pip install textual'.")
    sys.exit(1)


class PaletteApp(App):
    """UI for selecting a base color and palette strategy."""

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("o", "open_preview", "Open Preview", priority=True),
    ]

    CSS = """
    #bottom_panel {
        height: 1fr;
    }
    #logger {
        width: 2fr;
    }
    #palette_preview {
        width: 1fr;
    }
    """

    def __init__(self, *args, **kwargs):
        """Initialize state and preload ink data."""
        logger.debug("PaletteApp.__init__ start")
        super().__init__(*args, **kwargs)
        self.log_file = None
        self.available_colors: list[tuple[str, str]] = []
        self.hex_to_label: dict[str, str] = {}
        self._mounted = False
        self.load_available_colors()
        logger.debug("PaletteApp.__init__ end")

    def load_available_colors(self) -> None:
        """
        Load inks from the ODS file to seed selection widgets.

        Populates ``self.available_colors`` and ``self.hex_to_label``.
        """
        logger.debug("Loading available colors from %s", ODS_PATH)
        try:
            reader = DataReader(ODS_PATH)
        except Exception as exc:
            logger.error("Failed to load %s: %s", ODS_PATH, exc)
            self.available_colors = []
            self.hex_to_label = {}
            return
        self.available_colors = []
        self.hex_to_label = {}
        for ink in reader.inks.values():
            hex_color = "#" + ink.color_rgb_hex
            label = f"{ink.brand} - {ink.name} (#{ink.color_rgb_hex})"
            self.available_colors.append((hex_color, label))
            self.hex_to_label[hex_color] = label
        logger.info("Loaded %d inks from %s", len(self.available_colors), ODS_PATH)

    def compose(self) -> ComposeResult:
        """
        Build the UI layout with inputs, strategy radio set, log, and preview pane.
        """
        logger.debug("compose() start")
        yield Header(show_clock=True)
        yield Static(f"Using ODS palette source: {ODS_PATH}", id="ods_hint")
        yield Static("Enter or choose a base color:", id="label_base")
        yield Input(placeholder="#ff0000", id="base_input")
        yield Button("Use highlighted ink", id="use_selected")
        yield Button("Random available color", id="random_base")
        yield Static("Available inks (Enter to pick):", id="label_available")
        if self.available_colors:
            options: Iterable[Option] = (
                Option(label, id=hex_color)
                for hex_color, label in self.available_colors
            )
            yield OptionList(*options, id="available_colors")
        else:
            yield Static("No inks loaded from data/golden.ods", id="available_empty")
        yield Static("Select palette strategy:", id="label_strategy")
        with RadioSet(id="strategies"):
            for idx, strat in enumerate(STRATEGIES):
                yield RadioButton(strat, id=f"strategy_{strat}", value=(idx == 0))
        yield Button("Generate palette", id="run")
        with Horizontal(id="bottom_panel"):
            yield Log(id="logger", highlight=False)
            yield Static("Palette preview not generated yet.", id="palette_preview")
        yield Button("Open preview", id="open_preview")
        yield Footer()

    def on_mount(self) -> None:
        """Open log file, cache log widget, and prime the base input."""
        logger.debug("on_mount() start")
        self.log_widget = self.query_one("#logger", Log)
        self.log_file = open(LOG_FILE, "a", encoding="utf-8")
        self._mounted = True
        if self.available_colors:
            first_hex, _ = self.available_colors[0]
            self.query_one("#base_input", Input).value = first_hex
        logger.debug("on_mount() complete")

    def on_unmount(self) -> None:
        """Close log file and persist color-name cache on exit."""
        logger.debug("on_unmount() start")
        if hasattr(self, "log_file") and self.log_file:
            self.log_file.close()
            logger.debug("Closed %s", LOG_FILE)
        save_color_name_cache(CACHE_FILE)
        self._update_preview_hint(f"Palette preview saved to: {PREVIEW_FILE}")

    def action_quit(self) -> None:
        """Persist color name cache on quit."""
        try:
            save_color_name_cache(CACHE_FILE)
        except Exception:
            pass
        self.exit()

    def on_close(self) -> None:
        """Handle close events (e.g., Ctrl+C, command palette) by exiting."""
        try:
            save_color_name_cache(CACHE_FILE)
        except Exception:
            pass
        self.exit()

    def action_open_preview(self) -> None:
        """Keyboard binding to open the generated preview image."""
        self.open_preview_image()

    def on_key(self, event: events.Key) -> None:
        """
        Handle key presses for quit shortcuts to ensure the app exits reliably.

        :param event: Textual key event.
        """
        if event.key in ("q", "ctrl+c"):
            event.stop()
            self.action_quit()

    def log_event(self, message: str) -> None:
        """
        Write message to on-screen log and log file.

        :param message: Text to log.
        """
        logger.info(message)
        try:
            if getattr(self, "_mounted", False):
                self.log_widget.write_line(message)
        except AttributeError:
            pass
        if self.log_file:
            self.log_file.write(message + "\n")
            self.log_file.flush()

    def normalize_base_color(self, raw: str) -> str:
        """
        Ensure base color is ``#RRGGBB`` and validate basic length.

        :param raw: User-entered base color string.
        :returns: Normalized hex with leading ``#``.
        :raises ValueError: If empty or wrong length.
        """
        base = raw.strip()
        if not base:
            raise ValueError("Base color is empty.")
        if not base.startswith("#"):
            base = "#" + base
        if len(base) != 7:
            raise ValueError("Base color must be in #RRGGBB format.")
        return base

    def generate_palette(self, base_color: str, strategy: str) -> list[tuple[str, str]]:
        """
        Generate palette and pair each color with the closest available ink.

        :param base_color: Hex ``#RRGGBB`` base color.
        :param strategy: Strategy name from ``STRATEGIES``.
        :returns: List of tuples ``(color, closest_available_hex)``.
        """
        if not self.available_colors:
            raise ValueError("No inks loaded from data/golden.ods.")
        available_hexes = [color for color, _ in self.available_colors]
        func = getattr(pg, strategy)
        if strategy in (
            "tetradic",
            "square_scheme",
            "split_complementary_accent",
            "oklch_sampling",
        ):
            palette = func(base_color)
        else:
            palette = func(available_hexes)
        return [(color, find_closest(color, available_hexes)) for color in palette]

    def _label_for_hex(self, hex_color: str) -> str:
        """Return brand/name without trailing hex, if known."""
        label = self.hex_to_label.get(hex_color, "")
        if " (#" in label:
            return label.split(" (#", 1)[0]
        return label

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """
        Populate the base color input when an ink is chosen from the list.

        :param event: Textual OptionSelected event.
        """
        hex_color = event.option.id or event.option.prompt
        label = self._label_for_hex(hex_color)
        self.query_one("#base_input", Input).value = hex_color
        suffix = f" ({label})" if label else ""
        self.log_event(
            f"Selected base color from inks: {format_hex_with_name(hex_color)}{suffix}"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Route button presses to handlers."""
        logger.debug("on_button_pressed: id=%s", event.button.id)
        if event.button.id == "run":
            self.handle_run()
        elif event.button.id == "random_base":
            self.handle_random_base()
        elif event.button.id == "use_selected":
            self.handle_use_selected()
        elif event.button.id == "open_preview":
            self.open_preview_image()

    def handle_random_base(self) -> None:
        """Set base color to a random available ink."""
        if not self.available_colors:
            self.log_event("No inks available to randomize from.")
            return
        hex_color, label = random.choice(self.available_colors)
        self.query_one("#base_input", Input).value = hex_color
        self.log_event(
            f"Random base color: {format_hex_with_name(hex_color)} ({label})"
        )

    def _update_preview_hint(self, message: str) -> None:
        """
        Update the preview sidebar text safely.

        :param message: Text to display in the preview panel.
        """
        try:
            preview = self.query_one("#palette_preview", Static)
            preview.update(message)
        except Exception:
            pass

    def render_palette_preview(
        self, palette: list[tuple[str, str]], out_path: str | None = None
    ) -> None:
        """
        Render palette preview PNG using draw.py helpers.

        :param palette: List of ``(color, closest)`` tuples.
        :param out_path: Optional override path for the preview PNG.
        """
        target_path = out_path or PREVIEW_FILE
        os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)
        img = Image.new("RGB", IMAGE_SIZE, "white")
        dr = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 16)
            font_bold = ImageFont.truetype("DejaVuSans.ttf", 18)
        except IOError:
            font = font_bold = ImageFont.load_default()
        markers = [(format_hex_with_name(color), color) for color, _closest in palette]
        draw_color_wheel(img)
        positions = draw_markers(dr, markers, font_bold)
        draw_legend(dr, positions, font, font_bold)
        img.save(target_path)
        self.log_event(f"Palette preview saved to: {target_path}")
        self._update_preview_hint(f"Palette preview saved to: {target_path}")

    def open_preview_image(self) -> None:
        """
        Open the generated preview PNG using the OS default viewer (macOS: ``open``).

        Falls back to logging an error if the preview file is missing.
        """
        if not os.path.exists(PREVIEW_FILE):
            self.log_event(f"Preview file not found: {PREVIEW_FILE}")
            return
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", PREVIEW_FILE])
            else:
                subprocess.Popen(["xdg-open", PREVIEW_FILE])
        except Exception as exc:
            self.log_event(f"Could not open preview: {exc}")

    def handle_use_selected(self) -> None:
        """
        Use the currently highlighted ink from the list as base color.

        :raises: Logs guidance if no highlight is present.
        """
        try:
            option_list = self.query_one("#available_colors", OptionList)
        except Exception:
            self.log_event("Ink list not available.")
            return
        if option_list.highlighted is None:
            self.log_event("Highlight an ink (arrow keys + Enter) to use it.")
            return
        # highlighted is an index; fetch the actual Option object
        option = option_list.get_option_at_index(option_list.highlighted)
        hex_color = option.id or option.prompt
        label = self._label_for_hex(hex_color)
        self.query_one("#base_input", Input).value = hex_color
        suffix = f" ({label})" if label else ""
        self.log_event(
            f"Using highlighted ink: {format_hex_with_name(hex_color)}{suffix}"
        )

    def handle_run(self) -> None:
        """Generate the palette based on current selections."""
        base_input = self.query_one("#base_input", Input).value or ""
        try:
            base_color = self.normalize_base_color(base_input)
        except ValueError as exc:
            self.log_event(str(exc))
            return
        try:
            strategy = next(
                btn.label.plain if hasattr(btn.label, "plain") else str(btn.label)
                for btn in self.query("#strategies RadioButton")
                if btn.value
            )
        except StopIteration:
            self.log_event("Select a palette strategy.")
            return
        self.log_event(
            f"Generating palette with {strategy} using "
            f"{format_hex_with_name(base_color)} (ODS source: {ODS_PATH})"
        )
        try:
            palette = self.generate_palette(base_color, strategy)
        except Exception as exc:
            logger.exception("Palette generation failed")
            self.log_event(f"Error: {exc}")
            return
        self.render_palette_preview(palette)
        for color, closest in palette:
            label = self._label_for_hex(closest)
            suffix = f" ({label})" if label else ""
            self.log_event(
                f"{format_hex_with_name(color)} -> "
                f"closest available {format_hex_with_name(closest)}{suffix}"
            )


if __name__ == "__main__":
    logger.info("__main__ start")
    app = PaletteApp()
    try:
        logger.debug("Calling app.run()")
        app.run()
        logger.debug("app.run() completed")
    except Exception as e:
        logger.debug("__main__ exception: %s", e)
        raise
    finally:
        logger.info("__main__ end")
