"""QUESTION_FLOW_MATRIX — fluxos de pergunta operacional cobertos pelo critic (P0/herança)."""

from __future__ import annotations

from typing import Any

# Escopo do plano critic_suficiência_mercado — linhas fora do escopo não entram aqui.
QUESTION_FLOW_MATRIX: list[dict[str, Any]] = [
    {
        "id": "stock_bare",
        "message": "estoque",
        "kind": "plan_actions_no_name_error",
        "workspace": {},
        "previous_messages": [],
    },
    {
        "id": "stock_bare_multiturn",
        "message": "estoque",
        "kind": "plan_actions_no_name_error",
        "workspace": {"workingMemory": {}},
        "previous_messages": [
            {"role": "user", "content": "estoque"},
            {
                "role": "assistant",
                "content": "Não ficou claro o que você precisa. Pode reformular?",
            },
        ],
    },
    {
        "id": "stock_with_code",
        "message": "estoque do produto 10080047",
        "kind": "intent_stock",
        "expect_intent": "stock",
    },
    {
        "id": "stock_ground_from_memory",
        "message": "busque o estoque desse produto",
        "kind": "ground_code",
        "memory_snapshot": {"operationalFocus": {"productCode": "10080047"}},
        "expect_code": "10080047",
    },
    {
        "id": "overview_me_fale",
        "message": "me fale do produto 10080047",
        "kind": "overview_trigger",
    },
    {
        "id": "narrow_so_estoque",
        "message": "só estoque do produto 10080047",
        "kind": "narrow_exclude_overview",
    },
    {
        "id": "stock_low_followup",
        "message": "estoque",
        "kind": "critic_stock_low",
    },
    {
        "id": "sales_empty_nf_clarify",
        "message": "vendas",
        "kind": "critic_sales_empty",
    },
    {
        "id": "cap_fast_deferred",
        "message": "estoque",
        "kind": "critic_cap_deferred",
    },
    {
        "id": "multi_intent_deferred",
        "message": "estoque e fornecedores 10080022",
        "kind": "multi_intent_continuation",
    },
    {
        "id": "preview_simulate",
        "message": "estoque 10080047",
        "kind": "sufficiency_audit_shape",
    },
    {
        "id": "intent_cases_stock_desc_analyser",
        "message": "descrição do produto 10080047",
        "kind": "intent_description",
        "expect_intent": "description",
    },
]

QUESTION_FLOW_REQUIRED_IDS: frozenset[str] = frozenset(
    str(item["id"]) for item in QUESTION_FLOW_MATRIX
)
