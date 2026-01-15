"""
.. module:: config_loader
   :synopsis: Configuration loader for project-wide settings.

Configuration is read from ``config.toml`` located beside this module. If the file
is missing or malformed, sane defaults are applied. Sphinx will include this
module in the API docs for easy reference.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Dict

_DEFAULTS: Dict[str, Any] = {
    "ods_path": "data/golden.ods",
    "palette_log_file": "colorwheel_palett_ui.log",
    "color_name_cache": "data/color_names.pickle",
    "color_api_url": "https://api.color.pizza/v1/",
    "wheel_size": 600,
    "legend_width": 260,
    "marker_radius": 6,
}

_CONFIG_CACHE: Dict[str, Any] | None = None
_CONFIG_PATH = Path(__file__).resolve().parent / "config.toml"


def load_config() -> Dict[str, Any]:
    """
    Load configuration from ``config.toml`` with defaults as fallback.

    :returns: Mapping of configuration keys to values.
    :rtype: dict[str, Any]
    """
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    data = _DEFAULTS.copy()
    if _CONFIG_PATH.exists():
        try:
            loaded = tomllib.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data.update(loaded)
        except Exception:
            # Ignore malformed configuration and stick with defaults
            pass
    _CONFIG_CACHE = data
    return _CONFIG_CACHE
