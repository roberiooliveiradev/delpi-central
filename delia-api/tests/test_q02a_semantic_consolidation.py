"""Q02-A semantic consolidation — RED/GREEN behavioral matrix.

Captures I04 remediation outcomes: formats owner selection without
lexical specialist branches, conversational SIPOC without owner, topic
change after owner turns, provider-neutral rename/reorder, and
singleton-irrelevant fail-closed. No ACT.
"""

from __future__ import annotations

import pytest

from app.application.capability_provision.mcp_provider import (
    McpCapabilityProvider,
)
from app.application.capability_provision.orchestration import (
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    INTERACTION_ADMISSION_INSTRUCTION_ID,
    NATIVE_ASSESSMENT_INSTRUCTION_ID,
    ARGUMENTS_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
    _GUIDANCE_FAMILY_ORDER,
    _index_option_rows,
    _index_selection_is_member,
    _prior_transform_probe_eligible,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.specialist_interop.contracts import (
    RemoteToolDescriptor,
    RemoteToolOutcome,
)
from app.domain.evidence.model import EpistemicClass
from app.domain.interaction.model import TurnKind
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
)
from tests.test_specialist_capability_orchestration import (
    DAVI_TOOLS,
    FakePort,
    FakeProposalModel,
    TEO_TOOLS,
    TEST_MODEL_REF,
    _interop,
    _select,
)


FORMATS_ASK = "Quais formatos de dados estão disponíveis?"
FORMATS_PARAPHRASE = (
    "Que tipos de formato de dados o catálogo operacional publica?"
)
FORMATS_NEGATION = (
    "Não quero produtos cadastrados — quais formatos de dados "
    "estão disponíveis no catálogo operacional?"
)
SIPOC_ASK = "O que é SIPOC?"


def _formats_catalog_tools(*, remote_name: str = "get_catalog"):
    return (
        RemoteToolDescriptor(
            remote_name=remote_name,
            operation_class="READ",
            description=(
                "List operational data formats and media types "
                "published by this surface catalog."
            ),
        ),
        RemoteToolDescriptor(
            remote_name="list_playlists",
            operation_class="READ",
            description="List playlists.",
        ),
    )


def _davi_discovery_tools():
    return (
        RemoteToolDescriptor(
            remote_name="discover_delpi_information",
            operation_class="DISCOVERY",
            description=(
                "Semantic search over DELPI product/register actions."
            ),
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        ),
    )


def _teo_method_tools():
    return (
        RemoteToolDescriptor(
            remote_name="get_methodology_guide",
            operation_class="READ",
            description="Return process methodology guidance sections.",
        ),
        RemoteToolDescriptor(
            remote_name="get_catalog",
            operation_class="DISCOVERY",
            description="List methodology guide topics.",
        ),
    )


def _orch(tools_by_specialist, proposal, specialist_ids=None):
    port = FakePort(tools_by_specialist=tools_by_specialist)
    ids = specialist_ids or tuple(tools_by_specialist)
    model = FakeProposalModel(proposal)
    orch = OperationalCapabilityOrchestrator(
        [McpCapabilityProvider(_interop(port), ids)],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    return orch, port, model


def test_q02a_coverage_inquiry_detector_removed():
    """Lexical coverage detector must not drive selection (S01/F40)."""
    import app.application.capability_provision.orchestration as orch_mod

    assert not hasattr(orch_mod, "_is_information_coverage_inquiry")


def test_q02a_formats_selects_format_catalog_not_product_discovery():
    """C02 wiring: canned FakeProposalModel routes to format catalog.

    NOT_PROVEN for real-LLM semantic preference among DAVI/TÉO/VISTA —
    that requires authorized live model evaluation (RQ-02).
    """
    proposal = {
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
            "remote_name": "get_catalog",
            "goal_class": "read",
        },
        NATIVE_ASSESSMENT_INSTRUCTION_ID: {"status": "sufficient"},
        ARGUMENTS_INSTRUCTION_ID: {"arguments": {}},
    }
    orch, port, model = _orch(
        {
            "davi": _davi_discovery_tools(),
            "teo": _teo_method_tools(),
            "vista": _formats_catalog_tools(),
        },
        proposal,
        specialist_ids=("davi", "teo", "vista"),
    )
    outcomes = {
        ("vista", "get_catalog"): RemoteToolOutcome(
            content_text="Formatos: CSV, JSON, Parquet.",
            structured={
                "formats": ["CSV", "JSON", "Parquet"],
                "eligible_action_count": 3,
            },
        )
    }
    port._outcomes = {"get_catalog": outcomes[("vista", "get_catalog")]}
    attempt = orch.attempt(FORMATS_ASK)
    purposes = [r.task_purpose_id for r in model.requests]
    assert INTERACTION_ADMISSION_INSTRUCTION_ID in purposes
    assert GROUP_SELECTION_INSTRUCTION_ID in purposes
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert any(call[1] == "get_catalog" for call in port.calls)
    assert "discover_delpi_information" not in {
        call[1] for call in port.calls
    }
    content = (attempt.content or "").lower()
    assert any(call[1] == "get_catalog" for call in port.calls)
    assert "csv" in content or "json" in content or "parquet" in content or "format" in content


def test_q02a_formats_paraphrase_and_negation_same_owner_path():
    proposal = {
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
            "remote_name": "list_data_formats",
            "goal_class": "read",
        },
        NATIVE_ASSESSMENT_INSTRUCTION_ID: {"status": "sufficient"},
        ARGUMENTS_INSTRUCTION_ID: {"arguments": {}},
    }
    tools = {
        "davi": _davi_discovery_tools(),
        "vista": _formats_catalog_tools(remote_name="list_data_formats"),
    }
    for ask in (FORMATS_PARAPHRASE, FORMATS_NEGATION):
        orch, port, _ = _orch(
            tools, proposal, specialist_ids=("davi", "vista")
        )
        port._outcomes = {
            "list_data_formats": RemoteToolOutcome(
                content_text="Formatos: CSV.",
                structured={"formats": ["CSV"]},
            )
        }
        attempt = orch.attempt(ask)
        assert attempt.status is GovernedCapabilityStatus.SUCCESS
        assert any(c[1] == "list_data_formats" for c in port.calls)


def test_q02a_renamed_format_capability_still_selectable():
    proposal = {
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
            "remote_name": "enumerate_export_formats_v2",
            "goal_class": "read",
        },
        NATIVE_ASSESSMENT_INSTRUCTION_ID: {"status": "sufficient"},
        ARGUMENTS_INSTRUCTION_ID: {"arguments": {}},
    }
    tools = (
        RemoteToolDescriptor(
            remote_name="enumerate_export_formats_v2",
            operation_class="READ",
            description="Enumerate export data formats available.",
        ),
    )
    orch, port, _ = _orch(
        {"vista": tools},
        proposal,
        specialist_ids=("vista",),
    )
    port._outcomes = {
        "enumerate_export_formats_v2": RemoteToolOutcome(
            content_text="XML, YAML",
            structured={"formats": ["XML", "YAML"]},
        )
    }
    attempt = orch.attempt(FORMATS_ASK)
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert port.calls[0][1] == "enumerate_export_formats_v2"


def test_q02a_catalog_order_does_not_force_first_group():
    """Model must pick by semantics; first listed group is not default."""
    proposal = {
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
            "remote_name": "get_catalog",
            "goal_class": "read",
        },
        NATIVE_ASSESSMENT_INSTRUCTION_ID: {"status": "sufficient"},
        ARGUMENTS_INSTRUCTION_ID: {"arguments": {}},
    }
    # Insertion order puts product discovery first.
    orch, port, model = _orch(
        {
            "davi": _davi_discovery_tools(),
            "vista": _formats_catalog_tools(),
        },
        proposal,
        specialist_ids=("davi", "vista"),
    )
    port._outcomes = {
        "get_catalog": RemoteToolOutcome(
            content_text="CSV",
            structured={"formats": ["CSV"]},
        )
    }
    attempt = orch.attempt(FORMATS_ASK)
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    group_reqs = [
        r
        for r in model.requests
        if r.task_purpose_id == GROUP_SELECTION_INSTRUCTION_ID
    ]
    assert group_reqs, "singleton short-circuit must not skip group select"
    assert port.calls[0][1] == "get_catalog"


def test_q02a_singleton_irrelevant_group_not_forced():
    """One eligible provider that does not match → not forced (S20)."""
    proposal = {
        INTERACTION_ADMISSION_INSTRUCTION_ID: {
            "requires_owner_surface": True,
            "interaction_class": "operational",
        },
        GROUP_SELECTION_INSTRUCTION_ID: {"applicable": False},
    }
    orch, port, model = _orch(
        {"davi": _davi_discovery_tools()},
        proposal,
        specialist_ids=("davi",),
    )
    attempt = orch.attempt(FORMATS_ASK)
    assert GROUP_SELECTION_INSTRUCTION_ID in [
        r.task_purpose_id for r in model.requests
    ]
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert port.calls == []


def test_q02a_sipoc_conversational_without_owner():
    proposal = {
        INTERACTION_ADMISSION_INSTRUCTION_ID: {
            "requires_owner_surface": False,
            "interaction_class": "explanation",
        }
    }
    orch, port, model = _orch(
        {
            "davi": _davi_discovery_tools(),
            "teo": _teo_method_tools(),
            "vista": _formats_catalog_tools(),
        },
        proposal,
        specialist_ids=("davi", "teo", "vista"),
    )
    attempt = orch.attempt(SIPOC_ASK)
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert port.calls == []
    assert INTERACTION_ADMISSION_INSTRUCTION_ID in [
        r.task_purpose_id for r in model.requests
    ]
    assert GROUP_SELECTION_INSTRUCTION_ID not in [
        r.task_purpose_id for r in model.requests
    ]


def test_q02a_topic_change_after_owner_allows_admission():
    """Prior owner turn must not skip admission (S21)."""
    prior = (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT,
            content="Liste produtos.",
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content="Encontrei 2 registros.",
            epistemic_class=EpistemicClass.OBSERVATION,
        ),
    )
    proposal = {
        INTERACTION_ADMISSION_INSTRUCTION_ID: {
            "requires_owner_surface": False,
            "interaction_class": "explanation",
        }
    }
    orch, port, model = _orch(
        {"davi": DAVI_TOOLS, "teo": TEO_TOOLS},
        proposal,
        specialist_ids=("davi", "teo"),
    )
    attempt = orch.attempt(SIPOC_ASK, prior_turns=prior)
    assert INTERACTION_ADMISSION_INSTRUCTION_ID in [
        r.task_purpose_id for r in model.requests
    ]
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert port.calls == []


def test_q02a_hypothetical_continuity_stays_non_owner():
    prior = (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT,
            content="Dê três melhorias hipotéticas para um processo.",
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content="1) Kanban 2) SMED 3) Heijunka — hipóteses.",
            epistemic_class=EpistemicClass.HYPOTHESIS,
        ),
    )
    proposal = {
        INTERACTION_ADMISSION_INSTRUCTION_ID: {
            "requires_owner_surface": False,
            "interaction_class": "hypothetical",
        }
    }
    orch, port, _ = _orch(
        {"davi": DAVI_TOOLS},
        proposal,
        specialist_ids=("davi",),
    )
    attempt = orch.attempt(
        "Agora compare a primeira e a segunda.",
        prior_turns=prior,
    )
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert port.calls == []


def test_q02a_index_no_lexical_rerank_or_veto():
    structured = {
        "items": [
            {"id": "currency_format", "label": "Currency"},
            {"id": "legibility_guide", "label": "Legibility"},
        ]
    }
    options = _index_option_rows(structured, ("topic",))
    # Owner catalog order is preserved verbatim — no lexical rerank.
    assert [r["identifier"] for r in options] == [
        "currency_format",
        "legibility_guide",
    ]
    assert _index_selection_is_member("legibility_guide", options)
    assert not _index_selection_is_member("invented_id", options)


def test_q02a_prior_transform_probe_typed_only():
    goal = OperationalCapabilityOrchestrator._TurnGoal(
        goal_class="read",
        declared=True,
        comparison_requested=False,
    )
    assert not _prior_transform_probe_eligible(
        "com base na metodologia anterior acima", goal
    )
    goal_cmp = OperationalCapabilityOrchestrator._TurnGoal(
        goal_class="compare",
        declared=True,
        comparison_requested=True,
    )
    assert _prior_transform_probe_eligible("compare os dois", goal_cmp)


def test_q02a_guidance_family_order_is_lexical_free_constant():
    # Stable non-lexical presentation order; limitations always included.
    assert "limitations" in _GUIDANCE_FAMILY_ORDER
    assert set(_GUIDANCE_FAMILY_ORDER) == {
        "objective",
        "when",
        "steps",
        "prerequisites",
        "criteria",
        "limitations",
    }


def test_q02a_no_act_on_formats_read():
    proposal = {
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
            "remote_name": "get_catalog",
            "goal_class": "read",
        },
        NATIVE_ASSESSMENT_INSTRUCTION_ID: {"status": "sufficient"},
        ARGUMENTS_INSTRUCTION_ID: {"arguments": {}},
    }
    orch, port, _ = _orch(
        {"vista": _formats_catalog_tools()},
        proposal,
        specialist_ids=("vista",),
    )
    port._outcomes = {
        "get_catalog": RemoteToolOutcome(
            content_text="CSV",
            structured={"formats": ["CSV"]},
        )
    }
    attempt = orch.attempt(FORMATS_ASK)
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "commit_proposal" not in {c[0] for c in port.calls}
    assert not getattr(attempt, "confirmation_request", None)


def test_q02a_rework_missing_group_proposal_singleton_fails_closed():
    """RQ-03: proposal None must not soft-select the sole live group."""
    from app.application.model_invocation.contracts import (
        ProviderInvocationPayload,
    )

    class MissingGroupFake(FakeProposalModel):
        def invoke(self, request):
            self.requests.append(request)
            purpose = request.task_purpose_id
            if purpose == GROUP_SELECTION_INSTRUCTION_ID:
                return ProviderInvocationPayload(
                    structured_output=None,
                    generated_at="2026-01-01T00:00:00+00:00",
                )
            if purpose == INTERACTION_ADMISSION_INSTRUCTION_ID:
                return ProviderInvocationPayload(
                    structured_output={
                        "requires_owner_surface": True,
                        "interaction_class": "operational",
                    },
                    generated_at="2026-01-01T00:00:00+00:00",
                )
            return ProviderInvocationPayload(
                structured_output={
                    "applicable": True,
                    "remote_name": "discover_delpi_information",
                    "goal_class": "read",
                },
                generated_at="2026-01-01T00:00:00+00:00",
            )

    port = FakePort(
        tools_by_specialist={"davi": _davi_discovery_tools()}
    )
    orch = OperationalCapabilityOrchestrator(
        [McpCapabilityProvider(_interop(port), ("davi",))],
        invoke_model=InvokeModel(MissingGroupFake({})),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(FORMATS_ASK)
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert port.calls == []


def test_q02a_rework_wrong_group_proposal_not_formats_task_pass():
    """RQ-02: scripted wrong owner proves plumbing, not task success."""
    proposal = {
        INTERACTION_ADMISSION_INSTRUCTION_ID: {
            "requires_owner_surface": True,
            "interaction_class": "operational",
        },
        GROUP_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "capability_group_id": "mcp:davi",
        },
        CAPABILITY_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "remote_name": "discover_delpi_information",
            "goal_class": "read",
        },
        NATIVE_ASSESSMENT_INSTRUCTION_ID: {"status": "sufficient"},
        ARGUMENTS_INSTRUCTION_ID: {"arguments": {"query": "formatos"}},
    }
    orch, port, _ = _orch(
        {
            "davi": _davi_discovery_tools(),
            "vista": _formats_catalog_tools(),
        },
        proposal,
        specialist_ids=("davi", "vista"),
    )
    port._outcomes = {
        "discover_delpi_information": RemoteToolOutcome(
            content_text="Produtos: TUBO 30x30.",
            structured={"items": [{"description": "TUBO 30x30"}]},
        )
    }
    attempt = orch.attempt(FORMATS_ASK)
    assert any(c[1] == "discover_delpi_information" for c in port.calls)
    assert "get_catalog" not in {c[1] for c in port.calls}
    content = (attempt.content or "").lower()
    assert "parquet" not in content
    assert "csv" not in content or "tubo" in content


def test_q02a_rework_empty_capability_after_group_is_inconclusive():
    """RQ-02: applicable group + missing capability → no owner invoke."""
    from app.application.model_invocation.contracts import (
        ProviderInvocationPayload,
    )

    class EmptyCapFake(FakeProposalModel):
        def invoke(self, request):
            self.requests.append(request)
            purpose = request.task_purpose_id
            payloads = {
                INTERACTION_ADMISSION_INSTRUCTION_ID: {
                    "requires_owner_surface": True,
                    "interaction_class": "operational",
                },
                GROUP_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "capability_group_id": "mcp:vista",
                },
                CAPABILITY_SELECTION_INSTRUCTION_ID: None,
            }
            return ProviderInvocationPayload(
                structured_output=payloads.get(purpose),
                generated_at="2026-01-01T00:00:00+00:00",
            )

    port = FakePort(
        tools_by_specialist={
            "vista": _formats_catalog_tools(),
            "davi": _davi_discovery_tools(),
        }
    )
    orch = OperationalCapabilityOrchestrator(
        [McpCapabilityProvider(_interop(port), ("vista", "davi"))],
        invoke_model=InvokeModel(EmptyCapFake({})),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(FORMATS_ASK)
    assert port.calls == []
    assert attempt.status in {
        GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
        GovernedCapabilityStatus.NOT_APPLICABLE,
    }


def test_q02a_rework_sipoc_wiring_not_content_oracle():
    """SIPOC canned admission is wiring-only; content outcome NOT_PROVEN."""
    proposal = {
        INTERACTION_ADMISSION_INSTRUCTION_ID: {
            "requires_owner_surface": False,
            "interaction_class": "explanation",
        }
    }
    orch, port, _ = _orch(
        {"teo": _teo_method_tools()},
        proposal,
        specialist_ids=("teo",),
    )
    attempt = orch.attempt(SIPOC_ASK)
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert port.calls == []
    assert not (attempt.content or "").strip()
