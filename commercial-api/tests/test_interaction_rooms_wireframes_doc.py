from pathlib import Path

DOC = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "12-roadmap-e-evolucao"
    / "commercial"
    / "WIREFRAMES.md"
).read_text(encoding="utf-8")

_IDS = tuple(f"WF-SALA-0{i}" for i in range(1, 9))

_KIT = (
    "PageHero",
    "RoomInboxList",
    "RoomHeader",
    "MessageThread",
    "MentionComposer",
    "EntityUnfurlCard",
    "ReactionBar",
    "createHostContainedDrawerShell",
)


def test_wireframes_include_sala_ids_and_kit() -> None:
    missing = [item for item in _IDS if item not in DOC]
    assert not missing, missing
    missing_kit = [item for item in _KIT if item not in DOC]
    assert not missing_kit, missing_kit
    assert "/interaction-rooms" in DOC
    assert "attachment:" in DOC or "colar imagem" in DOC.lower()
