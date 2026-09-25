"""Persistência canônica do período: uma única intenção por camada.

Cobre normalize_period_params_for_persistence / merge_period_params_layer —
boundary compartilhado por editor, VISTA/GPT e dataDefaults de playlist.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

from tv_app.application.services.data.tv_data_binding_hydrate_service import (
    hydrate_comunicado_data_bindings,
    hydrate_data_binding,
)
from tv_app.application.services.tv_date_range_preset_service import (
    merge_period_params_layer,
    normalize_period_params_for_persistence,
    params_declare_period_intent,
)


class _FakeCatalog:
    def __init__(self, routes: dict[str, dict]) -> None:
        self._routes = routes

    def get_route(self, operation_id: str) -> dict[str, Any] | None:
        return self._routes.get(operation_id)


_ROL_ROUTE = {
    "operationId": "get_commercial_rol_summary",
    "paramSchema": {
        "start_date": {"type": "string"},
        "end_date": {"type": "string"},
        "branch": {"type": "string", "optional": True},
    },
}


def test_normalize_dynamic_preset_clears_stale_custom_dates():
    """Preset dinâmico + datas «Personalizado» stale → só o preset persiste."""
    out = normalize_period_params_for_persistence(
        {
            "dateRangePreset": "this_year",
            "start_date": "2026-01-01",
            "end_date": "2026-09-24",
            "branch": "01",
        }
    )
    assert out == {"dateRangePreset": "this_year", "branch": "01"}


def test_normalize_dynamic_preset_clears_all_date_aliases():
    """Aliases legados (dataInicio/date_start/issue_date_start/…) também saem."""
    out = normalize_period_params_for_persistence(
        {
            "dateRangePreset": "this_year",
            "start_date": "2026-01-01",
            "end_date": "2026-09-24",
            "date_start": "2026-01-01",
            "date_end": "2026-09-24",
            "dataInicio": "2026-01-01",
            "dataFim": "2026-09-24",
            "issue_date_start": "2026-01-01",
            "issue_date_end": "2026-09-24",
            "modified_from": "2026-01-01",
            "modified_to": "2026-09-24",
            "from": "2026-01-01",
            "to": "2026-09-24",
            "competence": "202609",
            "branch": "01",
        }
    )
    assert out == {"dateRangePreset": "this_year", "branch": "01"}


def test_normalize_custom_preset_keeps_dates():
    params = {
        "dateRangePreset": "custom",
        "start_date": "2026-01-01",
        "end_date": "2026-06-30",
        "branch": "01",
    }
    assert normalize_period_params_for_persistence(params) == params


def test_normalize_no_preset_keeps_explicit_dates():
    """Datas explícitas sem preset são intenção custom canônica — preservar."""
    params = {"start_date": "2026-01-10", "end_date": "2026-02-20", "branch": "01"}
    assert normalize_period_params_for_persistence(params) == params


def test_normalize_unknown_preset_keeps_dates():
    """Preset inválido não pode destruir datas custom (evitar perda silenciosa)."""
    params = {
        "dateRangePreset": "bogus",
        "start_date": "2026-01-01",
        "end_date": "2026-06-30",
    }
    assert normalize_period_params_for_persistence(params) == params


def test_normalize_period_days_beats_stale_preset():
    """Mesmo blob com this_month + periodDays → periodDays vence (parity com merge)."""
    out = normalize_period_params_for_persistence(
        {"dateRangePreset": "this_month", "periodDays": 7, "branch": "01"}
    )
    assert out == {"periodDays": 7, "branch": "01"}


def test_normalize_last_n_days_keeps_period_days():
    """«Últimos N dias»: preset e N são a mesma intenção — coexistem."""
    out = normalize_period_params_for_persistence(
        {
            "dateRangePreset": "last_n_days",
            "periodDays": 10,
            "start_date": "2026-01-01",
            "end_date": "2026-09-24",
        }
    )
    assert out == {"dateRangePreset": "last_n_days", "periodDays": 10}


def test_normalize_dynamic_preset_drops_competence():
    """Competência SI não convive com preset relativo (parity com merge runtime)."""
    out = normalize_period_params_for_persistence(
        {"dateRangePreset": "previous_month", "competence": "202608"}
    )
    assert out == {"dateRangePreset": "previous_month"}


def test_params_declare_period_intent():
    assert params_declare_period_intent({"dateRangePreset": "this_year"}) is True
    assert params_declare_period_intent({"dateRangePreset": "custom"}) is True
    assert params_declare_period_intent({"start_date": "2026-01-01"}) is True
    assert params_declare_period_intent({"end_date": "2026-06-30"}) is True
    assert params_declare_period_intent({"periodDays": 7}) is True
    assert params_declare_period_intent({"branch": "01"}) is False
    assert params_declare_period_intent({"competence": "202609"}) is False
    assert params_declare_period_intent({"dateRangePreset": ""}) is False
    assert params_declare_period_intent(None) is False
    assert params_declare_period_intent("bad") is False


def test_merge_layer_preset_patch_clears_base_dates():
    """VISTA/UI manda só {this_year} sobre blob com datas custom → datas saem."""
    out = merge_period_params_layer(
        {
            "dateRangePreset": "custom",
            "start_date": "2026-09-01",
            "end_date": "2026-09-20",
            "branch": "01",
        },
        {"dateRangePreset": "this_year"},
    )
    assert out == {"dateRangePreset": "this_year", "branch": "01"}


def test_merge_layer_dates_patch_clears_base_preset():
    """Patch com datas explícitas (custom implícito) substitui preset do blob base."""
    out = merge_period_params_layer(
        {"dateRangePreset": "this_month_full", "branch": "01"},
        {"start_date": "2026-01-01", "end_date": "2026-06-30"},
    )
    assert out == {"start_date": "2026-01-01", "end_date": "2026-06-30", "branch": "01"}


def test_merge_layer_patch_without_period_keeps_base_period():
    """Patch sem período não destrói a intenção de período do blob base."""
    out = merge_period_params_layer(
        {"dateRangePreset": "this_year", "branch": "01"},
        {"branch": "02"},
    )
    assert out == {"dateRangePreset": "this_year", "branch": "02"}


def test_merge_layer_preset_patch_clears_period_days_and_competence():
    out = merge_period_params_layer(
        {"periodDays": 30, "competence": "202608", "branch": "01"},
        {"dateRangePreset": "this_year"},
    )
    assert out == {"dateRangePreset": "this_year", "branch": "01"}


def test_hydrate_dynamic_preset_clears_stale_custom_dates():
    """VISTA/merge pode gravar this_year + start/end antigos — hydrate limpa."""
    binding, _diag = hydrate_data_binding(
        {
            "operationId": "get_commercial_rol_summary",
            "params": {
                "dateRangePreset": "this_year",
                "start_date": "2026-09-01",
                "end_date": "2026-09-20",
                "branch": "01",
            },
        },
        _ROL_ROUTE,
    )
    assert binding["params"] == {"dateRangePreset": "this_year", "branch": "01"}


def test_hydrate_custom_preset_keeps_manual_dates():
    binding, _diag = hydrate_data_binding(
        {
            "operationId": "get_commercial_rol_summary",
            "params": {
                "dateRangePreset": "custom",
                "start_date": "2026-01-01",
                "end_date": "2026-06-30",
            },
        },
        _ROL_ROUTE,
    )
    assert binding["params"]["start_date"] == "2026-01-01"
    assert binding["params"]["end_date"] == "2026-06-30"
    assert binding["params"]["dateRangePreset"] == "custom"


def test_hydrate_data_filters_clears_stale_dates_with_preset():
    """dataFilters (filtros da tela) passam pelo mesmo normalizador de período."""
    catalog = _FakeCatalog({"get_ok": dict(_ROL_ROUTE, operationId="get_ok")})
    cfg, _summary = hydrate_comunicado_data_bindings(
        {
            "blocks": [
                {
                    "id": "a",
                    "type": "data_source",
                    "dataBinding": {"operationId": "get_ok", "params": {}},
                }
            ],
            "dataFilters": {
                "dateRangePreset": "same_period_previous_year",
                "start_date": "2026-09-01",
                "end_date": "2026-09-20",
                "branch": "01",
            },
        },
        catalog=catalog,
    )
    assert cfg["dataFilters"] == {
        "dateRangePreset": "same_period_previous_year",
        "branch": "01",
    }


def test_patch_playlist_data_defaults_persist_clears_stale_dates(monkeypatch):
    """Write boundary: dataDefaults com preset dinâmico não guarda datas stale."""
    from tv_app.application.services.tv_presentation_write_service import (
        TvPresentationWriteService,
    )

    playlist_id = uuid4()
    saved: list[dict[str, Any]] = []
    repo = MagicMock()
    repo.get_revision.return_value = 3
    repo.get_by_id.return_value = {
        "id": str(playlist_id),
        "revision": 3,
        "dataDefaults": {
            "dateRangePreset": "custom",
            "start_date": "2026-09-01",
            "end_date": "2026-09-20",
            "branch": "01",
        },
    }
    repo.update_data_defaults.side_effect = lambda _pid, defaults, **_kw: saved.append(
        defaults
    ) or {"id": str(playlist_id), "dataDefaults": defaults}

    monkeypatch.setattr(
        "tv_app.application.services.tv_presentation_write_service.notify_presentation_changed",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "tv_app.application.services.presentation_change_notifier.notify_playlist_library_changed",
        lambda **kwargs: None,
    )

    writes = TvPresentationWriteService(repo=repo)
    writes.patch_playlist_data_defaults(
        playlist_id,
        data_defaults={"dateRangePreset": "this_year"},
        actor_user_id="user-1",
    )
    assert saved == [{"dateRangePreset": "this_year", "branch": "01"}]


def test_patch_playlist_data_defaults_replace_normalizes(monkeypatch):
    """replace=True também normaliza — preset novo remove datas do próprio patch."""
    from tv_app.application.services.tv_presentation_write_service import (
        TvPresentationWriteService,
    )

    playlist_id = uuid4()
    saved: list[dict[str, Any]] = []
    repo = MagicMock()
    repo.get_revision.return_value = 1
    repo.get_by_id.return_value = {
        "id": str(playlist_id),
        "revision": 1,
        "dataDefaults": {"branch": "02"},
    }
    repo.update_data_defaults.side_effect = lambda _pid, defaults, **_kw: saved.append(
        defaults
    ) or {"id": str(playlist_id), "dataDefaults": defaults}

    monkeypatch.setattr(
        "tv_app.application.services.tv_presentation_write_service.notify_presentation_changed",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "tv_app.application.services.presentation_change_notifier.notify_playlist_library_changed",
        lambda **kwargs: None,
    )

    writes = TvPresentationWriteService(repo=repo)
    writes.patch_playlist_data_defaults(
        playlist_id,
        data_defaults={
            "dateRangePreset": "same_period_previous_year",
            "start_date": "2025-09-01",
            "end_date": "2025-09-25",
        },
        actor_user_id="user-1",
        replace=True,
    )
    assert saved == [{"dateRangePreset": "same_period_previous_year"}]


def test_relayer_playlist_scope_clears_stale_dates():
    """re_layer promovendo preset para playlist remove datas custom antigas."""
    from tv_app.application.services.data.filter_relayer_service import apply_relayer

    playlist_defaults = {
        "dateRangePreset": "custom",
        "start_date": "2026-09-01",
        "end_date": "2026-09-20",
        "branch": "01",
    }
    native_config = {
        "blocks": [
            {
                "id": "src-a",
                "type": "data_source",
                "dataBinding": {"params": {"dateRangePreset": "this_year"}},
            }
        ]
    }
    _cfg, new_defaults, promoted = apply_relayer(
        native_config,
        scope="playlist",
        keys=["dateRangePreset"],
        playlist_defaults=playlist_defaults,
    )
    assert promoted == {"dateRangePreset": "this_year"}
    assert new_defaults == {"dateRangePreset": "this_year", "branch": "01"}


def test_relayer_slide_scope_clears_stale_dates_in_data_filters():
    """Mesma regra ao promover para dataFilters da tela."""
    from tv_app.application.services.data.filter_relayer_service import apply_relayer

    native_config = {
        "dataFilters": {
            "dateRangePreset": "custom",
            "start_date": "2026-09-01",
            "end_date": "2026-09-20",
        },
        "blocks": [
            {
                "id": "src-a",
                "type": "data_source",
                "dataBinding": {"params": {"dateRangePreset": "this_year"}},
            }
        ],
    }
    cfg, _defaults, _promoted = apply_relayer(
        native_config,
        scope="slide",
        keys=["dateRangePreset"],
        playlist_defaults=None,
    )
    assert cfg["dataFilters"] == {"dateRangePreset": "this_year"}
