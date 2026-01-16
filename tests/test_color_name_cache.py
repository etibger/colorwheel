"""
Tests for color name memoization, persistence, and API fallbacks.
"""

import pickle

from utils.color_utils import (
    COLOR_NAME_CACHE,
    hex_to_color_name,
    load_color_name_cache,
    save_color_name_cache,
)


def test_load_color_name_cache(tmp_path):
    cache_file = tmp_path / "cache.pkl"
    data = {"#123456": "Custom Name"}
    with open(cache_file, "wb") as f:
        pickle.dump(data, f)
    COLOR_NAME_CACHE.clear()
    assert load_color_name_cache(str(cache_file)) is True
    assert COLOR_NAME_CACHE["#123456"] == "Custom Name"


def test_hex_to_color_name_memoization(monkeypatch, tmp_path):
    calls = []

    def fake_api(hex_code):
        calls.append(hex_code)
        return "API Name"

    monkeypatch.setattr("utils.color_utils.get_color_name_from_api", fake_api)
    COLOR_NAME_CACHE.clear()
    assert hex_to_color_name("#abcdef") == "API Name"
    assert hex_to_color_name("#abcdef") == "API Name"
    assert len(calls) == 1, "API should be called only once due to caching"
    save_path = tmp_path / "saved.pkl"
    save_color_name_cache(str(save_path))
    loaded = pickle.load(open(save_path, "rb"))
    assert loaded["#abcdef"] == "API Name"
