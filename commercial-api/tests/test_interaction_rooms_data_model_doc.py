from pathlib import Path

DOC = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "12-roadmap-e-evolucao"
    / "commercial"
    / "DATA-MODEL.md"
).read_text(encoding="utf-8")

_EN_TABLES = (
    "interaction_rooms",
    "interaction_room_members",
    "interaction_messages",
    "interaction_mentions",
    "interaction_reactions",
    "interaction_pins",
)

_FORBIDDEN_PT_TABLES = (
    "sala_interacao",
    "salas_interacao",
    "mencoes",
    "mensagens_sala",
)


def test_data_model_documents_interaction_tables_in_english() -> None:
    for name in _EN_TABLES:
        assert f"`{name}`" in DOC, f"DATA-MODEL sem tabela {name}"
    assert "room_message" in DOC
    assert "### 8.1" in DOC
    assert "source_interaction_message_id" in DOC
    assert "V020" in DOC
    assert "V021" in DOC
    assert "uq_commercial_interaction_rooms_wall_global" in DOC
    assert "markdown" in DOC.lower()
    assert "parent_id" in DOC


def test_data_model_has_no_portuguese_table_names() -> None:
    lowered = DOC.lower()
    for name in _FORBIDDEN_PT_TABLES:
        assert name not in lowered, f"nome PT de tabela no DATA-MODEL: {name}"
