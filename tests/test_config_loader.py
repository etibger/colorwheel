"""
Tests for config_loader.load_config defaults and overrides.
"""

from config_loader import load_config


def test_load_config_defaults(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text("", encoding="utf-8")
    monkeypatch.setattr("config_loader._CONFIG_PATH", cfg_path)
    # Reset cache
    monkeypatch.setattr("config_loader._CONFIG_CACHE", None)
    cfg = load_config()
    assert cfg["ods_path"] == "data/golden.ods"


def test_load_config_override(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text('palette_log_file = "custom.log"\n', encoding="utf-8")
    monkeypatch.setattr("config_loader._CONFIG_PATH", cfg_path)
    monkeypatch.setattr("config_loader._CONFIG_CACHE", None)
    cfg = load_config()
    assert cfg["palette_log_file"] == "custom.log"
    # Defaults should remain for other keys
    assert cfg["wheel_size"] == 600
