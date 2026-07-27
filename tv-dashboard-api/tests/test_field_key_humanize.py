"""Testes do humanize centralizado de chaves de campo."""

from tv_app.domain.services.field_key_humanize import (
    humanize_field_key,
    is_weak_field_label,
)


def test_humanize_field_key_uses_full_key_map():
    assert humanize_field_key("gross_savings_month") == "Economia bruta (mês)"
    assert humanize_field_key("month") == "Mês"
    assert humanize_field_key("goal_value") == "Valor da meta"


def test_humanize_field_key_translates_tokens():
    assert humanize_field_key("gross_cost_rate") == "Bruto custo taxa"
    assert humanize_field_key("goal_amount") == "Meta valor"


def test_is_weak_field_label():
    assert is_weak_field_label("month", "month") is True
    assert is_weak_field_label("month", "Mês") is False
