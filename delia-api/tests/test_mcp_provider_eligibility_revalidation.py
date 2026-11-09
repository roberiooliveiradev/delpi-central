"""R1-RW01: Core eligibility revalidation at invoke time."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.application.ports.mcp_provider_eligibility_port import (
    McpProviderEligibilityError,
)
from app.infrastructure.interoperability.mcp.core_eligibility_guard import (
    CoreMcpProviderEligibilityGuard,
)
from app.infrastructure.interoperability.mcp.core_provider_registry import (
    CoreMcpProviderRegistryClient,
    CoreMcpProviderRegistryError,
)


def test_guard_allows_eligible_provider():
    client = MagicMock(spec=CoreMcpProviderRegistryClient)
    client.list_eligible.return_value = [
        {"providerRef": "davi"},
        {"providerRef": "teo"},
    ]
    CoreMcpProviderEligibilityGuard(client).require_eligible("davi")


def test_guard_blocks_revoked_provider():
    client = MagicMock(spec=CoreMcpProviderRegistryClient)
    client.list_eligible.return_value = [{"providerRef": "teo"}]
    with pytest.raises(McpProviderEligibilityError) as exc:
        CoreMcpProviderEligibilityGuard(client).require_eligible("davi")
    assert exc.value.code == "mcp_provider_not_eligible"


def test_guard_fail_closed_when_core_unavailable():
    client = MagicMock(spec=CoreMcpProviderRegistryClient)
    client.list_eligible.side_effect = CoreMcpProviderRegistryError(
        "core_unavailable"
    )
    with pytest.raises(McpProviderEligibilityError) as exc:
        CoreMcpProviderEligibilityGuard(client).require_eligible("davi")
    assert exc.value.code == "mcp_provider_registry_unavailable"


def test_governed_invoke_revalidates_before_wire():
    """Simulate post-composition revoke: eligibility blocks invoke."""
    from app.application.capability_provision.contracts import (
        CapabilityGroup,
        ProviderCapability,
    )
    from app.application.capability_provision.governed_capability_orchestrator import (
        OperationalCapabilityOrchestrator,
    )
    from app.application.interaction.capability_attempt import (
        GovernedCapabilityStatus,
    )
    from app.application.interaction.turn_budget import TurnDeadline
    from app.domain.evidence.model import SourceRef
    from app.domain.specialist_interop.model import SpecialistOperationClass
    import time

    group = CapabilityGroup(
        provider_id="mcp",
        group_id="davi",
        owner_ref="api-delpi",
        display_name="DAVI",
        capabilities=(
            ProviderCapability(
                capability_id="davi.execute_delpi_information",
                group_id="davi",
                provider_id="mcp",
                remote_name="execute_delpi_information",
                owner="api-delpi",
                operation_class=SpecialistOperationClass.READ,
                description="x",
                input_schema={"type": "object"},
                binding={
                    "specialist_id": "davi",
                    "remote_name": "execute_delpi_information",
                },
            ),
        ),
        source=SourceRef(
            source_id="api-delpi",
            source_system="api-delpi",
            provider_name="DAVI",
        ),
    )

    class _Prov:
        provider_id = "mcp"

        def list_groups(self, **_kwargs):
            from app.application.capability_provision.contracts import (
                ProviderSurface,
            )

            return ProviderSurface(groups=(group,), failures=())

    class _Block:
        def require_eligible(self, provider_ref: str) -> None:
            raise McpProviderEligibilityError(
                "mcp_provider_not_eligible", "revoked"
            )

    orch = OperationalCapabilityOrchestrator(
        [_Prov()],
        orchestration_instructions={"x": "y"},
        mcp_provider_eligibility=_Block(),
    )
    # Bypass live group fetch by stubbing _groups
    orch._groups = lambda *_a, **_k: ({"mcp:davi": group}, ())  # type: ignore[method-assign]
    deadline = TurnDeadline.start(30.0)
    attempt = orch._governed_semantic_tool_invoke(
        capability_id="davi.execute_delpi_information",
        arguments={},
        input_text="q",
        correlation="c1",
        actor_user_id="u1",
        session_id="s1",
        workspace_context=None,
        prior_turns=(),
        prepare_only=False,
        deadline=deadline,
    )
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert attempt.error_code == "mcp_provider_not_eligible"
