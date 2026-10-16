"""Deterministic DATA_DIAGNOSIS evaluator — drives each corpus case through
the OWNER service that produces the diagnosis, then classifies the observed
surface against the frozen expectation.

Eval/test code only. No production diagnosis logic is duplicated here:
preview cases go through GptActionsDispatchService.preview_data_block with
a deterministic gateway double; binding cases through
PresentationPatchService.preview; DataModel through inspect_data_model;
filter layering through FilterDigestService; route-miss delegates to the
frozen P6 evaluator; the cross-boundary case asserts methodology ownership
in the frozen P5 corpus.
"""

from __future__ import annotations

import copy
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.services.comunicado_data_enrichment_service import (
    ComunicadoDataEnrichmentService,
    reset_comunicado_data_block_cache,
)
from tv_app.application.services.data.filter_digest_service import (
    FilterDigestService,
)
from tv_app.application.services.data.presentation_mutation import (
    PresentationPatchError,
    PresentationPatchService,
)
from tv_app.application.services.data.slide_data_resolution_service import (
    SlideDataResolutionService,
)
from tv_app.application.services.data.tv_data_preview_service import (
    TvDataPreviewService,
)
from tv_app.application.services.playlist_access_service import PlaylistAccess
from tv_app.application.services.tv_data_route_catalog_service import (
    TvDataRouteCatalogService,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
    clear_presentation_ops_content_cache,
)
from tv_app.application.services.data.presentation_mutation_telemetry import (
    reset_presentation_mutation_telemetry,
)

from tests.data_diagnosis_corpus import (
    DATA_DIAGNOSIS_CORPUS,
    NEXT_STEP_ALLOWED,
)
from tests.design_methodology_corpus import CORPUS as P5_CORPUS
from tests.run_solution_intelligence_eval import evaluate_case as p6_evaluate
from tests.solution_intelligence_corpus import P6_CORPUS

_ERROR_CLASSES = {
    "PARAM_REQUIRED",
    "PARAM_INVALID",
    "BINDING_FIELD_MISSING",
    "MODEL_NOT_FOUND",
    "TRANSFORM_ERROR",
    "RUNTIME_SOURCE_ERROR",
}
_CODE_TO_DIAGNOSIS = {
    "PARAM_REQUIRED": "PARAM_REQUIRED",
    "PARAM_INVALID": "PARAM_INVALID",
    "DATA_BINDING_FIELD_MISSING": "BINDING_FIELD_MISSING",
    "RESOURCE_NOT_FOUND": "MODEL_NOT_FOUND",
}


def _user():
    return SimpleNamespace(is_superadmin=True, permissions=[], id="actor-1")


def _dispatch(payloads=None, fails=None, *, catalog=None, slides=None):
    """Owner-level dispatch with a deterministic gateway double."""
    gateway = MagicMock()

    def _fetch(operation_id, params=None, **kw):
        if fails and operation_id in fails:
            exc = fails[operation_id]
            raise exc if isinstance(exc, Exception) else Exception(str(exc))
        return (payloads or {}).get(operation_id)

    gateway.fetch_by_operation_id.side_effect = _fetch
    cat = catalog or TvDataRouteCatalogService()
    enrichment = ComunicadoDataEnrichmentService(catalog=cat, gateway=gateway)
    preview = TvDataPreviewService(
        catalog=cat,
        enrichment=enrichment,
        resolution=SlideDataResolutionService(catalog=cat, enrichment=enrichment),
    )
    writes = MagicMock()
    writes.list_slides.return_value = list(slides or [])
    writes.get_slide.side_effect = lambda slide_id, playlist_id=None: (
        next(
            (s for s in (slides or []) if str(s.get("id")) == str(slide_id)),
            None,
        )
        or (_ for _ in ()).throw(Exception("slide not found"))
    )
    access = MagicMock()
    access.resolve.return_value = PlaylistAccess(
        level="owner", playlist={"id": "pl", "dataDefaults": {}}
    )
    access.actor_id.return_value = "actor-1"
    return GptActionsDispatchService(
        repo=MagicMock(),
        writes=writes,
        commit=MagicMock(),
        access=access,
        preview=preview,
        catalog=cat,
    )


class _FakeCatalog:
    def __init__(self, routes):
        self._routes = dict(routes)

    def get_route(self, operation_id: str):
        return self._routes.get(operation_id)


def _observe_preview(case: dict) -> dict:
    fx = case["fixture"]
    catalog = None
    if fx.get("route"):
        catalog = _FakeCatalog({fx["operationId"]: fx["route"]})
    dispatch = _dispatch(
        fx.get("payloads") or {}, fx.get("fails"), catalog=catalog
    )
    if fx.get("operationId"):
        body = {
            "operationId": fx["operationId"],
            "params": fx.get("params") or {},
        }
    else:
        block = fx["block"]
        body = {
            "block": block,
            "nativeConfig": {"version": 5, "blocks": [block]},
        }
    try:
        result = dispatch.preview_data_block(
            user=_user(), body=body, authorization=None
        )
    except GptActionsError as exc:
        code = getattr(exc, "code", None)
        return {
            "diagnosis": _CODE_TO_DIAGNOSIS.get(code, "UNTYPED_ERROR"),
            "code": code,
            "stage": None,
            "rows": 0,
        }
    error = result.get("error") if isinstance(result.get("error"), dict) else None
    block = result.get("block") if isinstance(result.get("block"), dict) else {}
    rows = len(GptActionsDispatchService._rows_from_preview_block(block))
    if error:
        stage = str(error.get("stage") or "")
        diagnosis = (
            "TRANSFORM_ERROR" if stage == "transform" else "RUNTIME_SOURCE_ERROR"
        )
        return {
            "diagnosis": diagnosis,
            "code": error.get("code"),
            "stage": stage,
            "rows": rows,
        }
    return {
        "diagnosis": "HEALTHY_DATA" if rows > 0 else "EMPTY_RESULT",
        "code": None,
        "stage": None,
        "rows": rows,
    }


def _observe_binding(case: dict) -> dict:
    fx = case["fixture"]
    reset_presentation_mutation_telemetry()
    clear_presentation_ops_content_cache()
    playlist_id = str(uuid4())
    slide_id = str(uuid4())
    blocks = [fx["source_block"], fx["consumer_block"]]

    class _Repo:
        def get_by_id(self, pid):
            return {"id": str(pid), "revision": 1, "dataDefaults": {}}

        def get_slide(self, sid, playlist_id=None):
            return {
                "id": str(sid),
                "nativeConfig": {"version": 5, "blocks": copy.deepcopy(blocks)},
            }

    class _FakeResolution:
        def resolve_blocks(self, items, **kwargs):
            out = []
            for item in items:
                entry = dict(item)
                entry["resolved"] = {}
                out.append(entry)
            return out

    svc = PresentationPatchService(
        catalog=_FakeCatalog({}),
        repo=_Repo(),
        resolution=_FakeResolution(),
    )
    try:
        svc.preview(
            {
                "target": {"playlistId": playlist_id, "slideId": slide_id},
                "ops": fx["ops"],
                "catalogVersion": PresentationOpsContentService.catalog_version(),
            },
            user=SimpleNamespace(is_superadmin=True, permissions=[], id="u1"),
        )
    except PresentationPatchError as exc:
        code = getattr(exc, "code", None)
        return {
            "diagnosis": _CODE_TO_DIAGNOSIS.get(code, "UNTYPED_ERROR"),
            "code": code,
            "stage": None,
            "rows": 0,
        }
    finally:
        reset_presentation_mutation_telemetry()
        clear_presentation_ops_content_cache()
    return {"diagnosis": "HEALTHY_DATA", "code": None, "stage": None, "rows": 0}


def _observe_model(case: dict) -> dict:
    slide_id = str(uuid4())
    slides = [
        {"id": slide_id, "nativeConfig": {"version": 5, "blocks": []}}
    ]
    dispatch = _dispatch(slides=slides)
    try:
        dispatch.inspect_data_model(
            user=_user(),
            playlist_id=str(uuid4()),
            slide_id=slide_id,
            model_id=case["fixture"]["modelId"],
            authorization=None,
        )
    except GptActionsError as exc:
        code = getattr(exc, "code", None)
        return {
            "diagnosis": _CODE_TO_DIAGNOSIS.get(code, "UNTYPED_ERROR"),
            "code": code,
            "stage": None,
            "rows": 0,
        }
    return {"diagnosis": "HEALTHY_DATA", "code": None, "stage": None, "rows": 0}


def _observe_filter_digest(case: dict) -> dict:
    fx = case["fixture"]
    digest = FilterDigestService.digest_slide(
        fx["native_config"],
        programming_defaults=fx.get("programming_defaults"),
    )
    hints = digest.get("wrongLayerHints") or []
    return {
        "diagnosis": "WRONG_LAYER_FILTER" if hints else "HEALTHY_DATA",
        "code": None,
        "stage": None,
        "rows": 0,
        "hints": list(hints),
    }


def _observe_route_miss(case: dict) -> dict:
    case_id = case["fixture"]["p6_case_id"]
    p6_case = next((c for c in P6_CORPUS if c["id"] == case_id), None)
    if p6_case is None:
        return {"diagnosis": "UNTYPED_ERROR", "code": None, "stage": None, "rows": 0}
    row = p6_evaluate(p6_case)
    ok = (
        not row["raised"]
        and row["miss_invariant"]
        and row["gap"] is not None
    )
    return {
        "diagnosis": "ROUTE_MISS_NOT_ABSENCE" if ok else "FALSE_ABSENCE",
        "code": row.get("gap"),
        "stage": None,
        "rows": 0,
    }


def _observe_cross_boundary(case: dict) -> dict:
    case_id = case["fixture"]["p5_case_id"]
    p5_case = next((c for c in P5_CORPUS if c["id"] == case_id), None)
    if p5_case is None:
        return {"diagnosis": "UNTYPED_ERROR", "code": None, "stage": None, "rows": 0}
    methodology_keys = {
        "family_in",
        "family_not_in",
        "readiness",
        "readiness_in",
        "fabricated",
        "evidence_level_in",
    }
    owned = bool(set(p5_case.get("expect") or {}) & methodology_keys)
    return {
        "diagnosis": "CROSS_BOUNDARY_DESIGN" if owned else "UNTYPED_ERROR",
        "code": None,
        "stage": None,
        "rows": 0,
    }


_OBSERVERS = {
    "preview": _observe_preview,
    "binding": _observe_binding,
    "model": _observe_model,
    "filter_digest": _observe_filter_digest,
    "route_miss": _observe_route_miss,
    "cross_boundary": _observe_cross_boundary,
}


def evaluate_case(case: dict) -> dict:
    """Run one case through its owner and classify against expectation."""
    reset_comunicado_data_block_cache()
    try:
        observed = _OBSERVERS[case["kind"]](case)
    finally:
        reset_comunicado_data_block_cache()
    exp = case["expect"]
    failures: list[str] = []
    obs_diag = observed["diagnosis"]

    if obs_diag != exp["diagnosis"]:
        if exp["diagnosis"] == "EMPTY_RESULT" and obs_diag in _ERROR_CLASSES:
            failures.append("FALSE_EMPTY_AS_ERROR")
        elif exp["diagnosis"] in _ERROR_CLASSES and obs_diag in {
            "EMPTY_RESULT",
            "HEALTHY_DATA",
        }:
            failures.append("FALSE_ERROR_AS_EMPTY")
        elif exp["diagnosis"] == "ROUTE_MISS_NOT_ABSENCE":
            failures.append("FALSE_ABSENCE")
        else:
            failures.append("WRONG_DIAGNOSIS")
    if obs_diag == "UNTYPED_ERROR":
        if "UNTYPED_ERROR" not in failures:
            failures.append("UNTYPED_ERROR")
    elif exp.get("code") and observed.get("code") != exp["code"]:
        failures.append("UNTYPED_ERROR")
    if exp.get("stage") and observed.get("stage") != exp["stage"]:
        failures.append("WRONG_STAGE")
    if "min_rows" in exp and observed.get("rows", 0) < exp["min_rows"]:
        failures.append("WRONG_ROW_COUNT")
    if "max_rows" in exp and observed.get("rows", 0) > exp["max_rows"]:
        failures.append("WRONG_ROW_COUNT")
    if "hint_prefix" in exp and not any(
        str(h).startswith(exp["hint_prefix"]) for h in observed.get("hints") or []
    ):
        failures.append("WRONG_HINT")
    if exp.get("next_step") and (
        exp["next_step"]
        not in NEXT_STEP_ALLOWED.get(obs_diag, set())
    ):
        failures.append("WRONG_NEXT_STEP")
    return {
        "caseId": case["caseId"],
        "ok": not failures,
        "expected": exp["diagnosis"],
        "observed": obs_diag,
        "observedCode": observed.get("code"),
        "observedStage": observed.get("stage"),
        "failures": failures,
    }


_SAFETY_COUNTERS = (
    "FALSE_EMPTY_AS_ERROR",
    "FALSE_ERROR_AS_EMPTY",
    "FALSE_ABSENCE",
    "UNTYPED_ERROR",
    "WRONG_NEXT_STEP",
)


def evaluate_all() -> dict:
    rows = [evaluate_case(case) for case in DATA_DIAGNOSIS_CORPUS]
    counters = {key: 0 for key in _SAFETY_COUNTERS}
    for row in rows:
        for flag in row["failures"]:
            if flag in counters:
                counters[flag] += 1
    return {
        "passed": sum(1 for row in rows if row["ok"]),
        "total": len(rows),
        "safety": counters,
        "failures": [
            {
                "caseId": row["caseId"],
                "expected": row["expected"],
                "observed": row["observed"],
                "observedCode": row["observedCode"],
                "flags": row["failures"],
            }
            for row in rows
            if not row["ok"]
        ],
    }
