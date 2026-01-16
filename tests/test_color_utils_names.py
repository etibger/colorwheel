"""
Tests for color_utils.hex_to_color_name, covering API and fallback paths.
"""

import json

from utils.color_utils import hex_to_color_name


class DummyResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


def test_hex_to_color_name_api(monkeypatch):
    payload = {"colors": [{"name": "Candy Green"}]}

    def fake_urlopen(_req):
        return DummyResponse(payload)

    monkeypatch.setattr("apis.color_name_api.urllib.request.urlopen", fake_urlopen)
    assert hex_to_color_name("#37ce00") == "Candy Green"


def test_hex_to_color_name_fallback(monkeypatch):
    # Simulate API failure to trigger local fallback search
    monkeypatch.setattr(
        "apis.color_name_api.urllib.request.urlopen",
        lambda _req: (_ for _ in ()).throw(RuntimeError("net down")),
    )
    assert hex_to_color_name("#36c000") in {"Candy Green", "Lime", "Green"}
