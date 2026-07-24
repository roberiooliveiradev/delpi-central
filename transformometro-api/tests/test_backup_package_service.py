from __future__ import annotations

import io
import json
import zipfile
from unittest.mock import MagicMock

import pytest

from tm_app.application.services.backup_package_service import (
    CADASTRO_FILENAME,
    MANIFEST_FILENAME,
    TransformometroBackupPackageService,
    evidence_archive_path,
    processo_arquivo_archive_path,
)
from tm_app.application.services.json_backup_service import SCHEMA_VERSION


def _sample_cadastro() -> dict:
    rid = "22222222-2222-2222-2222-222222222222"
    eid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    pid = "11111111-1111-1111-1111-111111111111"
    aid = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    return {
        "schema_version": SCHEMA_VERSION,
        "exported_at": "2026-07-06T00:00:00+00:00",
        "import_format": "modern",
        "counts": {
            "revisao_evidencias": 1,
            "processo_arquivos": 1,
            "evidence_files": 1,
            "processo_arquivo_files": 1,
        },
        "filiais": [],
        "setores": [],
        "setor_filiais": [],
        "processo_filiais": [],
        "processo_setores": [],
        "processos": [],
        "processo_instancias": [],
        "processo_instancia_setores": [],
        "processo_diagramas": [],
        "instancia_diagrama_escopos": [],
        "revisao_diagrama_overlays": [],
        "processo_decomposicao": [],
        "instancia_decomposicao_escopos": [],
        "revisao_decomposicao_overlays": [],
        "recursos_compartilhados": [],
        "revisoes": [
            {
                "revisao_id": rid,
                "processo_id": pid,
                "versao_revisao": "v1",
                "deletado": False,
            }
        ],
        "medicoes": [],
        "investimentos": [],
        "recurso_custos": [],
        "revisao_recursos_compartilhados": [],
        "revisao_evidencias": [
            {
                "evidencia_id": eid,
                "revisao_id": rid,
                "tipo": "anexo",
                "nome_arquivo": "doc.pdf",
                "nome_armazenado": "abc123.pdf",
                "tipo_mime": "application/pdf",
                "tamanho_bytes": 4,
            }
        ],
        "processo_arquivos": [
            {
                "arquivo_id": aid,
                "processo_id": pid,
                "tipo": "documento",
                "nome_arquivo": "IGD IDD METAS rev01.xlsx",
                "nome_armazenado": "def456.xlsx",
                "tipo_mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "tamanho_bytes": 8,
            }
        ],
    }


def _build_zip(cadastro: dict, binary_files: dict[str, bytes] | None = None) -> bytes:
    import hashlib

    binary_files = binary_files or {}
    cadastro_bytes = json.dumps(cadastro).encode("utf-8")
    entries = {
        CADASTRO_FILENAME: {
            "sha256": hashlib.sha256(cadastro_bytes).hexdigest(),
            "size_bytes": len(cadastro_bytes),
        }
    }
    for path, content in binary_files.items():
        entries[path] = {
            "sha256": hashlib.sha256(content).hexdigest(),
            "size_bytes": len(content),
        }
    manifest = {
        "package_format": "transformometro_backup",
        "package_version": "1.0",
        "schema_version": cadastro.get("schema_version"),
        "entries": entries,
    }
    manifest_bytes = json.dumps(manifest).encode("utf-8")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(CADASTRO_FILENAME, cadastro_bytes)
        archive.writestr(MANIFEST_FILENAME, manifest_bytes)
        for path, content in binary_files.items():
            archive.writestr(path, content)
    return buffer.getvalue()


def test_evidence_archive_path():
    path = evidence_archive_path("22222222-2222-2222-2222-222222222222", "file.pdf")
    assert path == "evidencias/22222222-2222-2222-2222-222222222222/file.pdf"


def test_processo_arquivo_archive_path():
    path = processo_arquivo_archive_path("11111111-1111-1111-1111-111111111111", "file.xlsx")
    assert path == "processo_arquivos/11111111-1111-1111-1111-111111111111/file.xlsx"


def test_export_package_includes_manifest_evidence_and_processo_arquivos():
    cadastro = _sample_cadastro()
    rid = cadastro["revisao_evidencias"][0]["revisao_id"]
    stored_ev = cadastro["revisao_evidencias"][0]["nome_armazenado"]
    pid = cadastro["processo_arquivos"][0]["processo_id"]
    stored_arq = cadastro["processo_arquivos"][0]["nome_armazenado"]
    json_backup = MagicMock()
    json_backup.export_bundle.return_value = cadastro

    evidence_storage = MagicMock()
    evidence_path = MagicMock()
    evidence_path.read_bytes.return_value = b"PDF1"
    evidence_storage.resolve_file.return_value = evidence_path

    processo_storage = MagicMock()
    processo_path = MagicMock()
    processo_path.read_bytes.return_value = b"XLSXDATA"
    processo_storage.resolve_file.return_value = processo_path

    service = TransformometroBackupPackageService(
        json_backup=json_backup,
        storage=evidence_storage,
        processo_arquivo_storage=processo_storage,
    )
    payload = service.export_package()

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = set(archive.namelist())
        assert MANIFEST_FILENAME in names
        assert CADASTRO_FILENAME in names
        assert evidence_archive_path(rid, stored_ev) in names
        assert processo_arquivo_archive_path(pid, stored_arq) in names
        manifest = json.loads(archive.read(MANIFEST_FILENAME))
        assert manifest["package_format"] == "transformometro_backup"
        assert manifest["schema_version"] == SCHEMA_VERSION
        assert manifest["counts"]["evidence_files"] == 1
        assert manifest["counts"]["processo_arquivo_files"] == 1


def test_export_package_fails_when_processo_arquivo_missing_on_disk():
    cadastro = _sample_cadastro()
    cadastro["revisao_evidencias"] = []
    json_backup = MagicMock()
    json_backup.export_bundle.return_value = cadastro

    evidence_storage = MagicMock()
    processo_storage = MagicMock()
    processo_storage.resolve_file.side_effect = FileNotFoundError("missing")

    service = TransformometroBackupPackageService(
        json_backup=json_backup,
        storage=evidence_storage,
        processo_arquivo_storage=processo_storage,
    )
    with pytest.raises(ValueError, match="arquivo do processo"):
        service.export_package()


def test_preview_package_rejects_missing_evidence_file():
    cadastro = _sample_cadastro()
    cadastro["processo_arquivos"] = []
    raw = _build_zip(cadastro)
    json_backup = MagicMock()
    json_backup.preview.return_value = {
        "valid": True,
        "errors": [],
        "mode": "merge",
        "entities": {},
    }
    service = TransformometroBackupPackageService(
        json_backup=json_backup,
        storage=MagicMock(),
        processo_arquivo_storage=MagicMock(),
    )
    result = service.preview_package(raw, "merge", "modern")
    assert result["valid"] is False
    assert any("Evidência sem arquivo" in err for err in result["errors"])


def test_preview_package_rejects_missing_processo_arquivo():
    cadastro = _sample_cadastro()
    cadastro["revisao_evidencias"] = []
    raw = _build_zip(cadastro)
    json_backup = MagicMock()
    json_backup.preview.return_value = {
        "valid": True,
        "errors": [],
        "mode": "merge",
        "entities": {},
    }
    service = TransformometroBackupPackageService(
        json_backup=json_backup,
        storage=MagicMock(),
        processo_arquivo_storage=MagicMock(),
    )
    result = service.preview_package(raw, "merge", "modern")
    assert result["valid"] is False
    assert any("Arquivo do processo sem binário" in err for err in result["errors"])


def test_apply_package_restores_files_on_replace():
    cadastro = _sample_cadastro()
    rid = cadastro["revisao_evidencias"][0]["revisao_id"]
    stored_ev = cadastro["revisao_evidencias"][0]["nome_armazenado"]
    pid = cadastro["processo_arquivos"][0]["processo_id"]
    stored_arq = cadastro["processo_arquivos"][0]["nome_armazenado"]
    rel_ev = evidence_archive_path(rid, stored_ev)
    rel_arq = processo_arquivo_archive_path(pid, stored_arq)
    raw = _build_zip(cadastro, {rel_ev: b"DATA", rel_arq: b"PROC"})

    json_backup = MagicMock()
    json_backup.preview.return_value = {
        "valid": True,
        "errors": [],
        "mode": "replace",
        "entities": {},
    }
    json_backup.apply.return_value = {"mode": "replace", "entities": {}}

    from pathlib import Path

    tmp_ev = Path("/tmp/tm-backup-test-evidence")
    tmp_arq = Path("/tmp/tm-backup-test-processo-arquivos")
    evidence_storage = MagicMock()
    evidence_storage.base_dir = tmp_ev
    processo_storage = MagicMock()
    processo_storage.base_dir = tmp_arq

    service = TransformometroBackupPackageService(
        json_backup=json_backup,
        storage=evidence_storage,
        processo_arquivo_storage=processo_storage,
    )
    import shutil

    for path in (tmp_ev, tmp_arq):
        if path.exists():
            shutil.rmtree(path)
    result = service.apply_package(raw, "replace", "modern")

    assert result["evidence_files_restored"] == 1
    assert result["processo_arquivo_files_restored"] == 1
    assert (tmp_ev / rid / stored_ev).read_bytes() == b"DATA"
    assert (tmp_arq / pid / stored_arq).read_bytes() == b"PROC"
    json_backup.apply.assert_called_once()
    for path in (tmp_ev, tmp_arq):
        if path.exists():
            shutil.rmtree(path)
