"""C3-INTERACTION-RUNTIME-01 — interactive conversation vertical slice.

Covers auth boundary, request validation, application semantics, bounded
response, and the full HTTP -> Application -> port -> DELIA_RESULT path.
"""

from __future__ import annotations

import pytest

from app.application.interaction.contracts import (
    InteractiveTurnRequest,
    InteractiveTurnResult,
)
from app.application.interaction.errors import InteractionError
from app.application.interaction.handle_interactive_turn import (
    DEFAULT_MODEL_REF,
    HandleInteractiveConversationTurn,
    has_delia_access,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.create_app import create_app
from app.domain.interaction.model import TurnKind
from app.infrastructure.model_invocation.deterministic_test_adapter import (
    DeterministicTestAdapter,
)


PATH = "/interaction/turns"


def _context(
    permissions: tuple[str, ...] = ("delia.access",),
    is_superadmin: bool = False,
) -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id="u1",
        name="User",
        email="u@example.com",
        effective_permissions=permissions,
        is_superadmin=is_superadmin,
    )


class _Provider:
    def __init__(self, context: PlatformAccessContext | None = None, exc=None):
        self._context = context or _context()
        self._exc = exc

    def resolve(self, bearer_token: str):
        if self._exc is not None:
            raise self._exc
        return self._context


def _client(context=None, provider_exc=None, handler=None, port=None):
    app = create_app(
        testing=True,
        platform_access_provider=_Provider(context, provider_exc),
        model_invocation_port=port,
        interaction_turn_handler=handler,
    )
    return app.test_client()


def _post(client, body=None, headers=None, raw=None):
    kwargs = {}
    if raw is not None:
        kwargs["data"] = raw
        kwargs["content_type"] = "application/json"
    else:
        kwargs["json"] = body
    kwargs["headers"] = headers or {"Authorization": "Bearer t"}
    return client.post(PATH, **kwargs)


def _use_case(behavior: str = "success") -> HandleInteractiveConversationTurn:
    return HandleInteractiveConversationTurn(
        InvokeModel(DeterministicTestAdapter(behavior=behavior))
    )


# --- A. AuthN / AuthZ -------------------------------------------------------


def test_missing_authorization_header_returns_401():
    response = _client().post(PATH, json={"input": "oi"})
    assert response.status_code == 401
    assert response.get_json()["code"] == "unauthenticated"


def test_invalid_bearer_scheme_returns_401():
    response = _client().post(
        PATH, json={"input": "oi"}, headers={"Authorization": "Basic abc"}
    )
    assert response.status_code == 401


def test_core_unavailable_fails_closed_503():
    from app.application.ports.platform_access_port import (
        AuthorityUnavailableError,
    )

    client = _client(provider_exc=AuthorityUnavailableError("core_unavailable"))
    response = _post(client, {"input": "oi"})
    assert response.status_code == 503


def test_authentication_failure_returns_401():
    from app.application.ports.platform_access_port import AuthenticationError

    client = _client(provider_exc=AuthenticationError("invalid_token"))
    response = _post(client, {"input": "oi"})
    assert response.status_code == 401


def test_no_delia_access_returns_403():
    client = _client(context=_context(permissions=("other.permission",)))
    response = _post(client, {"input": "oi"})
    assert response.status_code == 403
    assert response.get_json()["code"] == "forbidden"


def test_delia_access_allows_interaction():
    response = _post(_client(), {"input": "olá DÉLIA"})
    assert response.status_code == 200


def test_superadmin_allows_interaction():
    client = _client(context=_context(permissions=(), is_superadmin=True))
    response = _post(client, {"input": "oi"})
    assert response.status_code == 200


def test_use_case_rejects_none_context():
    with pytest.raises(InteractionError) as excinfo:
        _use_case().execute(
            InteractiveTurnRequest(access_context=None, input_text="oi")
        )
    assert excinfo.value.code == "unauthenticated"


# --- B. Request validation ---------------------------------------------------


def test_missing_input_returns_invalid_request():
    response = _post(_client(), {})
    assert response.status_code == 400
    assert response.get_json()["code"] == "invalid_request"


def test_blank_input_returns_invalid_request():
    response = _post(_client(), {"input": "   "})
    assert response.status_code == 400


def test_oversized_input_returns_invalid_request():
    response = _post(_client(), {"input": "x" * 16_385})
    assert response.status_code == 400


def test_boundary_size_input_accepted():
    response = _post(_client(), {"input": "x" * 16_384})
    assert response.status_code == 200


@pytest.mark.parametrize(
    "field",
    [
        "permissions",
        "roles",
        "is_superadmin",
        "provider",
        "model",
        "agent",
        "system_prompt",
        "tools",
        "act",
        "prepare",
        "credentials",
        "session_id",
        "authorization",
    ],
)
def test_forbidden_request_fields_rejected(field):
    response = _post(_client(), {"input": "oi", field: "x"})
    assert response.status_code == 400
    assert response.get_json()["code"] == "invalid_request"


def test_non_json_body_rejected():
    response = _post(_client(), raw="not json")
    assert response.status_code == 400


# --- C. Application ----------------------------------------------------------


def test_request_scoped_session_and_turns_created():
    result = _use_case().execute(
        InteractiveTurnRequest(access_context=_context(), input_text="oi")
    )
    assert isinstance(result, InteractiveTurnResult)
    assert result.session_id and result.user_turn_id and result.result_turn_id
    assert result.session_id != result.user_turn_id
    assert result.user_turn_id != result.result_turn_id


def test_model_invocation_port_is_invoked():
    captured = {}

    class SpyAdapter(DeterministicTestAdapter):
        def invoke(self, request):
            captured["request"] = request
            return super().invoke(request)

    use_case = HandleInteractiveConversationTurn(InvokeModel(SpyAdapter()))
    use_case.execute(
        InteractiveTurnRequest(access_context=_context(), input_text="oi")
    )
    request = captured["request"]
    assert request.task_purpose_id == "delia.interaction.turn"
    assert request.model_ref == DEFAULT_MODEL_REF
    assert request.timeout_seconds == 30.0
    assert request.instruction_lineage.instruction_id == "delia.interaction.base"


def test_result_epistemic_class_defaults_to_hypothesis():
    result = _use_case().execute(
        InteractiveTurnRequest(access_context=_context(), input_text="oi")
    )
    assert result.epistemic_class.value == "HYPOTHESIS"


def test_provider_claiming_fact_never_produces_fact():
    result = _use_case("claim_fact").execute(
        InteractiveTurnRequest(access_context=_context(), input_text="oi")
    )
    assert result.epistemic_class.value != "FACT"


def test_tool_call_output_rejected_forbidden():
    with pytest.raises(InteractionError) as excinfo:
        _use_case("tool_calls").execute(
            InteractiveTurnRequest(access_context=_context(), input_text="oi")
        )
    assert excinfo.value.code == "forbidden_model_output"


def test_secret_bearing_output_rejected_forbidden():
    with pytest.raises(InteractionError) as excinfo:
        _use_case("secret").execute(
            InteractiveTurnRequest(access_context=_context(), input_text="oi")
        )
    assert excinfo.value.code == "forbidden_model_output"


def test_cot_bearing_output_rejected_forbidden():
    with pytest.raises(InteractionError) as excinfo:
        _use_case("cot").execute(
            InteractiveTurnRequest(access_context=_context(), input_text="oi")
        )
    assert excinfo.value.code == "forbidden_model_output"


def test_invalid_structured_output_mapped():
    with pytest.raises(InteractionError) as excinfo:
        _use_case("missing_fields").execute(
            InteractiveTurnRequest(access_context=_context(), input_text="oi")
        )
    assert excinfo.value.code == "invalid_model_output"


def test_provider_unavailable_mapped():
    with pytest.raises(InteractionError) as excinfo:
        _use_case("unavailable").execute(
            InteractiveTurnRequest(access_context=_context(), input_text="oi")
        )
    assert excinfo.value.code == "model_unavailable"


def test_timeout_mapped():
    with pytest.raises(InteractionError) as excinfo:
        _use_case("timeout").execute(
            InteractiveTurnRequest(access_context=_context(), input_text="oi")
        )
    assert excinfo.value.code == "model_timeout"


def test_raw_sdk_exception_maps_to_model_unavailable():
    with pytest.raises(InteractionError) as excinfo:
        _use_case("raw_exception").execute(
            InteractiveTurnRequest(access_context=_context(), input_text="oi")
        )
    assert excinfo.value.code == "model_unavailable"


def test_no_act_authorization_side_effect():
    result = _use_case().execute(
        InteractiveTurnRequest(access_context=_context(), input_text="oi")
    )
    assert result.authorizes_act() is False
    assert result.is_fact() is False


def test_no_session_persistence_objects_exist():
    import app.application.interaction as interaction_pkg
    import pathlib

    source = "".join(
        p.read_text() for p in pathlib.Path(interaction_pkg.__file__).parent.rglob("*.py")
    )
    for forbidden in ("SessionRepository", "MessageRepository", "ConversationRepository"):
        assert forbidden not in source


# --- D. Response contract + full vertical integration -----------------------


def test_full_vertical_http_path_returns_bounded_result():
    response = _post(_client(), {"input": "olá DÉLIA"})
    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == {
        "session_id",
        "user_turn_id",
        "result_turn_id",
        "content",
        "epistemic_class",
        "limitations",
        "generated_at",
        "model_invocation_id",
    }
    assert body["epistemic_class"] == "HYPOTHESIS"
    assert body["content"].strip()
    assert isinstance(body["limitations"], list)


def test_response_does_not_leak_provider_or_authority_internals():
    response = _post(_client(), {"input": "oi"})
    text = response.get_data(as_text=True)
    for leaked in (
        "Bearer",
        "instruction",
        "system_prompt",
        "tool_call",
        "chain_of_thought",
        "delia.access",
        "effective_permissions",
        "provider",
    ):
        assert leaked not in text


def test_error_body_has_bounded_code_and_detail():
    response = _post(_client(context=_context(permissions=())), {"input": "oi"})
    body = response.get_json()
    assert set(body) == {"detail", "code"}


def test_http_timeout_maps_to_504():
    client = _client(port=DeterministicTestAdapter(behavior="timeout"))
    response = _post(client, {"input": "oi"})
    assert response.status_code == 504
    assert response.get_json()["code"] == "model_timeout"


def test_http_forbidden_model_output_maps_to_502():
    client = _client(port=DeterministicTestAdapter(behavior="secret"))
    response = _post(client, {"input": "oi"})
    assert response.status_code == 502


def test_turn_kind_separation_user_input_vs_result():
    # USER_INPUT carries untrusted data; DELIA_RESULT carries the
    # classified output — both recorded on one request-scoped session.
    assert TurnKind.USER_INPUT.value == "USER_INPUT"
    assert TurnKind.DELIA_RESULT.value == "DELIA_RESULT"
