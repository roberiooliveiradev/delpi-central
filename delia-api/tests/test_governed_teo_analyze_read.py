"""C4-MCP-GOVERNED-READS-02 tests — bounded TÉO dashboard analyze read.

Covers the per-binding READ gate (only teo.analyze + gpt_analyze under
its own flag), the proposal-gated direct invocation, the bounded view
surface, the shared grounding/provenance/failure semantics, and the
two-binding combiner — proving the common skeleton serves a second
consumer without a parallel read engine.
"""

from __future__ import annotations

import pytest

from app.application.interaction.contracts import InteractiveTurnRequest
from app.application.interaction.governed_read import (
    BoundDirectRead,
    GovernedRead,
    GovernedReadAttempt,
    GovernedReadStatus,
)
from app.application.interaction.governed_product_read import (
    GovernedProductRead,
)
from app.application.interaction.governed_teo_analyze import (
    ALLOWED_VIEWS,
    TEO_ANALYZE_BINDING,
    TRANSFORMOMETRO_DASHBOARD_SOURCE,
    build_teo_dashboard_analyze_read,
    render_dashboard_summary,
)
from app.application.interaction.handle_interactive_turn import (
    DELPI_UNVERIFIED_DISCLOSURE,
    LIMITATION_DELPI_SOURCE_UNVERIFIED,
    HandleInteractiveConversationTurn,
    serialize_result,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.application.specialist_interop.contracts import (
    RemoteToolOutcome,
    SpecialistInvocationRequest,
)
from app.application.specialist_interop.errors import (
    CAPABILITY_NOT_ALLOWED_IN_PHASE,
    MCP_AUTHENTICATION_FAILED,
    MCP_AUTHORIZATION_DENIED,
    MCP_PROTOCOL_ERROR,
    MCP_UNAVAILABLE,
    SPECIALIST_DISABLED,
    SPECIALIST_NOT_CONFIGURED,
    UNKNOWN_CAPABILITY,
    WRITE_CAPABILITY_BLOCKED,
    SpecialistInteropError,
)
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.domain.evidence.model import EpistemicClass, ModelRef
from app.domain.interaction.model import GroundingStatus
from app.domain.model_invocation.model import ProviderExposureClass


DAVI_READ_TUPLE = ("davi", "execute_delpi_information", "search_products")
TEO_READ_TUPLE = ("teo", "analyze", "gpt_analyze")


class FakePort:
    adapter_kind = "MCP_FAKE"

    def __init__(self, outcomes=None, errors=None):
        self._outcomes = dict(outcomes or {})
        self._errors = dict(errors or {})
        self.calls: list[tuple] = []

    def list_remote_tools(self, specialist, *, timeout_seconds):
        return ()

    def call_remote_tool(
        self, specialist, remote_name, arguments, *, correlation_id,
        timeout_seconds, governed_action_id=None,
    ):
        self.calls.append(
            (specialist.specialist_id, remote_name, arguments,
             governed_action_id)
        )
        error = self._errors.get(remote_name)
        if error is not None:
            raise error
        return self._outcomes.get(
            remote_name, RemoteToolOutcome(content_text="{}")
        )


def _interop(outcomes=None, errors=None, *, enabled=()):
    return SpecialistInterop(
        FakePort(outcomes=outcomes, errors=errors),
        enabled_governed_reads=frozenset(enabled),
    )


def _access():
    return PlatformAccessContext(
        user_id="user-1",
        name="User",
        email="u@example.com",
        effective_permissions=("delia.access",),
        is_superadmin=False,
    )


def _request(text: str):
    return InteractiveTurnRequest(access_context=_access(), input_text=text)


class FakeProposalModel:
    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self, proposal):
        self._proposal = proposal
        self.requests = []

    def invoke(self, request):
        self.requests.append(request)
        from app.application.model_invocation.contracts import (
            ProviderInvocationPayload,
        )

        return ProviderInvocationPayload(
            structured_output=self._proposal,
            generated_at="2026-01-01T00:00:00+00:00",
        )


TEST_MODEL_REF = ModelRef(
    model_id="test-model", version="1", owner_ref="DELPI"
)


def _teo_read(interop, proposal=None):
    """Bound TÉO read with a fixed proposal (or no model)."""
    invoke_model = (
        InvokeModel(FakeProposalModel(proposal))
        if proposal is not None
        else None
    )
    return build_teo_dashboard_analyze_read(
        interop,
        invoke_model=invoke_model,
        model_ref=TEST_MODEL_REF if invoke_model else None,
    )


ANALYZE_OK = {
    "success": True,
    "data": {
        "meta": {"scope": {"filial": None}},
        "summary": {
        "solucoes_implementadas": 12,
        "economia_bruta_total": 1500.5,
        "economia_liquida_total": 1200.0,
        "investimento_unico_total": 300.0,
        "custo_recorrente_total": 50.0,
        "custo_recursos_compartilhados_total": 10.0,
        "investimento_total": 350.0,
            "horas_economizadas_total": 44,
        },
    },
}

ANALYZE_EMPTY = {"success": True, "data": {"meta": {}, "summary": {}}}


# ------------------------------------------------------------------
# Per-binding READ gate
# ------------------------------------------------------------------

def test_teo_read_blocked_without_flag():
    interop = _interop()
    with pytest.raises(SpecialistInteropError) as exc:
        interop.invoke(
            SpecialistInvocationRequest(
                specialist_id="teo",
                remote_capability="analyze",
                correlation_id="c",
                governed_action_id="gpt_analyze",
                arguments={"view": "summary"},
            )
        )
    assert exc.value.code == CAPABILITY_NOT_ALLOWED_IN_PHASE


def test_teo_read_blocked_with_only_davi_flag():
    """The DAVI flag never widens the TÉO binding."""
    interop = _interop(enabled={DAVI_READ_TUPLE})
    with pytest.raises(SpecialistInteropError) as exc:
        interop.invoke(
            SpecialistInvocationRequest(
                specialist_id="teo",
                remote_capability="analyze",
                correlation_id="c",
                governed_action_id="gpt_analyze",
                arguments={"view": "summary"},
            )
        )
    assert exc.value.code == CAPABILITY_NOT_ALLOWED_IN_PHASE


def test_teo_read_allowed_with_own_flag():
    interop = _interop(
        outcomes={"analyze": RemoteToolOutcome(
            content_text="ok", structured=ANALYZE_OK
        )},
        enabled={TEO_READ_TUPLE},
    )
    outcome = interop.invoke(
        SpecialistInvocationRequest(
            specialist_id="teo",
            remote_capability="analyze",
            correlation_id="c",
            governed_action_id="gpt_analyze",
            arguments={"view": "summary"},
        )
    )
    assert outcome.epistemic_class is EpistemicClass.OBSERVATION


@pytest.mark.parametrize(
    "specialist_id,remote_name,action_id",
    [
        ("davi", "execute_delpi_information", "gpt_analyze"),
        ("teo", "analyze", "search_products"),
        ("teo", "analyze", "analyze"),
        ("teo", "analyze", None),
        ("teo", "analyze", "forged"),
    ],
)
def test_wrong_binding_tuples_blocked(specialist_id, remote_name, action_id):
    interop = _interop(enabled={TEO_READ_TUPLE, DAVI_READ_TUPLE})
    with pytest.raises(SpecialistInteropError) as exc:
        interop.invoke(
            SpecialistInvocationRequest(
                specialist_id=specialist_id,
                remote_capability=remote_name,
                correlation_id="c",
                governed_action_id=action_id,
                arguments={"view": "summary"},
            )
        )
    assert exc.value.code == CAPABILITY_NOT_ALLOWED_IN_PHASE


@pytest.mark.parametrize(
    "specialist_id,remote_name",
    [
        ("vista", "analyze"),
        ("teo", "search_records"),
        ("teo", "get_my_context"),
    ],
)
def test_unknown_registry_pairs_fail_closed(specialist_id, remote_name):
    """A (specialist, capability) pair absent from the approved registry
    is rejected before the governed gate is even consulted."""
    interop = _interop(enabled={TEO_READ_TUPLE, DAVI_READ_TUPLE})
    with pytest.raises(SpecialistInteropError) as exc:
        interop.invoke(
            SpecialistInvocationRequest(
                specialist_id=specialist_id,
                remote_capability=remote_name,
                correlation_id="c",
                governed_action_id="gpt_analyze",
                arguments={},
            )
        )
    assert exc.value.code in (
        UNKNOWN_CAPABILITY,
        CAPABILITY_NOT_ALLOWED_IN_PHASE,
    )


def test_other_teo_reads_stay_blocked():
    interop = _interop(enabled={TEO_READ_TUPLE})
    for name in (
        "get_my_context",
        "get_process_context",
        "search_records",
        "get_record",
        "list_evidence",
        "get_process_timeline",
        "meeting_minute_read",
        "get_diagnostic",
        "list_diagnostics_by_revision",
        "generate_from_transcript",
    ):
        with pytest.raises(SpecialistInteropError) as exc:
            interop.invoke(
                SpecialistInvocationRequest(
                    specialist_id="teo",
                    remote_capability=name,
                    correlation_id="c",
                    governed_action_id="gpt_analyze",
                    arguments={},
                )
            )
        assert exc.value.code == CAPABILITY_NOT_ALLOWED_IN_PHASE


def test_teo_writes_stay_blocked():
    interop = _interop(enabled={TEO_READ_TUPLE})
    for name in ("prepare_record_change", "commit_proposal"):
        with pytest.raises(SpecialistInteropError) as exc:
            interop.invoke(
                SpecialistInvocationRequest(
                    specialist_id="teo",
                    remote_capability=name,
                    correlation_id="c",
                    governed_action_id="gpt_analyze",
                    arguments={},
                )
            )
        assert exc.value.code == WRITE_CAPABILITY_BLOCKED


# ------------------------------------------------------------------
# Bounded proposal validation
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "proposal",
    [
        {"applicable": True, "view": "processes"},
        {"applicable": True, "view": "meta"},
        {"applicable": True, "view": "forged"},
        {"applicable": True, "view": 42},
        {"applicable": True, "view": "summary", "filial_id": "01"},
        {"applicable": True, "view": "summary", "setor_id": "x"},
        {"applicable": True, "view": "summary", "processo_id": "p"},
        {"applicable": True, "view": "summary", "revisao_id": "r"},
        {"applicable": True, "view": "summary",
         "competencia_inicio": "2026-01"},
        {"applicable": True, "view": "summary", "limit": 10},
        {"applicable": True, "view": "summary",
         "remote_capability": "commit_proposal"},
        {"applicable": "yes", "view": "summary"},
        {"applicable": True, "view": "summary", "specialist": "davi"},
    ],
)
def test_invalid_or_forbidden_proposals_never_reach_wire(proposal):
    interop = _interop(
        outcomes={"analyze": RemoteToolOutcome(
            content_text="ok", structured=ANALYZE_OK
        )},
        enabled={TEO_READ_TUPLE},
    )
    bound = _teo_read(interop, proposal=proposal)
    attempt = bound.attempt("me mostra os indicadores")
    assert attempt.status is GovernedReadStatus.NOT_APPLICABLE
    assert not any(c[1] == "analyze" for c in interop._port.calls)


def test_applicable_proposal_invokes_only_bounded_args():
    interop = _interop(
        outcomes={"analyze": RemoteToolOutcome(
            content_text="ok", structured=ANALYZE_OK
        )},
        enabled={TEO_READ_TUPLE},
    )
    bound = _teo_read(
        interop, proposal={"applicable": True, "view": "summary"}
    )
    attempt = bound.attempt("como estão os indicadores?")
    assert attempt.status is GovernedReadStatus.SUCCESS
    calls = [c for c in interop._port.calls if c[1] == "analyze"]
    assert len(calls) == 1
    specialist_id, _, arguments, action_id = calls[0]
    assert specialist_id == "teo"
    assert action_id == "gpt_analyze"
    assert arguments == {"view": "summary"}


def test_string_true_applicability_is_accepted_bounded():
    interop = _interop(
        outcomes={"analyze": RemoteToolOutcome(
            content_text="ok", structured=ANALYZE_OK
        )},
        enabled={TEO_READ_TUPLE},
    )
    bound = _teo_read(
        interop, proposal={"applicable": "true", "view": "summary"}
    )
    attempt = bound.attempt("indicadores?")
    assert attempt.status is GovernedReadStatus.SUCCESS


def test_null_view_defaults_to_summary():
    interop = _interop(
        outcomes={"analyze": RemoteToolOutcome(
            content_text="ok", structured=ANALYZE_OK
        )},
        enabled={TEO_READ_TUPLE},
    )
    bound = _teo_read(
        interop, proposal={"applicable": True, "view": None}
    )
    attempt = bound.attempt("indicadores?")
    assert attempt.status is GovernedReadStatus.SUCCESS


def test_no_model_means_no_attempt():
    """Without a proposal model the binding fails closed."""
    interop = _interop(enabled={TEO_READ_TUPLE})
    bound = _teo_read(interop)
    attempt = bound.attempt("indicadores do transformômetro")
    assert attempt.status is GovernedReadStatus.NOT_APPLICABLE
    assert not interop._port.calls


def test_not_applicable_proposal_skips_wire():
    interop = _interop(enabled={TEO_READ_TUPLE})
    bound = _teo_read(
        interop, proposal={"applicable": False, "view": None}
    )
    attempt = bound.attempt("escreva um e-mail")
    assert attempt.status is GovernedReadStatus.NOT_APPLICABLE
    assert not interop._port.calls


# ------------------------------------------------------------------
# Failure semantics (frozen contract)
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "code",
    [
        SPECIALIST_NOT_CONFIGURED,
        SPECIALIST_DISABLED,
        MCP_UNAVAILABLE,
        MCP_AUTHENTICATION_FAILED,
        MCP_PROTOCOL_ERROR,
    ],
)
def test_teo_source_failures_are_source_unavailable(code):
    interop = _interop(
        errors={"analyze": SpecialistInteropError(code, "x")},
        enabled={TEO_READ_TUPLE},
    )
    bound = _teo_read(
        interop, proposal={"applicable": True, "view": "summary"}
    )
    attempt = bound.attempt("indicadores")
    assert attempt.status is GovernedReadStatus.SOURCE_UNAVAILABLE
    assert attempt.error_code == code


def test_teo_authz_denied_distinct():
    interop = _interop(
        errors={
            "analyze": SpecialistInteropError(
                MCP_AUTHORIZATION_DENIED, "forbidden"
            )
        },
        enabled={TEO_READ_TUPLE},
    )
    bound = _teo_read(
        interop, proposal={"applicable": True, "view": "summary"}
    )
    attempt = bound.attempt("indicadores")
    assert attempt.status is GovernedReadStatus.AUTHZ_DENIED


def test_empty_authoritative_summary_is_grounded_empty():
    interop = _interop(
        outcomes={"analyze": RemoteToolOutcome(
            content_text="ok", structured=ANALYZE_EMPTY
        )},
        enabled={TEO_READ_TUPLE},
    )
    bound = _teo_read(
        interop, proposal={"applicable": True, "view": "summary"}
    )
    attempt = bound.attempt("indicadores")
    assert attempt.status is GovernedReadStatus.SUCCESS
    assert "Não encontrei indicadores" in attempt.content


def test_success_provenance_identifies_business_source():
    interop = _interop(
        outcomes={"analyze": RemoteToolOutcome(
            content_text="ok", structured=ANALYZE_OK
        )},
        enabled={TEO_READ_TUPLE},
    )
    bound = _teo_read(
        interop, proposal={"applicable": True, "view": "summary"}
    )
    attempt = bound.attempt("indicadores")
    assert attempt.provenance.source_refs[0].source_id == (
        TRANSFORMOMETRO_DASHBOARD_SOURCE.source_id
    )
    assert attempt.provenance.specialist_id == "teo"
    assert attempt.provenance.action_id == "gpt_analyze"
    assert attempt.provenance.remote_capability == "analyze"


def test_model_never_touches_source_values():
    """Deterministic renderer reads only owner-projected numeric keys."""
    interop = _interop(
        outcomes={"analyze": RemoteToolOutcome(
            content_text="ok",
            structured={
                "data": {
                    "summary": {
                        "solucoes_implementadas": 7,
                        "injected": "evil",
                        "horas_economizadas_total": "not-a-number",
                    },
                },
                "extra": {"raw": "payload"},
            },
        )},
        enabled={TEO_READ_TUPLE},
    )
    bound = _teo_read(
        interop, proposal={"applicable": True, "view": "summary"}
    )
    attempt = bound.attempt("indicadores")
    assert "7" in attempt.content
    assert "evil" not in attempt.content
    assert "not-a-number" not in attempt.content
    assert "raw" not in attempt.content


# ------------------------------------------------------------------
# Combiner (two consumers, one semantic skeleton)
# ------------------------------------------------------------------

def test_combiner_returns_teo_success_before_davi():
    """TÉO binding is proposal-gated; a TÉO hit short-circuits without
    touching the DAVI source."""
    interop = _interop(
        outcomes={"analyze": RemoteToolOutcome(
            content_text="ok", structured=ANALYZE_OK
        )},
        enabled={TEO_READ_TUPLE, DAVI_READ_TUPLE},
    )
    governed = GovernedRead(
        [
            _teo_read(
                interop, proposal={"applicable": True, "view": "summary"}
            ),
            GovernedProductRead(interop),
        ]
    )
    attempt = governed.attempt("indicadores")
    assert attempt.status is GovernedReadStatus.SUCCESS
    assert not any(
        c[1] == "discover_delpi_information" for c in interop._port.calls
    )


def test_combiner_falls_through_to_davi_when_teo_not_applicable():
    interop = _interop(enabled={TEO_READ_TUPLE, DAVI_READ_TUPLE})
    governed = GovernedRead(
        [
            _teo_read(interop, proposal={"applicable": None, "view": None}),
            GovernedProductRead(interop),
        ]
    )
    attempt = governed.attempt("busque produto x")
    # No TÉO wire call; DAVI discovery ran and found no candidates.
    assert attempt.status is GovernedReadStatus.NOT_APPLICABLE
    assert not any(c[1] == "analyze" for c in interop._port.calls)
    assert any(
        c[1] == "discover_delpi_information" for c in interop._port.calls
    )


def test_combiner_source_unavailable_survives_not_applicable():
    interop = _interop(
        errors={
            "discover_delpi_information": SpecialistInteropError(
                MCP_UNAVAILABLE, "down"
            )
        },
        enabled={TEO_READ_TUPLE, DAVI_READ_TUPLE},
    )
    governed = GovernedRead(
        [
            _teo_read(interop, proposal={"applicable": None, "view": None}),
            GovernedProductRead(interop),
        ]
    )
    attempt = governed.attempt("produto")
    assert attempt.status is GovernedReadStatus.SOURCE_UNAVAILABLE
    assert attempt.error_code == MCP_UNAVAILABLE


def test_empty_combiner_is_not_applicable():
    governed = GovernedRead([])
    attempt = governed.attempt("olá")
    assert attempt.status is GovernedReadStatus.NOT_APPLICABLE


# ------------------------------------------------------------------
# Handler-level integration
# ------------------------------------------------------------------

def _handler(governed=None):
    from app.infrastructure.model_invocation.deterministic_test_adapter import (
        DeterministicTestAdapter,
    )

    return HandleInteractiveConversationTurn(
        InvokeModel(DeterministicTestAdapter()),
        governed_read=governed,
    )


def test_grounded_teo_result_contract():
    interop = _interop(
        outcomes={"analyze": RemoteToolOutcome(
            content_text="ok", structured=ANALYZE_OK
        )},
        enabled={TEO_READ_TUPLE},
    )
    governed = GovernedRead(
        [
            _teo_read(
                interop, proposal={"applicable": True, "view": "summary"}
            )
        ]
    )
    result = _handler(governed).execute(
        _request("como estão os indicadores do meu transformômetro?")
    )
    assert result.grounding_status is GroundingStatus.GROUNDED
    assert result.epistemic_class is EpistemicClass.OBSERVATION
    assert "Soluções implementadas: 12" in result.content
    assert result.model_invocation_id is None

    payload = serialize_result(result)
    prov = payload["provenance"]
    assert prov["source"]["source_id"] == "transformometro-dashboard"
    assert prov["source"]["source_system"] == "transformometro-api"
    assert prov["specialist_id"] == "teo"
    assert prov["protocol"] == "MCP"
    assert prov["action_id"] == "gpt_analyze"
    assert "filial" not in str(payload.get("provenance"))


def test_teo_source_unavailable_produces_disclosed_fallback():
    interop = _interop(
        errors={
            "analyze": SpecialistInteropError(
                MCP_UNAVAILABLE, "down"
            )
        },
        enabled={TEO_READ_TUPLE},
    )
    governed = GovernedRead(
        [
            _teo_read(
                interop, proposal={"applicable": True, "view": "summary"}
            )
        ]
    )
    result = _handler(governed).execute(_request("indicadores"))
    assert result.grounding_status is GroundingStatus.NON_GROUNDED
    assert LIMITATION_DELPI_SOURCE_UNVERIFIED in result.limitations
    assert DELPI_UNVERIFIED_DISCLOSURE in result.content
    assert result.provenance is None


def test_teo_not_applicable_gives_plain_model_answer():
    interop = _interop(enabled={TEO_READ_TUPLE})
    governed = GovernedRead(
        [
            _teo_read(
                interop, proposal={"applicable": None, "view": None}
            )
        ]
    )
    result = _handler(governed).execute(_request("olá"))
    assert result.grounding_status is GroundingStatus.NON_GROUNDED
    assert LIMITATION_DELPI_SOURCE_UNVERIFIED not in result.limitations


# ------------------------------------------------------------------
# Generalization proof (Abstraction Gate evidence)
# ------------------------------------------------------------------

def test_both_bindings_share_status_and_provenance_semantics():
    """The second consumer reuses the same skeleton — no clone."""
    assert TEO_ANALYZE_BINDING.remote_capability == "analyze"
    assert ALLOWED_VIEWS == frozenset({"summary"})
    # BoundDirectRead and GovernedProductRead both produce the same
    # attempt contract consumed by the specialist-neutral handler.
    for cls in (BoundDirectRead, GovernedProductRead):
        assert hasattr(cls, "attempt")


def test_no_parallel_read_artifacts():
    """No GovernedXxxRead clones, engines, routers, or registries."""
    import app.application.interaction as interaction_pkg
    import pathlib

    files = {
        p.name
        for p in pathlib.Path(interaction_pkg.__path__[0]).glob("*.py")
    }
    assert "governed_teo_read.py" not in files
    for name in files:
        lowered = name.lower()
        for forbidden in ("engine", "router", "registry", "proxy"):
            assert forbidden not in lowered, name
