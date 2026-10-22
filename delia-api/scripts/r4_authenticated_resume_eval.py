"""DELIA-C3-GOVERNED-RESUME-R4-AUTHENTICATED-MCP-VERIFICATION-01.

Authenticated post-resume verification on the REAL chain:

    user question → Ollama (local only) → governed orchestration →
    delegated credential exchange (RFC 8693) → real MCP READ.

The subject bearer is a REAL dev-portal user token obtained via the
password grant on the ``delpi-central`` client — the same seam the
NDJSON worker binds (``bind_subject_bearer``). No token, password or
payload is ever printed; output is sanitized JSON.

Environment contract (all required, fail-closed):
  R4_DEV_USERNAME / R4_DEV_PASSWORD   dev portal test user
  R4_KC_TOKEN_URL                     password-grant endpoint
  R4_KC_ADMIN / R4_KC_ADMIN_PASSWORD  ONLY for the revocation scenario
  R4_KC_ADMIN_TOKEN_URL               master-realm admin grant endpoint
  DELIA_LLM_*                         Ollama-only (policy-gated)
  DELIA_MCP_* / DELIA_EXCHANGE_*      real dev specialists + exchange

Scenarios:
  S1 read_without_timeout        real chain end-to-end, no injection
  S2 read_after_llm_retry        one injected model_timeout at
                                 select_capability → CONTINUING →
                                 attempt 2 reaches real READ
  S3 timeout_after_read_outcome  injected timeout AFTER the READ
                                 outcome completes (grounded_synthesis)
                                 → attempt 2 replays the checkpoint;
                                 MCP invoke count must stay 1
  S4 revocation_before_resume    injected timeout at admission +
                                 user disabled between attempts →
                                 attempt 2 fails closed on the live
                                 exchange wire; user re-enabled
  S5 invalid_subject_bearer      forged bearer → exchange fails
                                 closed → honest terminal
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter

sys.path.insert(0, "/app")

from app.application.interaction.contracts import InteractiveTurnRequest
from app.application.model_invocation.errors import (
    TIMEOUT,
    ModelInvocationError,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.composition.root_composer import (
    DEFAULT_INTERACTION_MODEL_REF,
    _compose_turn_handler,
    _wire_delegated_credential_provider,
)
from app.domain.evidence.model import ModelRef
from app.infrastructure.auth.subject_bearer import (
    bind_subject_bearer,
    unbind_subject_bearer,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.interoperability.config import (
    specialist_connections_from_settings,
)
from app.infrastructure.interoperability.mcp.adapter import (
    McpSpecialistAdapter,
)
from app.infrastructure.model_invocation.openai_compatible_adapter import (
    OpenAICompatibleModelInvocationAdapter,
)

QUESTIONS = {
    "mcp_davi": "o mcp davi",
    "last_process": "qual o ultimo processo cadastrado?",
    # Semantically specific question that routes to a parameterless
    # READ (vista.list_playlists) — small local models need a concrete
    # owner+capability hint to reach invocation without clarification.
    "vista_playlists": "use o mcp vista para listar as playlists",
}


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def _post_form(url: str, fields: dict, timeout: float = 15.0) -> dict:
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _subject_token() -> str:
    """Password grant on the dev portal client — real user identity."""
    token = _post_form(
        _env("R4_KC_TOKEN_URL"),
        {
            "grant_type": "password",
            "client_id": _env("R4_KC_CLIENT_ID") or "delpi-central",
            "username": _env("R4_DEV_USERNAME"),
            "password": _env("R4_DEV_PASSWORD"),
            "scope": "openid",
        },
    ).get("access_token")
    if not token:
        raise SystemExit("subject token grant failed (presence-only)")
    return token


def _admin_token() -> str:
    token = _post_form(
        _env("R4_KC_ADMIN_TOKEN_URL"),
        {
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": _env("R4_KC_ADMIN"),
            "password": _env("R4_KC_ADMIN_PASSWORD"),
        },
    ).get("access_token")
    if not token:
        raise SystemExit("admin token grant failed (presence-only)")
    return token


def _set_user_enabled(enabled: bool) -> None:
    """Toggle the dev test user — revocation seam. Re-enabling is the
    caller's finally-duty; nothing but the boolean is recorded."""
    base = _env("R4_KC_BASE_URL") or "http://keycloak:8080/auth"
    realm = _env("R4_KC_REALM") or "delpi"
    admin = _admin_token()
    headers = {"Authorization": f"Bearer {admin}"}
    q = urllib.parse.urlencode({"username": _env("R4_DEV_USERNAME")})
    req = urllib.request.Request(
        f"{base}/admin/realms/{realm}/users?{q}", headers=headers
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        users = json.loads(resp.read().decode())
    if not users:
        raise SystemExit("dev user not found for revocation scenario")
    uid = users[0]["id"]
    req = urllib.request.Request(
        f"{base}/admin/realms/{realm}/users/{uid}",
        data=json.dumps({"enabled": enabled}).encode(),
        headers={**headers, "Content-Type": "application/json"},
        method="PUT",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        resp.read()


class _GuardedAdapter:
    """Real adapter + deterministic one-shot timeout injection at a
    chosen purpose — identical semantic to a real provider timeout
    (``ModelInvocationError(TIMEOUT)`` → ``_StageDeadlineExceeded``)."""

    def __init__(self, adapter, inject_purpose: str | None = None,
                 on_inject=None) -> None:
        self._adapter = adapter
        self.counts: Counter = Counter()
        self.calls: list[dict] = []
        self._inject_purpose = inject_purpose
        self._injected = False
        self._on_inject = on_inject

    def __getattr__(self, name):
        return getattr(self._adapter, name)

    def invoke(self, request):
        self.counts[request.task_purpose_id] += 1
        started = time.monotonic()
        if (
            self._inject_purpose
            and request.task_purpose_id == self._inject_purpose
            and not self._injected
        ):
            self._injected = True
            if self._on_inject is not None:
                self._on_inject()
            self.calls.append(
                {
                    "purpose": request.task_purpose_id,
                    "ms": int((time.monotonic() - started) * 1000),
                    "error": "injected_timeout",
                }
            )
            raise ModelInvocationError(TIMEOUT, "injected stage timeout")
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
                "finish": str(getattr(payload, "finish_status", "")),
                "in_units": getattr(usage, "input_units", None),
                "out_units": getattr(usage, "output_units", None),
            }
        )
        return payload


class _CountingMcpAdapter:
    """Delegates to the real McpSpecialistAdapter; counts the wire."""

    def __init__(self, adapter) -> None:
        self._adapter = adapter
        self.list_calls = 0
        self.invoke_calls = 0
        self.invoke_targets: list[str] = []

    def __getattr__(self, name):
        return getattr(self._adapter, name)

    def list_remote_tools(self, *args, **kwargs):
        self.list_calls += 1
        return self._adapter.list_remote_tools(*args, **kwargs)

    def call_remote_tool(self, specialist, remote_name, *args, **kwargs):
        self.invoke_calls += 1
        self.invoke_targets.append(
            f"{getattr(specialist, 'value', specialist)}:{remote_name}"
        )
        return self._adapter.call_remote_tool(
            specialist, remote_name, *args, **kwargs
        )


def _context() -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id="r4-eval",
        name="R4 Eval",
        email="r4-eval@example.com",
        effective_permissions=("delia.access",),
        is_superadmin=False,
    )


def _compose(inject_purpose=None, on_inject=None):
    settings = Settings()
    if settings.llm_egress_blocked_reason:
        raise SystemExit(f"refused: {settings.llm_egress_blocked_reason}")
    connections = specialist_connections_from_settings(settings)
    mcp = _CountingMcpAdapter(
        McpSpecialistAdapter(
            connections,
            credential_provider=_wire_delegated_credential_provider(
                settings, connections
            ),
        )
    )
    interop = SpecialistInterop(mcp)
    guarded = _GuardedAdapter(
        OpenAICompatibleModelInvocationAdapter(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
            default_max_output_units=settings.llm_max_output_tokens,
        ),
        inject_purpose=inject_purpose,
        on_inject=on_inject,
    )
    handler = _compose_turn_handler(
        InvokeModel(guarded),
        ModelRef(
            model_id=settings.llm_model,
            version="configured",
            owner_ref="DELPI",
            provider_ref="openai_compatible",
        ),
        interop,
        settings,
        connections,
    )
    return handler, guarded, mcp


def _run(handler, guarded, mcp, question: str, bearer: str,
         cancel_check=None) -> dict:
    events: list[str] = []
    started = time.monotonic()
    binding = bind_subject_bearer(bearer)
    error = None
    result = None
    try:
        result = handler.execute(
            InteractiveTurnRequest(
                access_context=_context(), input_text=question
            ),
            activity_channel=lambda e: events.append(
                getattr(e.phase, "value", str(e.phase))
            ),
            cancel_check=cancel_check,
        )
    except Exception as exc:  # honest terminal capture
        error = getattr(exc, "code", type(exc).__name__)
    finally:
        unbind_subject_bearer(binding)
    return {
        "elapsed_s": round(time.monotonic() - started, 2),
        "error": error,
        "grounding": str(getattr(result, "grounding_status", "")),
        "continuing_events": events.count("CONTINUING"),
        "phases": events,
        "model_calls": dict(guarded.counts),
        "model_call_detail": guarded.calls,
        "mcp_list_calls": mcp.list_calls,
        "mcp_invoke_calls": mcp.invoke_calls,
        "mcp_invoke_targets": mcp.invoke_targets,
        "content_head": (getattr(result, "content", "") or "")[:100],
    }


def _run_until(handler_runs: list, predicate, limit: int = 3) -> dict:
    """CPU-only Ollama is non-deterministic under contention: a stage
    may time out before the scenario seam is reached. Retry a fresh
    governed turn (new checkpoint, new subject token) until the
    predicate holds or the budget of tries is spent."""
    last = None
    for i in range(limit):
        last = handler_runs[i]()
        last["try_index"] = i
        if predicate(last):
            break
    return last


def _interop_probe(specialist_id: str, remote: str,
                   arguments=None, timeout: float = 15.0) -> dict:
    """Live-wire interop scenario: real bearer → real exchange → real
    owner contract enforcement at the SpecialistInterop seam. Records
    only typed error codes, never payloads."""
    from app.application.specialist_interop.contracts import (
        SpecialistCatalogRequest,
        SpecialistInvocationRequest,
    )

    settings = Settings()
    connections = specialist_connections_from_settings(settings)
    mcp = _CountingMcpAdapter(
        McpSpecialistAdapter(
            connections,
            credential_provider=_wire_delegated_credential_provider(
                settings, connections
            ),
        )
    )
    interop = SpecialistInterop(mcp)
    token = _subject_token()
    binding = bind_subject_bearer(token)
    result = {"specialist": specialist_id, "remote": remote}
    try:
        catalog = interop.discover_catalog(
            SpecialistCatalogRequest(
                specialist_id=specialist_id,
                correlation_id="r4-probe-catalog",
            )
        )
        result["advertised"] = len(catalog.capabilities)
        result["blocked"] = list(catalog.blocked_remote_names)
        result["remote_advertised"] = remote in {
            c.remote_name for c in catalog.capabilities
        }
        try:
            outcome = interop.invoke(
                SpecialistInvocationRequest(
                    specialist_id=specialist_id,
                    remote_capability=remote,
                    correlation_id="r4-probe-invoke",
                    arguments=arguments or {},
                    timeout_seconds=timeout,
                )
            )
            result["invoke_error"] = None
            result["invoke_outcome"] = str(
                getattr(outcome, "status", outcome)
            )[:80]
        except Exception as exc:
            result["invoke_error"] = getattr(
                exc, "code", type(exc).__name__
            )
    except Exception as exc:
        result["catalog_error"] = getattr(
            exc, "code", type(exc).__name__
        )
    finally:
        unbind_subject_bearer(binding)
    result["mcp_list_calls"] = mcp.list_calls
    result["mcp_invoke_calls"] = mcp.invoke_calls
    result["mcp_invoke_targets"] = mcp.invoke_targets
    return result


def main() -> int:
    for required in (
        "R4_DEV_USERNAME",
        "R4_DEV_PASSWORD",
        "R4_KC_TOKEN_URL",
    ):
        if not _env(required):
            return _fail(f"missing env {required}")

    out = {"model": _env("DELIA_LLM_MODEL"), "scenarios": {}}

    def _fresh(question, inject=None, on_inject=None, cancel_at=None):
        handler, guarded, mcp = _compose(
            inject_purpose=inject, on_inject=on_inject
        )
        cancel_calls = {"n": 0}

        def _cancel_check():
            cancel_calls["n"] += 1
            return cancel_at is not None and cancel_calls["n"] >= cancel_at

        def _do():
            return _run(
                handler, guarded, mcp, question, _subject_token(),
                cancel_check=_cancel_check if cancel_at else None,
            )

        _do.guarded = guarded
        return _do

    def _reached_read(v):
        return v["mcp_invoke_calls"] >= 1

    def _injected(v):
        return any(
            c.get("error") == "injected_timeout"
            for c in v["model_call_detail"]
        )

    # S1 — real chain, no injection; retry until a real READ lands
    out["scenarios"]["S1_read_without_timeout"] = _run_until(
        [_fresh(QUESTIONS["vista_playlists"]) for _ in range(3)],
        _reached_read,
    )

    # S2 — injected LLM timeout at select_capability → CONTINUING →
    # attempt 2 reaches the real READ on the live wire.
    runners = [
        _fresh(
            QUESTIONS["vista_playlists"],
            inject="delia.capability_orchestration.select_capability",
        )
        for _ in range(3)
    ]
    out["scenarios"]["S2_read_after_llm_retry"] = _run_until(
        runners,
        lambda v: _injected(v) and _reached_read(v),
    )

    # S3 — timeout AFTER the READ outcome completes (synthesis stage)
    # → checkpoint replay on attempt 2; MCP invoke count must stay 1.
    runners = [
        _fresh(
            QUESTIONS["vista_playlists"],
            inject="delia.capability_orchestration.grounded_synthesis",
        )
        for _ in range(3)
    ]
    out["scenarios"]["S3_timeout_after_read_outcome"] = _run_until(
        runners,
        lambda v: _injected(v) and v["mcp_invoke_calls"] == 1,
    )

    # S4 — revocation strictly before the resumed attempt: inject at a
    # RESUMABLE stage (select_capability), disable the user between
    # attempts, then prove attempt 2 fails closed on the live wire.
    if _env("R4_KC_ADMIN") and _env("R4_KC_ADMIN_PASSWORD"):
        try:
            runners = [
                _fresh(
                    QUESTIONS["vista_playlists"],
                    inject="delia.capability_orchestration"
                    ".select_capability",
                    on_inject=lambda: _set_user_enabled(False),
                )
                for _ in range(3)
            ]
            out["scenarios"]["S4_revocation_before_resume"] = _run_until(
                runners, _injected
            )
        finally:
            try:
                _set_user_enabled(True)
                out["user_restored"] = True
            except Exception:
                out["user_restored"] = "FAILED — restore manually"
    else:
        out["scenarios"]["S4_revocation_before_resume"] = "TEST_NOT_RUN"

    # S5 — forged bearer fails closed at the exchange
    handler, guarded, mcp = _compose()
    out["scenarios"]["S5_invalid_subject_bearer"] = _run(
        handler, guarded, mcp,
        QUESTIONS["mcp_davi"], "invalid.bearer.token",
    )

    # S6 — capability unavailable: catalog lists live, the capability is
    # NOT advertised → UNKNOWN_CAPABILITY on the real wire.
    out["scenarios"]["S6_capability_unavailable"] = _interop_probe(
        "davi", "nonexistent_capability"
    )

    # S7 — real MCP failure: dead base URL on the real wire → surface
    # listing fails closed; no fallback, no invocation.
    saved = os.environ.get("DELIA_MCP_DAVI_BASE_URL")
    os.environ["DELIA_MCP_DAVI_BASE_URL"] = "http://api-delpi:9/mcp"
    try:
        out["scenarios"]["S7_real_mcp_failure"] = _interop_probe(
            "davi", "discover_delpi_information"
        )
    finally:
        if saved is None:
            del os.environ["DELIA_MCP_DAVI_BASE_URL"]
        else:
            os.environ["DELIA_MCP_DAVI_BASE_URL"] = saved

    # S8 — PREPARE/ACT non-repetition: enumerate live catalogs; invoke a
    # non-READ-class advertised tool → refused before tools/call. If
    # none is advertised, invoke a forged capability → UNKNOWN_*.
    settings = Settings()
    connections = specialist_connections_from_settings(settings)
    mcp = _CountingMcpAdapter(
        McpSpecialistAdapter(
            connections,
            credential_provider=_wire_delegated_credential_provider(
                settings, connections
            ),
        )
    )
    interop = SpecialistInterop(mcp)
    from app.application.specialist_interop.contracts import (
        SpecialistCatalogRequest,
        SpecialistInvocationRequest,
    )
    from app.domain.specialist_interop.rules import (
        invocable_in_interactive_phase,
        operation_class_from_owner,
    )
    token = _subject_token()
    binding = bind_subject_bearer(token)
    s8 = {"non_invocable_advertised": []}
    try:
        for sid in connections:
            try:
                cat = interop.discover_catalog(
                    SpecialistCatalogRequest(
                        specialist_id=str(sid), correlation_id="r4-s8"
                    )
                )
            except Exception as exc:
                s8.setdefault("catalog_errors", []).append(
                    f"{sid}:{getattr(exc, 'code', type(exc).__name__)}"
                )
                continue
            for cap in cat.capabilities:
                cls = operation_class_from_owner(cap.operation_class)
                if not invocable_in_interactive_phase(cls):
                    s8["non_invocable_advertised"].append(
                        f"{sid}.{cap.remote_name}:{cls}"
                    )
        # refuse a forged capability — governed guard before tools/call
        try:
            interop.invoke(
                SpecialistInvocationRequest(
                    specialist_id="davi",
                    remote_capability="__forged_write__",
                    correlation_id="r4-s8-forged",
                    arguments={},
                )
            )
            s8["forged_invoke"] = "NOT_REFUSED"
        except Exception as exc:
            s8["forged_invoke"] = getattr(exc, "code", type(exc).__name__)
    finally:
        unbind_subject_bearer(binding)
    s8["mcp_list_calls"] = mcp.list_calls
    s8["mcp_invoke_calls"] = mcp.invoke_calls
    s8["mcp_invoke_targets"] = mcp.invoke_targets
    out["scenarios"]["S8_prepare_act_guard"] = s8

    # S9 — cancellation during processing: cancel_check fires from the
    # second check onward → honest bounded terminal, single result.
    runners = [_fresh(QUESTIONS["mcp_davi"], cancel_at=2)]
    out["scenarios"]["S9_cancellation_during_processing"] = runners[0]()

    # S10 — schema/argument contract: real advertised READ tool invoked
    # with bogus arguments → governed/owner validation refuses on the
    # live wire (no fabricated outcome).
    out["scenarios"]["S10_invalid_arguments"] = _interop_probe(
        "davi",
        "discover_delpi_information",
        arguments={"__bogus__": "x"},
    )

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def _fail(msg: str) -> int:
    print(json.dumps({"error": msg}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
