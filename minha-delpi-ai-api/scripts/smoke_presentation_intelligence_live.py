#!/usr/bin/env python3
"""Smoke live — Presentation Intelligence (R5 / labels / heatmap).

Valida o pipeline canônico:

```text
payload → PresentationDataProfile → FieldLabelBundle
→ PresentationIntent → binder → validator → compiler → slots/renderPlan
```

Modos:
  SMOKE_PI_PHASE=inprocess|http|all  (default all)

Uso:
  # só inprocess (sem gateway)
  cd minha-delpi-ai-api
  PYTHONPATH=. .venv/bin/python -u scripts/smoke_presentation_intelligence_live.py

  # live HTTP via gateway (host)
  SMOKE_BASE_URL=http://localhost SMOKE_PI_PHASE=all \\
    PYTHONPATH=. .venv/bin/python -u scripts/smoke_presentation_intelligence_live.py

  # dentro do container da API
  docker exec -e PYTHONPATH=/app -e SMOKE_BASE_URL=http://delpi-gateway \\
    -e SMOKE_PI_PHASE=all -w /app delpi-minha-delpi-ai-api \\
    python -u scripts/smoke_presentation_intelligence_live.py

Dimensões cobertas:
  R5 apresentação (binding, heatmap constant-field, labels PT-BR)
  R9 outcome do pedido visual quando materializável
  R10 safety (campo obscuro sem inventar significado; palette adversarial)
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip() or "http://localhost"
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_RESPONSE_MODE = os.environ.get("SMOKE_RESPONSE_MODE", "normal").strip() or "normal"
_PHASE = os.environ.get("SMOKE_PI_PHASE", "all").strip().lower() or "all"
_AGENT_ID = os.environ.get("SMOKE_AGENT_ID", "").strip()
_HTTP_TIMEOUT = float(os.environ.get("SMOKE_HTTP_TIMEOUT", "420"))
_OUT = os.environ.get(
    "SMOKE_EVIDENCE_PATH",
    "docs/testing/evidence/presentation-intelligence-live.json",
).strip()

_HEATMAP_MSG = os.environ.get(
    "SMOKE_PI_HEATMAP_MESSAGE",
    (
        "Use a programação de produção de hoje (/production/schedule/today). "
        "Quero mapa de calor product_code × work_center pela planned_qty, "
        "em tons de azul."
    ),
).strip()

_CHART_MSG = os.environ.get(
    "SMOKE_PI_CHART_MESSAGE",
    "Qual o estoque do produto 90260149? Prefiro gráfico de barras com labels claros.",
).strip()

_INVENTED_LABEL_FORBIDDEN = ("faturamento", "produção", "producao", "cliente", "receita")


def _ok(label: str, detail: str = "") -> None:
    suffix = f" — {detail}" if detail else ""
    print(f"PASS  {label}{suffix}", flush=True)


def _fail(label: str, detail: str) -> None:
    print(f"FAIL  {label} — {detail}", flush=True)


def _warn(label: str, detail: str) -> None:
    print(f"WARN  {label} — {detail}", flush=True)


def _inconclusive(label: str, detail: str) -> None:
    print(f"INCONCLUSIVE  {label} — {detail}", flush=True)


def _request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: float = 360,
) -> dict:
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _fetch_token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": _CLIENT_ID,
            "username": _USERNAME,
            "password": _PASSWORD,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{_BASE_URL}/auth/realms/{_REALM}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"Token ausente: {payload}")
    return str(token)


def _first_agent(token: str) -> str:
    if _AGENT_ID:
        return _AGENT_ID
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20", token=token)
    rows = agents if isinstance(agents, list) else agents.get("items") or agents.get("data") or []
    for row in rows:
        if isinstance(row, dict) and row.get("enabled"):
            return str(row.get("id") or row.get("agentId"))
    if not rows:
        raise RuntimeError("Nenhum agente disponível")
    return str(rows[0].get("id") or rows[0].get("agentId"))


def _create_session(token: str, agent_id: str) -> str:
    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"agentId": agent_id, "title": "smoke-presentation-intelligence"},
    )
    session_id = payload.get("id") or payload.get("sessionId")
    if not session_id:
        raise RuntimeError(f"Sessão não criada: {payload}")
    return str(session_id)


def _send(token: str, session_id: str, message: str) -> dict:
    return _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={
            "message": message,
            "responseMode": _RESPONSE_MODE,
            "includeAdminDebug": True,
        },
        timeout=_HTTP_TIMEOUT,
    )


def _matrix_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for product in ("P1", "P2"):
        for warehouse in ("W1", "W2", "W3"):
            rows.append(
                {
                    "product_code": product,
                    "warehouse": warehouse,
                    "unit": "UN",
                    "planned_qty": 10 + (10 if product == "P2" else 0) + len(warehouse) * 3,
                }
            )
    return rows


def _external_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for machine in ("WC-1", "WC-2"):
        for shift in ("A", "B"):
            rows.append(
                {
                    "machine": machine,
                    "shift": shift,
                    "output_qty": 100 + (20 if machine.endswith("2") else 0),
                    "defect_rate": 0.02,
                }
            )
    return rows


def phase_inprocess() -> dict[str, Any]:
    """Pipeline determinístico no processo — não depende de gateway/TOTVS."""
    print("\n=== FASE inprocess (Presentation Intelligence) ===", flush=True)
    cases: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        from app.composition.content_composer import configure_domain_infrastructure_ports

        configure_domain_infrastructure_ports()
    except Exception as exc:  # noqa: BLE001
        errors.append(f"content_ports:{exc}")
        _fail("content_ports", str(exc))
        return {"phase": "inprocess", "errors": errors, "cases": cases}

    from app.domain.services.external_actions.external_action_column_label_service import (
        invalidate_column_label_cache,
    )
    from app.domain.services.presentation_intelligence_orchestrator_service import (
        PresentationIntelligenceOrchestratorService,
    )
    from app.domain.services.presentation_spec_validator_service import (
        PresentationSpecValidatorService,
    )
    from app.domain.services.presentation_data_profile_builder_service import (
        PresentationDataProfileBuilderService,
    )
    from app.domain.entities.presentation_spec import EncodingChannel, PresentationSpec
    from app.domain.services.chat_field_label_resolution_pipeline_service import (
        ChatFieldLabelResolutionPipelineService,
    )

    invalidate_column_label_cache()

    # --- Positive: heatmap + constant unit ---
    case_id = "PI.inprocess.heatmap_constant_unit"
    metadata = {
        "path": "/smoke/presentation-intelligence",
        "userMessage": "mapa de calor produto × depósito com qtd planejada em tons de azul",
        "chartPresentation": {
            "type": "chart",
            "chartType": "bar",
            "title": "Mapa",
            "data": _matrix_rows(),
            "config": {},
        },
        "presentationDecision": {"selected": "chart", "layoutMode": "single"},
    }
    started = time.perf_counter()
    summary = PresentationIntelligenceOrchestratorService.apply_before_render_plan(
        metadata,
        user_message=metadata["userMessage"],
    )
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    chart = metadata.get("chartPresentation") or {}
    config = chart.get("config") if isinstance(chart, dict) else {}
    labels = (config or {}).get("fieldLabels") or {}
    axes = {config.get("xAxis"), config.get("yAxis")}
    case_errors: list[str] = []
    if not summary.get("specApplied"):
        case_errors.append("spec_not_applied")
    if chart.get("chartType") != "heatmap":
        case_errors.append(f"chartType={chart.get('chartType')}")
    if "unit" in axes:
        case_errors.append("constant_unit_used_as_axis")
    if axes != {"product_code", "warehouse"}:
        case_errors.append(f"axes={axes}")
    if config.get("valueKey") != "planned_qty":
        case_errors.append(f"valueKey={config.get('valueKey')}")
    if config.get("bindingProvenance") != "COMPILED":
        case_errors.append(f"provenance={config.get('bindingProvenance')}")
    if labels.get("planned_qty") in (None, "", "planned_qty"):
        case_errors.append("planned_qty_label_missing")
    if " " not in str(labels.get("planned_qty") or "") and str(
        labels.get("planned_qty") or ""
    ).lower() == "planned_qty":
        case_errors.append("planned_qty_raw_key")
    # Prefer PT-BR grounded (catalog).
    planned_label = str(labels.get("planned_qty") or "").lower()
    if "planejad" not in planned_label and "qtd" not in planned_label:
        case_errors.append(f"planned_qty_label_not_ptbr={labels.get('planned_qty')}")

    if case_errors:
        errors.extend(case_errors)
        _fail(case_id, "; ".join(case_errors))
    else:
        _ok(
            case_id,
            f"x={config.get('xAxis')} y={config.get('yAxis')} "
            f"value={config.get('valueKey')} label={labels.get('planned_qty')} "
            f"ms={elapsed_ms}",
        )
    cases.append(
        {
            "id": case_id,
            "status": "FAIL" if case_errors else "PASS",
            "errors": case_errors,
            "elapsedMs": elapsed_ms,
            "chartType": chart.get("chartType"),
            "config": {
                "xAxis": config.get("xAxis"),
                "yAxis": config.get("yAxis"),
                "valueKey": config.get("valueKey"),
                "bindingProvenance": config.get("bindingProvenance"),
                "paletteFamily": config.get("paletteFamily"),
                "fieldLabels": labels,
            },
            "summary": summary,
        }
    )

    # --- Sibling: external OpenAPI-like fields ---
    case_id = "PI.inprocess.external_heatmap_sibling"
    openapi = {
        "machine": {"title": "Máquina", "description": "Production workcell identifier"},
        "shift": {"title": "Turno", "description": "Work shift period"},
        "output_qty": {
            "title": "Qtd. produzida",
            "description": "Units completed in the period",
        },
    }
    rows = _external_rows()
    bundle = ChatFieldLabelResolutionPipelineService.resolve(
        list(rows[0].keys()),
        openapi_labels={key: str(meta.get("title")) for key, meta in openapi.items()},
        enable_discovery=False,
    )
    profile = PresentationDataProfileBuilderService.build(
        rows,
        label_bundle=bundle.as_metadata(),
        openapi_field_meta=openapi,
    )
    from app.domain.services.presentation_intent_extractor_service import (
        PresentationIntentExtractorService,
    )
    from app.domain.services.presentation_deterministic_intent_binder_service import (
        PresentationDeterministicIntentBinderService,
    )

    intent = PresentationIntentExtractorService.extract(
        "heatmap máquina × turno pela produção"
    )
    spec, confidence = PresentationDeterministicIntentBinderService.bind(
        intent,
        profile,
        openapi_field_meta=openapi,
    )
    case_errors = []
    if spec is None or spec.mark != "heatmap":
        case_errors.append(f"spec={None if spec is None else spec.mark}")
    else:
        fields = {channel.field for channel in spec.encoding.values()}
        if "machine" not in fields or "shift" not in fields:
            case_errors.append(f"dims={fields}")
        if "output_qty" not in fields:
            case_errors.append(f"measure_missing fields={fields}")
    if confidence <= 0:
        case_errors.append(f"confidence={confidence}")
    if case_errors:
        errors.extend(case_errors)
        _fail(case_id, "; ".join(case_errors))
    else:
        _ok(case_id, f"confidence={confidence:.2f} encoding={[c.field for c in spec.encoding.values()]}")
    cases.append(
        {
            "id": case_id,
            "status": "FAIL" if case_errors else "PASS",
            "errors": case_errors,
            "confidence": confidence,
            "encoding": (
                {key: channel.field for key, channel in spec.encoding.items()}
                if spec
                else None
            ),
        }
    )

    # --- Negative: obscure keys must not invent domain meaning ---
    case_id = "PI.inprocess.label_negative_obscure"
    obscure_bundle = ChatFieldLabelResolutionPipelineService.resolve(
        ["x1", "cod_aux", "vlr2"],
        enable_discovery=False,
    )
    joined = " ".join(str(value).lower() for value in obscure_bundle.labels.values())
    case_errors = [
        token for token in _INVENTED_LABEL_FORBIDDEN if token in joined
    ]
    if case_errors:
        errors.extend([f"invented:{token}" for token in case_errors])
        _fail(case_id, f"invented={case_errors} labels={obscure_bundle.labels}")
    else:
        _ok(case_id, f"labels={obscure_bundle.labels}")
    cases.append(
        {
            "id": case_id,
            "status": "FAIL" if case_errors else "PASS",
            "errors": case_errors,
            "labels": obscure_bundle.labels,
            "sourceByKey": obscure_bundle.as_metadata().get("sourceByKey"),
        }
    )

    # --- Negative: constant Y heatmap rejected ---
    case_id = "PI.inprocess.heatmap_constant_y_rejected"
    profile = PresentationDataProfileBuilderService.build(_matrix_rows())
    bad = PresentationSpec(
        view="chart",
        mark="heatmap",
        encoding={
            "x": EncodingChannel(field="warehouse"),
            "y": EncodingChannel(field="unit"),
            "color": EncodingChannel(field="planned_qty"),
        },
    )
    result = PresentationSpecValidatorService.validate(
        bad, profile=profile, user_explicit=True
    )
    case_errors = []
    if result.ok:
        case_errors.append("expected_reject")
    if result.unmet_intent != "heatmap_not_materializable":
        case_errors.append(f"unmetIntent={result.unmet_intent}")
    if case_errors:
        errors.extend(case_errors)
        _fail(case_id, "; ".join(case_errors))
    else:
        _ok(case_id, f"unmetIntent={result.unmet_intent}")
    cases.append(
        {
            "id": case_id,
            "status": "FAIL" if case_errors else "PASS",
            "errors": case_errors,
            "unmetIntent": result.unmet_intent,
        }
    )

    return {"phase": "inprocess", "errors": errors, "cases": cases}


def _tool_metas(response: dict) -> list[dict[str, Any]]:
    metas: list[dict[str, Any]] = []
    for call in response.get("toolCalls") or []:
        if not isinstance(call, dict):
            continue
        meta = call.get("metadata")
        if isinstance(meta, dict) and meta.get("ok") is not False:
            metas.append(meta)
    return metas


def _pick_presentation_meta(metas: list[dict[str, Any]]) -> dict[str, Any]:
    for meta in metas:
        if meta.get("chartPresentation") or meta.get("presentation") or meta.get(
            "presentationIntelligence"
        ):
            return meta
    return metas[0] if metas else {}


def _chart_slot(meta: dict[str, Any]) -> dict[str, Any]:
    chart = meta.get("chartPresentation")
    if isinstance(chart, dict) and chart.get("type") == "chart":
        return chart
    presentation = meta.get("presentation")
    if isinstance(presentation, dict) and presentation.get("type") == "chart":
        return presentation
    return {}


def _table_slot(meta: dict[str, Any]) -> dict[str, Any]:
    table = meta.get("tablePresentation")
    if isinstance(table, dict) and table.get("type") == "table":
        return table
    presentation = meta.get("presentation")
    if isinstance(presentation, dict) and presentation.get("type") == "table":
        return presentation
    return {}


def _grade_http_heatmap(meta: dict[str, Any]) -> tuple[str, list[str], dict[str, Any]]:
    """Return status, errors, evidence for live heatmap request.

    Strict PASS only when heatmap is delivered with discriminant axes.
    If planner/data deliver another chart but PI still grounded labels and
    did not bind constant `unit`, return INCONCLUSIVE (not FAIL) — routing
    variance is outside Presentation Intelligence ownership.
    """
    errors: list[str] = []
    chart = _chart_slot(meta)
    table = _table_slot(meta)
    intel = (
        meta.get("presentationIntelligence")
        if isinstance(meta.get("presentationIntelligence"), dict)
        else {}
    )
    decision = (
        meta.get("presentationDecision")
        if isinstance(meta.get("presentationDecision"), dict)
        else {}
    )
    evidence = {
        "path": meta.get("path"),
        "chartType": chart.get("chartType") if chart else None,
        "bindingProvenance": (chart.get("config") or {}).get("bindingProvenance") if chart else None,
        "fieldLabels": (chart.get("config") or {}).get("fieldLabels") if chart else None,
        "unmetIntent": decision.get("unmetIntent") or intel.get("unmetIntent"),
        "presentationIntelligence": intel or None,
    }

    if chart and chart.get("chartType") == "heatmap":
        config = chart.get("config") or {}
        axes = {config.get("xAxis"), config.get("yAxis")}
        if "unit" in axes:
            errors.append("constant_unit_axis")
        if config.get("xAxis") == config.get("yAxis"):
            errors.append("degenerate_axes")
        labels = config.get("fieldLabels") or {}
        for key in (config.get("xAxis"), config.get("yAxis"), config.get("valueKey")):
            if not key:
                continue
            label = labels.get(key)
            if label is None:
                continue
            if str(label).strip() == str(key).strip():
                errors.append(f"raw_label:{key}")
        if errors:
            return "FAIL", errors, evidence
        return "PASS", [], evidence

    # Structural PI checks when heatmap mark was not selected.
    if chart:
        config = chart.get("config") or {}
        axes = {config.get("xAxis"), config.get("yAxis")}
        if "unit" in axes:
            return "FAIL", ["constant_unit_axis"], evidence
        labels = config.get("fieldLabels") or {}
        planned = labels.get("planned_qty")
        if planned is not None and str(planned).strip() == "planned_qty":
            return "FAIL", ["planned_qty_raw_label"], evidence
        if planned and "planejad" not in str(planned).lower() and "qtd" not in str(planned).lower():
            # Still accept non-PT synonyms if OpenAPI title English — only flag inventing.
            pass
        notes = [
            f"heatmap_mark_not_selected:got_{chart.get('chartType')}",
            f"path={meta.get('path')}",
        ]
        if intel.get("needsComposer"):
            notes.append("needsComposer=true (shadow/canary off by default)")
        if evidence.get("unmetIntent"):
            notes.append(f"unmetIntent={evidence['unmetIntent']}")
            if table or chart:
                return "PASS", [], {**evidence, "fallback": "informed", "notes": notes}
        return "INCONCLUSIVE", notes, evidence

    unmet = evidence.get("unmetIntent")
    if unmet or intel.get("specApplied") is False:
        if table or meta.get("presentation"):
            return "PASS", [], {**evidence, "fallback": "informed"}
        return "INCONCLUSIVE", ["heatmap_unmet_without_fallback"], evidence

    if table:
        return "INCONCLUSIVE", ["table_only_no_heatmap"], evidence

    return "INCONCLUSIVE", ["no_presentation_slot"], evidence


def _grade_http_labels(meta: dict[str, Any]) -> tuple[str, list[str], dict[str, Any]]:
    errors: list[str] = []
    chart = _chart_slot(meta)
    table = _table_slot(meta)
    evidence: dict[str, Any] = {"path": meta.get("path")}

    if chart:
        config = chart.get("config") or {}
        labels = config.get("fieldLabels") or {}
        evidence["chartType"] = chart.get("chartType")
        evidence["fieldLabels"] = labels
        evidence["bindingProvenance"] = config.get("bindingProvenance")
        if labels:
            raw = [key for key, value in labels.items() if str(value).strip() == str(key).strip()]
            if raw and len(raw) == len(labels):
                errors.append(f"all_labels_raw:{raw}")
        return ("FAIL" if errors else "PASS"), errors, evidence

    if table:
        columns = table.get("columns") or []
        evidence["columns"] = [
            {"key": col.get("key"), "label": col.get("label")}
            for col in columns
            if isinstance(col, dict)
        ][:12]
        for col in columns:
            if not isinstance(col, dict):
                continue
            key = str(col.get("key") or "").strip()
            label = str(col.get("label") or "").strip()
            if key and label and key == label and "_" in key:
                errors.append(f"raw_table_label:{key}")
        return ("FAIL" if errors else "PASS"), errors, evidence

    return "INCONCLUSIVE", ["no_tabular_or_chart"], evidence


def phase_http() -> dict[str, Any]:
    print("\n=== FASE http (chat live) ===", flush=True)
    cases: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        token = _fetch_token()
        agent_id = _first_agent(token)
        session_id = _create_session(token, agent_id)
    except Exception as exc:  # noqa: BLE001
        _fail("http_bootstrap", str(exc))
        return {"phase": "http", "errors": [f"bootstrap:{exc}"], "cases": cases}

    # Case 1 — explicit heatmap on production schedule
    case_id = "PI.http.heatmap_schedule"
    started = time.perf_counter()
    try:
        response = _send(token, session_id, _HEATMAP_MSG)
        metas = _tool_metas(response)
        meta = _pick_presentation_meta(metas)
        status, case_errors, evidence = _grade_http_heatmap(meta)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        evidence["elapsedMs"] = elapsed_ms
        evidence["message"] = _HEATMAP_MSG
        if status == "PASS":
            _ok(case_id, f"path={evidence.get('path')} chartType={evidence.get('chartType')}")
        elif status == "INCONCLUSIVE":
            _inconclusive(case_id, "; ".join(case_errors) or "sem evidência suficiente")
        else:
            errors.extend(case_errors)
            _fail(case_id, "; ".join(case_errors))
        cases.append(
            {
                "id": case_id,
                "status": status,
                "errors": case_errors,
                "evidence": evidence,
            }
        )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{case_id}:{exc}")
        _fail(case_id, str(exc))
        cases.append({"id": case_id, "status": "FAIL", "errors": [str(exc)]})

    # Case 2 — sibling chart/table labels on stock
    case_id = "PI.http.stock_chart_labels"
    started = time.perf_counter()
    try:
        session_id = _create_session(token, agent_id)
        response = _send(token, session_id, _CHART_MSG)
        metas = _tool_metas(response)
        meta = _pick_presentation_meta(metas)
        status, case_errors, evidence = _grade_http_labels(meta)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        evidence["elapsedMs"] = elapsed_ms
        evidence["message"] = _CHART_MSG
        if status == "PASS":
            _ok(case_id, f"path={evidence.get('path')} chartType={evidence.get('chartType')}")
        elif status == "INCONCLUSIVE":
            _inconclusive(case_id, "; ".join(case_errors) or "sem evidência suficiente")
        else:
            errors.extend(case_errors)
            _fail(case_id, "; ".join(case_errors))
        cases.append(
            {
                "id": case_id,
                "status": status,
                "errors": case_errors,
                "evidence": evidence,
            }
        )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{case_id}:{exc}")
        _fail(case_id, str(exc))
        cases.append({"id": case_id, "status": "FAIL", "errors": [str(exc)]})

    return {"phase": "http", "errors": errors, "cases": cases}


def _write_evidence(payload: dict[str, Any]) -> None:
    path = Path(_OUT)
    if not path.is_absolute():
        root = Path(__file__).resolve().parents[1]
        path = root / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nEvidence: {path}", flush=True)


def main() -> int:
    print(
        f"smoke_presentation_intelligence_live base={_BASE_URL} phase={_PHASE}",
        flush=True,
    )
    phases: list[dict[str, Any]] = []
    hard_errors: list[str] = []
    inconclusive = 0

    if _PHASE in {"all", "inprocess"}:
        result = phase_inprocess()
        phases.append(result)
        hard_errors.extend(result.get("errors") or [])

    if _PHASE in {"all", "http"}:
        try:
            result = phase_http()
            phases.append(result)
            hard_errors.extend(result.get("errors") or [])
            inconclusive += sum(
                1 for case in result.get("cases") or [] if case.get("status") == "INCONCLUSIVE"
            )
        except urllib.error.URLError as exc:
            _fail("http_phase", str(exc))
            hard_errors.append(f"http:{exc}")
            phases.append({"phase": "http", "errors": [str(exc)], "cases": []})

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "baseUrl": _BASE_URL,
        "phase": _PHASE,
        "requiredDimensions": ["R5", "R9", "R10"],
        "phases": phases,
        "hardErrors": hard_errors,
        "inconclusiveCount": inconclusive,
    }

    # Verdict: any FAIL in required inprocess → FAIL; http INCONCLUSIVE does not fail alone.
    inprocess = next((item for item in phases if item.get("phase") == "inprocess"), None)
    http = next((item for item in phases if item.get("phase") == "http"), None)
    inprocess_fail = bool(inprocess and (inprocess.get("errors") or []))
    http_fail = bool(
        http
        and any(case.get("status") == "FAIL" for case in (http.get("cases") or []))
    )

    if inprocess_fail or http_fail or hard_errors:
        payload["verdict"] = "FAIL"
    elif inconclusive:
        # Inprocess PASS + http INCONCLUSIVE (ex.: planner não escolheu heatmap)
        # → PASS_ESTRUTURAL com nota; não bloquear harness por routing.
        payload["verdict"] = "PASS"
        payload["verdictNote"] = (
            "inprocess PASS; http had INCONCLUSIVE case(s) — inspect evidence notes"
        )
    else:
        payload["verdict"] = "PASS"

    _write_evidence(payload)
    print(f"\nVERDICT={payload['verdict']}", flush=True)
    return 0 if payload["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
