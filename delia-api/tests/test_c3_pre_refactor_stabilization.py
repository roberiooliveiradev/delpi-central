"""DELIA-C3-PRE-REFACTOR — functional stabilization before R0–R7.

Production evidence (doc 126, real Kimi + authorized identity):

- P1/D5: ``get_catalog`` projected the ``productGuide`` index whole —
  its excerpt nearly fills the 2000-char render budget — and the
  concrete ``displayFormatCatalog`` section (the actual formats answer)
  was starved out of the response.
- P3/D8-R: a referential follow-up ("esse material") produced a
  discovery query carrying no resolved referent → owner discover
  returned ``candidate_count=0`` → honest insufficiency. The same owner
  discover returns candidates for a natural re-ask; the missing piece
  is context-folding into the discovery query (model proposal side and
  the deterministic discover leg).
- P4: governed ``field_labels`` resolve only in the composed paths;
  the deterministic ``_format_structured``/guidance renderers printed
  raw keys (``Group code``, ``use_when``…).

Generalizing bounds: no provider branches, no lexical intent rules, no
new engines — the render budget is shared fairly, labels flow through
the existing governed leaf, and discovery gains ONE bounded
context-folded retry when the first query misses and prior turns exist.
"""

from __future__ import annotations

from pathlib import Path

from app.application.capability_provision.mcp_provider import (
    McpCapabilityProvider,
)
from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION,
    CANDIDATE_ARGUMENTS_INSTRUCTION,
    OperationalCapabilityOrchestrator,
    _context_folded_discovery_query,
    _deterministic_guidance_content,
    render_specialist_outcome,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    ConversationContextTurn,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.specialist_interop.contracts import (
    RemoteToolOutcome,
)
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.domain.interaction.model import TurnKind
from app.domain.specialist_interop.model import EpistemicClass
from app.infrastructure.config.cri_instruction_resource import (
    load_cri_instruction_clause,
    load_cri_presentation_vocabulary,
)
from tests.test_specialist_capability_orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    _select,
    CANDIDATE_ARGUMENTS_INSTRUCTION_ID,
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    DAVI_TOOLS,
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
_LABELS = load_cri_presentation_vocabulary(_VOCAB_PATH).field_labels

# Minimized real prod VISTA ``get_catalog`` payload — guide index plus
# the concrete format catalog that answers the formats question.
_VISTA_CATALOG = {
    "status": "success",
    "data": {
        "catalogVersion": "2026.10.05.lossless",
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
            "entities": [
                {
                    "id": "playlist",
                    "kind": "ENTITY",
                    "filterable_fields": ["playlistId"],
                }
            ],
        },
        "productGuide": {
            "schema": "product_guide_index_v1",
            "topics": [
                {
                    "id": f"topic_{i}",
                    "title": f"Tópico de guia {i}",
                    "summary": "S" * 90,
                }
                for i in range(18)
            ],
        },
    },
}

_VISTA_GUIDE_DOC = {
    "status": "success",
    "data": {
        "schema": "product_guide_v1",
        "guide": {
            "id": "display_formats",
            "title": "Formatos de exibição",
            "summary": "Como valores são formatados para exibição.",
            "purpose": "Explicar o que é display format.",
            "use_when": ["O usuário pergunta como formatar moeda"],
            "do_not_use_when": ["A pergunta é sobre transform de dado"],
            "how_to_use": ["formatId seleciona o formato"],
        },
    },
}


def _proposals(remote_name, goal=None):
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
        GOAL_INSTRUCTION_ID: goal or {"goal_class": "read"},
        NATIVE_ASSESSMENT_INSTRUCTION_ID: {"status": "sufficient"},
        ARGUMENTS_INSTRUCTION_ID: {"arguments": {}},
    }


def _vista_orch(port, proposal):
    clause = load_cri_instruction_clause(_CRI_RESOURCE_PATH)
    return OperationalCapabilityOrchestrator(
        [McpCapabilityProvider(SpecialistInterop(port), ("vista",))],
        invoke_model=InvokeModel(FakeProposalModel(proposal)),
        model_ref=TEST_MODEL_REF,
        field_labels=_LABELS,
        cri_instruction_clause=clause.text,
    )


# --- P1: concrete format evidence is never starved by a guide index ---


def test_d5_catalog_surfaces_concrete_format_evidence():
    port = FakePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        outcomes={
            "get_catalog": RemoteToolOutcome(
                content_text="catalog", structured=_VISTA_CATALOG
            )
        },
    )
    orch = _vista_orch(port, _proposals("get_catalog"))
    attempt = orch.attempt(
        "Quais formatos de dados e visualizações estão disponíveis "
        "nos painéis operacionais?"
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    # The concrete owner-published formats are the answer — the guide
    # index alone cannot consume the whole render budget.
    assert "number-2" in attempt.content
    assert "currency-brl" in attempt.content


def test_d5_catalog_index_is_bounded_and_disclosed():
    content = _deterministic_guidance_content(
        _VISTA_CATALOG, field_labels=_LABELS
    )
    assert content is not None
    body, _limitations = content
    # Both families must appear; the index gets a bounded preview.
    assert "number-2" in body
    assert len(body) <= 2000


def test_sibling_owner_catalog_same_projection():
    sibling = {
        "data": {
            "productGuide": {
                "topics": [
                    {"id": f"t{i}", "title": "x" * 120}
                    for i in range(15)
                ]
            },
            "displayFormatCatalog": [
                {"formatId": "date-br", "spec": {"category": "date"}}
            ],
        }
    }
    content = _deterministic_guidance_content(
        sibling, field_labels=_LABELS
    )
    assert content is not None
    assert "date-br" in content[0]


# --- P4: governed labels reach the deterministic render paths ---------


def test_catalog_sections_use_governed_ptbr_labels():
    content = _deterministic_guidance_content(
        _VISTA_CATALOG, field_labels=_LABELS
    )
    assert content is not None
    body, _ = content
    assert "Catálogo de formatos" in body
    assert "displayFormatCatalog" not in body
    assert "Guia do produto" in body
    assert "productGuide" not in body


def test_guide_doc_uses_governed_ptbr_labels():
    content = _deterministic_guidance_content(
        _VISTA_GUIDE_DOC, field_labels=_LABELS
    )
    assert content is not None
    body, _ = content
    assert "Resumo" in body
    assert "Finalidade" in body
    assert "Instru" in body  # instruções de uso
    assert "Restri" in body  # restrições de uso
    # Raw structural keys never reach the user surface.
    for raw in ("use_when", "how_to_use", "do_not_use_when"):
        assert raw not in body


def test_business_record_labels_via_render():
    from app.domain.specialist_interop.model import (
        InteropProtocol,
        SpecialistOutcome,
        SpecialistResultProvenance,
        SpecialistResultStatus,
    )

    spec = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="davi",
            remote_name="delpi.get_product_summary",
            protocol=InteropProtocol.MCP,
            correlation_id="corr-p4",
            observed_at="2026-10-23T00:00:00Z",
        ),
        content_text="",
        structured={
            "data": {
                "code": "10080043",
                "description": "TERM. OLHAL M6",
                "group_code": "1008",
                "product_code": "10080043",
                "group_category": "MP",
            }
        },
    )
    body, _ = render_specialist_outcome(spec, field_labels=_LABELS)
    assert "Código do grupo" in body
    assert "Código do produto" in body
    assert "Categoria do grupo" in body
    assert "10080043" in body  # values preserved verbatim


# --- P3: referential follow-up folds prior context into discovery ------


def _prior_material_turns():
    return (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT,
            content="Qual é a descrição do material de código 10080043?",
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content=(
                "Código: 10080043 — TERM. OLHAL M6 6,30MM "
                "4,00-6,00MM2 ESTANHADO ROHS"
            ),
            epistemic_class=EpistemicClass.OBSERVATION,
        ),
    )


def test_context_folded_query_only_when_prior_turns_exist():
    assert (
        _context_folded_discovery_query("consulte novamente", ())
        is None
    )
    folded = _context_folded_discovery_query(
        "Você pode consultar novamente o cadastro desse material?",
        _prior_material_turns(),
    )
    assert folded is not None
    assert "desse material" in folded
    assert "10080043" in folded
    assert len(folded) <= 400


def test_instructions_resolve_referential_expressions():
    """The existing instruction contracts must direct the model to
    restate concrete referents from prior turns — provider-neutral."""
    for instruction in (
        ARGUMENTS_INSTRUCTION,
        CANDIDATE_ARGUMENTS_INSTRUCTION,
    ):
        assert "prior" in instruction.lower()
        assert "refer" in instruction.lower()


def test_d8r_referential_followup_retries_discovery_once():
    """Zero-candidate referential query + prior context → ONE bounded
    discovery retry with the folded query; candidate then chains."""

    class ContextAwarePort(FakePort):
        def call_remote_tool(
            self, specialist, remote_name, arguments, **kw
        ):
            self.calls.append(
                (specialist.specialist_id, remote_name, dict(arguments))
            )
            if remote_name == "discover_delpi_information":
                query = str(arguments.get("query") or "")
                if "10080043" in query:
                    return RemoteToolOutcome(
                        content_text="{}",
                        structured={
                            "candidates": [
                                {
                                    "action_id": "get_product",
                                    "candidate_token": "tok-1",
                                    "argument_schema": {
                                        "type": "object",
                                        "properties": {},
                                    },
                                }
                            ]
                        },
                    )
                return RemoteToolOutcome(
                    content_text="{}",
                    structured={"candidates": []},
                )
            return RemoteToolOutcome(
                content_text="{}",
                structured={
                    "data": {
                        "code": "10080043",
                        "description": "TERM. OLHAL M6",
                    }
                },
            )

    proposal = _select("davi", "execute_delpi_information", {"arguments": {}})
    proposal[CANDIDATE_ARGUMENTS_INSTRUCTION_ID] = {"arguments": {}}
    port = ContextAwarePort(tools_by_specialist={"davi": DAVI_TOOLS})
    orch = OperationalCapabilityOrchestrator(
        [McpCapabilityProvider(SpecialistInterop(port), ("davi",))],
        invoke_model=InvokeModel(FakeProposalModel(proposal)),
        model_ref=TEST_MODEL_REF,
        field_labels=_LABELS,
    )
    attempt = orch.attempt(
        "Você pode consultar novamente o cadastro desse material e "
        "confirmar sua descrição?",
        prior_turns=_prior_material_turns(),
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    discover_calls = [
        c for c in port.calls if c[1] == "discover_delpi_information"
    ]
    execute_calls = [
        c for c in port.calls if c[1] == "execute_delpi_information"
    ]
    # Exactly one bounded retry with the context-folded query.
    assert len(discover_calls) == 2
    assert "10080043" in str(discover_calls[-1][2])
    assert execute_calls, "candidate must chain into the owner READ"
    assert "TERM. OLHAL M6" in attempt.content


def test_no_prior_context_never_retries_discovery():
    """Without prior turns a discovery miss stays a single owner
    call — the retry never fires spuriously."""

    class EmptyPort(FakePort):
        def call_remote_tool(
            self, specialist, remote_name, arguments, **kw
        ):
            self.calls.append(
                (specialist.specialist_id, remote_name, dict(arguments))
            )
            return RemoteToolOutcome(
                content_text="{}", structured={"candidates": []}
            )

    proposal = _select("davi", "execute_delpi_information", {"arguments": {}})
    proposal[CANDIDATE_ARGUMENTS_INSTRUCTION_ID] = {"arguments": {}}
    port = EmptyPort(tools_by_specialist={"davi": DAVI_TOOLS})
    orch = OperationalCapabilityOrchestrator(
        [McpCapabilityProvider(SpecialistInterop(port), ("davi",))],
        invoke_model=InvokeModel(FakeProposalModel(proposal)),
        model_ref=TEST_MODEL_REF,
    )
    orch.attempt("consulte o material")
    discover_calls = [
        c for c in port.calls if c[1] == "discover_delpi_information"
    ]
    assert len(discover_calls) == 1
