"""Regressão: registros MyWEG sem identificação não bloqueiam demanda válida."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from production_control_app.application.services.myweg_needs_service import MyWegNeedsService
from production_control_app.jobs.myweg_needs_publisher.payload_builder import (
    _split_unidentified_materials,
    build_ingest_payload,
)
from tests.test_myweg_needs_e2 import InMemoryMyWegNeedsRepository


def _rows():
    source = [
        {
            "material_weg_tratado": "MAT-VALIDO",
            "material_weg_original": "MAT-VALIDO",
            "origem_material_weg": "WEG",
            "codigo_referencia_weg": "",
            "codigo_produto_delpi": "",
            "quantidade": "1000",
            "unidade": "UN",
            "data_remessa": "19/11/2026",
            "linha_fonte": "3",
            "documento": "",
        }
    ]
    for line, qty in [("115", "140.0"), ("171", "240.0")]:
        bad = dict(source[0])
        bad.update({
            "material_weg_tratado": "",
            "material_weg_original": "",
            "codigo_referencia_weg": "",
            "codigo_produto_delpi": "",
            "quantidade": qty,
            "linha_fonte": line,
        })
        source.append(bad)
    return source


def _artifacts(rows):
    return SimpleNamespace(
        collection_id="20261119_080020_20261119_050019_EXPORT_20261119_050017",
        collected_at=datetime(2026, 11, 19, 8, 0, tzinfo=timezone.utc),
        source_rows=rows,
        file_hashes={
            "necessidades_tratadas.csv": "a" * 64,
            "necessidades_tratadas.xlsx": "b" * 64,
            "para_conferencia_pcp.csv": "c" * 64,
            "resumo.json": "d" * 64,
        },
    )


def test_partial_ingest_preserves_valid_demand_and_audits_380_un():
    rows = _rows()
    before = deepcopy(rows)
    built = build_ingest_payload(_artifacts(rows))
    quality = built["quality"]
    assert quality["sourceRecordCount"] == 3
    assert quality["excludedCount"] == 2
    assert quality["excludedQuantityUn"] == "380"
    assert quality["excludedQuantityMi"] == "0.38"
    assert [item["sourceLine"] for item in quality["excludedRecords"]] == ["115", "171"]
    assert built["record_count"] == 1
    assert built["payload"]["record_count"] == 1
    assert len(built["payload"]["records"]) == 1
    assert built["batch"]["source_files"]["quality"] == quality
    assert built["batch"]["totals"]["quantidade_original_un"] == "1000"
    assert rows == before


def test_other_invalid_rows_remain_fail_closed():
    rows = _rows()
    rows[1]["unidade"] = "MIL"
    with pytest.raises(ValueError, match="Unidade não suportada"):
        build_ingest_payload(_artifacts(rows))
    rows = _rows()
    rows[0]["quantidade"] = "-1"
    with pytest.raises(ValueError):
        build_ingest_payload(_artifacts(rows))
    only_bad = _rows()[1:]
    with pytest.raises(ValueError, match="sem registros válidos"):
        build_ingest_payload(_artifacts(only_bad))


class _FakeNotifications:
    def __init__(self):
        self.sent = []

    def dispatch(self, payload):
        self.sent.append(payload)
        return {"ok": True}


def test_notification_postcommit_once_per_collection_and_branch_scoped():
    built = build_ingest_payload(_artifacts(_rows()))
    repo = InMemoryMyWegNeedsRepository()
    gateway = _FakeNotifications()
    service = MyWegNeedsService(repo, notification_gateway=gateway)
    first = service.ingest_batch(built["payload"], idempotency_key=built["idempotency_key"])
    again = service.ingest_batch(built["payload"], idempotency_key=built["idempotency_key"])
    assert first["created"] is True
    assert again["created"] is False
    assert first["quality"]["excludedCount"] == 2
    assert len(gateway.sent) == 1
    assert gateway.sent[0]["category"] == "production_control_myweg_import_warnings"
    assert gateway.sent[0]["requiredPermissionCodes"] == ["production-control.view.filial-02"]
    assert repo.get_latest_batch()["record_count"] == 1


def test_legacy_valid_batch_remains_compatible():
    raw = _rows()[0]
    valid, quality = _split_unidentified_materials([raw])
    assert valid == [raw]
    assert quality is None
