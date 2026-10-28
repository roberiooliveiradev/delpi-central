#!/usr/bin/env python3
"""DELIA-C3-DAVI-EXCLUSIVE-DELPI-DOMAIN-ACCESS-REFACTOR-01 — paired eval.

Compares the SAME logical scenarios through both provider families:

  B0 — direct path: OpenApiCapabilityProvider + real HttpOpenApiInvoker
       against a queued fake owner HTTP layer.
  B1 — DAVI path:   McpCapabilityProvider + real SpecialistInterop
       against a scripted SpecialistInteropPort (fake MCP wire:
       discover_delpi_information + execute_delpi_information,
       owner discover->candidate->execute flow preserved).

Identical stage-conditioned model proposals per family; identical
initial owner rejection; identical repair proposal. Zero network,
zero production queries, deterministic — no uncontrolled admission.

  docker run --rm -v <delia-api>:/app -v <docs>:/docs \\
    -v <plugins>:/plugins -w /app <img> \\
    python scripts/governed_davi_migration_eval.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter

sys.path.insert(0, "/app")

import logging

logging.getLogger("app").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

from app.application.capability_provision.mcp_provider import (  # noqa: E402
    McpCapabilityProvider,
)
from app.application.capability_provision.openapi_provider import (  # noqa: E402
    OpenApiCapabilityProvider,
)
from app.application.capability_provision.orchestration import (  # noqa: E402
    ARGUMENTS_INSTRUCTION_ID,
    GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
)
from app.application.model_invocation.invoke_model import (  # noqa: E402
    InvokeModel,
)
from app.application.specialist_interop.contracts import (  # noqa: E402
    RemoteToolDescriptor,
    RemoteToolOutcome,
)
from app.application.specialist_interop.errors import (  # noqa: E402
    MCP_AUTHORIZATION_DENIED,
    MCP_UNAVAILABLE,
    SpecialistInteropError,
)
from app.application.specialist_interop.specialist_interop import (  # noqa: E402
    SpecialistInterop,
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
RECORDS_HTTP = {
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
RECORDS_MCP = {
    "action_id": "search_products",
    "status": "ok",
    "entity": "product",
    "items": [
        {"product_code": "10080092", "description": "TERM. BALA 0,50-2,27MM2"},
        {"product_code": "10081004", "description": "TERM. BALA 1,00-2,50MM2"},
    ],
    "total": 2,
}
DISCOVERY_OK = RemoteToolOutcome(
    content_text="Discovery completed.",
    structured={
        "candidates": [
            {
                "candidate_token": "tok-1",
                "action_id": "search_products",
                "description": "Buscar produtos DELPI",
            }
        ]
    },
)
EXECUTE_OK = RemoteToolOutcome(
    content_text="Execution completed.",
    structured=RECORDS_MCP,
)


# ---------------------------------------------------------------------------
# B0 — direct OpenAPI path (real adapter, queued envelopes)
# ---------------------------------------------------------------------------


def _env400(**kw):
    body = {
        "success": False,
        "message": kw.pop("message", PRODUCT_TYPE_MSG),
        "data": None,
        "error": kw.pop("error", None),
    }
    return FakeResponse(kw.pop("status", 400), body)


def _wire_b0(responses):
    queue = list(responses)
    calls: list[str] = []

    def http_get(url, headers=None, timeout=None, stream=None):
        calls.append("wire")
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


# ---------------------------------------------------------------------------
# B1 — DAVI MCP path (real interop + provider, scripted port)
# ---------------------------------------------------------------------------


class FakeDaviPort:
    """Scripted SpecialistInteropPort — fake MCP wire for DAVI."""

    adapter_kind = "MCP_FAKE"

    def __init__(self, scripted):
        # scripted: {remote_name: [RemoteToolOutcome|Exception, ...]}
        self._scripted = {k: list(v) for k, v in scripted.items()}
        self.calls: list[str] = []

    def list_remote_tools(self, specialist, *, timeout_seconds):
        return (
            RemoteToolDescriptor(
                remote_name="discover_delpi_information",
                operation_class="DISCOVERY",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer"},
                    },
                    "required": ["query"],
                },
            ),
            RemoteToolDescriptor(
                remote_name="execute_delpi_information",
                operation_class="READ",
                input_schema={
                    "type": "object",
                    "properties": {
                        "candidate_token": {"type": "string"},
                        "arguments": {"type": "object"},
                    },
                    "required": ["candidate_token"],
                },
            ),
        )

    def call_remote_tool(
        self, specialist, remote_name, arguments, *, correlation_id,
        timeout_seconds,
    ):
        self.calls.append(remote_name)
        queue = self._scripted.get(remote_name) or []
        if queue:
            item = queue.pop(0)
            if isinstance(item, Exception):
                raise item
            return item
        return RemoteToolOutcome(
            content_text="unexpected call", is_error=True
        )


def _wire_b1(scripted):
    port = FakeDaviPort(scripted)
    provider = McpCapabilityProvider(
        SpecialistInterop(port), ["davi"]
    )
    return provider, port.calls


def _davi_error(code, message=PRODUCT_TYPE_MSG, recoverable=False):
    return RemoteToolOutcome(
        content_text="Invalid execute parameters.",
        structured={
            "code": code,
            "recoverable": recoverable,
            "message": message,
        },
        is_error=True,
    )


def _argument_validation_error(recoverable=True):
    return _davi_error("ARGUMENT_VALIDATION", recoverable=recoverable)


# ---------------------------------------------------------------------------
# Shared attempt driver — identical proposals per family
# ---------------------------------------------------------------------------


def _attempt(provider, proposal):
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
    return attempt, error, model


def _proposal_b0(repair_args):
    first_args = {"product_id": "x", "detail": "terminal bala"}
    return [
        _select("openapi:delpi", "delpi.get_product", args={
            "arguments": first_args,
        }, relevance=None),
        {ARGUMENTS_INSTRUCTION_ID: {"arguments": repair_args}},
        {ARGUMENTS_INSTRUCTION_ID: {"arguments": repair_args}},
        {GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID: {
            "correspondence": "corresponds"}},
    ]


def _proposal_b1(repair_args):
    # execute schema: candidate_token (orchestrated) + arguments (model)
    inner = {"product_type": "terminal bala"}
    return [
        _select("mcp:davi", "execute_delpi_information", args={
            "arguments": {"arguments": inner},
        }, relevance=None),
        {ARGUMENTS_INSTRUCTION_ID: {
            "arguments": {"arguments": repair_args}}},
        {ARGUMENTS_INSTRUCTION_ID: {
            "arguments": {"arguments": repair_args}}},
        {GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID: {
            "correspondence": "corresponds"}},
    ]


def _run_b0(responses, repair_args):
    provider, calls = _wire_b0(responses)
    attempt, error, model = _attempt(
        provider, _proposal_b0(repair_args)
    )
    return {
        "status": str(getattr(attempt, "status", None)),
        "error": error,
        "wire_calls": len(calls),
        "model_calls": dict(Counter(
            r.task_purpose_id.split(".")[-1] for r in model.requests
        )),
    }


def _run_b1(scripted, repair_args):
    provider, calls = _wire_b1(scripted)
    attempt, error, model = _attempt(
        provider, _proposal_b1(repair_args)
    )
    return {
        "status": str(getattr(attempt, "status", None)),
        "error": error,
        "wire_calls": len(calls),
        "wire_sequence": list(calls),
        "model_calls": dict(Counter(
            r.task_purpose_id.split(".")[-1] for r in model.requests
        )),
    }


def _mcp_error(text="remote failure", structured=None):
    return RemoteToolOutcome(
        content_text=text, structured=structured, is_error=True
    )


def main() -> int:
    out: dict = {}
    repair_b0 = {"product_id": "x", "detail": "MP"}
    repair_b1 = {"detail": "MP"}
    declared = {"code": "VALIDATION_ERROR", "recoverable": True}
    undeclared = None

    # 1 — declared-recoverable argument rejection -> repair -> success
    out["declared_recoverable_rejection"] = {
        "b0_direct": _run_b0(
            [_env400(error=dict(declared)), FakeResponse(200, RECORDS_HTTP)],
            repair_b0,
        ),
        "b1_davi": _run_b1(
            {
                "discover_delpi_information": [DISCOVERY_OK, DISCOVERY_OK],
                "execute_delpi_information": [
                    _argument_validation_error(),
                    EXECUTE_OK,
                ],
            },
            repair_b1,
        ),
    }

    # 2 — undeclared/untyped rejection -> terminal, no repair
    out["undeclared_rejection"] = {
        "b0_direct": _run_b0(
            [_env400(error=undeclared), FakeResponse(200, RECORDS_HTTP)],
            repair_b0,
        ),
        "b1_davi": _run_b1(
            {
                "discover_delpi_information": [DISCOVERY_OK],
                "execute_delpi_information": [
                    _mcp_error(
                        structured={
                            "code": "BUSINESS_RULE",
                            "message": "not repairable",
                        }
                    )
                ],
            },
            repair_b1,
        ),
    }

    # 3 — explicit non-recoverable -> terminal both
    out["explicit_non_recoverable"] = {
        "b0_direct": _run_b0(
            [_env400(error={"code": "VALIDATION_ERROR",
                            "recoverable": False})],
            repair_b0,
        ),
        "b1_davi": _run_b1(
            {
                "discover_delpi_information": [DISCOVERY_OK],
                "execute_delpi_information": [
                    _argument_validation_error(recoverable=False)
                ],
            },
            repair_b1,
        ),
    }

    # 4 — AuthZ denied -> terminal both
    out["forbidden"] = {
        "b0_direct": _run_b0(
            [FakeResponse(403, {"success": False})], repair_b0
        ),
        "b1_davi": _run_b1(
            {
                "discover_delpi_information": [DISCOVERY_OK],
                "execute_delpi_information": [
                    SpecialistInteropError(
                        MCP_AUTHORIZATION_DENIED, "forbidden"
                    )
                ],
            },
            repair_b1,
        ),
    }

    # 5 — transient/unavailable -> terminal both
    out["transient_unavailable"] = {
        "b0_direct": _run_b0(
            [FakeResponse(500, {"success": False})], repair_b0
        ),
        "b1_davi": _run_b1(
            {
                "discover_delpi_information": [DISCOVERY_OK],
                "execute_delpi_information": [
                    SpecialistInteropError(
                        MCP_UNAVAILABLE, "specialist unavailable"
                    )
                ],
            },
            repair_b1,
        ),
    }

    # 6 — persistent declared rejection -> bounded stop both
    out["repeated_declared_rejection"] = {
        "b0_direct": _run_b0(
            [
                _env400(error=dict(declared)),
                _env400(error=dict(declared)),
                _env400(error=dict(declared)),
            ],
            repair_b0,
        ),
        "b1_davi": _run_b1(
            {
                "discover_delpi_information": [
                    DISCOVERY_OK, DISCOVERY_OK, DISCOVERY_OK,
                ],
                "execute_delpi_information": [
                    _argument_validation_error(),
                    _argument_validation_error(),
                    _argument_validation_error(),
                ],
            },
            repair_b1,
        ),
    }

    # 7 — hardened contract (DELIA-C3-DAVI-EXCLUSIVE-COMPLETION-01):
    # the legacy ambiguous VALIDATION_ERROR code must fail closed —
    # only ARGUMENT_VALIDATION + recoverable:true opens repair.
    out["legacy_generic_code_terminal"] = {
        "b1_davi": _run_b1(
            {
                "discover_delpi_information": [DISCOVERY_OK],
                "execute_delpi_information": [
                    _mcp_error(
                        structured={
                            "code": "VALIDATION_ERROR",
                            "message": PRODUCT_TYPE_MSG,
                        }
                    )
                ],
            },
            repair_b1,
        ),
    }

    # 8 — typed authorization tool-result -> AUTHZ_DENIED, terminal
    out["typed_authorization_denied"] = {
        "b1_davi": _run_b1(
            {
                "discover_delpi_information": [DISCOVERY_OK],
                "execute_delpi_information": [
                    _davi_error("AUTHORIZATION_DENIED", "Forbidden")
                ],
            },
            repair_b1,
        ),
    }

    # 9 — capability not allowed -> terminal, never repairable
    out["capability_not_allowed"] = {
        "b1_davi": _run_b1(
            {
                "discover_delpi_information": [DISCOVERY_OK],
                "execute_delpi_information": [
                    _davi_error(
                        "CAPABILITY_NOT_ALLOWED",
                        "Action is not DAVI-eligible",
                    )
                ],
            },
            repair_b1,
        ),
    }

    # 10 — owner execution failure -> terminal, not an argument error
    out["owner_execution_error"] = {
        "b1_davi": _run_b1(
            {
                "discover_delpi_information": [DISCOVERY_OK],
                "execute_delpi_information": [
                    _davi_error(
                        "OWNER_EXECUTION_ERROR",
                        "Catalog action execution failed",
                    )
                ],
            },
            repair_b1,
        ),
    }

    # Capability coverage matrix (owner contract state at HEAD):
    # api-delpi/app/content/davi_external_read_allowlist.json and
    # delia-api/config/openapi_declarations.delpi.json. The two
    # blocked capabilities have no approved DAVI substitute —
    # OWNER_DECISION_REQUIRED, direct binding preserved.
    out["capability_coverage"] = {
        "search_products": {
            "davi_coverage": "MIGRATED",
            "input_parity": (
                "DIRECT had product_type|sort|direction|"
                "customer_reference; DAVI allows code|description|"
                "group_code|page|page_size — OWNER_DECISION_REQUIRED"
            ),
            "output_projection": "product_code|description|group_category",
        },
        "get_product_stock": {
            "davi_coverage": "MIGRATED",
            "input_parity": "COMPATIBLE",
            "output_projection": "bounded owner projection",
        },
        "get_product_summary": {
            "davi_coverage": "OWNER_DECISION_REQUIRED",
            "owner_disposition": "explicitlyNotApproved/DEFER",
            "direct_binding": "PRESERVED",
        },
        "search_customers": {
            "davi_coverage": "OWNER_DECISION_REQUIRED",
            "owner_disposition": "no coverage decision in allowlist",
            "direct_binding": "PRESERVED",
        },
    }

    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
