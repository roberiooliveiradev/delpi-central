"""C3 Task 14 — declared goal requirements reach the argument stage.

TASK: DELIA-C3-SEMANTIC-ARGUMENT-AND-ORDERING-REMEDIATION-01

Locks:
- A goal that declares ``answer_requirements`` (ordering / min_items /
  complete_coverage) projects them into the ``<schema>`` block the
  argument-proposal model sees — the model cannot formulate
  ordering-compatible arguments for a requirement it never sees.
- Requirement-free goals keep the prior block shape (no
  ``declared_requirements`` key) — baseline parity.
- The projection carries requirement VALUES verbatim (bounded typed
  vocabulary), never free text.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.infrastructure.config.cri_instruction_resource import (
    load_cri_instruction_clause,
)
from tests.conftest import load_test_orchestration_instructions
from tests.test_c3_goal_to_owner_execution import (
    _PagingProvider,
    _ProposalModel,
    _process,
    _proposal,
    _teo_process_page,
    TEST_MODEL_REF,
)


def _orchestrator(provider, proposal):
    clause = load_cri_instruction_clause(
        Path(__file__).resolve().parents[1]
        / "config"
        / "cri_instructions.delpi.json"
    )
    model = _ProposalModel(proposal)
    return (
        OperationalCapabilityOrchestrator(
            [provider],
            invoke_model=InvokeModel(model),
            model_ref=TEST_MODEL_REF,
            response_intelligence_enabled=True,
            cri_instruction_clause=clause.text,
            cri_instruction_version=clause.version,
            orchestration_instructions=(
                load_test_orchestration_instructions()
            ),
        ),
        model,
    )


def _schema_block_of(request) -> dict[str, Any]:
    """Extract the ``<schema>`` JSON block the arguments-stage model
    actually received (the block payload is serialized verbatim into
    ``input_text``)."""
    text = request.input_text
    start = text.index("<schema>") + len("<schema>")
    end = text.index("</schema>")
    return json.loads(text[start:end].strip())


def _arguments_requests(model) -> list:
    return [
        r
        for r in model.requests
        if r.task_purpose_id == ARGUMENTS_INSTRUCTION_ID
    ]


def _paging_provider() -> _PagingProvider:
    return _PagingProvider(
        [
            _teo_process_page(
                [_process("p1", "Proc A", "2026-10-29T10:00:00Z")],
                total=1,
            ),
        ]
    )


class TestDeclaredRequirementsReachArgumentStage:
    """The argument-proposal block must carry the goal's declared
    requirements so the model can align argument formulation with
    ordering/quantity semantics instead of inventing text filters."""

    def test_ordering_requirement_projected_into_arguments_block(self):
        provider = _paging_provider()
        orch, model = _orchestrator(
            provider,
            _proposal(
                {
                    "goal_class": "read",
                    "answer_requirements": {"ordering": "newest_first"},
                }
            ),
        )
        orch.attempt("qual o ultimo processo?")
        requests = _arguments_requests(model)
        assert requests, "arguments stage was not invoked"
        block = _schema_block_of(requests[0])
        declared = block.get("declared_requirements")
        assert declared == {"ordering": "newest_first"}, (
            f"declared ordering never reached the argument model: {block!r}"
        )

    def test_min_items_requirement_projected_into_arguments_block(self):
        provider = _paging_provider()
        orch, model = _orchestrator(
            provider,
            _proposal(
                {
                    "goal_class": "read",
                    "answer_requirements": {"min_items": 3},
                }
            ),
        )
        orch.attempt("traga tres registros")
        requests = _arguments_requests(model)
        assert requests
        block = _schema_block_of(requests[0])
        declared = block.get("declared_requirements")
        assert declared == {"min_items": 3}

    def test_requirement_free_goal_keeps_block_shape(self):
        provider = _paging_provider()
        orch, model = _orchestrator(
            provider, _proposal({"goal_class": "read"})
        )
        orch.attempt("liste os registros")
        requests = _arguments_requests(model)
        assert requests
        block = _schema_block_of(requests[0])
        assert "declared_requirements" not in block
