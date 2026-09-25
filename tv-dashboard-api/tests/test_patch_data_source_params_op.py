"""patch_data_source_params — patch atomico de params de data_source existente."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from tv_app.application.services.data.presentation_ops_content_service import (
    clear_presentation_ops_content_cache,
)
from tv_app.application.services.data.presentation_mutation import (
    PresentationPatchError,
    PresentationPatchService,
)
from tv_app.application.services.data.presentation_mutation_telemetry import (
    reset_presentation_mutation_telemetry,
)


SLIDE_ID = "11111111-1111-1111-1111-111111111111"
PLAYLIST_ID = "00000000-0000-0000-0000-000000000001"

ROL_ROUTE = {
    "operationId": "get_commercial_rol_summary",
    "label": "ROL comercial — resumo",
    "paramStrategy": "date_range",
    "dateRangeKeys": ["start_date", "end_date"],
    "openEndedDateRange": False,
    "paramSchema": {
        "branch": {"type": "string", "optional": True},
        "customer_segment": {"type": "string", "optional": True},
        "start_date": {"type": "string", "optional": True},
        "end_date": {"type": "string", "optional": True},
    },
}

_SOURCE_BLOCK = {
    "id": "rx_tot_y26",
    "type": "data_source",
    "frame": {"x": 10, "y": 20, "w": 30, "h": 40},
    "dataBinding": {
        "operationId": "get_commercial_rol_summary",
        "params": {
            "dateRangePreset": "custom",
            "start_date": "2026-01-01",
            "end_date": "2026-09-24",
            "branch": "01",
        },
        "displayMode": "kpi",
        "label": "ROL acumulado 2026",
        "refreshSec": 120,
    },
    "dataTransform": {"steps": [{"op": "keepRows", "count": 1, "from": "top"}]},
    "fieldLabels": {"rol": "ROL"},
}


class _FakeCatalog:
    def __init__(self, routes: dict[str, dict]) -> None:
        self._routes = routes

    def get_route(self, operation_id: str):
        return self._routes.get(operation_id)


class _FakeRepo:
    def __init__(self) -> None:
        self.slides: dict[str, dict[str, Any]] = {
            SLIDE_ID: {
                "id": SLIDE_ID,
                "title": "Realizado 2025 x 2026 - Cards",
                "durationSec": 30,
                "isActive": True,
                "nativeConfig": {
                    "version": 5,
                    "blocks": [
                        copy.deepcopy(_SOURCE_BLOCK),
                        {"id": "kpi-1", "type": "kpi_view", "dataSourceId": "rx_tot_y26"},
                    ],
                },
            }
        }
        self.updated: list[dict[str, Any]] = []

    def get_slide(self, slide_id, *, playlist_id=None):
        from tv_app.infrastructure.persistence.repositories.playlist_repository import (
            SlideNotFoundError,
        )

        key = str(slide_id)
        if key not in self.slides:
            raise SlideNotFoundError(key)
        return copy.deepcopy(self.slides[key])

    def get_by_id(self, playlist_id):
        return {"id": str(playlist_id), "dataDefaults": {}, "revision": 7}

    def get_revision(self, playlist_id):
        return 7


@pytest.fixture(autouse=True)
def _reset():
    reset_presentation_mutation_telemetry()
    clear_presentation_ops_content_cache()
    yield
    reset_presentation_mutation_telemetry()
    clear_presentation_ops_content_cache()


def _service(repo: _FakeRepo | None = None) -> PresentationPatchService:
    return PresentationPatchService(
        catalog=_FakeCatalog({"get_commercial_rol_summary": ROL_ROUTE}),
        repo=repo or _FakeRepo(),
    )


def _preview(svc: PresentationPatchService, op: dict[str, Any]) -> dict[str, Any]:
    return svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [op],
        },
        user={"sub": "u1"},
        authorization="Bearer x",
    )


def _source_block(result: dict[str, Any]) -> dict[str, Any]:
    return next(
        block
        for block in result["nativeConfig"]["blocks"]
        if block["id"] == "rx_tot_y26"
    )


def test_patch_spec_example_custom_to_this_year():
    """Contrato do spec: custom+datas + set preset + unset datas → só o preset."""
    result = _preview(
        _service(),
        {
            "op": "patch_data_source_params",
            "blockId": "rx_tot_y26",
            "set": {"dateRangePreset": "this_year"},
            "unset": ["start_date", "end_date"],
        },
    )
    assert result["ok"] is True
    params = _source_block(result)["dataBinding"]["params"]
    assert params == {"dateRangePreset": "this_year", "branch": "01"}

    patch_report = result["sideEffects"]["dataSourceParamPatches"][0]
    assert patch_report["blockId"] == "rx_tot_y26"
    assert patch_report["changed"]["set"] == {"dateRangePreset": "this_year"}
    assert "custom" not in params.values()


def test_patch_preserves_block_identity_and_siblings():
    """operationId/transforms/bindings/layout/label/displayMode/refreshSec intactos."""
    result = _preview(
        _service(),
        {
            "op": "patch_data_source_params",
            "blockId": "rx_tot_y26",
            "set": {"dateRangePreset": "same_period_previous_year"},
        },
    )
    block = _source_block(result)
    assert block["frame"] == _SOURCE_BLOCK["frame"]
    assert block["dataTransform"] == _SOURCE_BLOCK["dataTransform"]
    assert block["fieldLabels"] == _SOURCE_BLOCK["fieldLabels"]
    binding = block["dataBinding"]
    assert binding["operationId"] == "get_commercial_rol_summary"
    assert binding["displayMode"] == "kpi"
    assert binding["label"] == "ROL acumulado 2026"
    assert binding["refreshSec"] == 120
    kpi = next(b for b in result["nativeConfig"]["blocks"] if b["id"] == "kpi-1")
    assert kpi["dataSourceId"] == "rx_tot_y26"


def test_patch_preset_alone_removes_stale_dates_without_unset():
    """Intenção de período é atômica: set preset já remove datas stale."""
    result = _preview(
        _service(),
        {
            "op": "patch_data_source_params",
            "blockId": "rx_tot_y26",
            "set": {"dateRangePreset": "this_month_full"},
        },
    )
    params = _source_block(result)["dataBinding"]["params"]
    assert params == {"dateRangePreset": "this_month_full", "branch": "01"}


def test_patch_idempotent_same_end_state():
    svc = _service()
    op = {
        "op": "patch_data_source_params",
        "blockId": "rx_tot_y26",
        "set": {"dateRangePreset": "this_year"},
        "unset": ["start_date", "end_date"],
    }
    first = _source_block(_preview(svc, op))["dataBinding"]["params"]
    second = _source_block(_preview(svc, op))["dataBinding"]["params"]
    assert first == second == {"dateRangePreset": "this_year", "branch": "01"}


def test_patch_rejects_unknown_param_key():
    with pytest.raises(PresentationPatchError, match="não aceita"):
        _preview(
            _service(),
            {
                "op": "patch_data_source_params",
                "blockId": "rx_tot_y26",
                "set": {"not_a_real_param": "x"},
            },
        )


def test_patch_rejects_unknown_block():
    with pytest.raises(PresentationPatchError, match="rx_missing"):
        _preview(
            _service(),
            {
                "op": "patch_data_source_params",
                "blockId": "rx_missing",
                "set": {"dateRangePreset": "this_year"},
            },
        )


def test_patch_rejects_non_primitive_set_value():
    """Payload aninhado fora do inputSchema falha no contrato antes do reducer."""
    with pytest.raises(PresentationPatchError, match="inválido"):
        _preview(
            _service(),
            {
                "op": "patch_data_source_params",
                "blockId": "rx_tot_y26",
                "set": {"branch": ["01", "02"]},
            },
        )


def test_patch_empty_value_in_set_behaves_as_unset():
    result = _preview(
        _service(),
        {
            "op": "patch_data_source_params",
            "blockId": "rx_tot_y26",
            "set": {"start_date": "", "end_date": "", "dateRangePreset": "this_year"},
        },
    )
    params = _source_block(result)["dataBinding"]["params"]
    assert params == {"dateRangePreset": "this_year", "branch": "01"}


def test_patch_legacy_alias_remapped_to_canonical_key():
    result = _preview(
        _service(),
        {
            "op": "patch_data_source_params",
            "blockId": "rx_tot_y26",
            "set": {
                "dateRangePreset": "custom",
                "dataInicio": "2026-01-01",
                "dataFim": "2026-09-24",
            },
            "unset": ["start_date", "end_date"],
        },
    )
    params = _source_block(result)["dataBinding"]["params"]
    assert params["start_date"] == "2026-01-01"
    assert params["end_date"] == "2026-09-24"
    assert "dataInicio" not in params and "dataFim" not in params


def test_patch_only_unset_keeps_period_intent_custom():
    result = _preview(
        _service(),
        {
            "op": "patch_data_source_params",
            "blockId": "rx_tot_y26",
            "unset": ["dateRangePreset"],
        },
    )
    params = _source_block(result)["dataBinding"]["params"]
    # Sem preset, datas explícitas permanecem = intenção custom.
    assert params["start_date"] == "2026-01-01"
    assert params["end_date"] == "2026-09-24"
    assert "dateRangePreset" not in params
