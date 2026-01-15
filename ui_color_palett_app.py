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
import random
import sys
from typing import Iterable

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
from data_reader import DataReader

ODS_PATH = "data/golden.ods"
LOG_FILE = "colorwheel_palett_ui.log"


def verbosity_to_loglevel(verbosity: int) -> int:
    # Map verbosity count to logging levels: 0->ERROR, 1->WARNING, 2->INFO, >=3->DEBUG
    if verbosity <= 0:
        return logging.ERROR
    if verbosity == 1:
        return logging.WARNING
    if verbosity == 2:
        return logging.INFO
    return logging.DEBUG


def setup_logging(verbose: int) -> logging.Logger:
    """Configure and return a logger based on verbosity count."""
    level = verbosity_to_loglevel(verbose)
    logger = logging.getLogger("color_palett_ui")
    logger.setLevel(level)
    logger.propagate = False
    err = logging.StreamHandler(sys.stderr)
    err.setLevel(logging.INFO)
    err.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(level)
    fh.setFormatter(
        logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
    )
    logger.addHandler(err)
    logger.addHandler(fh)
    logger.debug("Logging initialized at level %s", logging.getLevelName(level))
    return logger


def init_cli() -> logging.Logger:
    """Parse CLI args and configure logger."""
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
try:
    from textual.app import App, ComposeResult

    logger.debug("Imported textual modules successfully")
except ImportError:
    logger.error("'textual' library not found - install with 'pip install textual'.")
    sys.exit(1)


class PaletteApp(App):
    """UI for selecting a base color and palette strategy."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    CSS = None

    def __init__(self, *args, **kwargs):
        logger.debug("PaletteApp.__init__ start")
        super().__init__(*args, **kwargs)
        self.log_file = None
        self.available_colors: list[tuple[str, str]] = []
        self.hex_to_label: dict[str, str] = {}
        self._mounted = False
        self.load_available_colors()
        logger.debug("PaletteApp.__init__ end")

    def load_available_colors(self) -> None:
        """Load inks from the ODS file to seed selection widgets."""
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
        yield Log(id="logger", highlight=False)
        yield Footer()

    def on_mount(self) -> None:
        logger.debug("on_mount() start")
        self.log_widget = self.query_one("#logger", Log)
        self.log_file = open(LOG_FILE, "a", encoding="utf-8")
        self._mounted = True
        if self.available_colors:
            first_hex, _ = self.available_colors[0]
            self.query_one("#base_input", Input).value = first_hex
        logger.debug("on_mount() complete")

    def on_unmount(self) -> None:
        logger.debug("on_unmount() start")
        if hasattr(self, "log_file") and self.log_file:
            self.log_file.close()
            logger.debug("Closed %s", LOG_FILE)

    def log_event(self, message: str) -> None:
        """Write message to console and log file."""
        try:
            if getattr(self, "_mounted", False):
                self.log_widget.write_line(message)
        except AttributeError:
            pass
        if self.log_file:
            self.log_file.write(message + "\n")
            self.log_file.flush()

    def normalize_base_color(self, raw: str) -> str:
        """Ensure base color is #RRGGBB and validate basic length."""
        base = raw.strip()
        if not base:
            raise ValueError("Base color is empty.")
        if not base.startswith("#"):
            base = "#" + base
        if len(base) != 7:
            raise ValueError("Base color must be in #RRGGBB format.")
        return base

    def generate_palette(self, base_color: str, strategy: str) -> list[tuple[str, str]]:
        """Generate palette and pair each color with the closest available ink."""
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
        """Populate the base color input when an ink is chosen."""
        hex_color = event.option.id or event.option.prompt
        label = self._label_for_hex(hex_color)
        self.query_one("#base_input", Input).value = hex_color
        suffix = f" ({label})" if label else ""
        self.log_event(f"Selected base color from inks: {hex_color}{suffix}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        logger.debug("on_button_pressed: id=%s", event.button.id)
        if event.button.id == "run":
            self.handle_run()
        elif event.button.id == "random_base":
            self.handle_random_base()
        elif event.button.id == "use_selected":
            self.handle_use_selected()

    def handle_random_base(self) -> None:
        """Set base color to a random available ink."""
        if not self.available_colors:
            self.log_event("No inks available to randomize from.")
            return
        hex_color, label = random.choice(self.available_colors)
        self.query_one("#base_input", Input).value = hex_color
        self.log_event(f"Random base color: {label}")

    def handle_use_selected(self) -> None:
        """Use the currently highlighted ink from the list as base color."""
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
        self.log_event(f"Using highlighted ink: {hex_color}{suffix}")

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
            f"Generating palette with {strategy} using {base_color} "
            f"(ODS source: {ODS_PATH})"
        )
        try:
            palette = self.generate_palette(base_color, strategy)
        except Exception as exc:
            logger.exception("Palette generation failed")
            self.log_event(f"Error: {exc}")
            return
        for color, closest in palette:
            label = self._label_for_hex(closest)
            suffix = f" ({label})" if label else ""
            self.log_event(f"{color} -> closest available {closest}{suffix}")


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
