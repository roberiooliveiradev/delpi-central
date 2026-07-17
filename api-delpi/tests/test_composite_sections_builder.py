from app.application.services.composite_sections_builder import build_composite_sections


def test_build_composite_sections_marks_summary_as_truncated() -> None:
    sections = build_composite_sections(
        {
            "structure": {"items": [{"code": "50219001"}], "total": 10},
            "guide": {"items": [], "total": 0},
        },
        view="summary",
        section_keys=("structure", "guide"),
    )

    assert len(sections) == 2
    assert sections[0]["key"] == "structure"
    assert sections[0]["itemCount"] == 10
    assert sections[0]["truncated"] is True


def test_build_composite_sections_detects_partial_page() -> None:
    sections = build_composite_sections(
        {
            "structure": {"items": [{"code": "1"}, {"code": "2"}], "total": 8},
        },
        view="full",
        section_keys=("structure",),
    )

    assert sections[0]["truncated"] is True
    assert sections[0]["itemCount"] == 8


def test_build_composite_sections_labels_safety_stock_blocks() -> None:
    sections = build_composite_sections(
        {
            "open_purchase_orders": {"items": [], "total": 0},
            "open_commitments": {"items": [{"op": "1"}], "total": 1},
            "stock_projection": {"items": [{"seq": 1}, {"seq": 2}], "total": 2},
        },
        section_keys=(
            "open_purchase_orders",
            "open_commitments",
            "stock_projection",
        ),
    )

    assert [section["label"] for section in sections] == [
        "Pedidos de compra em aberto",
        "Empenhos em aberto",
        "Extrato projetado de saldo",
    ]
    assert sections[2]["itemCount"] == 2
