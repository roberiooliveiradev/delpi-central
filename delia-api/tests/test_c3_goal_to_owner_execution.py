"""C3 Task 13 — goal-to-owner execution reliability.

TASK: DELIA-C3-GOAL-TO-OWNER-CAUSAL-REMEDIATION-AND-PRODUCTION-DEPLOY-01

Locks:
- E2: declared answer requirements (ordering / complete_coverage /
  min_items) trigger the EXISTING bounded page walk when the owner's
  first page cannot prove them — 'the latest' becomes answerable
  through the authorized contract (owner orders records, pagination
  is contract-surface) instead of an unreachable goal.
- The walk is never triggered by requirement-free turns (baseline
  parity) and stays bounded by max_pages / deadline / page failures.
- A page cursor not present in the sent arguments is discovered from
  the capability's own published input schema — typed as the owner
  declared it (TÉO ``page`` is a string).
- COUNT-intent aggregation semantics are unchanged.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from app.application.capability_provision.contracts import (
    CapabilityGroup,
    ProviderCapability,
    ProviderSurface,
)
from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID,
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    GOAL_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    LIMITATION_INSUFFICIENT_EVIDENCE,
)
from app.application.model_invocation.contracts import (
    ProviderInvocationPayload,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.domain.evidence.model import ModelRef, SourceRef
from app.domain.model_invocation.model import ProviderExposureClass
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from tests.conftest import load_test_orchestration_instructions


TEST_MODEL_REF = ModelRef(
    model_id="test-model", version="1", owner_ref="DELPI"
)

_STAGE_IDS = frozenset(
    {
        GROUP_SELECTION_INSTRUCTION_ID,
        CAPABILITY_SELECTION_INSTRUCTION_ID,
        ARGUMENTS_INSTRUCTION_ID,
        GOAL_INSTRUCTION_ID,
        GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID,
    }
)


@pytest.fixture
def capture_mode_logs(caplog):
    app_logger = logging.getLogger("app")
    previous = (app_logger.propagate, app_logger.level)
    app_logger.propagate = True
    app_logger.setLevel(logging.INFO)
    try:
        with caplog.at_level(logging.INFO):
            yield caplog
    finally:
        app_logger.propagate, app_logger.level = previous


class _ProposalModel:
    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self, proposal):
        items = list(proposal) if isinstance(proposal, list) else [proposal]
        self._queues: dict[str, list] = {}
        self.requests = []
        self._generic: list = []
        for item in items:
            if isinstance(item, dict) and set(item) & _STAGE_IDS:
                for purpose, payload in item.items():
                    self._queues.setdefault(purpose, []).append(payload)
            else:
                self._generic.append(item)
        self._last: dict[str, object] = {}

    def invoke(self, request):
        self.requests.append(request)
        purpose = request.task_purpose_id
        queue = self._queues.get(purpose)
        if queue:
            resolved = queue.pop(0)
        elif purpose == (
            "delia.capability_orchestration.interaction_admission"
        ):
            resolved = self._last.get(purpose)
        elif self._generic:
            resolved = self._generic.pop(0)
        else:
            resolved = self._last.get(purpose)
        if resolved is not None:
            self._last[purpose] = resolved
        return ProviderInvocationPayload(
            structured_output=resolved,
            generated_at="2026-01-01T00:00:00+00:00",
        )


def _outcome(structured) -> SpecialistOutcome:
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="provider_alpha:guide",
            remote_name="record_read",
            protocol=InteropProtocol.MCP,
            correlation_id="corr-t13",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text="Execution completed.",
        is_complete=True,
        structured=structured,
        limitations=(),
    )


def _teo_process_page(
    items: list[dict[str, Any]], total: int
) -> dict[str, Any]:
    """TÉO ``record_read`` search envelope — ``{total, items}`` inside
    the tool's ``{success,message,data}`` wrapper; no page/has_more
    keys (exact replayed owner shape)."""
    return {
        "success": True,
        "message": "Registros.",
        "data": {"total": total, "items": list(items)},
    }


def _process(processo_id: str, name: str, updated: str) -> dict[str, Any]:
    return {
        "processo_id": processo_id,
        "nome_processo": name,
        "created_at": updated,
        "updated_at": updated,
    }


class _PagingProvider:
    """Returns pages in invocation order (like the owner honoring the
    declared ``page`` cursor); ``fail_pages`` marks page indexes that
    raise the provider error."""

    def __init__(self, pages, *, fail_pages=frozenset()):
        self.provider_id = "mcp"
        self._pages = list(pages)
        self._fail = set(fail_pages)
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self._index = 0

    def list_groups(self, *, correlation_id, timeout_seconds=None):
        cap = ProviderCapability(
            capability_id="alpha.record_read",
            group_id="alpha",
            provider_id="mcp",
            remote_name="record_read",
            owner="alpha",
            operation_class=SpecialistOperationClass.READ,
            description="record read",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "entity": {"type": "string"},
                    "q": {"type": "string"},
                    # TÉO contract: the page cursor is a STRING.
                    "page": {"type": "string"},
                    "page_size": {"type": "string"},
                },
                "required": ["action", "entity"],
            },
            binding={"ref": "record_read"},
        )
        return ProviderSurface(
            groups=(
                CapabilityGroup(
                    provider_id="mcp",
                    group_id="alpha",
                    owner_ref="alpha",
                    display_name="alpha",
                    capabilities=(cap,),
                    source=SourceRef(
                        source_id="alpha",
                        source_system="alpha",
                        provider_name="alpha",
                    ),
                ),
            )
        )

    def invoke(self, capability, arguments, *, correlation_id,
               timeout_seconds=None):
        self.calls.append((capability.remote_name, dict(arguments)))
        idx = self._index
        self._index += 1
        if idx in self._fail:
            from app.application.capability_provision.contracts import (
                CapabilityProviderError,
            )

            raise CapabilityProviderError("page_failure", "page failed")
        return _outcome(self._pages[min(idx, len(self._pages) - 1)])


class _NoCursorProvider(_PagingProvider):
    """Capability with NO page cursor anywhere — walk impossible."""

    def list_groups(self, *, correlation_id, timeout_seconds=None):
        surface = super().list_groups(
            correlation_id=correlation_id
        )
        cap = surface.groups[0].capabilities[0]
        slim = ProviderCapability(
            capability_id=cap.capability_id,
            group_id=cap.group_id,
            provider_id=cap.provider_id,
            remote_name=cap.remote_name,
            owner=cap.owner,
            operation_class=cap.operation_class,
            description=cap.description,
            input_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "entity": {"type": "string"},
                    "q": {"type": "string"},
                },
                "required": ["action", "entity"],
            },
            binding=cap.binding,
        )
        group = surface.groups[0]
        return ProviderSurface(
            groups=(
                CapabilityGroup(
                    provider_id=group.provider_id,
                    group_id=group.group_id,
                    owner_ref=group.owner_ref,
                    display_name=group.display_name,
                    capabilities=(slim,),
                    source=group.source,
                ),
            )
        )


def _cri_orchestrator(provider, proposal):
    from app.infrastructure.config.cri_instruction_resource import (
        load_cri_instruction_clause,
    )

    clause = load_cri_instruction_clause(
        Path(__file__).resolve().parents[1]
        / "config"
        / "cri_instructions.delpi.json"
    )
    return OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(_ProposalModel(proposal)),
        model_ref=TEST_MODEL_REF,
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
        orchestration_instructions=(
            load_test_orchestration_instructions()
        ),
    )


def _proposal(goal=None):
    proposal = {
        GROUP_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "capability_group_id": "mcp:alpha",
        },
        CAPABILITY_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "remote_name": "record_read",
        },
        ARGUMENTS_INSTRUCTION_ID: {
            "arguments": {"action": "search", "entity": "process"}
        },
        GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID: {
            "correspondence": "corresponds",
        },
    }
    if goal is not None:
        proposal[CAPABILITY_SELECTION_INSTRUCTION_ID].update(goal)
    return proposal


def _attempt(provider, goal=None, text="qual o ultimo processo?"):
    orch = _cri_orchestrator(provider, _proposal(goal))
    return orch.attempt(text)


# ---------------------------------------------------------------------------
# E2 — ordering requirement drives the existing bounded page walk
# ---------------------------------------------------------------------------


def test_ordering_requirement_walks_pages_and_answers_latest(
    capture_mode_logs,
):
    """'último processo' — owner emits updated_at DESC pages with an
    authoritative total; a declared ordering makes the goal reachable:
    the bounded walk completes coverage, ordering is proven on the
    full set, records[0] is the latest."""
    pages = [
        _teo_process_page(
            [
                _process("p5", "Proc E", "2026-10-29T10:00:00Z"),
                _process("p4", "Proc D", "2026-10-28T09:00:00Z"),
            ],
            total=5,
        ),
        _teo_process_page(
            [
                _process("p3", "Proc C", "2026-10-27T08:00:00Z"),
                _process("p2", "Proc B", "2026-10-26T07:00:00Z"),
            ],
            total=5,
        ),
        _teo_process_page(
            [_process("p1", "Proc A", "2026-10-25T06:00:00Z")],
            total=5,
        ),
    ]
    provider = _PagingProvider(pages)
    attempt = _attempt(
        provider,
        goal={
            "goal_class": "read",
            "answer_requirements": {"ordering": "newest_first"},
        },
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    # The walk fetched the missing pages through the declared cursor.
    assert len(provider.calls) == 3
    assert provider.calls[0][1].get("page") is None
    assert provider.calls[1][1]["page"] == "2"
    assert provider.calls[2][1]["page"] == "3"
    assert LIMITATION_INSUFFICIENT_EVIDENCE not in attempt.limitations
    assert "decision=answered" in capture_mode_logs.text
    # The presented answer carries the actual latest record.
    assert "Proc E" in (attempt.content or "")


def test_no_requirements_single_page_call_only(capture_mode_logs):
    """Baseline parity — a requirement-free read never walks pages."""
    provider = _PagingProvider(
        [
            _teo_process_page(
                [_process("p1", "Proc A", "2026-10-29T10:00:00Z")],
                total=5,
            ),
        ]
    )
    attempt = _attempt(provider, goal={"goal_class": "read"})
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert len(provider.calls) == 1


def test_ordering_on_unordered_owner_records_stays_insufficient(
    capture_mode_logs,
):
    """Full coverage can still fail the ordering proof — honest
    insufficiency, never a picked 'latest' from an unordered set."""
    provider = _PagingProvider(
        [
            _teo_process_page(
                [
                    _process("p1", "Proc A", "2026-10-25T06:00:00Z"),
                    _process("p5", "Proc E", "2026-10-29T10:00:00Z"),
                ],
                total=3,
            ),
            _teo_process_page(
                [_process("p3", "Proc C", "2026-10-27T08:00:00Z")],
                total=3,
            ),
        ]
    )
    attempt = _attempt(
        provider,
        goal={
            "goal_class": "read",
            "answer_requirements": {"ordering": "newest_first"},
        },
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert len(provider.calls) >= 2
    assert LIMITATION_INSUFFICIENT_EVIDENCE in attempt.limitations
    assert "ordering_unproven" in capture_mode_logs.text


def test_min_items_shortfall_walks_until_quantity_met(capture_mode_logs):
    """'dois exemplos' with one item on page one of three — the
    declared quantity drives the walk until evidence satisfies it."""
    provider = _PagingProvider(
        [
            _teo_process_page(
                [_process("p1", "Item A", "2026-10-29T10:00:00Z")],
                total=3,
            ),
            _teo_process_page(
                [
                    _process("p2", "Item B", "2026-10-28T09:00:00Z"),
                    _process("p3", "Item C", "2026-10-27T08:00:00Z"),
                ],
                total=3,
            ),
        ]
    )
    attempt = _attempt(
        provider,
        goal={
            "goal_class": "read",
            "answer_requirements": {"min_items": 2},
        },
        text="me de dois exemplos de processo",
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert len(provider.calls) == 2
    assert LIMITATION_INSUFFICIENT_EVIDENCE not in attempt.limitations


def test_min_items_met_on_first_page_never_walks(capture_mode_logs):
    provider = _PagingProvider(
        [
            _teo_process_page(
                [
                    _process("p1", "Item A", "2026-10-29T10:00:00Z"),
                    _process("p2", "Item B", "2026-10-28T09:00:00Z"),
                ],
                total=2,
            ),
        ]
    )
    attempt = _attempt(
        provider,
        goal={
            "goal_class": "read",
            "answer_requirements": {"min_items": 2},
        },
    )
    assert len(provider.calls) == 1
    assert LIMITATION_INSUFFICIENT_EVIDENCE not in attempt.limitations


def test_complete_coverage_declared_walks_remaining_pages(
    capture_mode_logs,
):
    provider = _PagingProvider(
        [
            _teo_process_page(
                [_process("p1", "Item A", "2026-10-29T10:00:00Z")],
                total=2,
            ),
            _teo_process_page(
                [_process("p2", "Item B", "2026-10-28T09:00:00Z")],
                total=2,
            ),
        ]
    )
    attempt = _attempt(
        provider,
        goal={
            "goal_class": "read",
            "answer_requirements": {"complete_coverage": True},
        },
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert len(provider.calls) == 2
    assert LIMITATION_INSUFFICIENT_EVIDENCE not in attempt.limitations


def test_explicit_empty_page_never_walks(capture_mode_logs):
    """Authoritative empty (total=0) is a definitive answer — no
    further owner calls."""
    provider = _PagingProvider(
        [_teo_process_page([], total=0)]
    )
    attempt = _attempt(
        provider,
        goal={
            "goal_class": "read",
            "answer_requirements": {"ordering": "newest_first"},
        },
    )
    assert len(provider.calls) == 1
    assert "empty_result" in capture_mode_logs.text


def test_walk_stays_bounded_when_total_exceeds_page_budget(
    capture_mode_logs,
):
    """A collection larger than the page bound yields a partial walk —
    coverage stays unproven and the verdict is honest insufficiency,
    never an answered 'latest'."""
    from app.application.capability_provision.paginated_result_semantics import (
        DEFAULT_MAX_PAGES,
    )

    pages = [
        _teo_process_page(
            [_process(f"p{i}", f"P{i}", "2026-10-29T10:00:00Z")],
            total=1000,
        )
        for i in range(DEFAULT_MAX_PAGES + 2)
    ]
    provider = _PagingProvider(pages)
    attempt = _attempt(
        provider,
        goal={
            "goal_class": "read",
            "answer_requirements": {"ordering": "newest_first"},
        },
    )
    assert len(provider.calls) <= DEFAULT_MAX_PAGES
    assert LIMITATION_INSUFFICIENT_EVIDENCE in attempt.limitations


def test_page_failure_mid_walk_stays_insufficient(capture_mode_logs):
    provider = _PagingProvider(
        [
            _teo_process_page(
                [_process("p1", "A", "2026-10-29T10:00:00Z")],
                total=4,
            ),
            _teo_process_page(
                [_process("p2", "B", "2026-10-28T09:00:00Z")],
                total=4,
            ),
        ],
        fail_pages={1},
    )
    attempt = _attempt(
        provider,
        goal={
            "goal_class": "read",
            "answer_requirements": {"ordering": "newest_first"},
        },
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert LIMITATION_INSUFFICIENT_EVIDENCE in attempt.limitations


def test_ordering_without_page_cursor_anywhere_never_walks(
    capture_mode_logs,
):
    """No cursor in sent args AND none declared by the capability —
    the gap is honest coverage_unproven, not a fabricated walk."""
    provider = _NoCursorProvider(
        [
            _teo_process_page(
                [
                    _process("p2", "B", "2026-10-29T10:00:00Z"),
                    _process("p1", "A", "2026-10-28T09:00:00Z"),
                ],
                total=4,
            ),
        ]
    )
    attempt = _attempt(
        provider,
        goal={
            "goal_class": "read",
            "answer_requirements": {"ordering": "newest_first"},
        },
    )
    assert len(provider.calls) == 1
    assert LIMITATION_INSUFFICIENT_EVIDENCE in attempt.limitations
    assert "coverage_unproven" in capture_mode_logs.text


def test_ordering_complete_first_page_never_walks(capture_mode_logs):
    """A complete, ordered first page answers without extra calls."""
    provider = _PagingProvider(
        [
            _teo_process_page(
                [
                    _process("p2", "B", "2026-10-29T10:00:00Z"),
                    _process("p1", "A", "2026-10-28T09:00:00Z"),
                ],
                total=2,
            ),
        ]
    )
    attempt = _attempt(
        provider,
        goal={
            "goal_class": "read",
            "answer_requirements": {"ordering": "newest_first"},
        },
    )
    assert len(provider.calls) == 1
    assert LIMITATION_INSUFFICIENT_EVIDENCE not in attempt.limitations
    assert "decision=answered" in capture_mode_logs.text
