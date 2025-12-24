"""
Textual-based interactive interface for data format conversion and color wheel output.
"""

import argparse
import logging
import sys

from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Log,
    RadioButton,
    RadioSet,
    Static,
)

from ui_converters import handle_conversion


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
    logger = logging.getLogger("colorwheel_ui")
    logger.setLevel(level)
    logger.propagate = False
    # stderr handler: always show INFO or higher
    err = logging.StreamHandler(sys.stderr)
    err.setLevel(logging.INFO)
    err.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    # file handler: log up to verbose level
    fh = logging.FileHandler("colorwheel_ui.log")
    fh.setLevel(level)
    fh.setFormatter(
        logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
    )
    logger.addHandler(err)
    logger.addHandler(fh)
    logger.debug("Logging initialized at level %s", logging.getLevelName(level))
    return logger


def init_cli() -> tuple[int, logging.Logger]:
    """Parse CLI args and configure logger."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (use -v, -vv)",
    )
    # parse_known_args allows downstream libraries (e.g. Textual)
    # to receive their own flags
    args, _ = parser.parse_known_args()
    logger = setup_logging(args.verbose)
    # Debug initial messages based on verbose
    logger.debug("ui.py execution begins (verbosity=%d)", args.verbose)
    logger.debug("attempting to import textual modules")
    # Return only configured logger
    return logger


# Initialize CLI parsing and logger
logger = init_cli()
try:
    from textual.app import App, ComposeResult

    logger.debug("Imported textual modules successfully")
except ImportError:
    logger.error("'textual' library not found - install with 'pip install textual'.")
    sys.exit(1)

logger.debug("Module imported")


class ConverterApp(App):
    """A simple UI to choose input/output formats and run conversion."""

    """
    CSS styling for layout.
    """
    # Keybindings: quit app
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    # Use default CSS styling
    CSS = None

    def __init__(self, *args, **kwargs):
        logger.debug("ConverterApp.__init__ start")
        super().__init__(*args, **kwargs)
        logger.debug("ConverterApp.__init__ end")

    def compose(self) -> ComposeResult:
        logger.debug("compose() start")
        yield Header(show_clock=True)
        # Help instructions for navigation
        yield Static("Use Tab to navigate and Enter to select.", id="help_text")
        yield Static("Select Input Format:", id="label_input")
        with RadioSet(id="input"):  # input format options
            yield RadioButton("ODS", id="ods_in")
            yield RadioButton("SQL DB", id="sql_in")
            yield RadioButton("JSON", id="json_in", value=True)
        # Input file selection
        yield Static("Input file path:", id="label_input_path")
        yield Input(placeholder="e.g. data/file.ods or data/db.sqlite", id="input_path")
        yield Static("Select Output Format:", id="label_output")
        with RadioSet(id="output"):  # output format options
            yield RadioButton("ODS", id="ods_out")
            yield RadioButton("SQL DB", id="sql_out")
            yield RadioButton("JSON", id="json_out")
            yield RadioButton("PNG", id="png_out", value=True)
        # Output file selection
        yield Static("Output file path:", id="label_output_path")
        yield Input(placeholder="e.g. output.json or wheel.png", id="output_path")
        logger.debug("yielding Run button")
        yield Button("Run", id="run")
        logger.debug("yielding Log console")
        # Logger panel for events (use 'logger' id to avoid shadowing App.console)
        yield Log(id="logger", highlight=False)
        # Footer at bottom
        yield Footer()

    def on_mount(self) -> None:
        logger.debug("on_mount() start")
        # Retrieve log widget
        self.log_widget = self.query_one("#logger", Log)
        # Open GUI event log file
        self.log_file = open("colorwheel_textual.log", "a", encoding="utf-8")
        logger.debug("Opened colorwheel_textual.log")
        # Mark as mounted and avoid early log rendering
        self._mounted = True
        logger.debug("on_mount() complete")

    def on_unmount(self) -> None:
        """Close log file on exit."""
        logger.debug("on_unmount() start")
        # Safely close GUI event log file
        if hasattr(self, "log_file") and self.log_file:
            self.log_file.close()
            logger.debug("Closed colorwheel_textual.log")

    def log_event(self, message: str) -> None:
        """Write message to console and log file."""
        # Safely write to log widget and file
        try:
            if getattr(self, "_mounted", False):
                # Write each message as a new line
                self.log_widget.write_line(message)
        except AttributeError:
            # Skip widget write if unsupported
            pass
        # Always write to log file
        self.log_file.write(message + "\n")
        self.log_file.flush()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the Run button press."""
        logger.debug(f"on_button_pressed: id={event.button.id}")
        if event.button.id != "run":
            logger.debug("on_button_pressed: ignored non-run")
            return
        # Retrieve selected formats from RadioButtons
        input_choice = next(
            btn.label for btn in self.query("#input RadioButton") if btn.value
        )
        output_choice = next(
            btn.label for btn in self.query("#output RadioButton") if btn.value
        )
        # Retrieve file paths
        input_path = self.query_one("#input_path", Input).value or ""
        output_path = self.query_one("#output_path", Input).value or ""
        self.log_event(
            f"Converting from {input_choice}:{input_path} "
            f"to {output_choice}:{output_path}..."
        )
        try:
            logger.debug("Starting conversion dispatch")
            handle_conversion(input_choice, output_choice, input_path, output_path)
        except Exception as e:
            logger.debug(f"Conversion error: {e}")
            self.log_event(f"Error: {e}")


if __name__ == "__main__":
    # Entry point: debug start
    logger.info("__main__ start")
    app = ConverterApp()
    # Run the app and capture any exceptions
    try:
        logger.debug("Calling app.run()")
        app.run()
        logger.debug("app.run() completed")
    except Exception as e:
        logger.debug(f"__main__ exception: {e}")
        raise
    finally:
        logger.info("__main__ end")
