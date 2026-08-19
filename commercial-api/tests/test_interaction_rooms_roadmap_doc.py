from __future__ import annotations

import re
from pathlib import Path

DOC_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "12-roadmap-e-evolucao"
    / "commercial"
    / "ROADMAP-INTERACTION-ROOM.md"
)

_STEP_IDS = (
    "E1.S1",
    "E1.S2",
    "E1.S3",
    "E2.S1",
    "E2.S2",
    "E3.S1",
    "E3.S2",
    "E3.S3",
    "E3.S4",
    "E3.S5",
    "E3.S6",
    "E5.S1",
    "E5.S2",
    "E5.S3",
    "E5.S4",
    "E5.S5",
    "E6.S1",
    "E6.S2",
    "E6.S3",
    "E6.S4",
    "E6.S5",
    "E6.S6",
    "E6.S7",
    "E6.S8",
    "E6.S9",
    "E7.S1",
    "E7.S2",
    "E7.S3",
    "E7.S4",
    "E7.S5",
    "E7.S6",
    "E8.S1",
    "E8.S2",
    "E8.S3",
    "E8.S4",
)

_HEADING = re.compile(r"^### (E\d+\.S\d+) —", re.MULTILINE)

_LAYER_MARKERS = (
    "Front (plugin-ui",
    "Front (MFE",
    "Backend (commercial-api",
)


def _roadmap() -> str:
    assert DOC_PATH.is_file(), f"missing {DOC_PATH}"
    return DOC_PATH.read_text(encoding="utf-8")


def test_roadmap_exists_and_is_backlog() -> None:
    text = _roadmap()
    assert "backlog" in text.lower()
    assert "up-dev-sequential" in text
    assert "body_text" in text


def test_each_substep_lists_front_and_backend() -> None:
    text = _roadmap()
    matches = list(_HEADING.finditer(text))
    found = [m.group(1) for m in matches]
    missing_ids = [sid for sid in _STEP_IDS if sid not in found]
    extra = [sid for sid in found if sid not in _STEP_IDS]
    assert not missing_ids, missing_ids
    assert not extra, extra

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end]
        sid = match.group(1)
        missing = [marker for marker in _LAYER_MARKERS if marker not in chunk]
        assert not missing, f"{sid} missing {missing}"
