"""
Unit tests for color_name_api.get_color_name_from_api with mocked HTTP.
"""

import json

import pytest

from apis.color_name_api import get_color_name_from_api


class DummyResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


def test_get_color_name_from_api(monkeypatch):
    payload = {"colors": [{"name": "Candy Green"}]}

    def fake_urlopen(_req):
        return DummyResponse(payload)

    monkeypatch.setattr("apis.color_name_api.urllib.request.urlopen", fake_urlopen)
    assert get_color_name_from_api("#37ce00") == "Candy Green"


def test_get_color_name_from_api_missing(monkeypatch):
    payload = {"colors": []}

    def fake_urlopen(_req):
        return DummyResponse(payload)

    monkeypatch.setattr("apis.color_name_api.urllib.request.urlopen", fake_urlopen)
    with pytest.raises(ValueError):
        get_color_name_from_api("#000000")
