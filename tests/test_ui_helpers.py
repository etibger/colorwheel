"""
Unit tests for ``ui_data_fmt_conv.py`` helper functions.

Overview
--------
Exercises ``verbosity_to_loglevel`` and ``init_cli``.
"""

import logging
import sys

import pytest

import ui_data_fmt_conv as ui

def test_verbosity_to_loglevel():
    """Map verbosity counts to logging levels correctly."""
    assert ui.verbosity_to_loglevel(0) == logging.ERROR
    assert ui.verbosity_to_loglevel(1) == logging.WARNING
    assert ui.verbosity_to_loglevel(2) == logging.INFO
    assert ui.verbosity_to_loglevel(3) == logging.DEBUG

@pytest.mark.parametrize("argv, expected_level", [
    (["ui_data_fmt_conv.py"], logging.ERROR),
    (["ui_data_fmt_conv.py", "-v"], logging.WARNING),
    (["ui_data_fmt_conv.py", "-vv"], logging.INFO),
    (["ui_data_fmt_conv.py", "-vvv"], logging.DEBUG),
])
def test_init_cli_sets_logger_level(monkeypatch, argv, expected_level):
    """init_cli returns a logger with level matching verbosity flags."""
    # Prevent pytest from capturing '-v' flags
    monkeypatch.setenv('PYTEST_DISABLE_PLUGIN_AUTOLOAD', '1')
    monkeypatch.setattr(sys, 'argv', argv)
    logger = ui.init_cli()
    assert isinstance(logger, logging.Logger)
    assert logger.level == expected_level
    # Should have both console and file handlers
    handler_types = {type(h) for h in logger.handlers}
    assert logging.StreamHandler in handler_types
    assert logging.FileHandler in handler_types
