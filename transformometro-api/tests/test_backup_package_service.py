from __future__ import annotations

import io
import json
import zipfile
from unittest.mock import MagicMock

from tm_app.application.services.backup_package_service import (
    CADASTRO_FILENAME,
    MANIFEST_FILENAME,
    TransformometroBackupPackageService,
    evidence_archive_path,
)
from tm_app.application.services.json_backup_service import SCHEMA_VERSION


def _sample_cadastro() -> dict:
    rid = "22222222-2222-2222-2222-222222222222"
    eid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    return {
        "schema_version": SCHEMA_VERSION,
        "exported_at": "2026-07-06T00:00:00+00:00",
        "import_format": "modern",
        "counts": {"revisao_evidencias": 1, "evidence_files": 1},
        "filiais": [],
        "setores": [],
        "setor_filiais": [],
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
        "revisoes": [{"revisao_id": rid, "processo_id": "11111111-1111-1111-1111-111111111111", "versao_revisao": "v1", "deletado": False}],
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
    }


def _build_zip(cadastro: dict, evidence_files: dict[str, bytes] | None = None) -> bytes:
    import hashlib

    evidence_files = evidence_files or {}
    cadastro_bytes = json.dumps(cadastro).encode("utf-8")
    entries = {
        CADASTRO_FILENAME: {
            "sha256": hashlib.sha256(cadastro_bytes).hexdigest(),
            "size_bytes": len(cadastro_bytes),
        }
    }
    for path, content in evidence_files.items():
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
        for path, content in evidence_files.items():
            archive.writestr(path, content)
    return buffer.getvalue()


def test_evidence_archive_path():
    path = evidence_archive_path("22222222-2222-2222-2222-222222222222", "file.pdf")
    assert path == "evidencias/22222222-2222-2222-2222-222222222222/file.pdf"


def test_export_package_includes_manifest_and_evidence():
    cadastro = _sample_cadastro()
    rid = cadastro["revisao_evidencias"][0]["revisao_id"]
    stored = cadastro["revisao_evidencias"][0]["nome_armazenado"]
    json_backup = MagicMock()
    json_backup.export_bundle.return_value = cadastro

    storage = MagicMock()
    mock_path = MagicMock()
    mock_path.read_bytes.return_value = b"PDF1"
    storage.resolve_file.return_value = mock_path

    service = TransformometroBackupPackageService(json_backup=json_backup, storage=storage)
    payload = service.export_package()

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = set(archive.namelist())
        assert MANIFEST_FILENAME in names
        assert CADASTRO_FILENAME in names
        assert evidence_archive_path(rid, stored) in names
        manifest = json.loads(archive.read(MANIFEST_FILENAME))
        assert manifest["package_format"] == "transformometro_backup"
        assert manifest["schema_version"] == SCHEMA_VERSION


def test_preview_package_rejects_missing_evidence_file():
    cadastro = _sample_cadastro()
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
    )
    result = service.preview_package(raw, "merge", "modern")
    assert result["valid"] is False
    assert any("Evidência sem arquivo" in err for err in result["errors"])


def test_apply_package_restores_files_on_replace():
    cadastro = _sample_cadastro()
    rid = cadastro["revisao_evidencias"][0]["revisao_id"]
    stored = cadastro["revisao_evidencias"][0]["nome_armazenado"]
    rel = evidence_archive_path(rid, stored)
    raw = _build_zip(cadastro, {rel: b"DATA"})

    json_backup = MagicMock()
    json_backup.preview.return_value = {
        "valid": True,
        "errors": [],
        "mode": "replace",
        "entities": {},
    }
    json_backup.apply.return_value = {"mode": "replace", "entities": {}}

    from pathlib import Path

    tmp_base = Path("/tmp/tm-backup-test-evidence")
    storage = MagicMock()
    storage.base_dir = tmp_base

    service = TransformometroBackupPackageService(json_backup=json_backup, storage=storage)
    if tmp_base.exists():
        import shutil

        shutil.rmtree(tmp_base)
    result = service.apply_package(raw, "replace", "modern")

    assert result["evidence_files_restored"] == 1
    assert (tmp_base / rid / stored).read_bytes() == b"DATA"
    json_backup.apply.assert_called_once()
    if tmp_base.exists():
        import shutil

        shutil.rmtree(tmp_base)
