"""Guardrails de consumer/schema para transforms em fonte compartilhada."""

from __future__ import annotations

import copy
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
    clear_presentation_ops_content_cache,
)
from tv_app.application.services.data.presentation_mutation import (
    PresentationPatchError,
    PresentationPatchService,
)
from tv_app.application.services.data.presentation_mutation_telemetry import (
    reset_presentation_mutation_telemetry,
)


ROL_ROUTE = {
    "operationId": "get_commercial_rol_summary",
    "label": "ROL comercial — resumo",
    "paramStrategy": "date_range",
    "dateRangeKeys": ["start_date", "end_date"],
    "openEndedDateRange": True,
    "paramSchema": {
        "start_date": {"type": "string", "optional": True},
        "end_date": {"type": "string", "optional": True},
    },
    "valueFields": ["branch", "segment", "rol", "comparable_goal", "rol_target_pct"],
}

_SOURCE = {
    "id": "src-1",
    "type": "data_source",
    "dataBinding": {
        "operationId": "get_commercial_rol_summary",
        "params": {},
        "label": "ROL",
    },
}


class _FakeCatalog:
    def get_route(self, operation_id: str):
        return {"get_commercial_rol_summary": ROL_ROUTE}.get(operation_id)


def _repo_with(blocks: list[dict[str, Any]]):
    playlist_id = str(uuid4())
    slide_id = str(uuid4())

    class _Repo:
        def get_by_id(self, pid):
            return {"id": str(pid), "revision": 1, "dataDefaults": {}}

        def get_slide(self, sid, playlist_id=None):
            return {
                "id": str(sid),
                "nativeConfig": {"version": 5, "blocks": copy.deepcopy(blocks)},
            }

    return _Repo(), playlist_id, slide_id


def _svc(repo) -> PresentationPatchService:
    return PresentationPatchService(catalog=_FakeCatalog(), repo=repo)


def _preview(svc, playlist_id, slide_id, ops):
    return svc.preview(
        {
            "target": {"playlistId": playlist_id, "slideId": slide_id},
            "ops": ops,
            "catalogVersion": PresentationOpsContentService.catalog_version(),
        },
        user=SimpleNamespace(is_superadmin=True, permissions=[], id="u1"),
    )


@pytest.fixture(autouse=True)
def _reset():
    reset_presentation_mutation_telemetry()
    clear_presentation_ops_content_cache()
    yield
    reset_presentation_mutation_telemetry()
    clear_presentation_ops_content_cache()


def test_set_transform_removing_bound_field_is_rejected():
    """select sem `rol` com kpi_view consumindo `rol` → erro antes de persistir."""
    repo, playlist_id, slide_id = _repo_with(
        [
            _SOURCE,
            {
                "id": "kpi-1",
                "type": "kpi_view",
                "dataSourceId": "src-1",
                "kpiProjection": {"metrics": [{"field": "rol"}]},
            },
        ]
    )
    with pytest.raises(PresentationPatchError) as exc:
        _preview(
            _svc(repo),
            playlist_id,
            slide_id,
            [
                {
                    "op": "set_data_transform",
                    "blockId": "src-1",
                    "steps": [{"op": "select", "columns": ["branch", "segment"]}],
                }
            ],
        )
    assert exc.value.code == "DATA_BINDING_FIELD_MISSING"
    assert "rol" in str(exc.value)


def test_set_transform_keeping_bound_field_passes():
    repo, playlist_id, slide_id = _repo_with(
        [
            _SOURCE,
            {
                "id": "kpi-1",
                "type": "kpi_view",
                "dataSourceId": "src-1",
                "kpiProjection": {"metrics": [{"field": "rol"}]},
            },
        ]
    )
    result = _preview(
        _svc(repo),
        playlist_id,
        slide_id,
        [
            {
                "op": "set_data_transform",
                "blockId": "src-1",
                "steps": [
                    {"op": "select", "columns": ["branch", "rol"]},
                    {"op": "addColumn", "name": "rol_x2", "expr": "rol * 2"},
                ],
            }
        ],
    )
    block = next(
        b for b in result["nativeConfig"]["blocks"] if b["id"] == "src-1"
    )
    assert len(block["dataTransform"]["steps"]) == 2


def test_shared_source_transform_breaking_other_consumer_is_rejected():
    """SOURCE compartilhada: transform para o card B não pode quebrar o card A."""
    repo, playlist_id, slide_id = _repo_with(
        [
            _SOURCE,
            {
                "id": "kpi-a",
                "type": "kpi_view",
                "dataSourceId": "src-1",
                "kpiProjection": {"metrics": [{"field": "rol"}]},
            },
            {
                "id": "txt-b",
                "type": "text",
                "dataSourceId": "src-1",
                "contentRuns": [{"dataRef": {"field": "rol_target_pct"}}],
            },
        ]
    )
    with pytest.raises(PresentationPatchError) as exc:
        _preview(
            _svc(repo),
            playlist_id,
            slide_id,
            [
                {
                    "op": "set_data_transform",
                    "blockId": "src-1",
                    "steps": [{"op": "select", "columns": ["rol"]}],
                }
            ],
        )
    assert exc.value.code == "DATA_BINDING_FIELD_MISSING"
    assert "txt-b" in exc.value.details["consumers"]


def test_transform_rename_of_bound_field_is_rejected():
    repo, playlist_id, slide_id = _repo_with(
        [
            _SOURCE,
            {
                "id": "txt-1",
                "type": "text",
                "dataSourceId": "src-1",
                "textProjection": {"field": "rol"},
            },
        ]
    )
    with pytest.raises(PresentationPatchError) as exc:
        _preview(
            _svc(repo),
            playlist_id,
            slide_id,
            [
                {
                    "op": "set_data_transform",
                    "blockId": "src-1",
                    "steps": [{"op": "rename", "from": "rol", "to": "rol_x"}],
                }
            ],
        )
    assert exc.value.code == "DATA_BINDING_FIELD_MISSING"


def test_transform_on_source_without_consumers_is_allowed():
    repo, playlist_id, slide_id = _repo_with([_SOURCE])
    result = _preview(
        _svc(repo),
        playlist_id,
        slide_id,
        [
            {
                "op": "set_data_transform",
                "blockId": "src-1",
                "steps": [{"op": "select", "columns": ["rol"]}],
            }
        ],
    )
    assert result["ok"] is True


def test_structural_transform_unknown_schema_with_consumers_is_rejected():
    """Schema indeterminável (fonte sem campos de rota declarados) + consumer
    + op estrutural → rejeita; não há como provar que o campo sobrevive."""
    source = {
        "id": "src-x",
        "type": "data_source",
        "dataBinding": {"operationId": "unknown_route", "params": {}},
    }
    repo, playlist_id, slide_id = _repo_with(
        [
            source,
            {
                "id": "txt-1",
                "type": "text",
                "dataSourceId": "src-x",
                "textProjection": {"field": "rol"},
            },
        ]
    )

    class _EmptyCatalog:
        def get_route(self, operation_id):
            return None

    svc = PresentationPatchService(catalog=_EmptyCatalog(), repo=repo)
    with pytest.raises(PresentationPatchError) as exc:
        _preview(
            svc,
            playlist_id,
            slide_id,
            [
                {
                    "op": "set_data_transform",
                    "blockId": "src-x",
                    "steps": [{"op": "rename", "from": "rol", "to": "r2"}],
                }
            ],
        )
    assert exc.value.code == "DATA_TRANSFORM_SCHEMA_UNKNOWN"


def test_upsert_data_source_transform_breaking_consumer_is_rejected():
    repo, playlist_id, slide_id = _repo_with(
        [
            _SOURCE,
            {
                "id": "kpi-1",
                "type": "kpi_view",
                "dataSourceId": "src-1",
                "kpiProjection": {"metrics": [{"field": "rol"}]},
            },
        ]
    )
    with pytest.raises(PresentationPatchError) as exc:
        _preview(
            _svc(repo),
            playlist_id,
            slide_id,
            [
                {
                    "op": "upsert_data_source",
                    "blockId": "src-1",
                    "operationId": "get_commercial_rol_summary",
                    "dataTransform": {
                        "steps": [{"op": "select", "columns": ["branch"]}]
                    },
                }
            ],
        )
    assert exc.value.code == "DATA_BINDING_FIELD_MISSING"


def test_upsert_block_binding_against_transformed_schema():
    """Consumer novo valida refs contra schema de saída da fonte (não a rota)."""
    transformed = dict(_SOURCE)
    transformed["dataTransform"] = {
        "steps": [
            {"op": "rename", "from": "rol", "to": "rol_prev"},
            {"op": "addColumn", "name": "rol_calc", "expr": "rol_prev * 2"},
        ]
    }
    repo, playlist_id, slide_id = _repo_with([transformed])
    svc = _svc(repo)

    # Campo removido pelo transform → binding inválido.
    with pytest.raises(PresentationPatchError) as exc:
        _preview(
            svc,
            playlist_id,
            slide_id,
            [
                {
                    "op": "upsert_block",
                    "createIfMissing": True,
                    "block": {
                        "id": "txt-new",
                        "type": "text",
                        "dataSourceId": "src-1",
                        "textProjection": {"field": "rol"},
                    },
                }
            ],
        )
    assert exc.value.code == "INVALID_PROJECTION_FIELD"

    # Campo derivado que só existe pós-transform → binding válido.
    result = _preview(
        svc,
        playlist_id,
        slide_id,
        [
            {
                "op": "upsert_block",
                "createIfMissing": True,
                "block": {
                    "id": "txt-new",
                    "type": "text",
                    "dataSourceId": "src-1",
                    "textProjection": {"field": "rol_calc"},
                },
            }
        ],
    )
    block = next(
        b for b in result["nativeConfig"]["blocks"] if b["id"] == "txt-new"
    )
    assert block["textProjection"]["field"] == "rol_calc"


def test_add_column_shadowing_route_field_is_rejected():
    """AUTHORITATIVE ROUTE FIELD > DERIVED: recalcular rol_target_pct quando a
    rota já o fornece deve ser rejeitado na mutation (não só em runtime)."""
    repo, playlist_id, slide_id = _repo_with([_SOURCE])
    with pytest.raises(PresentationPatchError) as exc:
        _preview(
            _svc(repo),
            playlist_id,
            slide_id,
            [
                {
                    "op": "set_data_transform",
                    "blockId": "src-1",
                    "steps": [
                        {
                            "op": "addColumn",
                            "name": "rol_target_pct",
                            "expr": "rol / comparable_goal * 100",
                        }
                    ],
                }
            ],
        )
    assert exc.value.code == "DATA_FIELD_AUTHORITATIVE"
    assert exc.value.details["field"] == "rol_target_pct"


def test_add_column_new_field_is_allowed():
    repo, playlist_id, slide_id = _repo_with([_SOURCE])
    result = _preview(
        _svc(repo),
        playlist_id,
        slide_id,
        [
            {
                "op": "set_data_transform",
                "blockId": "src-1",
                "steps": [
                    {
                        "op": "addColumn",
                        "name": "rol_share",
                        "expr": "rol * 2",
                    }
                ],
            }
        ],
    )
    assert result["ok"] is True


def test_invalid_transform_step_is_rejected_not_dropped():
    """Step malformado não pode sumir na sanitização (modelo ≠ intenção)."""
    repo, playlist_id, slide_id = _repo_with([_SOURCE])
    with pytest.raises(PresentationPatchError):
        _preview(
            _svc(repo),
            playlist_id,
            slide_id,
            [
                {
                    "op": "set_data_transform",
                    "blockId": "src-1",
                    "dataTransform": {
                        "steps": [
                            {"op": "keepRows", "count": 1},
                            {"op": "merge", "sourceId": "other"},  # sem keys
                        ]
                    },
                }
            ],
        )
