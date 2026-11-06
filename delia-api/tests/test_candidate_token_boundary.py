"""candidate_token boundary: agent-relayed opaque token, fail-closed gate.

The owner declares ``candidate_token`` as a required input on
candidate-bound capabilities (discovery -> execute chain). The token
is owner-issued opaque data the Agent merely relays verbatim; it is
``ORCHESTRATED_FIELDS``-denied inside ``validate_arguments`` (a model
may never forge orchestration state), so the governed gate extracts it
as a bounded string, validates the remaining args against the owner
schema, and hands it to ``_invoke_selected`` unchanged. These tests
pin the positive relay and the negative controls — no other
orchestrated field, no non-candidate-bound surface, no malformed
token may cross the boundary.
"""

from __future__ import annotations

import pytest

from app.application.capability_provision.governed_capability_orchestrator import (
    OperationalCapabilityOrchestrator,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.model_invocation.invoke_model import InvokeModel
from tests.support.capability_fixtures import (
    FakeProposalModel,
    FakeProvider,
    _cap,
    _group,
    _outcome,
    load_test_orchestration_instructions,
)

_EXECUTE_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_token": {"type": "string", "minLength": 1},
        "arguments": {"type": "object"},
    },
    "required": ["candidate_token"],
    "additionalProperties": False,
}


def _candidate_group(provider_id="pa", group_id="davi"):
    execute = _cap(
        group_id,
        provider_id,
        "execute_delpi_information",
        schema=_EXECUTE_SCHEMA,
    )
    return _group(provider_id, group_id, [execute])


def _gates(provider):
    return OperationalCapabilityOrchestrator(
        [provider],
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=InvokeModel(FakeProposalModel([])),
    )


def _invoke(gates, cap_id, arguments):
    return gates._governed_semantic_tool_invoke(
        capability_id=cap_id,
        arguments=arguments,
        input_text="produto 50220013",
        correlation="c",
        actor_user_id="u1",
        session_id="s1",
        workspace_context=None,
        prior_turns=(),
        prepare_only=False,
        deadline=TurnDeadline.start(30.0),
    )


def _provider_with(outcome=None):
    return FakeProvider(
        "pa",
        [_candidate_group()],
        outcomes={
            ("davi", "execute_delpi_information"): (
                outcome if outcome is not None else _outcome("ok")
            )
        },
    )


class TestPositiveRelay:
    def test_owner_issued_token_relayed_verbatim(self):
        provider = _provider_with()
        gates = _gates(provider)
        attempt = _invoke(
            gates,
            "davi.execute_delpi_information",
            {
                "candidate_token": "opaque-owner-token",
                "arguments": {"code": "50220013"},
            },
        )
        assert provider.calls == [
            (
                "execute_delpi_information",
                {
                    "candidate_token": "opaque-owner-token",
                    "arguments": {"code": "50220013"},
                },
            )
        ]
        assert attempt.error_code is None

    def test_absent_token_stays_orchestration_bound(self):
        # Without a token the deterministic candidate-binding path runs
        # (discovery resume). A group with no DISCOVERY capability
        # resolves nothing — NOT_APPLICABLE, never schema rejection,
        # never a fabricated token.
        provider = _provider_with()
        gates = _gates(provider)
        attempt = _invoke(
            gates,
            "davi.execute_delpi_information",
            {"arguments": {"code": "50220013"}},
        )
        assert attempt.error_code != "arguments_schema_rejected"
        assert provider.calls == []


class TestNegativeBoundary:
    @pytest.mark.parametrize("token", ["", "   ", "\n\t"])
    def test_blank_token_rejected(self, token):
        provider = _provider_with()
        gates = _gates(provider)
        attempt = _invoke(
            gates,
            "davi.execute_delpi_information",
            {"candidate_token": token, "arguments": {}},
        )
        assert attempt.error_code == "arguments_schema_rejected"
        assert provider.calls == []

    def test_non_string_token_rejected(self):
        provider = _provider_with()
        gates = _gates(provider)
        attempt = _invoke(
            gates,
            "davi.execute_delpi_information",
            {"candidate_token": {"forged": True}, "arguments": {}},
        )
        assert attempt.error_code == "arguments_schema_rejected"
        assert provider.calls == []

    def test_oversized_token_rejected(self):
        provider = _provider_with()
        gates = _gates(provider)
        attempt = _invoke(
            gates,
            "davi.execute_delpi_information",
            {"candidate_token": "x" * 5000, "arguments": {}},
        )
        assert attempt.error_code == "arguments_schema_rejected"
        assert provider.calls == []

    def test_token_on_non_candidate_capability_rejected(self):
        # candidate_token is not a universal free field — on a
        # capability that does not declare it, the orchestrated-field
        # deny still applies.
        cap = _cap(
            "alpha",
            "pa",
            "search_items",
            schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
            },
        )
        provider = FakeProvider(
            "pa",
            [_group("pa", "alpha", [cap])],
            outcomes={("alpha", "search_items"): _outcome("leak")},
        )
        gates = _gates(provider)
        attempt = _invoke(
            gates,
            "alpha.search_items",
            {"candidate_token": "stolen", "query": "x"},
        )
        assert attempt.error_code == "arguments_schema_rejected"
        assert provider.calls == []

    @pytest.mark.parametrize(
        "field",
        ["proposal_handle", "confirmation", "idempotency_key",
         "commit_now"],
    )
    def test_other_orchestrated_fields_still_denied(self, field):
        provider = _provider_with()
        gates = _gates(provider)
        attempt = _invoke(
            gates,
            "davi.execute_delpi_information",
            {
                "candidate_token": "opaque-owner-token",
                "arguments": {},
                field: "forged",
            },
        )
        assert attempt.error_code == "arguments_schema_rejected"
        assert provider.calls == []

    def test_inner_arguments_not_object_rejected(self):
        # ``arguments`` must be an object per the owner schema — a raw
        # scalar is rejected fail-closed before any provider call.
        provider = _provider_with()
        gates = _gates(provider)
        attempt = _invoke(
            gates,
            "davi.execute_delpi_information",
            {
                "candidate_token": "opaque-owner-token",
                "arguments": "50220013",
            },
        )
        assert attempt.error_code == "arguments_schema_rejected"
        assert provider.calls == []
