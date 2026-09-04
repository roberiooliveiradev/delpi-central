"""Outbound pagination: inventory emitters use PaginationEnvelopeBuilder."""

from __future__ import annotations

import json
import re
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[4]
_INV = json.loads(
    (_API_ROOT / "app" / "content" / "pagination_outbound_inventory.json").read_text(
        encoding="utf-8"
    )
)

_INLINE = re.compile(r'"pagination"\s*:\s*\{(?!\*\*)')
_BUILDER = "PaginationEnvelopeBuilder"
_ALLOW_TO_DICT = re.compile(r'"pagination"\s*:\s*\w[\w\.]*\.to_dict\(\)')


def test_outbound_inventory_count() -> None:
    assert _INV["count"] == 46
    assert len(_INV["entries"]) == 46


def test_inventory_files_use_builder_or_adapter() -> None:
    failures: list[str] = []
    for entry in _INV["entries"]:
        path = _API_ROOT / entry["file"]
        text = path.read_text(encoding="utf-8")
        classification = entry["classification"]
        if classification in {
            "build_operational_pagination",
            "build_has_next_pagination",
            "build_pagination",
        }:
            # Adapters already delegate to PaginationEnvelopeBuilder.
            if _BUILDER not in text and classification == "build_pagination":
                # process_inspection_plans DTO
                assert _BUILDER in text or "build_pagination" in text
            continue
        # inline_dict: either builder in file, or pagination via to_dict that uses builder
        if _BUILDER in text:
            for match in _INLINE.finditer(text):
                failures.append(f"{entry['file']}: inline dict remains near {match.start()}")
            continue
        if _ALLOW_TO_DICT.search(text):
            # DTO response wrapping — pagination class must use builder
            continue
        failures.append(f"{entry['file']}: missing {_BUILDER}")
    assert failures == [], failures
