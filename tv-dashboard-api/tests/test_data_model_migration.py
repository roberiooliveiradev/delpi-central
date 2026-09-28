"""DM4 — migração explícita legacy ``data_source`` → ``DataModel``.

Contrato: ``migrate_data_sources_to_model`` converte a fonte primária +
closure de dependências ``merge.sourceId`` em um DataModel de inputs
embutidos (ids preservados → referências de merge seguem válidas), rebinda
consumers do primário para ``modelId`` e só remove fontes sem consumidor
quando ``removeOrphanedSources=true``. Tudo passa pelos gates canônicos de
candidate state (execução do modelo + satisfação de campos dos consumers).
"""

from __future__ import annotations

import copy

import pytest

from test_data_model_foundation import (
    SLIDE_ID,
    _enrichment,
    _gateway_by_preset,
    _patch_service,
    _preview_envelope,
    _rol_payload,
    _user,
)
from tv_app.application.services.comunicado_data_enrichment_service import (
    reset_comunicado_data_block_cache,
)
from tv_app.application.services.data.presentation_mutation.patch_service import (
    PresentationPatchError,
)


@pytest.fixture(autouse=True)
def _clear_data_cache():
    reset_comunicado_data_block_cache()
    yield
    reset_comunicado_data_block_cache()


_OP = "get_commercial_rol_summary"

PREV = 4399153.22
CUR = 4516461.10


# ---------------------------------------------------------------------------
# Fixtures locais — slide legacy ROL (primário ds_cur merge ds_prev)
# ---------------------------------------------------------------------------


def _src(
    sid: str,
    *,
    preset: str = "this_year",
    transform: list[dict] | None = None,
    label: str | None = None,
    field_labels: dict | None = None,
) -> dict:
    block = {
        "id": sid,
        "type": "data_source",
        "queryName": sid,
        "dataBinding": {
            "operationId": _OP,
            "label": label,
            "params": {"branch": "01", "dateRangePreset": preset},
        },
    }
    if transform:
        block["dataTransform"] = {"version": 1, "steps": transform}
    if field_labels:
        block["fieldLabels"] = field_labels
    return block


def _kpi(block_id: str = "kpi1", field: str = "value", **extra) -> dict:
    block = {
        "id": block_id,
        "type": "kpi_view",
        "kpiProjection": {"metrics": [{"field": field, "label": "Var %"}]},
    }
    block.update(extra)
    return block


def _rol_sources() -> list[dict]:
    return [
        _src(
            "ds_prev",
            preset="same_period_previous_year",
            label="ROL ano anterior",
            transform=[
                {"op": "rename", "from": "rol", "to": "rol_prev"},
                {"op": "addColumn", "name": "join_key", "expr": "1"},
            ],
        ),
        _src(
            "ds_cur",
            preset="this_year",
            label="ROL atual",
            transform=[
                {"op": "addColumn", "name": "join_key", "expr": "1"},
                {
                    "op": "merge",
                    "sourceId": "ds_prev",
                    "leftKey": "join_key",
                    "rightKey": "join_key",
                    "columns": ["rol_prev"],
                },
                {
                    "op": "addColumn",
                    "name": "value",
                    "expr": "(rol / rol_prev - 1) * 100",
                },
            ],
        ),
    ]


def _slide(blocks: list[dict], models: list[dict] | None = None) -> dict:
    cfg = {"version": 5, "blocks": blocks}
    if models is not None:
        cfg["dataModels"] = models
    return {"id": SLIDE_ID, "nativeConfig": cfg}


def _rol_gateway():
    return _gateway_by_preset(
        {"previous": _rol_payload(PREV), "current": _rol_payload(CUR)}
    )


def _migrate_op(**extra) -> dict:
    op = {"op": "migrate_data_sources_to_model", "primaryDataSourceId": "ds_cur"}
    op.update(extra)
    return op


def _blocks_of(result: dict) -> list[dict]:
    return result["nativeConfig"].get("blocks") or []


def _block(result: dict, block_id: str) -> dict | None:
    for block in _blocks_of(result):
        if isinstance(block, dict) and str(block.get("id") or "") == block_id:
            return block
    return None


def _models_of(result: dict) -> list[dict]:
    return result["nativeConfig"].get("dataModels") or []


def _migration_report(result: dict) -> dict:
    return (result.get("sideEffects") or {}).get("dataModelMigration") or {}


# ---------------------------------------------------------------------------
# Migração simples (single-source)
# ---------------------------------------------------------------------------


class TestSimpleMigration:
    def test_single_source_visual_rebound_source_kept_by_default(self):
        slide = _slide(
            [_kpi(dataSourceId="ds1", field="rol"), _src("ds1", label="ROL")]
        )
        svc = _patch_service(_rol_gateway(), slide=slide)
        result = svc.preview(
            _preview_envelope([_migrate_op(primaryDataSourceId="ds1")]),
            user=_user(),
        )
        models = _models_of(result)
        assert len(models) == 1
        model = models[0]
        assert model["id"].startswith("mdl_")
        assert model["primaryInputId"] == "ds1"
        assert [i["id"] for i in model["inputs"]] == ["ds1"]
        assert model["inputs"][0]["operationId"] == _OP
        assert model["inputs"][0]["params"]["dateRangePreset"] == "this_year"
        assert model["transform"] in (None, {"steps": []})
        assert model["label"] == "ROL"

        visual = _block(result, "kpi1")
        assert visual["modelId"] == model["id"]
        assert "dataSourceId" not in visual

        # Conservador por default: fonte fica retida (embora removível).
        assert _block(result, "ds1") is not None
        report = _migration_report(result)
        assert report["modelId"] == model["id"]
        assert report["consumersRebound"] == ["kpi1"]
        assert report["legacySourcesRemoved"] == []
        assert report["legacySourcesRemovable"] == ["ds1"]
        assert report["rollback"] == "slide_revision"

    def test_remove_orphaned_sources_deletes_safe_source(self):
        slide = _slide([_kpi(dataSourceId="ds1", field="rol"), _src("ds1")])
        svc = _patch_service(_rol_gateway(), slide=slide)
        result = svc.preview(
            _preview_envelope(
                [_migrate_op(primaryDataSourceId="ds1", removeOrphanedSources=True)]
            ),
            user=_user(),
        )
        assert _block(result, "ds1") is None
        report = _migration_report(result)
        assert report["legacySourcesRemoved"] == ["ds1"]

    def test_preview_does_not_mutate_persisted_slide(self):
        blocks = [_kpi(dataSourceId="ds1", field="rol"), _src("ds1")]
        slide = _slide(blocks)
        before = copy.deepcopy(slide["nativeConfig"])
        svc = _patch_service(_rol_gateway(), slide=slide)
        svc.preview(
            _preview_envelope(
                [_migrate_op(primaryDataSourceId="ds1", removeOrphanedSources=True)]
            ),
            user=_user(),
        )
        assert slide["nativeConfig"] == before


# ---------------------------------------------------------------------------
# Migração multi-source — caso ROL real (≈2.6667)
# ---------------------------------------------------------------------------


class TestRolMultiSourceMigration:
    def test_rol_case_parity(self):
        """ds_cur(merge ds_prev) + KPI → modelo com 2 inputs; resultado
        idêntico ao legacy (≈2.6667)."""
        slide = _slide([_kpi(dataSourceId="ds_cur"), *_rol_sources()])
        svc = _patch_service(_rol_gateway(), slide=slide)
        result = svc.preview(
            _preview_envelope([_migrate_op()]),
            user=_user(),
        )
        models = _models_of(result)
        assert len(models) == 1
        model = models[0]
        assert model["primaryInputId"] == "ds_cur"
        assert {i["id"] for i in model["inputs"]} == {"ds_cur", "ds_prev"}
        prev_input = next(i for i in model["inputs"] if i["id"] == "ds_prev")
        # transform local do sibling preservado como input.transform
        steps = (prev_input.get("transform") or {}).get("steps") or []
        assert [s["op"] for s in steps] == ["rename", "addColumn"]
        # transform do primário promovido a model.transform (merge intacto)
        model_steps = (model.get("transform") or {}).get("steps") or []
        assert [s["op"] for s in model_steps] == [
            "addColumn",
            "merge",
            "addColumn",
        ]
        assert model_steps[1]["sourceId"] == "ds_prev"

        # Presets de período distintos preservados nos inputs
        params_by_id = {i["id"]: i["params"] for i in model["inputs"]}
        assert params_by_id["ds_cur"]["dateRangePreset"] == "this_year"
        assert params_by_id["ds_prev"]["dateRangePreset"] == (
            "same_period_previous_year"
        )

        # Paridade numérica no candidate state
        resolved = _enrichment(_rol_gateway()).enrich_data_models(
            [model], cfg=result["nativeConfig"], authorization=None
        )[model["id"]]
        assert not resolved.get("error"), resolved
        row = resolved["table"]["rows"][0]
        assert row["value"] == pytest.approx(2.6667, abs=0.01)

        visual = _block(result, "kpi1")
        assert visual["modelId"] == model["id"]

        # Sem removeOrphanedSources: ds_prev/ds_cur seguem no slide
        assert _block(result, "ds_cur") is not None
        assert _block(result, "ds_prev") is not None

    def test_multi_source_cleanup_removes_unconsumed_pair(self):
        slide = _slide([_kpi(dataSourceId="ds_cur"), *_rol_sources()])
        svc = _patch_service(_rol_gateway(), slide=slide)
        result = svc.preview(
            _preview_envelope([_migrate_op(removeOrphanedSources=True)]),
            user=_user(),
        )
        assert _block(result, "ds_cur") is None
        assert _block(result, "ds_prev") is None
        report = _migration_report(result)
        assert sorted(report["legacySourcesRemoved"]) == ["ds_cur", "ds_prev"]


# ---------------------------------------------------------------------------
# Shared source safety
# ---------------------------------------------------------------------------


class TestSharedSourceSafety:
    def test_sibling_with_direct_visual_is_retained(self):
        """ds_prev também alimenta visual próprio → retido, binding intacto."""
        slide = _slide(
            [
                _kpi("kpi1", dataSourceId="ds_cur"),
                _kpi("kpi2", field="rol_prev", dataSourceId="ds_prev"),
                *_rol_sources(),
            ]
        )
        svc = _patch_service(_rol_gateway(), slide=slide)
        result = svc.preview(
            _preview_envelope([_migrate_op(removeOrphanedSources=True)]),
            user=_user(),
        )
        model = _models_of(result)[0]
        assert {i["id"] for i in model["inputs"]} == {"ds_cur", "ds_prev"}
        # ds_prev mantido como fonte legacy — consumer direto segue ligado.
        prev_block = _block(result, "ds_prev")
        assert prev_block is not None
        kpi2 = _block(result, "kpi2")
        assert kpi2["dataSourceId"] == "ds_prev"
        assert "modelId" not in kpi2
        assert _block(result, "ds_cur") is None
        report = _migration_report(result)
        assert report["legacySourcesRetained"] == ["ds_prev"]
        assert report["legacySourcesRemoved"] == ["ds_cur"]

    def test_sibling_required_by_other_merge_is_retained(self):
        """ds_prev é dependência de merge de outra fonte não migrada → retido."""
        other = _src(
            "ds_other",
            preset="this_year",
            transform=[
                {"op": "addColumn", "name": "join_key", "expr": "1"},
                {
                    "op": "merge",
                    "sourceId": "ds_prev",
                    "leftKey": "join_key",
                    "rightKey": "join_key",
                    "columns": ["rol_prev"],
                },
            ],
        )
        slide = _slide(
            [
                _kpi("kpi1", dataSourceId="ds_cur"),
                _kpi("kpi2", field="rol", dataSourceId="ds_other"),
                *_rol_sources(),
                other,
            ]
        )
        svc = _patch_service(_rol_gateway(), slide=slide)
        result = svc.preview(
            _preview_envelope([_migrate_op(removeOrphanedSources=True)]),
            user=_user(),
        )
        assert _block(result, "ds_prev") is not None
        report = _migration_report(result)
        assert "ds_prev" in report["legacySourcesRetained"]

    def test_orphan_unrelated_source_never_touched(self):
        """Fonte órfã fora do closure migrado não entra no modelo nem é removida."""
        slide = _slide(
            [
                _kpi(dataSourceId="ds1", field="rol"),
                _src("ds1"),
                _src("ds_orphan", preset="same_period_previous_year"),
            ]
        )
        svc = _patch_service(_rol_gateway(), slide=slide)
        result = svc.preview(
            _preview_envelope(
                [_migrate_op(primaryDataSourceId="ds1", removeOrphanedSources=True)]
            ),
            user=_user(),
        )
        model = _models_of(result)[0]
        assert [i["id"] for i in model["inputs"]] == ["ds1"]
        assert _block(result, "ds_orphan") is not None

    def test_model_dependency_keeps_source(self):
        """Fonte já referenciada como input de modelo existente → não removida
        mesmo sem consumer visual."""
        existing_model = {
            "id": "mdl_existing",
            "primaryInputId": "ds_prev",
            "inputs": [
                {
                    "id": "ds_prev",
                    "operationId": _OP,
                    "params": {
                        "branch": "01",
                        "dateRangePreset": "same_period_previous_year",
                    },
                }
            ],
        }
        slide = _slide(
            [_kpi(dataSourceId="ds_cur"), *_rol_sources()],
            models=[existing_model],
        )
        svc = _patch_service(_rol_gateway(), slide=slide)
        result = svc.preview(
            _preview_envelope([_migrate_op(removeOrphanedSources=True)]),
            user=_user(),
        )
        # ds_prev segue no slide: é input de mdl_existing (model dependency).
        assert _block(result, "ds_prev") is not None
        report = _migration_report(result)
        assert "ds_prev" in report["legacySourcesRetained"]


# ---------------------------------------------------------------------------
# Consumers text / canvas cell
# ---------------------------------------------------------------------------


class TestTextAndCellConsumers:
    def test_text_consumer_rebound(self):
        text = {
            "id": "txt1",
            "type": "text",
            "dataSourceId": "ds1",
            "contentRuns": [
                {"text": "ROL: "},
                {"dataRef": {"field": "rol"}},
            ],
        }
        slide = _slide([text, _src("ds1")])
        svc = _patch_service(_rol_gateway(), slide=slide)
        result = svc.preview(
            _preview_envelope([_migrate_op(primaryDataSourceId="ds1")]),
            user=_user(),
        )
        model = _models_of(result)[0]
        bound = _block(result, "txt1")
        assert bound["modelId"] == model["id"]
        assert "dataSourceId" not in bound
        assert bound["contentRuns"][1]["dataRef"]["field"] == "rol"

    def test_canvas_table_cell_rebound(self):
        table = {
            "id": "tbl1",
            "type": "canvas_table",
            "cells": [
                [
                    {
                        "text": "",
                        "dataSourceId": "ds1",
                        "dataRef": {"field": "rol"},
                    },
                    {"text": "static"},
                ]
            ],
        }
        slide = _slide([table, _src("ds1")])
        svc = _patch_service(_rol_gateway(), slide=slide)
        result = svc.preview(
            _preview_envelope([_migrate_op(primaryDataSourceId="ds1")]),
            user=_user(),
        )
        model = _models_of(result)[0]
        cell = _block(result, "tbl1")["cells"][0][0]
        assert cell["modelId"] == model["id"]
        assert "dataSourceId" not in cell

    def test_canvas_cell_bound_to_sibling_keeps_sibling(self):
        """Célula ligada ao sibling → sibling retido com binding intacto."""
        table = {
            "id": "tbl1",
            "type": "canvas_table",
            "cells": [
                [{"text": "", "dataSourceId": "ds_prev", "dataRef": {"field": "rol_prev"}}]
            ],
        }
        slide = _slide(
            [_kpi(dataSourceId="ds_cur"), table, *_rol_sources()]
        )
        svc = _patch_service(_rol_gateway(), slide=slide)
        result = svc.preview(
            _preview_envelope([_migrate_op(removeOrphanedSources=True)]),
            user=_user(),
        )
        assert _block(result, "ds_prev") is not None
        cell = _block(result, "tbl1")["cells"][0][0]
        assert cell["dataSourceId"] == "ds_prev"

    def test_multiple_visuals_rebound_atomically(self):
        slide = _slide(
            [
                _kpi("kpi1", field="value", dataSourceId="ds_cur"),
                _kpi("kpi2", field="rol", dataSourceId="ds_cur"),
                {
                    "id": "txt1",
                    "type": "text",
                    "dataSourceId": "ds_cur",
                    "textProjection": {"field": "value"},
                },
                *_rol_sources(),
            ]
        )
        svc = _patch_service(_rol_gateway(), slide=slide)
        result = svc.preview(_preview_envelope([_migrate_op()]), user=_user())
        model = _models_of(result)[0]
        for bid in ("kpi1", "kpi2", "txt1"):
            assert _block(result, bid)["modelId"] == model["id"]
        assert sorted(_migration_report(result)["consumersRebound"]) == [
            "kpi1",
            "kpi2",
            "txt1",
        ]


# ---------------------------------------------------------------------------
# Contratos de erro / conflito
# ---------------------------------------------------------------------------


class TestMigrationErrors:
    def test_missing_consumer_field_rejects_migration(self):
        """Visual projeta campo inexistente no output do modelo → falha tipada,
        migração não acontece."""
        slide = _slide(
            [_kpi(dataSourceId="ds1", field="campo_inexistente"), _src("ds1")]
        )
        svc = _patch_service(_rol_gateway(), slide=slide)
        with pytest.raises(PresentationPatchError) as exc_info:
            svc.preview(
                _preview_envelope([_migrate_op(primaryDataSourceId="ds1")]),
                user=_user(),
            )
        assert exc_info.value.code == "DATA_BINDING_FIELD_MISSING"
        details = exc_info.value.details or {}
        assert "campo_inexistente" in str(details)

    def test_primary_not_found(self):
        slide = _slide([_src("ds1")])
        svc = _patch_service(_rol_gateway(), slide=slide)
        with pytest.raises(PresentationPatchError) as exc_info:
            svc.preview(
                _preview_envelope([_migrate_op(primaryDataSourceId="ghost")]),
                user=_user(),
            )
        assert exc_info.value.code == "data_model.migration_conflict"

    def test_primary_must_be_data_source(self):
        slide = _slide([_kpi(dataSourceId="ds1", field="rol"), _src("ds1")])
        svc = _patch_service(_rol_gateway(), slide=slide)
        with pytest.raises(PresentationPatchError) as exc_info:
            svc.preview(
                _preview_envelope([_migrate_op(primaryDataSourceId="kpi1")]),
                user=_user(),
            )
        assert exc_info.value.code == "data_model.migration_conflict"

    def test_model_id_collision_rejected(self):
        slide = _slide(
            [_kpi(dataSourceId="ds1", field="rol"), _src("ds1")],
            models=[
                {
                    "id": "mdl_taken",
                    "primaryInputId": "only",
                    "inputs": [
                        {
                            "id": "only",
                            "operationId": _OP,
                            "params": {"branch": "01"},
                        }
                    ],
                }
            ],
        )
        svc = _patch_service(_rol_gateway(), slide=slide)
        with pytest.raises(PresentationPatchError) as exc_info:
            svc.preview(
                _preview_envelope(
                    [_migrate_op(primaryDataSourceId="ds1", targetModelId="mdl_taken")]
                ),
                user=_user(),
            )
        assert exc_info.value.code == "data_model.migration_conflict"

    def test_unrelated_explicit_sibling_rejected(self):
        """relatedDataSourceIds só aceita dependências reais — sem adivinhar."""
        slide = _slide(
            [
                _kpi(dataSourceId="ds1", field="rol"),
                _src("ds1"),
                _src("ds_other", preset="same_period_previous_year"),
            ]
        )
        svc = _patch_service(_rol_gateway(), slide=slide)
        with pytest.raises(PresentationPatchError) as exc_info:
            svc.preview(
                _preview_envelope(
                    [
                        _migrate_op(
                            primaryDataSourceId="ds1",
                            relatedDataSourceIds=["ds_other"],
                        )
                    ]
                ),
                user=_user(),
            )
        assert exc_info.value.code == "data_model.migration_conflict"

    def test_fetch_failure_rolls_back_whole_mutation(self):
        """Upstream down → preview falha tipado; slide persistido intacto."""
        blocks = [_kpi(dataSourceId="ds1", field="rol"), _src("ds1")]
        slide = _slide(blocks)
        before = copy.deepcopy(slide["nativeConfig"])
        svc = _patch_service(
            _gateway_by_preset({}, fails={"current": Exception("upstream down")}),
            slide=slide,
        )
        with pytest.raises(PresentationPatchError):
            svc.preview(
                _preview_envelope([_migrate_op(primaryDataSourceId="ds1")]),
                user=_user(),
            )
        assert slide["nativeConfig"] == before

    def test_source_without_operation_id_rejected(self):
        bad = _src("ds1")
        bad["dataBinding"].pop("operationId")
        slide = _slide([_kpi(dataSourceId="ds1", field="rol"), bad])
        svc = _patch_service(_rol_gateway(), slide=slide)
        with pytest.raises(PresentationPatchError) as exc_info:
            svc.preview(
                _preview_envelope([_migrate_op(primaryDataSourceId="ds1")]),
                user=_user(),
            )
        assert exc_info.value.code == "data_model.migration_conflict"


# ---------------------------------------------------------------------------
# Preservação de contrato
# ---------------------------------------------------------------------------


class TestContractPreservation:
    def test_field_labels_carried_to_model(self):
        slide = _slide(
            [
                _kpi(dataSourceId="ds1", field="rol"),
                _src("ds1", field_labels={"rol": "Receita Líquida"}),
            ]
        )
        svc = _patch_service(_rol_gateway(), slide=slide)
        result = svc.preview(
            _preview_envelope([_migrate_op(primaryDataSourceId="ds1")]),
            user=_user(),
        )
        model = _models_of(result)[0]
        assert model["fieldLabels"]["rol"] == "Receita Líquida"

    def test_input_ids_preserve_source_ids_for_merge_refs(self):
        slide = _slide([_kpi(dataSourceId="ds_cur"), *_rol_sources()])
        svc = _patch_service(_rol_gateway(), slide=slide)
        result = svc.preview(_preview_envelope([_migrate_op()]), user=_user())
        model = _models_of(result)[0]
        input_ids = {i["id"] for i in model["inputs"]}
        merge_steps = [
            s
            for s in (model.get("transform") or {}).get("steps", [])
            if s.get("op") == "merge"
        ]
        for step in merge_steps:
            assert step["sourceId"] in input_ids

    def test_preset_params_not_materialized(self):
        """dateRangePreset vai para o input como parâmetro semântico —
        nenhuma data absoluta é materializada no modelo persistido."""
        slide = _slide([_kpi(dataSourceId="ds1", field="rol"), _src("ds1")])
        svc = _patch_service(_rol_gateway(), slide=slide)
        result = svc.preview(
            _preview_envelope([_migrate_op(primaryDataSourceId="ds1")]),
            user=_user(),
        )
        params = _models_of(result)[0]["inputs"][0]["params"]
        assert params["dateRangePreset"] == "this_year"
        assert "start_date" not in params
        assert "end_date" not in params

    def test_report_has_no_secrets(self):
        slide = _slide([_kpi(dataSourceId="ds_cur"), *_rol_sources()])
        svc = _patch_service(_rol_gateway(), slide=slide)
        result = svc.preview(_preview_envelope([_migrate_op()]), user=_user())
        report = _migration_report(result)
        import json as _json

        payload = _json.dumps(report).lower()
        for token in ("authorization", "bearer", "token", "secret", "password"):
            assert token not in payload


# ---------------------------------------------------------------------------
# Dispatch — operação exposta ao gate executável
# ---------------------------------------------------------------------------


class TestDispatchGate:
    def test_op_is_in_catalog(self):
        from tv_app.application.services.data.presentation_ops_content_service import (
            PresentationOpsContentService,
        )

        ops = PresentationOpsContentService.operations()
        spec = ops["migrate_data_sources_to_model"]
        assert spec["requiresSlide"] is True
        props = spec["inputSchema"]["properties"]
        assert "primaryDataSourceId" in props
        assert spec["inputSchema"]["required"] == ["op", "primaryDataSourceId"]

    def test_repeat_migration_of_same_id_conflicts(self):
        """Idempotência: modelo já existente com o targetModelId → conflito,
        nunca duplicado silenciosamente."""
        slide = _slide([_kpi(dataSourceId="ds1", field="rol"), _src("ds1")])
        svc = _patch_service(_rol_gateway(), slide=slide)
        first = svc.preview(
            _preview_envelope(
                [_migrate_op(primaryDataSourceId="ds1", targetModelId="mdl_once")]
            ),
            user=_user(),
        )
        assert _models_of(first)[0]["id"] == "mdl_once"
        # Segunda execução sobre o candidate persistido conflitaria em id —
        # a op falha antes de duplicar.
        slide2 = _slide(
            [_kpi(modelId="mdl_once"), _src("ds1")],
            models=_models_of(first),
        )
        svc2 = _patch_service(_rol_gateway(), slide=slide2)
        with pytest.raises(PresentationPatchError) as exc_info:
            svc2.preview(
                _preview_envelope(
                    [_migrate_op(primaryDataSourceId="ds1", targetModelId="mdl_once")]
                ),
                user=_user(),
            )
        assert exc_info.value.code == "data_model.migration_conflict"

    def test_repeat_migration_with_new_model_id_conflicts(self):
        """Idempotência: re-migrar fontes já embebidas como inputs de um modelo
        existente conflita mesmo com outro targetModelId — nunca cria um
        segundo modelo lógico para o mesmo grupo legacy."""
        slide = _slide([_kpi(dataSourceId="ds1", field="rol"), _src("ds1")])
        svc = _patch_service(_rol_gateway(), slide=slide)
        first = svc.preview(
            _preview_envelope(
                [_migrate_op(primaryDataSourceId="ds1", targetModelId="mdl_once")]
            ),
            user=_user(),
        )
        slide2 = _slide(
            [_kpi(modelId="mdl_once"), _src("ds1")],
            models=_models_of(first),
        )
        svc2 = _patch_service(_rol_gateway(), slide=slide2)
        with pytest.raises(PresentationPatchError) as exc_info:
            svc2.preview(
                _preview_envelope(
                    [_migrate_op(primaryDataSourceId="ds1", targetModelId="mdl_dup")]
                ),
                user=_user(),
            )
        assert exc_info.value.code == "data_model.migration_conflict"
        assert "mdl_once" in str(exc_info.value)


# ---------------------------------------------------------------------------
# inspect_data_model — superfície de leitura semântica VISTA
# ---------------------------------------------------------------------------


class TestInspectDataModel:
    def _dispatch(self, *, slide: dict, gateway):
        from unittest.mock import MagicMock
        from test_data_model_foundation import _Repo, PLAYLIST_ID
        from tv_app.application.gpt_actions.dispatch_service import (
            GptActionsDispatchService,
        )
        from tv_app.application.services.data.tv_data_preview_service import (
            TvDataPreviewService,
        )

        repo = _Repo(slide)
        writes = MagicMock()
        writes.get_slide.side_effect = lambda slide_id, playlist_id=None: repo.get_slide(
            slide_id, playlist_id=playlist_id
        )
        dispatch = GptActionsDispatchService(
            repo=repo,
            writes=writes,
            commit=MagicMock(),
            preview=TvDataPreviewService(enrichment=_enrichment(gateway)),
        )
        return dispatch

    def test_inspect_returns_definition_consumers_schema(self):
        model = {
            "id": "mdl_insp",
            "label": "ROL atual",
            "primaryInputId": "ds1",
            "inputs": [
                {
                    "id": "ds1",
                    "operationId": _OP,
                    "params": {"branch": "01", "dateRangePreset": "this_year"},
                }
            ],
            "fieldLabels": {"rol": "Receita"},
        }
        slide = _slide(
            [_kpi(field="rol", modelId="mdl_insp")], models=[model]
        )
        dispatch = self._dispatch(slide=slide, gateway=_rol_gateway())
        from test_data_model_foundation import PLAYLIST_ID
        from unittest.mock import patch
        from types import SimpleNamespace

        access = SimpleNamespace(
            can_read=True,
            can_edit=True,
            playlist={"dataDefaults": {"branch": "01"}},
        )
        with patch.object(dispatch._access, "resolve", return_value=access):
            out = dispatch.inspect_data_model(
                user=_user(),
                playlist_id=PLAYLIST_ID,
                slide_id=SLIDE_ID,
                model_id="mdl_insp",
                authorization=None,
            )
        assert out["modelId"] == "mdl_insp"
        assert out["definition"]["label"] == "ROL atual"
        assert out["definition"]["primaryInputId"] == "ds1"
        assert out["definition"]["inputs"][0]["operationId"] == _OP
        assert out["definition"]["fieldLabels"] == {"rol": "Receita"}
        assert out["consumers"] == {"kpi1": ["rol"]}
        assert out["consumerCount"] == 1
        assert out["runtime"]["state"] == "ready"
        cols = (out["outputSchema"] or {}).get("columns") or []
        assert "rol" in cols
        # Sem secrets/tokens no payload
        import json as _json

        payload = _json.dumps(out).lower()
        for token in ("authorization", "bearer", "token", "secret", "password"):
            assert token not in payload

    def test_inspect_without_runtime(self):
        model = {
            "id": "mdl_insp",
            "primaryInputId": "ds1",
            "inputs": [
                {
                    "id": "ds1",
                    "operationId": _OP,
                    "params": {"branch": "01"},
                }
            ],
        }
        slide = _slide([], models=[model])
        dispatch = self._dispatch(slide=slide, gateway=_rol_gateway())
        from test_data_model_foundation import PLAYLIST_ID
        from unittest.mock import patch
        from types import SimpleNamespace

        access = SimpleNamespace(can_read=True, playlist={"dataDefaults": {}})
        with patch.object(dispatch._access, "resolve", return_value=access):
            out = dispatch.inspect_data_model(
                user=_user(),
                playlist_id=PLAYLIST_ID,
                slide_id=SLIDE_ID,
                model_id="mdl_insp",
                authorization=None,
                include_runtime=False,
            )
        assert out["runtime"]["state"] == "not_executed"
        assert out["outputSchema"] is None
        assert out["consumers"] == {}

    def test_inspect_missing_model_404(self):
        from tv_app.application.gpt_actions.errors import GptActionsError
        from test_data_model_foundation import PLAYLIST_ID
        from unittest.mock import patch
        from types import SimpleNamespace

        slide = _slide([], models=[])
        dispatch = self._dispatch(slide=slide, gateway=_rol_gateway())
        access = SimpleNamespace(can_read=True, playlist={"dataDefaults": {}})
        with patch.object(dispatch._access, "resolve", return_value=access):
            with pytest.raises(GptActionsError) as exc_info:
                dispatch.inspect_data_model(
                    user=_user(),
                    playlist_id=PLAYLIST_ID,
                    slide_id=SLIDE_ID,
                    model_id="mdl_ghost",
                    authorization=None,
                )
        assert exc_info.value.status_code == 404

    def test_inspect_in_operation_ids_and_openapi(self):
        from tv_app.application.gpt_actions import GPT_ACTIONS_OPERATION_IDS
        from tv_app.application.gpt_actions.openapi_builder import (
            build_gpt_actions_openapi,
        )

        assert "gpt_inspect_data_model" in GPT_ACTIONS_OPERATION_IDS
        doc = build_gpt_actions_openapi()
        found = {
            op["operationId"]
            for methods in doc["paths"].values()
            for op in methods.values()
            if isinstance(op, dict) and op.get("operationId")
        }
        assert "gpt_inspect_data_model" in found
