"""Testes do humanize centralizado de chaves de campo."""

from tv_app.domain.services.field_key_humanize import (
    humanize_field_key,
    is_weak_field_label,
    split_field_key_tokens,
)


def test_humanize_field_key_uses_full_key_map():
    assert humanize_field_key("gross_savings_month") == "Economia bruta (mês)"
    assert humanize_field_key("month") == "Mês"
    assert humanize_field_key("goal_value") == "Meta cadastrada"
    assert humanize_field_key("comparable_goal") == "Meta do período"
    assert humanize_field_key("reference_goal") == "Meta mês (referência)"


def test_humanize_field_key_translates_tokens():
    assert humanize_field_key("gross_cost_rate") == "Bruto custo taxa"
    assert humanize_field_key("goal_amount") == "Meta valor"


def test_humanize_field_key_splits_camel_case_with_spaces():
    assert split_field_key_tokens("valorDia") == ["valor", "dia"]
    assert humanize_field_key("valorDia") == "Valor dia"
    assert humanize_field_key("valor_dia") == "Valor dia"
    assert humanize_field_key("totalQuantidade") == "Total quantidade"
    assert humanize_field_key("registrosSemCusto") == "Registros sem custo"
    assert humanize_field_key("totalValor") == "Total valor"


def test_is_weak_field_label():
    assert is_weak_field_label("month", "month") is True
    assert is_weak_field_label("month", "Mês") is False
    assert is_weak_field_label("valorDia", "Valordia") is True
    assert is_weak_field_label("valor_dia", "Valordia") is True
    assert is_weak_field_label("valorDia", "Valor do dia") is False
