#!/usr/bin/env python3
"""DELIA-C3-GOVERNED-READ-RECOVERY-IMPLEMENTATION-01 — local E2E eval.

Model-in-loop governed recovery validation, zero production queries:

    real local model (DELIA_LLM_* → Ollama baseline)
      → real orchestrator + real governed instructions/CRI clause
      → fake owner wire (in-process FakeProvider — no owner calls)

The fake owner reproduces ONLY the observable wire contract of the
Domain API: HTTP-400 recoverable argument rejection with the shared
envelope message (owner_argument_rejected + sanitized hint),
authorization denial, and authoritative pagination metadata. No
Domain API, Keycloak, network owner or production surface is
touched — the LLM and the deterministic code under test are real.

Scenarios:
  S1 direct_success            valid args → grounded records
  S2 recoverable_reformulation owner 400 → hint → reformulate → ok
  S3 coverage_pagination       page1 irrelevant + total/has_more →
                               semantic refine/paginate → ok
  S4 unauthorized_403          authz denial → terminal, 1 wire call
  S5 repeated_rejection        owner always rejects → bounded stop,
                               identical args never re-executed

Run inside the delia eval image on the dev network:

  docker run --rm --network <dev-net> \\
    -e DELIA_LLM_BASE_URL=http://delpi-ollama:11434/v1 \\
    -e DELIA_LLM_MODEL=<baseline> -e DELIA_LLM_API_KEY=eval \\
    -v <delia-api>:/app -w /app <img> \\
    python scripts/governed_read_recovery_eval.py

Never prints secrets; output is sanitized JSON + a PASS/FAIL line.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter

sys.path.insert(0, "/app")

import logging

logging.getLogger("app").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

from app.application.capability_provision.contracts import (  # noqa: E402
    CapabilityProviderError,
)
from app.application.capability_provision.orchestration import (  # noqa: E402
    OperationalCapabilityOrchestrator,
)
from app.application.model_invocation.invoke_model import (  # noqa: E402
    InvokeModel,
)
from app.infrastructure.config.settings import Settings  # noqa: E402
from app.infrastructure.model_invocation.openai_compatible_adapter import (  # noqa: E402
    OpenAICompatibleModelInvocationAdapter,
)
from tests.conftest import (  # noqa: E402
    load_test_orchestration_instructions,
)
from tests.test_goal_evidence_relevance import (  # noqa: E402
    FakeProvider,
    TEST_MODEL_REF,
    _cap,
    _cri_clause,
    _group,
    _outcome,
)


_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "product_type": {"type": "string"},
        "page": {"type": "integer", "minimum": 1},
        "page_size": {"type": "integer", "minimum": 1},
    },
}


def _search_cap():
    # Mirrors the real search_products surface shape: product_type
    # is a plain string (the owner validates the 2-char code rule).
    return _cap("alpha", "mcp", "search_items", schema=_SEARCH_SCHEMA)


def _arg_rejection(hint: str) -> CapabilityProviderError:
    # The wire code the OpenAPI adapter emits for a recoverable
    # owner argument rejection — literal, so this script also runs
    # unmodified against the pre-implementation baseline.
    return CapabilityProviderError(
        "owner_argument_rejected", "status=400", owner_hint=hint
    )

OWNER_HINT = (
    "product_type inválido: use códigos de 2 caracteres "
    "separados por vírgula (ex.: MP,PI,PA)."
)


class _GuardedAdapter:
    """Real adapter + sanitized per-purpose metrics."""

    def __init__(self, adapter) -> None:
        self._adapter = adapter
        self.counts: Counter = Counter()
        self.calls: list[dict] = []

    def __getattr__(self, name):
        return getattr(self._adapter, name)

    def invoke(self, request):
        self.counts[request.task_purpose_id] += 1
        started = time.monotonic()
        try:
            payload = self._adapter.invoke(request)
        except Exception as exc:
            self.calls.append(
                {
                    "purpose": request.task_purpose_id,
                    "ms": int((time.monotonic() - started) * 1000),
                    "error": getattr(exc, "code", type(exc).__name__),
                }
            )
            raise
        usage = getattr(payload, "usage", None)
        self.calls.append(
            {
                "purpose": request.task_purpose_id,
                "ms": int((time.monotonic() - started) * 1000),
                "in_units": getattr(usage, "input_units", None),
                "out_units": getattr(usage, "output_units", None),
                "structured": dict(
                    getattr(payload, "structured_output", {}) or {}
                ),
            }
        )
        return payload


class _OwnerWire:
    """Fake owner reproducing the Domain API wire contract.

    ``reject_rule(args) -> hint|None`` decides the recoverable
    400 rejection (owner-side validation); ``answer(args, n)``
    produces the paged outcome. Only observable contract behavior
    is simulated — no DÉLIA-side rule lives here.
    """

    def __init__(
        self,
        groups,
        *,
        reject_rule=None,
        answer=None,
        fail=None,
    ) -> None:
        self._provider = FakeProvider("mcp", groups, outcomes={})
        self.calls: list[dict] = []
        self._reject_rule = reject_rule
        self._answer = answer
        self._fail = fail
        self._provider.invoke = self._invoke  # type: ignore[method-assign]

    def __getattr__(self, name):
        return getattr(self._provider, name)

    def _invoke(self, capability, arguments, *, correlation_id,
                timeout_seconds=None):
        args = dict(arguments)
        self.calls.append(
            {"capability": capability.remote_name, "args": args}
        )
        if self._fail is not None:
            raise self._fail
        if self._reject_rule is not None:
            hint = self._reject_rule(args)
            if hint is not None:
                raise _arg_rejection(hint)
        return self._answer(args, len(self.calls))


def _product_type_rule(args: dict) -> str | None:
    """Owner-side contract: product_type must be 2-char codes."""
    value = args.get("product_type")
    if value is None:
        return None
    codes = str(value).split(",")
    if all(len(c.strip()) == 2 for c in codes):
        return None
    return OWNER_HINT


def _compose(provider, *, enabled=True):
    settings = Settings()
    if settings.llm_egress_blocked_reason:
        raise SystemExit(
            f"refused: {settings.llm_egress_blocked_reason}"
        )
    guarded = _GuardedAdapter(
        OpenAICompatibleModelInvocationAdapter(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
            default_max_output_units=settings.llm_max_output_tokens,
        )
    )
    clause = _cri_clause() if enabled else None
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(guarded),
        model_ref=TEST_MODEL_REF,
        response_intelligence_enabled=enabled,
        cri_instruction_clause=(
            clause.text if clause is not None else None
        ),
        cri_instruction_version=(
            clause.version if clause is not None else None
        ),
        orchestration_instructions=(
            load_test_orchestration_instructions()
        ),
    )
    return orch, guarded


def _record(question, orch, guarded, provider) -> dict:
    started = time.monotonic()
    error = None
    attempt = None
    try:
        attempt = orch.attempt(question)
    except Exception as exc:
        error = getattr(exc, "code", type(exc).__name__)
    return {
        "question": question,
        "status": str(getattr(attempt, "status", None)),
        "limitations": [
            str(x) for x in (getattr(attempt, "limitations", ()) or ())
        ],
        "error": error,
        "elapsed_s": round(time.monotonic() - started, 2),
        "owner_calls": list(provider.calls),
        "model_calls": dict(guarded.counts),
        "model_call_detail": [
            {
                k: v
                for k, v in c.items()
                if k in ("purpose", "ms", "in_units", "out_units", "error")
            }
            for c in guarded.calls
        ],
        "in_units": sum(c.get("in_units") or 0 for c in guarded.calls),
        "out_units": sum(
            c.get("out_units") or 0 for c in guarded.calls
        ),
    }


def main() -> int:
    groups = [
        _group("mcp", "alpha", [_search_cap(), _cap("alpha", "mcp", "read_items")])
    ]
    out: dict = {"model": os.environ.get("DELIA_LLM_MODEL")}

    relevant = _outcome(
        "ok",
        structured={
            "items": [
                {"name": "TERMINAL BALA 0,50-2,27MM2 ESTANHADO"},
                {"name": "TERMINAL BALA 1,00-2,50MM2 NIQUELADO"},
            ]
        },
    )

    def _run(name, question, provider_factory, reach=None):
        """Fresh governed turn per try (CPU 3B admission is
        non-deterministic); keep the first run that reaches the owner
        wire or exhaust the bounded tries — never best-of-N on the
        business outcome, only on reaching the evaluated path."""
        last = None
        for try_index in range(4):
            provider = provider_factory()
            orch, guarded = _compose(provider)
            last = _record(question, orch, guarded, provider)
            last["try_index"] = try_index
            if reach is None or reach(last):
                break
        out[name] = last

    def _reached_wire(rec):
        return len(rec["owner_calls"]) >= 1

    # S1 — direct success control.
    _run(
        "S1_direct_success",
        "use a capability search_items para trazer dois exemplos de terminal bala",
        lambda: _OwnerWire(groups, answer=lambda a, n: relevant),
        reach=_reached_wire,
    )

    # S2 — recoverable owner 400 → hint → reformulation.
    _run(
        "S2_recoverable_reformulation",
        "use a capability search_items para trazer dois exemplos de terminal bala",
        lambda: _OwnerWire(
            groups,
            reject_rule=_product_type_rule,
            answer=lambda a, n: relevant,
        ),
        reach=_reached_wire,
    )

    # S3 — coverage metadata → semantic refine/paginate.
    def _paged(args, n):
        if args.get("page", 1) == 1 and "bala" not in str(
            args.get("query", "")
        ):
            return _outcome(
                "ok",
                structured={
                    "items": [
                        {"name": "BALANCA 1"},
                        {"name": "BALANCA 2"},
                    ],
                    "page": 1,
                    "page_size": 2,
                    "total": 40,
                    "has_more": True,
                },
            )
        return relevant

    _run(
        "S3_coverage_pagination",
        "use a capability search_items para trazer dois exemplos de terminal bala",
        lambda: _OwnerWire(groups, answer=_paged),
        reach=_reached_wire,
    )

    # S4 — authorization denial is terminal: one wire call only.
    _run(
        "S4_unauthorized_403",
        "use a capability search_items para trazer dois exemplos de terminal bala",
        lambda: _OwnerWire(
            groups,
            fail=CapabilityProviderError(
                "mcp_authorization_denied", "status=403"
            ),
        ),
        reach=_reached_wire,
    )

    # S5 — persistent rejection: bounded stop, no verbatim re-exec.
    _run(
        "S5_repeated_rejection",
        "use a capability search_items para trazer dois exemplos de terminal bala",
        lambda: _OwnerWire(
            groups,
            reject_rule=lambda a: OWNER_HINT,
            answer=lambda a, n: relevant,
        ),
        reach=_reached_wire,
    )

    checks = {
        "S1_success": "SUCCESS" in out["S1_direct_success"]["status"],
        "S4_single_wire_call": len(
            out["S4_unauthorized_403"]["owner_calls"]
        )
        <= 1,
        "S4_not_success": "SUCCESS"
        not in out["S4_unauthorized_403"]["status"],
        "S5_bounded": len(out["S5_repeated_rejection"]["owner_calls"])
        <= 3,
        "S5_no_verbatim_reexec": len(
            {
                json.dumps(c["args"], sort_keys=True)
                for c in out["S5_repeated_rejection"]["owner_calls"]
            }
        )
        == len(out["S5_repeated_rejection"]["owner_calls"]),
    }
    out["checks"] = checks
    out["verdict"] = (
        "PASS" if all(checks.values()) else "FAIL"
    )
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
