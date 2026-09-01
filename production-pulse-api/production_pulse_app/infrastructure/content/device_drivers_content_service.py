from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "device_drivers.json"


@lru_cache(maxsize=1)
def load_device_drivers_catalog() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def get_driver_definitions() -> dict[str, Any]:
    catalog = load_device_drivers_catalog()
    drivers = catalog.get("drivers")
    if not isinstance(drivers, dict):
        return {}
    return drivers
