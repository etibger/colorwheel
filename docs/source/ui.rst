User Interfaces
===============

Two Textual-based interfaces ship with the project:

Converter UI
------------
``ui.py`` exposes ``ConverterApp`` for format conversions (ODS, SQL DB, JSON, PNG).

* Launch with ``python ui.py``.
* Choose input/output formats via radio buttons.
* Provide file paths in the input/output fields and click **Run**.
* Progress and errors are logged to ``colorwheel_textual.log``.

Palette UI
----------
``ui_color_palett_app.py`` exposes ``PaletteApp`` for palette exploration.

* Launch with ``python ui_color_palett_app.py``.
* Pick a base color manually or highlight an ink from the loaded ODS palette.
* Select a palette strategy (tetradic, square scheme, temperature-driven, value-driven, or OKLCH).
* Click **Generate palette** to see the computed colors and their closest available inks, including brand/name metadata.
* Logs are written to ``colorwheel_palett_ui.log`` and surfaced in the on-screen log widget.

Testing UIs
-----------
Both UIs support Textual's ``run_test`` helper for headless testing. See
``tests/test_ui_app.py`` and ``tests/test_ui_color_palett_app.py`` for examples
that drive the widgets, click buttons, and assert on generated files or log output.
