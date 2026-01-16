User Interfaces
===============

Three Textual-based interfaces ship with the project:

Master UI
---------
``ui/ui_master_app.py`` exposes ``MasterApp`` for choosing between the available UIs.

* Launch with ``python ui/ui_master_app.py``.
* Select **Data format conversion** or **Palette generation**.
* Click **Launch** to open the chosen interface.

Converter UI
------------
``ui/ui_data_fmt_conv.py`` exposes ``ConverterApp`` for format conversions (ODS, SQL DB, JSON, PNG).

* Launch with ``python ui/ui_data_fmt_conv.py``.
* Choose input/output formats via radio buttons.
* Provide file paths in the input/output fields and click **Run**.
* Progress and errors are logged to ``colorwheel_textual.log``.

Palette UI
----------
``ui/ui_color_palett_app.py`` exposes ``PaletteApp`` for palette exploration.

* Launch with ``python ui/ui_color_palett_app.py``.
* Pick a base color manually or highlight an ink from the loaded ODS palette.
* Select a palette strategy (tetradic, square scheme, temperature-driven, value-driven, or OKLCH).
* Click **Generate palette** to see the computed colors and their closest available inks, including brand/name metadata.
* Logs are written to ``colorwheel_palett_ui.log`` and surfaced in the on-screen log widget.

Testing UIs
-----------
All UIs support Textual's ``run_test`` helper for headless testing. See
``tests/test_ui_app.py``, ``tests/test_ui_color_palett_app.py``, and
``tests/test_ui_master_app.py`` for examples
that drive the widgets, click buttons, and assert on generated files or log output.
