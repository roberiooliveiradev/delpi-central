"""Unit tests for SC5 order-creator probe helpers (no TOTVS required)."""
from __future__ import annotations

from scripts.sql.sc5_order_creator_probe import candidate_columns


def test_candidate_columns_detects_user_like_names() -> None:
    cols = [
        "C5_NUM",
        "C5_CLIENTE",
        "C5_USERLGI",
        "C5_USRINC",
        "C5_MSUIDT",
        "C5_EMISSAO",
        "C5_VEND1",
    ]
    found = candidate_columns(cols)
    assert "C5_USERLGI" in found
    assert "C5_USRINC" in found
    assert "C5_MSUIDT" in found
    assert "C5_NUM" not in found


def test_candidate_columns_empty_when_no_user_fields() -> None:
    cols = ["C5_NUM", "C5_CLIENTE", "C5_EMISSAO", "C5_VEND1", "D_E_L_E_T_"]
    assert candidate_columns(cols) == []
