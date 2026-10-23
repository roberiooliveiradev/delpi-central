"""DELIA-C3-D5 — evidence-to-intent relevance gate (doc 124 AC-D5-01..09).

Production evidence (doc 123): a zero-candidate VISTA ``get_catalog``
DISCOVERY outcome projected ``capability_surface.entities`` contract
rows as the user answer for a question about display formats — while
the same payload carried the owner-published ``displayFormatCatalog``
guidance that answered it. The reformulation (``get_product_guide``
+ index select) fetched the right guide doc, projected it
deterministically, and the CRI envelope-only composition replaced the
projected guidance with a generic insufficiency text.

Generalizing rule: owner contract/schema metadata may only compose an
answer when the typed turn goal declared a contract/schema subject;
otherwise the governed deterministic projection (guidance or honest
miss) stands. Selection stays model-driven — no lexical intent rules,
no provider branches.
"""

from __future__ import annotations

from pathlib import Path

from app.application.capability_provision.mcp_provider import (
    McpCapabilityProvider,
)
from app.application.capability_provision.orchestration import (
    OperationalCapabilityOrchestrator,
)
from app.application.capability_provision.outcome_assessment import (
    OUTCOME_CONTRACT_FACTS,
    OUTCOME_ENVELOPE_ONLY,
    EvidenceFacts,
    assess_outcome,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    LIMITATION_INSUFFICIENT_EVIDENCE,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.specialist_interop.contracts import (
    RemoteToolDescriptor,
    RemoteToolOutcome,
)
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.infrastructure.config.cri_instruction_resource import (
    load_cri_instruction_clause,
    load_cri_presentation_vocabulary,
)
from tests.test_specialist_capability_orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    FakePort,
    FakeProposalModel,
    GOAL_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    INTERACTION_ADMISSION_INSTRUCTION_ID,
    NATIVE_ASSESSMENT_INSTRUCTION_ID,
    TEST_MODEL_REF,
    VISTA_TOOLS,
)

_CRI_RESOURCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "cri_instructions.delpi.json"
)
_VOCAB_PATH = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "cri_presentation.delpi.json"
)

# Minimized real prod VISTA ``get_catalog`` payload (2026-10-23, doc
# 123): contract metadata under ``capability_surface.entities`` AND the
# owner-published format documentation the question actually asked.
_VISTA_CATALOG = {
    "status": "success",
    "data": {
        "catalogVersion": "2026.10.05.lossless",
        "allowedOps": ["upsert_data_source", "list_playlists"],
        "capabilities": [
            {
                "key": "add_kpi_from_route",
                "op": "upsert_data_source",
                "whenToUse": "Adicionar um KPI no slide.",
            }
        ],
        "displayFormatCatalog": [
            {
                "formatId": "number-2",
                "spec": {"category": "number", "decimalPlaces": 2},
            },
            {
                "formatId": "currency-brl",
                "spec": {"category": "currency", "prefix": "R$"},
            },
        ],
        "capability_surface": {
            "agent_directives": {
                "authority": (
                    "Obey these directives before any playlist "
                    "mutation."
                ),
            },
            "entities": [
                {
                    "id": "playlist",
                    "kind": "ENTITY",
                    "filterable_fields": ["playlistId"],
                    "server_owned_fields": ["id", "revision"],
                }
            ],
        },
        "productGuide": {
            "schema": "product_guide_index_v1",
            "topics": [
                {
                    "id": "display_formats",
                    "title": "Formatos de exibição",
                }
            ],
        },
    },
}

# Same catalog without the guidance sections — honest-miss control.
_VISTA_CATALOG_NO_GUIDANCE = {
    "status": "success",
    "data": {
        "catalogVersion": "2026.10.05.lossless",
        "capability_surface": {
            "entities": [
                {
                    "id": "playlist",
                    "kind": "ENTITY",
                    "filterable_fields": ["playlistId"],
                }
            ],
        },
    },
}

# Minimized real prod ``get_product_guide`` topic doc (display_formats).
_VISTA_GUIDE_DOC = {
    "status": "success",
    "data": {
        "schema": "product_guide_v1",
        "section": "all",
        "guide": {
            "schema": "product_guide_v1",
            "id": "display_formats",
            "title": "Formatos de exibição",
            "summary": (
                "Como valores são formatados para exibição "
                "(moeda, percentual, data, número)."
            ),
            "authority": "GUIDANCE_NOT_DOMAIN_TRUTH",
            "purpose": "Explicar o que é display format.",
            "use_when": [
                "O usuário pergunta como formatar um número "
                "como moeda/percentual"
            ],
            "do_not_use_when": [
                "A pergunta é sobre transform de dado"
            ],
            "how_to_use": [
                "Display format é uma camada de apresentação",
                "formatId seleciona o formato",
                "spec declara parâmetros",
            ],
            "field_guidance": {
                "formatId": "seleciona o formato",
            },
        },
    },
}

_GUIDE_TOOLS = (
    RemoteToolDescriptor(
        remote_name="get_product_guide", operation_class="READ"
    ),
)


def _proposals(remote_name, goal):
    return {
        INTERACTION_ADMISSION_INSTRUCTION_ID: {
            "requires_owner_surface": True,
            "interaction_class": "operational",
        },
        GROUP_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "capability_group_id": "mcp:vista",
        },
        CAPABILITY_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "remote_name": remote_name,
        },
        GOAL_INSTRUCTION_ID: goal,
        NATIVE_ASSESSMENT_INSTRUCTION_ID: {"status": "sufficient"},
        ARGUMENTS_INSTRUCTION_ID: {"arguments": {}},
    }


def _cri_orchestrator(port, proposal):
    clause = load_cri_instruction_clause(_CRI_RESOURCE_PATH)
    vocab = load_cri_presentation_vocabulary(_VOCAB_PATH)
    return OperationalCapabilityOrchestrator(
        [McpCapabilityProvider(SpecialistInterop(port), ("vista",))],
        invoke_model=InvokeModel(FakeProposalModel(proposal)),
        model_ref=TEST_MODEL_REF,
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
        cri_presentation_vocabulary=vocab.sections,
        field_labels=vocab.field_labels,
    )


def _catalog_attempt(goal, structured=_VISTA_CATALOG):
    port = FakePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        outcomes={
            "get_catalog": RemoteToolOutcome(
                content_text="catalog", structured=structured
            )
        },
    )
    orch = _cri_orchestrator(
        port, _proposals("get_catalog", goal)
    )
    return port, orch.attempt(
        "Quais formatos de dados e visualizações estão disponíveis "
        "nos painéis operacionais?"
    )


# --- AC-D5-01: formats question never renders contract/schema rows ----


def test_d5_catalog_projects_formats_not_entity_schemas():
    port, attempt = _catalog_attempt({"goal_class": "read"})
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.content
    # The owner-published format catalog is the answer.
    assert "number-2" in attempt.content or "Formatos" in attempt.content
    # Contract/schema metadata never becomes the answer.
    assert "entities.playlist" not in attempt.content
    assert "server_owned_fields" not in attempt.content
    # Control-plane directives never leak (RC1/RC2 preserved).
    assert "agent_directives" not in attempt.content
    assert "Obey these directives" not in attempt.content


def test_d5_catalog_without_guidance_is_honest_miss():
    port, attempt = _catalog_attempt(
        {"goal_class": "read"},
        structured=_VISTA_CATALOG_NO_GUIDANCE,
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.content
    # Schema rows still never substitute for an unrelated ask.
    assert "entities.playlist" not in attempt.content
    assert "filterable_fields" not in attempt.content


# --- AC-D5-03: explicit contract question keeps the contract digest ---


def test_d5_contract_subject_keeps_contract_facts():
    port, attempt = _catalog_attempt(
        {"goal_class": "read", "contract_subject": True}
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "A fonte publica" in attempt.content
    assert "entities.playlist" in attempt.content


def test_d5_contract_subject_must_be_boolean_true():
    """Fail closed: a non-boolean declaration is unproven intent —
    contract metadata cannot substitute for a business ask."""
    port, attempt = _catalog_attempt(
        {"goal_class": "read", "contract_subject": "yes"}
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "entities.playlist" not in attempt.content


# --- AC-D5-02: guide doc projection is not discarded by the verdict ---


def test_d5r_guide_doc_projects_guidance_not_insufficiency():
    port = FakePort(
        tools_by_specialist={"vista": _GUIDE_TOOLS},
        outcomes={
            "get_product_guide": RemoteToolOutcome(
                content_text="guide", structured=_VISTA_GUIDE_DOC
            )
        },
    )
    orch = _cri_orchestrator(
        port, _proposals("get_product_guide", {"goal_class": "read"})
    )
    attempt = orch.attempt(
        "Que tipos de visualização posso utilizar nos dashboards?"
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.content
    assert "formatId seleciona o formato" in attempt.content
    # The verdict must not replace a governed projection with a
    # generic insufficiency or mark honest guidance as insufficient.
    assert "não retornou dados de negócio" not in attempt.content
    assert (
        LIMITATION_INSUFFICIENT_EVIDENCE not in attempt.limitations
    )


# --- verdict gate (unit) ----------------------------------------------


def test_assess_contract_facts_requires_declared_contract_subject():
    facts = EvidenceFacts(contract_facts=("entities.process: {}",))
    assert (
        assess_outcome(facts, contract_subject=True).decision
        == OUTCOME_CONTRACT_FACTS
    )
    assert (
        assess_outcome(facts, contract_subject=False).decision
        == OUTCOME_ENVELOPE_ONLY
    )
    # Default is unproven intent — never the schema digest.
    assert assess_outcome(facts).decision == OUTCOME_ENVELOPE_ONLY


# --- AC-D5-05: provider-neutral sibling --------------------------------


def test_d5_sibling_owner_catalog_same_semantics():
    """Same contract-metadata + guidance shape under a renamed owner —
    no provider branch, identical projection semantics."""
    sibling_catalog = {
        "status": "success",
        "data": {
            "capability_surface": {
                "entities": [
                    {
                        "id": "panel",
                        "kind": "ENTITY",
                        "filterable_fields": ["panelId"],
                    }
                ]
            },
            "displayFormatCatalog": [
                {"formatId": "date-br", "spec": {"category": "date"}}
            ],
            "productGuide": {
                "topics": [{"id": "formats", "title": "Formatos"}]
            },
        },
    }
    port, attempt = _catalog_attempt(
        {"goal_class": "read"}, structured=sibling_catalog
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "date-br" in attempt.content or "Formatos" in attempt.content
    assert "entities.panel" not in attempt.content
