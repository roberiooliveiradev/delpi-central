"""Vocative addressee -> declared owner surface constraint (cmp_09 class).

"NOME, investigue..." is a declared addressee: when the leading token
names a live provider it bounds the group-selection candidate surface.
A model pick of another live group fails revalidation closed instead
of silently substituting the wrong owner. A leading word that names no
live provider never constrains.
"""


def _vocative_orch(proposal_group):
    from app.application.capability_provision.orchestration import (
        GROUP_SELECTION_INSTRUCTION_ID,
    )
    from tests.test_governed_attempt_contract import build_engine
    from tests.test_goal_evidence_relevance import (
        _cri_clause,
        _group,
        _query_cap,
        FakeProposalModel,
        FakeProvider,
    )

    clause = _cri_clause()
    suri = _group("suri", "mcp", [_query_cap()])
    davi = _group("davi", "mcp", [_query_cap()])
    orch = build_engine(
        "delia",
        providers=[
            FakeProvider("suri", [suri]),
            FakeProvider("davi", [davi]),
        ],
        model=FakeProposalModel(
            [
                {
                    GROUP_SELECTION_INSTRUCTION_ID: {
                        "applicable": True,
                        "capability_group_id": proposal_group,
                    }
                }
            ]
        ),
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    return orch, {"mcp:suri": suri, "mcp:davi": davi}


def test_vocative_owner_constrains_candidates():
    orch, groups = _vocative_orch("mcp:davi")
    status, key = orch._select_group(
        "SURI, investigue os pedidos de compra em aberto", groups
    )
    assert (status, key) != ("selected", "mcp:davi")


def test_vocative_owner_selects_named():
    orch, groups = _vocative_orch("mcp:suri")
    status, key = orch._select_group(
        "SURI, investigue os pedidos de compra em aberto", groups
    )
    assert (status, key) == ("selected", "mcp:suri")


def test_non_provider_vocative_unrestricted():
    orch, groups = _vocative_orch("mcp:davi")
    status, key = orch._select_group(
        "Dados, mostre os pedidos de compra em aberto", groups
    )
    assert (status, key) == ("selected", "mcp:davi")


def test_mcp_named_live_provider_constrains():
    """'use o mcp suri' also bounds the candidate surface to the
    named provider — same declared-surface semantics as the
    vocative form."""
    orch, groups = _vocative_orch("mcp:davi")
    status, key = orch._select_group(
        "use o mcp suri para investigar pedidos de compra", groups
    )
    assert (status, key) != ("selected", "mcp:davi")
