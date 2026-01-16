"""
Master UI for launching the available Textual interfaces.

Overview
--------
Provides a single entry point for choosing between data format conversion and
palette generation UIs.

Usage
-----
Run ``python ui_master_app.py`` to start the selector UI.
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from textual.widgets import Button, Footer, Header, Log, RadioButton, RadioSet, Static

CHOICE_LABELS = {
    "data_conv": "Data format conversion",
    "palette_gen": "Palette generation",
}

CHOICE_TARGETS = {
    "data_conv": "ui_data_fmt_conv.py",
    "palette_gen": "ui_color_palett_app.py",
}


def verbosity_to_loglevel(verbosity: int) -> int:
    """
    Map verbosity count to logging levels.

    :param verbosity: Count of ``-v`` flags.
    :returns: Logging level value.
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
    logger = logging.getLogger("colorwheel_master_ui")
    logger.setLevel(level)
    logger.propagate = False
    err = logging.StreamHandler(sys.stderr)
    err.setLevel(logging.INFO)
    err.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    fh = logging.FileHandler("colorwheel_master_ui.log")
    fh.setLevel(level)
    fh.setFormatter(
        logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
    )
    logger.addHandler(err)
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
    logger.debug("ui_master_app.py execution begins (verbosity=%d)", args.verbose)
    logger.debug("attempting to import textual modules")
    return logger


logger = init_cli()
try:
    from textual.app import App, ComposeResult

    logger.debug("Imported textual modules successfully")
except ImportError:
    logger.error("'textual' library not found - install with 'pip install textual'.")
    sys.exit(1)


def build_launch_command(choice_key: str) -> list[str]:
    """
    Build the command to launch a selected UI.

    :param choice_key: Choice key from ``CHOICE_TARGETS``.
    :returns: Command list suitable for ``subprocess.run``.
    :raises ValueError: If the choice key is unknown.
    """
    target = CHOICE_TARGETS.get(choice_key)
    if not target:
        raise ValueError(f"Unknown UI choice: {choice_key}")
    script_path = Path(__file__).with_name(target)
    return [sys.executable, str(script_path)]


def spawn_app(command: Sequence[str]) -> subprocess.CompletedProcess:
    """
    Run the selected UI in a subprocess.

    :param command: Command list to execute.
    :returns: Completed process object.
    """
    return subprocess.run(command, check=True)


class MasterApp(App):
    """
    UI for selecting which interface to launch.

    Notes
    -----
    Spawns the selected UI as a subprocess and logs the action.
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    CSS = None

    def __init__(self, *args, **kwargs):
        logger.debug("MasterApp.__init__ start")
        super().__init__(*args, **kwargs)
        self.log_file = None
        self._mounted = False
        logger.debug("MasterApp.__init__ end")

    def compose(self) -> ComposeResult:
        logger.debug("compose() start")
        yield Header(show_clock=True)
        yield Static("Select an interface to launch:", id="help_text")
        with RadioSet(id="choice"):
            yield RadioButton(CHOICE_LABELS["data_conv"], id="data_conv", value=True)
            yield RadioButton(CHOICE_LABELS["palette_gen"], id="palette_gen")
        yield Button("Launch", id="launch")
        yield Log(id="logger", highlight=False)
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the log widget and log file."""
        logger.debug("on_mount() start")
        self.log_widget = self.query_one("#logger", Log)
        self.log_file = open("colorwheel_master_textual.log", "a", encoding="utf-8")
        self._mounted = True
        logger.debug("on_mount() complete")

    def on_unmount(self) -> None:
        """Close log file on exit."""
        logger.debug("on_unmount() start")
        if self.log_file:
            self.log_file.close()
            logger.debug("Closed colorwheel_master_textual.log")

    def log_event(self, message: str) -> None:
        """
        Write a message to the UI log and log file.

        :param message: Message to write.
        """
        if getattr(self, "_mounted", False):
            self.log_widget.write_line(message)
        if self.log_file:
            self.log_file.write(message + "\n")
            self.log_file.flush()

    def get_selected_choice(self) -> str:
        """
        Return the selected choice key.

        :returns: Choice key string.
        """
        selected = next(btn for btn in self.query("#choice RadioButton") if btn.value)
        return selected.id

    def launch_selected(self) -> None:
        """Launch the UI based on the selected radio button."""
        choice_key = self.get_selected_choice()
        command = build_launch_command(choice_key)
        self.log_event(f"Launching {CHOICE_LABELS[choice_key]}...")
        logger.debug("Launching command: %s", command)
        try:
            with self.suspend():
                spawn_app(command)
        except Exception as exc:
            message = str(exc).lower()
            if "suspend" not in message:
                raise
            logger.debug("Suspend unavailable (%s); launching without suspend", exc)
            spawn_app(command)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Launch button presses."""
        if event.button.id != "launch":
            return
        try:
            self.launch_selected()
        except Exception as exc:
            logger.error("Failed to launch selection: %s", exc)
            self.log_event(f"Error: {exc}")


if __name__ == "__main__":
    logger.info("__main__ start")
    app = MasterApp()
    try:
        logger.debug("Calling app.run()")
        app.run()
        logger.debug("app.run() completed")
    except Exception as exc:
        logger.debug("__main__ exception: %s", exc)
        raise
    finally:
        logger.info("__main__ end")
