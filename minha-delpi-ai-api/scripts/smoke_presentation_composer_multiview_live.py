#!/usr/bin/env python3
"""Smoke live — Presentation Composer multi-view T1–T5.

Aceite perceptível multi-turn (inprocess default; HTTP opcional):

| Turno | Prova |
|-------|-------|
| T1 | table default + labels |
| T2 | 3 cols + sort desc |
| T3 | bar chart |
| T4 | heatmap + paletteFamily sequential-blue |
| T5 | preferCanvas → canvasOpen |

Modos:
  SMOKE_PC_PHASE=inprocess|http|all  (default inprocess)

Uso:
  cd minha-delpi-ai-api
  PYTHONPATH=. .venv/bin/python -u scripts/smoke_presentation_composer_multiview_live.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_PHASE = os.environ.get("SMOKE_PC_PHASE", "inprocess").strip().lower() or "inprocess"
_OUT = os.environ.get(
    "SMOKE_EVIDENCE_PATH",
    "docs/testing/evidence/presentation-composer-multiview-live.json",
).strip()


def _ok(label: str, detail: str = "") -> None:
    suffix = f" — {detail}" if detail else ""
    print(f"PASS  {label}{suffix}", flush=True)


def _fail(label: str, detail: str) -> None:
    print(f"FAIL  {label} — {detail}", flush=True)


def _stock_rows() -> list[dict[str, Any]]:
    return [
        {"product_code": "90260149", "warehouse": "01", "balance": 120, "unit": "UN"},
        {"product_code": "90260149", "warehouse": "02", "balance": 45, "unit": "UN"},
        {"product_code": "90260149", "warehouse": "03", "balance": 80, "unit": "UN"},
    ]


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


def _base_metadata(*, rows: list[dict[str, Any]], user_message: str) -> dict[str, Any]:
    return {
        "path": "/smoke/presentation-composer-multiview",
        "userMessage": user_message,
        "tablePresentation": {
            "type": "table",
            "title": "Smoke",
            "columns": [{"key": key} for key in rows[0].keys()],
            "rows": rows,
        },
        "presentationDecision": {"selected": "table", "layoutMode": "single"},
    }


def phase_inprocess() -> dict[str, Any]:
    print("\n=== FASE inprocess (Presentation Composer T1–T5) ===", flush=True)
    cases: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        from app.composition.content_composer import configure_domain_infrastructure_ports

        configure_domain_infrastructure_ports()
    except Exception as exc:  # noqa: BLE001
        errors.append(f"content_ports:{exc}")
        _fail("content_ports", str(exc))
        return {"phase": "inprocess", "errors": errors, "cases": cases}

    from app.domain.entities.presentation_spec import (
        EncodingChannel,
        PresentationDeliverySpec,
        PresentationSpec,
        PresentationTableSpec,
    )
    from app.domain.services.presentation_data_profile_builder_service import (
        PresentationDataProfileBuilderService,
    )
    from app.domain.services.presentation_intelligence_orchestrator_service import (
        PresentationIntelligenceOrchestratorService,
    )
    from app.domain.services.presentation_spec_compiler_service import (
        PresentationSpecCompilerService,
    )
    from app.domain.services.presentation_compilers.presentation_delivery_compiler_service import (
        PresentationDeliveryCompilerService,
    )

    rows = _stock_rows()

    # --- T1: table default ---
    case_id = "PC.T1.table_default"
    metadata = _base_metadata(rows=rows, user_message="Qual o estoque? Prefiro tabela.")
    started = time.perf_counter()
    summary = PresentationIntelligenceOrchestratorService.apply_before_render_plan(
        metadata,
        user_message=metadata["userMessage"],
    )
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    table = metadata.get("tablePresentation") or {}
    case_errors: list[str] = []
    if table.get("type") != "table":
        case_errors.append(f"type={table.get('type')}")
    if not table.get("rows"):
        case_errors.append("no_rows")
    labels = {
        col.get("label")
        for col in (table.get("columns") or [])
        if isinstance(col, dict) and col.get("label")
    }
    if not labels:
        case_errors.append("missing_column_labels")
    if case_errors:
        errors.extend(case_errors)
        _fail(case_id, "; ".join(case_errors))
    else:
        _ok(case_id, f"cols={len(table.get('columns') or [])} ms={elapsed_ms}")
    cases.append(
        {
            "id": case_id,
            "status": "FAIL" if case_errors else "PASS",
            "errors": case_errors,
            "elapsedMs": elapsed_ms,
            "summary": summary,
        }
    )

    # --- T2: 3 cols + sort desc ---
    case_id = "PC.T2.table_three_cols_sort"
    metadata = _base_metadata(
        rows=_matrix_rows(),
        user_message="Mostre só produto, depósito e qtd planejada do maior pro menor",
    )
    profile = PresentationDataProfileBuilderService.build(_matrix_rows())
    spec = PresentationSpec(
        view="table",
        fields=("product_code", "warehouse", "planned_qty"),
        sort_field="planned_qty",
        sort_direction="desc",
        labels={
            "product_code": "Produto",
            "warehouse": "Depósito",
            "planned_qty": "Qtd. planejada",
        },
        table=PresentationTableSpec(hidden_fields=("unit",), density="compact"),
    )
    started = time.perf_counter()
    PresentationSpecCompilerService.compile_into_metadata(
        metadata,
        spec=spec,
        profile=profile,
    )
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    table = metadata["tablePresentation"]
    column_keys = [col["key"] for col in table.get("columns") or []]
    case_errors = []
    if column_keys != ["product_code", "warehouse", "planned_qty"]:
        case_errors.append(f"columns={column_keys}")
    if table["rows"][0]["planned_qty"] < table["rows"][-1]["planned_qty"]:
        case_errors.append("sort_not_desc")
    if "unit" in column_keys:
        case_errors.append("unit_visible")
    if case_errors:
        errors.extend(case_errors)
        _fail(case_id, "; ".join(case_errors))
    else:
        _ok(case_id, f"cols={column_keys} top_qty={table['rows'][0]['planned_qty']}")
    cases.append(
        {
            "id": case_id,
            "status": "FAIL" if case_errors else "PASS",
            "errors": case_errors,
            "elapsedMs": elapsed_ms,
            "columnKeys": column_keys,
        }
    )

    # --- T3: bar chart ---
    case_id = "PC.T3.bar_chart"
    metadata = _base_metadata(
        rows=_matrix_rows(),
        user_message="Prefiro gráfico de barras por depósito",
    )
    metadata["presentationDecision"] = {"selected": "bar_chart", "layoutMode": "single"}
    started = time.perf_counter()
    summary = PresentationIntelligenceOrchestratorService.apply_before_render_plan(
        metadata,
        user_message=metadata["userMessage"],
    )
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    chart = metadata.get("chartPresentation") or {}
    case_errors = []
    if chart.get("type") != "chart":
        case_errors.append(f"missing_chart={chart.get('type')}")
    elif chart.get("chartType") not in {"bar", "grouped_bar", "stacked_bar"}:
        case_errors.append(f"chartType={chart.get('chartType')}")
    if not summary.get("specApplied"):
        case_errors.append("spec_not_applied")
    if case_errors:
        errors.extend(case_errors)
        _fail(case_id, "; ".join(case_errors))
    else:
        _ok(case_id, f"chartType={chart.get('chartType')} ms={elapsed_ms}")
    cases.append(
        {
            "id": case_id,
            "status": "FAIL" if case_errors else "PASS",
            "errors": case_errors,
            "elapsedMs": elapsed_ms,
            "chartType": chart.get("chartType"),
        }
    )

    # --- T4: heatmap blue ---
    case_id = "PC.T4.heatmap_blue"
    metadata = {
        "path": "/smoke/presentation-composer-multiview",
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
    config = chart.get("config") or {}
    case_errors = []
    if chart.get("chartType") != "heatmap":
        case_errors.append(f"chartType={chart.get('chartType')}")
    palette = config.get("paletteFamily")
    if palette not in {"sequential-blue", "cool", "brand"}:
        case_errors.append(f"paletteFamily={palette}")
    axes = {config.get("xAxis"), config.get("yAxis")}
    if "unit" in axes:
        case_errors.append("constant_unit_axis")
    if not summary.get("specApplied"):
        case_errors.append("spec_not_applied")
    if case_errors:
        errors.extend(case_errors)
        _fail(case_id, "; ".join(case_errors))
    else:
        _ok(
            case_id,
            f"palette={palette} axes={axes} value={config.get('valueKey')}",
        )
    cases.append(
        {
            "id": case_id,
            "status": "FAIL" if case_errors else "PASS",
            "errors": case_errors,
            "elapsedMs": elapsed_ms,
            "config": {
                "chartType": chart.get("chartType"),
                "paletteFamily": palette,
                "xAxis": config.get("xAxis"),
                "yAxis": config.get("yAxis"),
            },
        }
    )

    # --- T5: preferCanvas ---
    case_id = "PC.T5.prefer_canvas"
    metadata = _base_metadata(rows=rows, user_message="Coloque na lousa")
    metadata["presentationConstraints"] = {"preferCanvas": True}
    profile = PresentationDataProfileBuilderService.build(rows)
    spec = PresentationSpec(
        view="table",
        delivery=PresentationDeliverySpec(prefer_canvas=True),
    )
    started = time.perf_counter()
    PresentationSpecCompilerService.compile_into_metadata(
        metadata,
        spec=spec,
        profile=profile,
    )
    PresentationDeliveryCompilerService.apply(metadata, spec=spec)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    case_errors = []
    if metadata.get("deliveryPreferCanvas") is not True:
        case_errors.append("deliveryPreferCanvas_missing")
    canvas = metadata.get("canvasOpen")
    if not isinstance(canvas, dict) or not canvas.get("markdown"):
        case_errors.append("canvasOpen_missing")
    if "canvasPresentation" in metadata:
        case_errors.append("legacy_canvasPresentation")
    if case_errors:
        errors.extend(case_errors)
        _fail(case_id, "; ".join(case_errors))
    else:
        _ok(case_id, f"title={canvas.get('title')} ms={elapsed_ms}")
    cases.append(
        {
            "id": case_id,
            "status": "FAIL" if case_errors else "PASS",
            "errors": case_errors,
            "elapsedMs": elapsed_ms,
            "canvasTitle": canvas.get("title") if isinstance(canvas, dict) else None,
        }
    )

    return {"phase": "inprocess", "errors": errors, "cases": cases}


def phase_http() -> dict[str, Any]:
    """Optional HTTP phase — delegates to PI smoke when gateway available."""
    print("\n=== FASE http (delegated — optional) ===", flush=True)
    try:
        from scripts import smoke_presentation_intelligence_live as pi_smoke

        pi_smoke._PHASE = "http"
        result = pi_smoke.phase_http()
        return {"phase": "http", "delegated": True, **result}
    except Exception as exc:  # noqa: BLE001
        _fail("http_delegate", str(exc))
        return {"phase": "http", "errors": [str(exc)], "cases": []}


def _write_evidence(payload: dict[str, Any]) -> None:
    path = Path(_OUT)
    if not path.is_absolute():
        root = Path(__file__).resolve().parents[1]
        path = root / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nEvidence: {path}", flush=True)


def main() -> int:
    print(f"smoke_presentation_composer_multiview_live phase={_PHASE}", flush=True)
    phases: list[dict[str, Any]] = []
    hard_errors: list[str] = []

    if _PHASE in {"all", "inprocess"}:
        result = phase_inprocess()
        phases.append(result)
        hard_errors.extend(result.get("errors") or [])

    if _PHASE in {"all", "http"}:
        result = phase_http()
        phases.append(result)
        hard_errors.extend(result.get("errors") or [])

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "phase": _PHASE,
        "requiredDimensions": ["R5", "R9"],
        "turns": ["T1", "T2", "T3", "T4", "T5"],
        "phases": phases,
        "hardErrors": hard_errors,
    }
    payload["verdict"] = "FAIL" if hard_errors else "PASS"
    _write_evidence(payload)
    print(f"\nVERDICT={payload['verdict']}", flush=True)
    return 0 if payload["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
