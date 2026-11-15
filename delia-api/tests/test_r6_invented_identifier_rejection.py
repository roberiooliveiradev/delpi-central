"""R6 — reject invented record codes in goal declaration.

When the user (and prior turns) never named a product/process code,
``declare_investigation_goal`` must not accept fabricated targets such
as ``P12345``. Legitimate identifiers present in context stay accepted;
filter adjectives like ``ativos`` are not treated as record codes.
"""

from __future__ import annotations

from app.infrastructure.orchestration.pydantic_ai_investigation import (
    invented_record_tokens,
)


def test_invented_codey_token_rejected_when_absent_from_context():
    invented = invented_record_tokens(
        ["P12345"],
        input_text="Quero ver a estrutura de um produto.",
        prior_turns=(),
    )
    assert invented == ["P12345"]


def test_literal_identifier_accepted_when_present_in_user_text():
    invented = invented_record_tokens(
        ["90260921"],
        input_text="estrutura do produto 90260921",
        prior_turns=(),
    )
    assert invented == []


def test_identifier_recovered_from_prior_turn():
    class _Turn:
        def __init__(self, content: str) -> None:
            self.content = content

    invented = invented_record_tokens(
        ["90260921"],
        input_text="90260921",
        prior_turns=(
            _Turn("Quero ver a estrutura de um produto."),
            _Turn("Qual é o código do produto?"),
        ),
    )
    assert invented == []


def test_filter_adjective_is_not_treated_as_invented_record():
    invented = invented_record_tokens(
        ["ativos"],
        input_text="Quantos processos de transformação estão ativos?",
        prior_turns=(),
    )
    assert invented == []


def test_proc_literal_absent_is_invented():
    invented = invented_record_tokens(
        ["PROC-9999"],
        input_text="liste processos ativos",
        prior_turns=(),
    )
    assert invented == ["PROC-9999"]


def test_angle_bracket_placeholder_is_invented():
    invented = invented_record_tokens(
        ["<código_do_produto>"],
        input_text="Quero ver a estrutura de um produto.",
        prior_turns=(),
    )
    assert invented == ["<código_do_produto>"]
