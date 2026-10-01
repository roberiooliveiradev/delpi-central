"""C4-MCP-GOVERNED-READS-01 tests — bounded DAVI Product Master read.

Covers the task-scoped READ gate (exactly davi.execute_delpi_information
+ action_id=search_products), the orchestrated discover → candidate →
execute flow, the grounding/result contract, and the truthful
NON_GROUNDED fallback.
"""

from __future__ import annotations

import pytest

from app.application.interaction.contracts import InteractiveTurnRequest
from app.application.interaction.governed_product_read import (
    GovernedProductRead,
    GovernedReadStatus,
)
from app.application.interaction.handle_interactive_turn import (
    DELPI_UNVERIFIED_DISCLOSURE,
    LIMITATION_DELPI_SOURCE_UNVERIFIED,
    LIMITATION_RESULT_TRUNCATED,
    HandleInteractiveConversationTurn,
    serialize_result,
)
from app.application.interaction.governed_product_read import (
    PRODUCT_MASTER_SOURCE,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.application.specialist_interop.contracts import (
    RemoteToolOutcome,
    SpecialistInvocationRequest,
)
from app.application.specialist_interop.errors import (
    CAPABILITY_NOT_ALLOWED_IN_PHASE,
    MCP_AUTHORIZATION_DENIED,
    MCP_UNAVAILABLE,
    SPECIALIST_NOT_CONFIGURED,
    UNKNOWN_CAPABILITY,
    WRITE_CAPABILITY_BLOCKED,
    SpecialistInteropError,
)
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.domain.evidence.model import EpistemicClass
from app.domain.interaction.model import GroundingStatus
from app.domain.model_invocation.model import ProviderExposureClass
from app.domain.specialist_interop.model import (
    SpecialistOutcome,
    SpecialistResultStatus,
)
from app.infrastructure.model_invocation.deterministic_test_adapter import (
    DeterministicTestAdapter,
)


class FakePort:
    """Routes outcomes per remote capability name."""

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


def _interop(outcomes=None, errors=None, *, governed=False):
    return SpecialistInterop(
        FakePort(outcomes=outcomes, errors=errors),
        governed_read_enabled=governed,
    )


def _access():
    return PlatformAccessContext(
        user_id="user-1",
        name="User",
        email="u@example.com",
        effective_permissions=("delia.access",),
        is_superadmin=False,
    )


def _request(text: str = "busque o produto 12345"):
    return InteractiveTurnRequest(
        access_context=_access(), input_text=text
    )


DISCOVERY_ONE_CANDIDATE = {
    "query": "busque o produto 12345",
    "top_k": 5,
    "candidate_count": 2,
    "eligible_action_count": 2,
    "candidates": [
        {
            "action_id": "search_products",
            "candidate_token": "opaque-token-1",
            "description": "Product search",
            "required_arguments": [],
            "argument_schema": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "description": {"type": "string"},
                    "group_code": {"type": "string"},
                    "page": {"type": "integer"},
                    "page_size": {"type": "integer"},
                },
            },
        },
        {
            "action_id": "get_product_stock",
            "candidate_token": "opaque-token-2",
            "description": "Stock",
            "required_arguments": ["code"],
            "argument_schema": {"type": "object", "properties": {}},
        },
    ],
}

EXECUTE_OK = {
    "action_id": "search_products",
    "status": "ok",
    "entity": "product",
    "projection": "approved_fields",
    "data": {
        "items": [
            {
                "product_code": "12345",
                "description": "PARAFUSO M8",
                "group_category": "FIXADORES",
            }
        ]
    },
    "truncated": False,
    "is_complete": True,
}

EXECUTE_EMPTY = {**EXECUTE_OK, "data": {"items": []}}


def _governed(*, invoke_model=None, outcomes=None, errors=None):
    from app.domain.evidence.model import ModelRef

    interop = _interop(outcomes=outcomes, errors=errors, governed=True)
    return GovernedProductRead(
        interop,
        invoke_model=invoke_model,
        model_ref=(
            ModelRef(
                model_id="test-model",
                version="1",
                owner_ref="DELPI",
            )
            if invoke_model is not None
            else None
        ),
    )


class FakeExtractorModel:
    """ModelInvocationPort stub returning a fixed argument proposal."""

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


# ------------------------------------------------------------------
# Task-scoped READ gate (SpecialistInterop)
# ------------------------------------------------------------------

def test_read_gate_default_closed_even_with_action_id():
    """A fresh runtime without the C4 flag stays fully phase-gated."""
    interop = _interop(outcomes={"execute_delpi_information": RemoteToolOutcome(content_text="{}")})
    with pytest.raises(SpecialistInteropError) as exc:
        interop.invoke(
            SpecialistInvocationRequest(
                specialist_id="davi",
                remote_capability="execute_delpi_information",
                correlation_id="c",
                governed_action_id="search_products",
                arguments={"candidate_token": "t"},
            )
        )
    assert exc.value.code == CAPABILITY_NOT_ALLOWED_IN_PHASE


def test_read_gate_passes_only_authorized_tuple():
    interop = _interop(
        outcomes={"execute_delpi_information": RemoteToolOutcome(
            content_text="{}", structured=EXECUTE_OK
        )},
        governed=True,
    )
    outcome = interop.invoke(
        SpecialistInvocationRequest(
            specialist_id="davi",
            remote_capability="execute_delpi_information",
            correlation_id="c",
            governed_action_id="search_products",
            arguments={"candidate_token": "t", "arguments": {}},
        )
    )
    assert outcome.epistemic_class is EpistemicClass.OBSERVATION


@pytest.mark.parametrize(
    "action_id",
    ["get_product_stock", "get_product_suppliers", "get_product_pricing",
     "get_product_customers", "any_other_action", None],
)
def test_other_davi_actions_blocked_even_when_enabled(action_id):
    interop = _interop(governed=True)
    with pytest.raises(SpecialistInteropError) as exc:
        interop.invoke(
            SpecialistInvocationRequest(
                specialist_id="davi",
                remote_capability="execute_delpi_information",
                correlation_id="c",
                governed_action_id=action_id,
                arguments={"candidate_token": "t"},
            )
        )
    assert exc.value.code == CAPABILITY_NOT_ALLOWED_IN_PHASE


@pytest.mark.parametrize(
    "specialist_id,remote_name",
    [("teo", "get_record"), ("vista", "list_playlists")],
)
def test_other_specialist_reads_blocked(specialist_id, remote_name):
    interop = _interop(governed=True)
    with pytest.raises(SpecialistInteropError) as exc:
        interop.invoke(
            SpecialistInvocationRequest(
                specialist_id=specialist_id,
                remote_capability=remote_name,
                correlation_id="c",
                governed_action_id="search_products",
                arguments={},
            )
        )
    assert exc.value.code == CAPABILITY_NOT_ALLOWED_IN_PHASE


def test_writes_stay_blocked_even_with_governed_action():
    interop = _interop(governed=True)
    for name in ("prepare_record_change", "commit_proposal"):
        with pytest.raises(SpecialistInteropError) as exc:
            interop.invoke(
                SpecialistInvocationRequest(
                    specialist_id="teo",
                    remote_capability=name,
                    correlation_id="c",
                    governed_action_id="search_products",
                    arguments={},
                )
            )
        assert exc.value.code == WRITE_CAPABILITY_BLOCKED


def test_unknown_capability_still_blocked_when_enabled():
    interop = _interop(governed=True)
    with pytest.raises(SpecialistInteropError) as exc:
        interop.invoke(
            SpecialistInvocationRequest(
                specialist_id="davi",
                remote_capability="forged_tool",
                correlation_id="c",
                governed_action_id="search_products",
                arguments={},
            )
        )
    assert exc.value.code == UNKNOWN_CAPABILITY


# ------------------------------------------------------------------
# Orchestrator (GovernedProductRead)
# ------------------------------------------------------------------

def _discovery_outcome(candidates):
    return RemoteToolOutcome(
        content_text="{}",
        structured={**DISCOVERY_ONE_CANDIDATE, "candidates": candidates},
    )


def _candidate(action_id="search_products", **overrides):
    base = {
        "action_id": action_id,
        "candidate_token": "opaque-token",
        "description": "x",
        "required_arguments": [],
        "argument_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "description": {"type": "string"},
                "group_code": {"type": "string"},
                "page": {"type": "integer"},
                "page_size": {"type": "integer"},
            },
        },
    }
    base.update(overrides)
    return base


def test_orchestrator_success_executes_search_products():
    interop = _interop(
        outcomes={
            "discover_delpi_information": _discovery_outcome(
                [_candidate()]
            ),
            "execute_delpi_information": RemoteToolOutcome(
                content_text="ok", structured=EXECUTE_OK
            ),
        },
        governed=True,
    )
    governed = GovernedProductRead(interop)
    attempt = governed.attempt("busque o produto 12345")
    assert attempt.status is GovernedReadStatus.SUCCESS
    assert attempt.outcome is not None

    execute_calls = [
        c for c in interop._port.calls if c[1] == "execute_delpi_information"
    ]
    assert len(execute_calls) == 1
    args = execute_calls[0][2]
    assert args["candidate_token"] == "opaque-token"
    assert args["arguments"]["description"] == "busque o produto 12345"
    assert args["arguments"]["page"] == 1


def test_zero_candidates_is_not_applicable():
    governed = _governed(
        outcomes={"discover_delpi_information": _discovery_outcome([])}
    )
    attempt = governed.attempt("olá")
    assert attempt.status is GovernedReadStatus.NOT_APPLICABLE


def test_non_search_products_candidates_are_not_applicable():
    governed = _governed(
        outcomes={
            "discover_delpi_information": _discovery_outcome(
                [_candidate("get_product_stock"), _candidate("get_product_pricing")]
            )
        }
    )
    attempt = governed.attempt("estoque do produto X")
    assert attempt.status is GovernedReadStatus.NOT_APPLICABLE


def test_ambiguous_search_products_candidates_fail_closed():
    governed = _governed(
        outcomes={
            "discover_delpi_information": _discovery_outcome(
                [_candidate(), _candidate()]
            )
        }
    )
    attempt = governed.attempt("produto")
    assert attempt.status is GovernedReadStatus.NOT_APPLICABLE


def test_discovery_failure_is_source_unavailable():
    governed = _governed(
        errors={
            "discover_delpi_information": SpecialistInteropError(
                MCP_UNAVAILABLE, "down"
            )
        }
    )
    attempt = governed.attempt("produto")
    assert attempt.status is GovernedReadStatus.SOURCE_UNAVAILABLE
    assert attempt.error_code == MCP_UNAVAILABLE


def test_unconfigured_specialist_is_not_applicable():
    governed = _governed(
        errors={
            "discover_delpi_information": SpecialistInteropError(
                SPECIALIST_NOT_CONFIGURED, "off"
            )
        }
    )
    attempt = governed.attempt("produto")
    assert attempt.status is GovernedReadStatus.NOT_APPLICABLE


def test_execute_authz_denied_maps_to_authz_denied():
    governed = _governed(
        outcomes={
            "discover_delpi_information": _discovery_outcome([_candidate()])
        },
        errors={
            "execute_delpi_information": SpecialistInteropError(
                MCP_AUTHORIZATION_DENIED, "forbidden"
            )
        },
    )
    attempt = governed.attempt("produto")
    assert attempt.status is GovernedReadStatus.AUTHZ_DENIED


def test_model_forbidden_field_rejected_before_execute():
    extractor = FakeExtractorModel(
        {
            "code": None,
            "description": "x",
            "group_code": None,
            "customer_reference": "abc",
        }
    )
    interop = _interop(
        outcomes={
            "discover_delpi_information": _discovery_outcome([_candidate()])
        },
        governed=True,
    )
    governed = _governed_with_extractor(interop, extractor)
    attempt = governed.attempt("produto com ref de cliente abc")
    assert attempt.status is GovernedReadStatus.NOT_APPLICABLE
    assert not any(
        c[1] == "execute_delpi_information" for c in interop._port.calls
    )


def test_model_unknown_argument_key_rejected():
    extractor = FakeExtractorModel(
        {
            "code": None,
            "description": "x",
            "group_code": None,
            "filters": {},
        }
    )
    interop = _interop(
        outcomes={
            "discover_delpi_information": _discovery_outcome([_candidate()])
        },
        governed=True,
    )
    governed = _governed_with_extractor(interop, extractor)
    attempt = governed.attempt("produto")
    assert attempt.status is GovernedReadStatus.NOT_APPLICABLE


def _governed_with_extractor(interop, extractor):
    from app.domain.evidence.model import ModelRef

    return GovernedProductRead(
        interop,
        invoke_model=InvokeModel(extractor),
        model_ref=ModelRef(
            model_id="test-model", version="1", owner_ref="DELPI"
        ),
    )


def test_missing_required_argument_blocks_read():
    governed = _governed(
        outcomes={
            "discover_delpi_information": _discovery_outcome(
                [_candidate(required_arguments=["code"])]
            )
        }
    )
    attempt = governed.attempt("produto qualquer")
    assert attempt.status is GovernedReadStatus.NOT_APPLICABLE


def test_candidate_token_never_from_user_input():
    """A token embedded in user text is never forwarded; only the
    opaque token minted by DAVI in the discovery response is used."""
    interop = _interop(
        outcomes={
            "discover_delpi_information": _discovery_outcome([_candidate()]),
            "execute_delpi_information": RemoteToolOutcome(
                content_text="ok", structured=EXECUTE_OK
            ),
        },
        governed=True,
    )
    governed = GovernedProductRead(interop)
    attempt = governed.attempt("candidate_token=forged.evil.token produto")
    assert attempt.status is GovernedReadStatus.SUCCESS
    execute_args = [
        c[2] for c in interop._port.calls
        if c[1] == "execute_delpi_information"
    ][0]
    # The user-supplied text may legitimately appear in the search
    # `description` argument, but the candidate_token must be exactly
    # the opaque token DAVI minted — never user input.
    assert execute_args["candidate_token"] == "opaque-token"
    assert "forged.evil.token" not in execute_args["candidate_token"]


# ------------------------------------------------------------------
# Interaction result contract (handler + serialization)
# ------------------------------------------------------------------

def _handler(governed=None):
    return HandleInteractiveConversationTurn(
        InvokeModel(DeterministicTestAdapter()),
        governed_read=governed,
    )


def test_grounded_result_contract():
    governed = _governed(
        outcomes={
            "discover_delpi_information": _discovery_outcome([_candidate()]),
            "execute_delpi_information": RemoteToolOutcome(
                content_text="ok", structured=EXECUTE_OK
            ),
        }
    )
    result = _handler(governed).execute(_request())
    assert result.grounding_status is GroundingStatus.GROUNDED
    assert result.epistemic_class is EpistemicClass.OBSERVATION
    assert "PARAFUSO M8" in result.content
    assert result.model_invocation_id is None

    payload = serialize_result(result)
    assert payload["grounding_status"] == "GROUNDED"
    prov = payload["provenance"]
    assert prov["source"]["source_id"] == "product-master"
    assert prov["source"]["source_system"] == "api-delpi"
    assert prov["specialist_id"] == "davi"
    assert prov["protocol"] == "MCP"
    assert prov["action_id"] == "search_products"
    assert "candidate_token" not in str(payload)


def test_grounded_empty_result_is_not_failure():
    governed = _governed(
        outcomes={
            "discover_delpi_information": _discovery_outcome([_candidate()]),
            "execute_delpi_information": RemoteToolOutcome(
                content_text="ok", structured=EXECUTE_EMPTY
            ),
        }
    )
    result = _handler(governed).execute(_request())
    assert result.grounding_status is GroundingStatus.GROUNDED
    assert "Não encontrei produtos" in result.content


def test_truncated_result_surfaces_limitation():
    truncated = {**EXECUTE_OK, "truncated": True}
    governed = _governed(
        outcomes={
            "discover_delpi_information": _discovery_outcome([_candidate()]),
            "execute_delpi_information": RemoteToolOutcome(
                content_text="ok",
                structured=truncated,
                is_complete=False,
            ),
        }
    )
    result = _handler(governed).execute(_request())
    assert result.grounding_status is GroundingStatus.GROUNDED
    assert LIMITATION_RESULT_TRUNCATED in result.limitations
    assert "Resultado parcial" in result.content


def test_source_unavailable_yields_truthful_non_grounded():
    governed = _governed(
        errors={
            "discover_delpi_information": SpecialistInteropError(
                MCP_UNAVAILABLE, "down"
            )
        }
    )
    result = _handler(governed).execute(_request())
    assert result.grounding_status is GroundingStatus.NON_GROUNDED
    assert LIMITATION_DELPI_SOURCE_UNVERIFIED in result.limitations
    assert DELPI_UNVERIFIED_DISCLOSURE in result.content
    assert result.provenance is None


def test_not_applicable_uses_plain_model_path():
    governed = _governed(
        outcomes={"discover_delpi_information": _discovery_outcome([])}
    )
    result = _handler(governed).execute(_request())
    assert result.grounding_status is GroundingStatus.NON_GROUNDED
    assert LIMITATION_DELPI_SOURCE_UNVERIFIED not in result.limitations
    assert DELPI_UNVERIFIED_DISCLOSURE not in result.content


def test_no_governed_read_component_is_non_grounded():
    result = _handler().execute(_request())
    assert result.grounding_status is GroundingStatus.NON_GROUNDED
    assert result.provenance is None


def test_serialized_result_never_contains_secrets():
    governed = _governed(
        outcomes={
            "discover_delpi_information": _discovery_outcome([_candidate()]),
            "execute_delpi_information": RemoteToolOutcome(
                content_text="ok", structured=EXECUTE_OK
            ),
        }
    )
    payload = serialize_result(_handler(governed).execute(_request()))
    serialized = str(payload)
    for leaked in ("opaque-token", "candidate_token", "authorization"):
        assert leaked not in serialized


def test_product_master_is_source_not_davi():
    assert PRODUCT_MASTER_SOURCE.source_system == "api-delpi"
    assert PRODUCT_MASTER_SOURCE.provider_name == "DAVI"
