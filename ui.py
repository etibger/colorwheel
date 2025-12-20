"""
Textual-based interactive interface for data format conversion and color wheel output.
"""

import datetime
import json
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

from main import generate_wheel_from_db

# Configure debug logging
logging.basicConfig(
    filename="colorwheel_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)
logging.debug("ui.py import start")
try:
    from textual.app import App, ComposeResult

    logging.debug("Imported textual modules successfully")
except ImportError:
    logging.error("'textual' library not found - install with 'pip install textual'.")
    print(
        "Error: 'textual' library is not installed. "
        "Please install it with 'pip install textual'",
        file=sys.stderr,
    )
    sys.exit(1)

# Simple startup debug
print("[DEBUG] ui.py loaded", file=sys.stderr, flush=True)

# Debug startup stages
print("[DEBUG] ui.py execution begins", file=sys.stderr, flush=True)
print("[DEBUG] attempting to import textual modules", file=sys.stderr, flush=True)

# Debug logger for startup stages
_debug_file = open("colorwheel_debug.log", "a", encoding="utf-8")


def debug(msg: str) -> None:
    ts = datetime.datetime.now().isoformat()
    _debug_file.write(f"{ts} [DEBUG] {msg}\n")
    _debug_file.flush()


debug("Module imported")
print("[DEBUG] Module imported", flush=True)
print("[DEBUG] Module imported")


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
        debug("ConverterApp.__init__ start")
        print("[DEBUG] ConverterApp.__init__ start")
        super().__init__(*args, **kwargs)
        debug("ConverterApp.__init__ end")
        print("[DEBUG] ConverterApp.__init__ end")

    def compose(self) -> ComposeResult:
        debug("compose() start")
        print("[DEBUG] compose() start")
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
        debug("yielding Run button")
        print("[DEBUG] yielding Run button")
        yield Button("Run", id="run")
        debug("yielding Log console")
        print("[DEBUG] yielding Log console")
        # Logger panel for events (use 'logger' id to avoid shadowing App.console)
        yield Log(id="logger", highlight=False)
        # Footer at bottom
        yield Footer()

    def on_mount(self) -> None:
        debug("on_mount() start")
        print("[DEBUG] on_mount() start")
        # Retrieve log widget
        self.log_widget = self.query_one("#logger", Log)
        # Open GUI event log file
        self.log_file = open("colorwheel_textual.log", "a", encoding="utf-8")
        debug("Opened colorwheel_textual.log")
        print("[DEBUG] Opened colorwheel_textual.log")
        # Mark as mounted and avoid early log rendering
        self._mounted = True
        debug("on_mount() complete")
        print("[DEBUG] on_mount() complete")

    def on_unmount(self) -> None:
        """Close log file on exit."""
        debug("on_unmount() start")
        # Safely close GUI event log file
        if hasattr(self, "log_file") and self.log_file:
            self.log_file.close()
            debug("Closed colorwheel_textual.log")

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
        debug(f"on_button_pressed: id={event.button.id}")
        if event.button.id != "run":
            debug("on_button_pressed: ignored non-run")
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
        # Perform conversion: SQL DB -> PNG
        try:
            debug("Starting conversion block")
            # SQL DB -> PNG
            if input_choice == "SQL DB" and output_choice == "PNG":
                generate_wheel_from_db(input_path, output_path)
                self.log_event(f"Generated PNG at {output_path}")
            # ODS -> JSON
            elif input_choice == "ODS" and output_choice == "JSON":
                from data_reader import DataReader

                reader = DataReader(input_path)
                pens = [
                    {
                        "id": p.id,
                        "brand": p.brand,
                        "name": p.name,
                        "nib_size": p.nib_size,
                        "body_color": p.body_color,
                    }
                    for p in reader.pens.values()
                ]
                inks = [
                    {
                        "id": i.id,
                        "brand": i.brand,
                        "name": i.name,
                        "srgb_h": i.color_srgb[0],
                        "srgb_s": i.color_srgb[1],
                        "srgb_v": i.color_srgb[2],
                        "rgb_hex": i.color_rgb_hex,
                    }
                    for i in reader.inks.values()
                ]
                setups = [
                    {"id": s.id, "pen_id": s.pen_id, "ink_id": s.ink_id}
                    for s in reader.setups.values()
                ]
                data = {"pens": pens, "inks": inks, "setups": setups}
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                self.log_event(f"Exported JSON at {output_path}")
            else:
                self.log_event("Selected conversion not implemented yet.")
        except Exception as e:
            debug(f"Error during conversion: {e}")
            self.log_event(f"Error during conversion: {e}")


if __name__ == "__main__":
    # Entry point: debug start
    debug("__main__ start")
    print("[DEBUG] __main__ start", flush=True)
    app = ConverterApp()
    # Run the app and capture any exceptions
    try:
        debug("Calling app.run()")
        print("[DEBUG] Calling app.run()", flush=True)
        app.run()
        debug("app.run() completed")
        print("[DEBUG] app.run() completed", flush=True)
    except Exception as e:
        debug(f"__main__ exception: {e}")
        print(f"[DEBUG] __main__ exception: {e}", flush=True)
        raise
    finally:
        debug("__main__ end")
        print("[DEBUG] __main__ end", flush=True)
