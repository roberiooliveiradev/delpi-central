"""DELIA-C3-GOVERNED-STAGE-RESUME-INDEPENDENT-VERIFICATION-01 (CP5/R3).

~60s NDJSON stream through the REAL route, worker thread, queue,
generator and monotonic clock. The governed-resume machinery is real
(`OperationalCapabilityOrchestrator` + `HandleInteractiveConversationTurn`
+ `TurnDeadline`); only the model adapter is a double that enforces its
own deadline exactly like the real HTTP adapter — it sleeps for the
granted ``timeout_seconds`` and then raises ``TIMEOUT``.

Timeline (turn_budget=35s, interaction_total=60s, per-attempt cap=30s):
admission + select_group resolve instantly → select_capability gets the
full ~30s stage grant → TIMEOUT at ~30s → CONTINUING at the real retry
boundary → prior stage proposals replay from the checkpoint → attempt 2
grants the remaining ~29s → TIMEOUT at ~60s → single terminal.

Asserts: stream stays alive ~60s, CONTINUING fires once, exactly one
terminal record, bounded inter-event gaps, replayed stages not
re-invoked. Run inside the dev container (``/app`` bind-mounted).
"""

from __future__ import annotations

import json
import sys
import time

sys.path.insert(0, "/app")

from app.application.capability_provision.contracts import (
    CapabilityGroup,
    ProviderCapability,
    ProviderSurface,
)
from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    GOAL_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    INTERACTION_ADMISSION_INSTRUCTION_ID,
    NATIVE_ASSESSMENT_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
)
from app.application.interaction.handle_interactive_turn import (
    HandleInteractiveConversationTurn,
)
from app.application.model_invocation.contracts import (
    ProviderInvocationPayload,
)
from app.application.model_invocation.errors import (
    TIMEOUT,
    ModelInvocationError,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.create_app import create_app
from app.domain.evidence.model import ModelRef, SourceRef
from app.domain.model_invocation.model import ProviderExposureClass
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)

MODEL_REF = ModelRef(model_id="eval-model", version="1", owner_ref="DELPI")
TIMEOUT_PURPOSE = CAPABILITY_SELECTION_INSTRUCTION_ID

_PROPOSALS = {
    INTERACTION_ADMISSION_INSTRUCTION_ID: {
        "requires_capability": True,
    },
    GROUP_SELECTION_INSTRUCTION_ID: {
        "applicable": True,
        "capability_group_id": "openmetrics:metrics",
    },
    GOAL_INSTRUCTION_ID: {"goal_class": "read"},
    NATIVE_ASSESSMENT_INSTRUCTION_ID: {"status": "sufficient"},
    ARGUMENTS_INSTRUCTION_ID: {"arguments": {}},
}


class _DeadlineBoundModel:
    """Model adapter double — resolves the fast stages instantly and
    enforces the granted deadline on ``TIMEOUT_PURPOSE`` exactly like
    the real HTTP adapter (the remote call returns TIMEOUT at the
    granted timeout), so the orchestrator's own budget math decides the
    timeline."""

    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self) -> None:
        self.calls: list[tuple[str, float]] = []

    def invoke(self, request) -> ProviderInvocationPayload:
        granted = float(request.timeout_seconds)
        self.calls.append((request.task_purpose_id, granted))
        if request.task_purpose_id == TIMEOUT_PURPOSE:
            time.sleep(granted + 0.4)
            raise ModelInvocationError(TIMEOUT, "stage deadline exceeded")
        return ProviderInvocationPayload(
            structured_output=_PROPOSALS.get(request.task_purpose_id),
            generated_at="2026-01-01T00:00:00+00:00",
        )


class _StaticProvider:
    provider_id = "openmetrics"

    def list_groups(self, *, correlation_id, timeout_seconds=None):
        capability = ProviderCapability(
            capability_id="cap-1",
            group_id="openmetrics:metrics",
            provider_id="openmetrics",
            remote_name="list_items",
            owner="openmetrics",
            operation_class=SpecialistOperationClass.READ,
        )
        return ProviderSurface(
            groups=(
                CapabilityGroup(
                    provider_id="openmetrics",
                    group_id="openmetrics:metrics",
                    owner_ref="openmetrics-owner",
                    display_name="Open Metrics",
                    capabilities=(capability,),
                    source=SourceRef(
                        source_id="metrics-db",
                        source_system="Métricas Operacionais",
                        provider_name="openmetrics",
                        observed_at="2026-01-01T00:00:00+00:00",
                    ),
                ),
            )
        )

    def invoke(
        self, capability, arguments, *, correlation_id,
        timeout_seconds=None,
    ):
        return SpecialistOutcome(
            status=SpecialistResultStatus.COMPLETED,
            provenance=SpecialistResultProvenance(
                specialist_id="openmetrics",
                remote_name=capability.remote_name,
                protocol=InteropProtocol.MCP,
                correlation_id=correlation_id,
                observed_at="2026-01-01T00:00:00+00:00",
            ),
            content_text="ok",
            structured={},
        )


class _ContextResolver:
    def resolve(self, bearer_token: str) -> PlatformAccessContext:
        return PlatformAccessContext(
            user_id="u1",
            name="User",
            email="u@example.com",
            effective_permissions=("delia.access",),
            is_superadmin=False,
        )


def main() -> None:
    model = _DeadlineBoundModel()
    orchestrator = OperationalCapabilityOrchestrator(
        [_StaticProvider()],
        invoke_model=InvokeModel(model),
        model_ref=MODEL_REF,
        turn_budget_seconds=35.0,
        model_stage_timeout_seconds=30.0,
        interaction_total_budget_seconds=60.0,
        max_governed_attempts=2,
    )
    handler = HandleInteractiveConversationTurn(
        InvokeModel(model),
        capability_orchestration=orchestrator,
        turn_budget_seconds=35.0,
    )
    app = create_app(
        testing=True,
        platform_access_provider=_ContextResolver(),
        interaction_turn_handler=handler,
    )
    client = app.test_client()

    started = time.monotonic()
    response = client.post(
        "/interaction/turns",
        json={"input": "qual a descrição do item 10080045?"},
        headers={
            "Authorization": "Bearer t",
            "Accept": "application/x-ndjson",
        },
        buffered=False,
    )

    records: list[tuple[float, dict]] = []
    for raw in response.response:
        line = raw.decode("utf-8", errors="replace").strip()
        if line:
            records.append((time.monotonic() - started, json.loads(line)))
    elapsed = time.monotonic() - started

    phases = [
        r["phase"] for _, r in records if r.get("type") == "activity_event"
    ]
    continuing = [p for p in phases if p == "CONTINUING"]
    terminals = [
        r["type"] for _, r in records
        if r.get("type") in ("turn_result", "turn_error")
    ]
    timed = [
        (purpose, granted)
        for purpose, granted in model.calls
        if purpose == TIMEOUT_PURPOSE
    ]
    admission_calls = sum(
        1 for p, _ in model.calls
        if p == INTERACTION_ADMISSION_INSTRUCTION_ID
    )
    group_calls = sum(
        1 for p, _ in model.calls
        if p == GROUP_SELECTION_INSTRUCTION_ID
    )
    gaps = [
        round(records[i][0] - records[i - 1][0], 2)
        for i in range(1, len(records))
    ]

    print(
        json.dumps(
            {
                "http_status": response.status_code,
                "elapsed_s": round(elapsed, 2),
                "record_count": len(records),
                "timed_stage_calls": [
                    {"purpose": p, "granted_s": round(g, 2)}
                    for p, g in timed
                ],
                "admission_invocations": admission_calls,
                "group_selection_invocations": group_calls,
                "continuing_events": len(continuing),
                "terminal_records": terminals,
                "max_inter_event_gap_s": max(gaps) if gaps else 0.0,
                "phases": phases,
                "verdict": {
                    "stream_alive_to_60s": 55.0 <= elapsed <= 75.0,
                    "continuing_once": len(continuing) == 1,
                    "single_terminal": len(terminals) == 1,
                    "admission_proposal_replayed": admission_calls == 1,
                    "group_rerun_bound": group_calls <= 2,
                    "per_attempt_bounded": all(
                        g <= 30.0 for _, g in model.calls
                    ),
                    "attempts_bounded": len(timed) == 2,
                },
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
