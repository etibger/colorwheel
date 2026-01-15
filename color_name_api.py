"""
Color name lookup via the Color.pizza API.

Uses the public endpoint documented at https://api.color.pizza/v1/?values=<HEX>.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from config_loader import load_config

CONFIG = load_config()
API_URL = CONFIG["color_api_url"]


def get_color_name_from_api(hex_color: str) -> str:
    """
    Resolve a hex color to a human-readable name using Color.pizza.

    :param hex_color: Color in ``#RRGGBB`` or ``RRGGBB`` format.
    :type hex_color: str
    :returns: The name reported by the API (e.g., ``"Candy Green"``).
    :rtype: str
    :raises ValueError: If the API response is missing a color name.
    """
    normalized = hex_color.lstrip("#")
    query = urllib.parse.urlencode({"values": normalized})
    req = urllib.request.Request(f"{API_URL}?{query}", method="GET")
    with urllib.request.urlopen(req) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    colors = payload.get("colors") or []
    if not colors or "name" not in colors[0]:
        raise ValueError(f"No color name found for {hex_color}")
    return colors[0]["name"]
