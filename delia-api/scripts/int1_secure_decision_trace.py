#!/usr/bin/env python3
"""INT-1 secure decision-trace capture (eval observability only).

Persists structured JSONL on a host path that outlives process/container
lifecycle. Does NOT alter Agent decision logic. Does NOT call external
LLM providers. Does NOT copy production environment.

Security gate (fail-closed):
  - DELIA_ENV != production refuses non-local LLM base URLs
  - localhost / host.docker.internal shaped URLs that would pass the
    existing egress host check are still refused here for *eval* unless
    DELIA_EVAL_EGRESS_AUTHORIZED=1 is set by an explicit security owner
    approval (ARCHITECTURE_DECISION_REQUIRED until then)

Usage:
  python scripts/int1_secure_decision_trace.py --dry-run
  python scripts/int1_secure_decision_trace.py --check-security-gate
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

# Host-persistent default under delia-api/.battery (gitignored).
_REPO_DELIA = Path(__file__).resolve().parents[1]
_DEFAULT_TRACE_ROOT = _REPO_DELIA / ".battery" / "int1-secure-decision-trace"

_SENSITIVE_KEY_FRAGMENTS = (
    "password",
    "secret",
    "token",
    "authorization",
    "api_key",
    "apikey",
    "cookie",
    "credential",
    "private_key",
    "bearer",
)


def _trace_root() -> Path:
    raw = (os.environ.get("DELIA_EVAL_TRACE_DIR") or "").strip()
    return Path(raw) if raw else _DEFAULT_TRACE_ROOT


def ensure_trace_dir(root: Path | None = None) -> Path:
    path = root or _trace_root()
    path.mkdir(parents=True, exist_ok=True)
    # Owner-only when filesystem permits (WSL/ext4).
    try:
        os.chmod(path, stat.S_IRWXU)
    except OSError:
        pass
    return path


def _is_sensitive_key(key: str) -> bool:
    lowered = key.casefold()
    return any(frag in lowered for frag in _SENSITIVE_KEY_FRAGMENTS)


def sanitize_mapping(value: Any, *, depth: int = 0) -> Any:
    """Redact secrets; keep structural arg types and allowlisted ids."""
    if depth > 6:
        return "<max_depth>"
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for raw_k, raw_v in value.items():
            key = str(raw_k)
            if _is_sensitive_key(key):
                out[key] = "<redacted>"
            else:
                out[key] = sanitize_mapping(raw_v, depth=depth + 1)
        return out
    if isinstance(value, (list, tuple)):
        return [sanitize_mapping(item, depth=depth + 1) for item in value[:32]]
    if isinstance(value, str):
        if len(value) > 500:
            return value[:500] + "<truncated>"
        return value
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return {"type": type(value).__name__}


def append_event(
    evaluation_id: str,
    event_type: str,
    payload: Mapping[str, Any],
    *,
    scenario_id: str | None = None,
    correlation_id: str | None = None,
    root: Path | None = None,
) -> Path:
    base = ensure_trace_dir(root)
    evaluation_dir = base / evaluation_id
    evaluation_dir.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(evaluation_dir, stat.S_IRWXU)
    except OSError:
        pass
    name = f"{scenario_id or 'session'}.jsonl"
    path = evaluation_dir / name
    record = {
        "schema_version": "int1_decision_trace_v1",
        "event_type": event_type,
        "evaluation_id": evaluation_id,
        "scenario_id": scenario_id,
        "correlation_id": correlation_id,
        "timestamp_unix_ms": int(time.time() * 1000),
        "payload": sanitize_mapping(dict(payload)),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return path


def check_security_gate() -> dict[str, Any]:
    """Fail-closed security inventory for INT-1 real Qwen eval."""
    # Import lazily so --dry-run schema checks can run without full app.
    sys.path.insert(0, str(_REPO_DELIA))
    from app.infrastructure.config.settings import (
        Settings,
        is_local_llm_host,
        llm_egress_blocked_reason,
    )

    settings = Settings()
    env = settings.environment
    base_url = settings.llm_base_url or ""
    host = urlsplit(base_url).hostname or ""
    local_host = is_local_llm_host(host) if host else False
    policy_blocks_external = (
        llm_egress_blocked_reason(env, base_url) is not None
        if base_url
        else env != "production"
    )
    # Explicit eval authorization — never inferred from connectivity.
    owner_flag = (os.environ.get("DELIA_EVAL_EGRESS_AUTHORIZED") or "").strip()
    owner_approved = owner_flag == "1"
    # Localhost-shaped URL that would satisfy Settings host check but
    # still forward to OpenRouter is the prior EXECUTION_DRIFT pattern.
    localhost_shaped = local_host and env != "production"
    bypass_pattern = localhost_shaped and not owner_approved

    model = settings.llm_model or ""
    target_model = "qwen/qwen3-14b"
    model_match = model == target_model

    # Local Ollama may host other qwen sizes — not a substitute for the
    # authorized target without coordination approval.
    result = {
        "SECURE_EVAL_GATE": "BLOCKED",
        "NONPROD_RUNTIME_ISOLATED": "NOT_PROVEN",
        "CREDENTIAL_ISOLATION": "NOT_PROVEN",
        "NETWORK_ACCESS_AUTHORIZED": "NOT_PROVEN",
        "MODEL_EGRESS_AUTHORIZED": "NOT_PROVEN",
        "MCP_READ_AUTHORIZED": "NOT_PROVEN",
        "PRODUCTION_UNTOUCHED": "NOT_OBSERVED_THIS_SCRIPT",
        "SECURITY_OWNER_APPROVAL": "NOT_PROVEN",
        "POLICY_EXTERNAL_LLM_NONPROD": (
            "REFUSED" if env != "production" else "PRODUCTION_PATH"
        ),
        "CURRENT_ENV": env,
        "CURRENT_LLM_HOST_CLASS": (
            "local_shaped" if local_host else ("empty" if not host else "external")
        ),
        "POLICY_BLOCKS_EXTERNAL_BASE_URL": policy_blocks_external,
        "LOCALHOST_SHAPED_BYPASS_PATTERN": bypass_pattern,
        "DELIA_EVAL_EGRESS_AUTHORIZED_FLAG": owner_approved,
        "TARGET_MODEL": target_model,
        "CONFIGURED_MODEL": model,
        "TARGET_MODEL_MATCH": model_match,
        "ARCHITECTURE_DECISION_REQUIRED": (
            "authorized nonprod external Qwen14B eval path "
            "(credential scope + egress + isolation)"
            if env != "production"
            else None
        ),
        "EXISTING_EQUIVALENT": "PARTIAL",
        "REUSE_DECISION": (
            "EXTEND_OBSERVABILITY_ONLY; "
            "NEW_AUTHORIZED_EGRESS_PATH_REQUIRES_ADR"
        ),
        "SECURITY_OWNER": "platform-security-identity-authorization + delivery/runtime",
        "APPROVED_EGRESS_PATH": "NONE_DOCUMENTED_FOR_NONPROD_OPENROUTER",
        "EVALUATION_CREDENTIAL_SCOPE": "NONE_PROVEN_SEPARATE_FROM_PROD",
        "BLOCKERS": [],
    }
    blockers: list[str] = []
    openrouter_host = host.lower() == "openrouter.ai"
    if env != "production" and not owner_approved:
        blockers.append("SECURITY_OWNER_APPROVAL missing for nonprod external model")
    # Localhost-shaped OpenRouter (prior EXECUTION_DRIFT) is always refused
    # for this eval — even with the flag. Use the real allowlisted host.
    if localhost_shaped:
        blockers.append(
            "localhost-shaped LLM URL forbidden for OpenRouter eval "
            "(use https://openrouter.ai/api/v1; do not use egress proxy)"
        )
    if env != "production" and base_url and policy_blocks_external:
        blockers.append("nonprod external LLM base URL refused by Settings policy")
    if owner_approved and base_url and not openrouter_host and not local_host:
        blockers.append(
            f"eval allowlist expects openrouter.ai, got host {host!r}"
        )
    if not model_match:
        blockers.append(
            f"configured model {model!r} != required target {target_model!r}"
        )
    if not owner_approved:
        blockers.append("MODEL_EGRESS_AUTHORIZED not proven")
        blockers.append("CREDENTIAL_ISOLATION not proven for eval identity")
        blockers.append("NETWORK_ACCESS_AUTHORIZED not proven")
    result["BLOCKERS"] = blockers
    if (
        not blockers
        and owner_approved
        and model_match
        and openrouter_host
        and not policy_blocks_external
    ):
        result["SECURE_EVAL_GATE"] = "READY_FOR_ISOLATED_EVAL"
        result["MODEL_EGRESS_AUTHORIZED"] = "PROVEN_ALLOWLIST_OPENROUTER"
        result["SECURITY_OWNER_APPROVAL"] = "PO_AUTHORIZED_EVAL_FLAG"
        result["APPROVED_EGRESS_PATH"] = "https://openrouter.ai/api/v1"
        result["ARCHITECTURE_DECISION_REQUIRED"] = None
        result["POLICY_EXTERNAL_LLM_NONPROD"] = (
            "ALLOWLISTED_WHEN_DELIA_EVAL_EGRESS_AUTHORIZED=1"
        )
        result["REUSE_DECISION"] = (
            "REUSE openrouter_qwen profile + explicit eval egress allowlist"
        )
    return result


def run_dry_run(*, root: Path | None = None) -> dict[str, Any]:
    """Deterministic capture without external provider or MCP wire."""
    base = ensure_trace_dir(root)
    evaluation_id = f"dryrun-{uuid.uuid4().hex[:12]}"
    correlation_id = f"corr-{uuid.uuid4().hex[:12]}"
    scenario_id = "DRY_P3_TOOL_SURFACE"

    # Exercise real progress classifier with a synthetic SUCCESS attempt
    # shape when importable; fall back to literal progress labels.
    progress_class = "NEW_INFORMATION"
    try:
        sys.path.insert(0, str(_REPO_DELIA))
        from app.application.capability_provision.semantic_capability_support import (
            INVESTIGATION_PROGRESS_NEW,
            INVESTIGATION_PROGRESS_RELATED,
            classify_investigation_progress,
        )
        from app.application.interaction.capability_attempt import (
            GovernedCapabilityAttempt,
            GovernedCapabilityStatus,
        )

        # Minimal attempt: no provenance → not business evidence → NONE
        empty = GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.SUCCESS,
            correlation_id=correlation_id,
            content="synthetic dashboard_summary_live",
        )
        progress_class = classify_investigation_progress(empty)
        # Related path requires obligations; document both labels exist.
        _ = (INVESTIGATION_PROGRESS_NEW, INVESTIGATION_PROGRESS_RELATED)
    except Exception as exc:  # noqa: BLE001 — dry-run must still persist
        progress_class = f"import_fallback:{type(exc).__name__}"

    append_event(
        evaluation_id,
        "evaluation_meta",
        {
            "evaluated_sha": "dry-run",
            "runtime_sha": "dry-run",
            "model_id": "function_model_dry_run",
            "model_profile": "none",
            "instruction_fingerprint": "dry-run",
            "policy_version": "int1_decision_trace_v1",
            "secure_eval_gate": "NOT_APPLICABLE_DRY_RUN",
        },
        scenario_id=scenario_id,
        correlation_id=correlation_id,
        root=base,
    )
    tool_surface = {
        "eligible_specialists": ["TEO", "VISTA", "DAVI"],
        "eligible_capabilities": [
            "teo.analyze",
            "vista.knowledge",
            "vista.read",
            "davi.read",
        ],
        "model_visible_tool_names": [
            "teo.analyze",
            "vista.knowledge",
            "vista.read",
            "davi.read",
        ],
        "model_visible_tool_descriptions": {
            "teo.analyze": "Analysis views including dashboard_summary_live|…",
            "vista.knowledge": "Product guides by topic (GUIDANCE_NOT_DOMAIN_TRUTH)",
            "vista.read": "Semantic read including product_guide.guide",
            "davi.read": "capability get_product_structure among catalog ids",
        },
        "model_visible_tool_schemas": {
            "teo.analyze": {
                "type": "object",
                "properties": {"view": {"type": "string"}},
                "required": ["view"],
            },
            "vista.knowledge": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "topic": {"type": "string"},
                },
            },
        },
        "capability_ids": [
            "teo.analyze",
            "vista.knowledge",
            "vista.read",
            "davi.read",
        ],
        "toolset_filters_applied": ["live_eligible_catalog", "write_class_excluded"],
    }
    append_event(
        evaluation_id,
        "model_visible_toolset",
        tool_surface,
        scenario_id=scenario_id,
        correlation_id=correlation_id,
        root=base,
    )
    append_event(
        evaluation_id,
        "tool_call",
        {
            "call_sequence_number": 1,
            "model_selected_tool": "teo.analyze",
            "capability_id": "teo.analyze",
            "specialist_id": "TEO",
            "argument_keys": ["view"],
            "argument_types": {"view": "str"},
            "sanitized_argument_values": {"view": "dashboard_summary_live"},
            "argument_validation_result": "accepted_synthetic",
            "owner_error_code": None,
            "owner_result_class": "ANALYSIS_SNAPSHOT",
            "owner_result_completeness": "partial",
            "evidence_refs": [1],
            "investigation_progress_class": progress_class,
            "coverage_state": "coverage_unknown",
            "retry_or_continue_reason": "dry_run_scripted",
            # Sensitive keys must be redacted by sanitize_mapping.
            "api_key": "should-never-persist",
            "authorization": "Bearer should-never-persist",
        },
        scenario_id=scenario_id,
        correlation_id=correlation_id,
        root=base,
    )
    append_event(
        evaluation_id,
        "finalization",
        {
            "declared_investigation_status": "partial",
            "declared_limitations": ["dry_run_only"],
            "material_obligations": [],
            "unmet_obligations": ["visualization_format_catalog"],
            "evidence_binding": {"accepted_refs": [1]},
            "coverage_result": "coverage_unknown",
            "final_governed_status": "SUCCESS",
            "final_business_outcome": "DRY_RUN_NOT_A_REAL_OUTCOME",
        },
        scenario_id=scenario_id,
        correlation_id=correlation_id,
        root=base,
    )

    jsonl_path = base / evaluation_id / f"{scenario_id}.jsonl"
    lines = jsonl_path.read_text(encoding="utf-8").splitlines()
    events = [json.loads(line) for line in lines]
    event_types = [item["event_type"] for item in events]
    tool_call = next(item for item in events if item["event_type"] == "tool_call")
    payload = tool_call["payload"]
    redacted_ok = (
        payload.get("api_key") == "<redacted>"
        and payload.get("authorization") == "<redacted>"
    )
    surface_ok = "model_visible_toolset" in event_types
    args_ok = "argument_keys" in payload and "sanitized_argument_values" in payload
    progress_ok = "investigation_progress_class" in payload
    fingerprint = hashlib.sha256(jsonl_path.read_bytes()).hexdigest()[:16]

    return {
        "evaluation_id": evaluation_id,
        "correlation_id": correlation_id,
        "scenario_id": scenario_id,
        "jsonl_path": str(jsonl_path),
        "event_count": len(events),
        "event_types": event_types,
        "TRACE_SCHEMA": "PASS" if event_types == [
            "evaluation_meta",
            "model_visible_toolset",
            "tool_call",
            "finalization",
        ]
        else "FAIL",
        "TRACE_SANITIZATION": "PASS" if redacted_ok else "FAIL",
        "TOOL_SURFACE_CAPTURE": "PASS" if surface_ok else "FAIL",
        "ARGUMENT_CAPTURE": "PASS" if args_ok else "FAIL",
        "PROGRESS_CAPTURE": "PASS" if progress_ok else "FAIL",
        "content_fingerprint": fingerprint,
        "progress_class_observed": progress_class,
    }


def verify_persistence_after_exit(
    evaluation_id: str,
    expected_fingerprint: str,
    *,
    root: Path | None = None,
) -> dict[str, str]:
    base = root or _trace_root()
    matches = list((base / evaluation_id).glob("*.jsonl"))
    if not matches:
        return {"TRACE_PERSISTENCE_AFTER_EXIT": "FAIL", "reason": "missing_jsonl"}
    path = matches[0]
    fingerprint = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    ok = fingerprint == expected_fingerprint and path.stat().st_size > 0
    return {
        "TRACE_PERSISTENCE_AFTER_EXIT": "PASS" if ok else "FAIL",
        "path": str(path),
        "fingerprint": fingerprint,
        "expected_fingerprint": expected_fingerprint,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check-security-gate", action="store_true")
    parser.add_argument(
        "--verify-persistence",
        nargs=2,
        metavar=("EVALUATION_ID", "FINGERPRINT"),
        help="Re-open host artifacts after process exit",
    )
    args = parser.parse_args(argv)

    if args.check_security_gate:
        result = check_security_gate()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("SECURE_EVAL_GATE") != "BLOCKED" else 2

    if args.verify_persistence:
        evaluation_id, fingerprint = args.verify_persistence
        print(
            json.dumps(
                verify_persistence_after_exit(evaluation_id, fingerprint),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.dry_run:
        first = run_dry_run()
        # Separate process verification is invoked by the shell wrapper;
        # also verify in-process that files remain after close.
        second = verify_persistence_after_exit(
            first["evaluation_id"], first["content_fingerprint"]
        )
        out = {**first, **second}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        gates = [
            out.get("TRACE_SCHEMA"),
            out.get("TRACE_PERSISTENCE_AFTER_EXIT"),
            out.get("TRACE_SANITIZATION"),
            out.get("TOOL_SURFACE_CAPTURE"),
            out.get("ARGUMENT_CAPTURE"),
            out.get("PROGRESS_CAPTURE"),
        ]
        return 0 if all(item == "PASS" for item in gates) else 1

    parser.print_help()
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
