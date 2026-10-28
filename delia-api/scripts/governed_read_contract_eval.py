#!/usr/bin/env python3
"""DELIA-C3-GOVERNED-READ-RECOVERY-CONTRACT-REMEDIATION-01 — matched eval.

Paired B0 (doc-176 impl) × B1 (rework impl) comparison through the
REAL OpenAPI adapter path:

    scripted model proposals (stage-conditioned, identical for B0/B1)
      → real orchestrator + real governed instructions/CRI clause
      → real HttpOpenApiInvoker + OpenApiCapabilityProvider
      → fake owner HTTP layer (queued FakeResponse envelopes)

Same model port shape, same capability surface, same initial owner
rejection, same repair proposal — admission flake removed entirely
by controlled entry at the arguments/recovery stages, exactly what
the independent review required. Zero network, zero production
queries.

Run the SAME script against the B0 tree (git archive 2615d9d97b)
and the B1 tree; diff the printed JSON matrix.

  docker run --rm -v <delia-api>:/app -v <docs>:/docs \\
    -v <plugins>:/plugins -w /app <img> \\
    python scripts/governed_read_contract_eval.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter

sys.path.insert(0, "/app")

import logging

logging.getLogger("app").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

from app.application.capability_provision.orchestration import (  # noqa: E402
    ARGUMENTS_INSTRUCTION_ID,
    GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
)
from app.application.model_invocation.invoke_model import (  # noqa: E402
    InvokeModel,
)
from app.application.capability_provision.openapi_provider import (  # noqa: E402
    OpenApiCapabilityProvider,
)
from app.infrastructure.openapi.http_invoker import (  # noqa: E402
    HttpOpenApiInvoker,
)
from tests.conftest import (  # noqa: E402
    load_test_orchestration_instructions,
)
from tests.test_goal_evidence_relevance import (  # noqa: E402
    FakeProposalModel,
    TEST_MODEL_REF,
    _cri_clause,
    _select,
)
from tests.test_openapi_capability_provider import (  # noqa: E402
    FakeResponse,
    _source,
)

PRODUCT_TYPE_MSG = (
    "product_type inválido: use códigos de 2 caracteres "
    "separados por vírgula (ex.: MP,PI,PA)."
)
RECORDS = {
    "success": True,
    "message": "ok",
    "data": {
        "items": [
            {"product_code": "10080092", "name": "TERM. BALA 0,50-2,27MM2"},
            {"product_code": "10081004", "name": "TERM. BALA 1,00-2,50MM2"},
        ],
        "page": 1,
        "page_size": 50,
        "total": 2,
        "total_pages": 1,
    },
    "error": None,
}


def _env400(**kw):
    body = {
        "success": False,
        "message": kw.pop("message", PRODUCT_TYPE_MSG),
        "data": None,
        "error": kw.pop("error", None),
    }
    return FakeResponse(kw.pop("status", 400), body)


def _wire(responses):
    """Provider wired to the real adapter; owner replies come from
    a queued envelope list. Every wire call is recorded."""
    queue = list(responses)
    calls: list[str] = []

    def http_get(url, headers=None, timeout=None, stream=None):
        calls.append(url.split("?")[0].rsplit("/", 1)[-1] + "?" + (
            url.split("?", 1)[1] if "?" in url else ""
        ))
        if queue:
            return queue.pop(0)
        return FakeResponse(500, {"success": False, "message": "eof"})

    invoker = HttpOpenApiInvoker(
        "http://h",
        source_id="delpi",
        subject_bearer_getter=lambda: "t",
        http_get=http_get,
    )
    return OpenApiCapabilityProvider([_source(invoker)]), calls


def _run(responses, repair_args=None):
    """Identical stage-conditioned input for every run:
    select delpi.get_product -> first args -> (recovery) repair args
    -> relevance corresponds. Same scripted proposals for B0/B1."""
    provider, calls = _wire(responses)
    proposal = [
        _select(
            "openapi:delpi",
            "delpi.get_product",
            args={
                "arguments": {
                    "product_id": "x",
                    "detail": "terminal bala",
                }
            },
            relevance=None,
        ),
        {
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": (
                    repair_args or {"product_id": "x", "detail": "MP"}
                )
            }
        },
        {
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": (
                    repair_args or {"product_id": "x", "detail": "MP"}
                )
            }
        },
        {
            GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID: {
                "correspondence": "corresponds",
            }
        },
    ]
    clause = _cri_clause()
    model = FakeProposalModel(proposal)
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
        orchestration_instructions=load_test_orchestration_instructions(),
    )
    error = None
    attempt = None
    try:
        attempt = orch.attempt("traga exemplos de terminal bala")
    except Exception as exc:
        error = getattr(exc, "code", type(exc).__name__)
    coverage = None
    arg_requests = [
        r
        for r in model.requests
        if r.task_purpose_id == ARGUMENTS_INSTRUCTION_ID
    ]
    if len(arg_requests) >= 2 and "<schema>" in (
        arg_requests[-1].input_text or ""
    ):
        block = json.loads(
            arg_requests[-1].input_text.split("<schema>", 1)[1]
            .split("</schema>", 1)[0]
        )
        fb = block.get("relevance_feedback")
        fb = json.loads(fb) if isinstance(fb, str) else fb
        if isinstance(fb, dict):
            coverage = fb.get("coverage")
    return {
        "status": str(getattr(attempt, "status", None)),
        "error": error,
        "wire_calls": len(calls),
        "coverage_feedback": coverage,
        "model_calls": dict(
            Counter(r.task_purpose_id.split(".")[-1] for r in model.requests)
        ),
    }


def main() -> int:
    out: dict = {}

    declared = {"code": "VALIDATION_ERROR", "recoverable": True}
    undeclared = None
    scenarios = {
        # Blocking review case: envelope without declaration.
        "undeclared_400": [
            _env400(error=undeclared),
            FakeResponse(200, RECORDS),
        ],
        # Explicit owner declaration -> recoverable on both.
        "declared_recoverable_400": [
            _env400(error=dict(declared)),
            FakeResponse(200, RECORDS),
        ],
        # Owner negation -> terminal on both.
        "declared_recoverable_false": [
            _env400(error={"code": "BUSINESS", "recoverable": False}),
        ],
        # Typed non-validation code, no flag.
        "untyped_code_400": [
            _env400(error={"code": "BUSINESS_RULE"}),
            FakeResponse(200, RECORDS),
        ],
        # Typed validation code on 422.
        "validation_code_422": [
            _env400(status=422, error=dict(declared)),
            FakeResponse(200, RECORDS),
        ],
        # Bare 422 without contract.
        "bare_422": [
            _env400(status=422, error=undeclared),
            FakeResponse(200, RECORDS),
        ],
        # AuthZ — terminal, single wire call, both.
        "forbidden_403": [FakeResponse(403, {"success": False})],
        # Transient — existing behavior, both.
        "server_500": [FakeResponse(500, {"success": False})],
        # Persistent declared rejection: bounded repair loop, both.
        "repeated_declared_rejection": [
            _env400(error=dict(declared)),
            _env400(error=dict(declared)),
            _env400(error=dict(declared)),
        ],
    }
    for name, responses in scenarios.items():
        out[name] = _run(responses)

    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
