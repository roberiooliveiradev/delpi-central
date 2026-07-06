from __future__ import annotations

import hashlib
import io
import json
import shutil
import zipfile
from datetime import datetime, timezone
from typing import Any

from tm_app.application.services.json_backup_service import (
    ExportMode,
    ImportFormat,
    JsonBackupService,
)
from tm_app.application.services.revisao_evidence_storage import RevisaoEvidenceStorage
from tm_app.config import settings
from tm_app.core.serialize import json_safe
from tm_app.infrastructure.persistence.json_backup_repository import REVISAO_EVIDENCIAS_BUNDLE_KEY

PACKAGE_FORMAT = "transformometro_backup"
PACKAGE_VERSION = "1.0"
MANIFEST_FILENAME = "manifest.json"
CADASTRO_FILENAME = "cadastro.json"
EVIDENCE_PREFIX = "evidencias/"


def evidence_archive_path(revisao_id: str, stored_name: str) -> str:
    return f"{EVIDENCE_PREFIX}{revisao_id.strip()}/{stored_name.strip()}"


def _sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _is_safe_archive_path(path: str) -> bool:
    normalized = path.replace("\\", "/").strip()
    if not normalized or normalized.startswith("/") or ".." in normalized.split("/"):
        return False
    if normalized == CADASTRO_FILENAME or normalized == MANIFEST_FILENAME:
        return True
    if normalized.startswith(EVIDENCE_PREFIX):
        parts = normalized.split("/")
        return len(parts) == 3 and bool(parts[1]) and bool(parts[2])
    return False


class TransformometroBackupPackageService:
    def __init__(
        self,
        json_backup: JsonBackupService | None = None,
        storage: RevisaoEvidenceStorage | None = None,
    ) -> None:
        self._json_backup = json_backup or JsonBackupService()
        self._storage = storage or RevisaoEvidenceStorage()
        self._max_bytes = int(
            getattr(settings, "TM_BACKUP_PACKAGE_MAX_BYTES", 500 * 1024 * 1024)
        )

    def export_package(self) -> bytes:
        cadastro = self._json_backup.export_bundle()
        cadastro_bytes = json.dumps(
            json_safe(cadastro), ensure_ascii=False, indent=2
        ).encode("utf-8")

        entries: dict[str, dict[str, Any]] = {
            CADASTRO_FILENAME: {
                "sha256": _sha256_hex(cadastro_bytes),
                "size_bytes": len(cadastro_bytes),
            }
        }

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(CADASTRO_FILENAME, cadastro_bytes)

            for row in cadastro.get(REVISAO_EVIDENCIAS_BUNDLE_KEY) or []:
                if not isinstance(row, dict):
                    continue
                stored_name = (row.get("nome_armazenado") or "").strip()
                revisao_id = str(row.get("revisao_id") or "").strip()
                if not stored_name or not revisao_id:
                    continue
                try:
                    file_path = self._storage.resolve_file(
                        revisao_id=revisao_id, stored_name=stored_name
                    )
                except Exception:
                    continue
                rel_path = evidence_archive_path(revisao_id, stored_name)
                content = file_path.read_bytes()
                archive.writestr(rel_path, content)
                entries[rel_path] = {
                    "sha256": _sha256_hex(content),
                    "size_bytes": len(content),
                }

            manifest = {
                "package_format": PACKAGE_FORMAT,
                "package_version": PACKAGE_VERSION,
                "schema_version": cadastro.get("schema_version"),
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "entries": entries,
                "counts": {
                    **(cadastro.get("counts") or {}),
                    "evidence_files": sum(
                        1 for key in entries if key.startswith(EVIDENCE_PREFIX)
                    ),
                },
            }
            manifest_bytes = json.dumps(
                json_safe(manifest), ensure_ascii=False, indent=2
            ).encode("utf-8")
            archive.writestr(MANIFEST_FILENAME, manifest_bytes)

        payload = buffer.getvalue()
        if len(payload) > self._max_bytes:
            raise ValueError(
                f"Pacote excede o limite de {self._max_bytes // (1024 * 1024)} MB."
            )
        return payload

    def parse_package(self, raw: bytes) -> tuple[dict[str, Any], dict[str, bytes], dict[str, Any]]:
        if len(raw) > self._max_bytes:
            raise ValueError(
                f"Pacote excede o limite de {self._max_bytes // (1024 * 1024)} MB."
            )

        files: dict[str, bytes] = {}
        with zipfile.ZipFile(io.BytesIO(raw), "r") as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                name = info.filename.replace("\\", "/").strip()
                if not _is_safe_archive_path(name):
                    raise ValueError(f"Caminho inválido no pacote: {name}")
                files[name] = archive.read(info)

        manifest_raw = files.get(MANIFEST_FILENAME)
        if not manifest_raw:
            raise ValueError("Pacote sem manifest.json.")

        manifest = json.loads(manifest_raw.decode("utf-8"))
        if manifest.get("package_format") != PACKAGE_FORMAT:
            raise ValueError("Formato de pacote não reconhecido.")

        cadastro_raw = files.get(CADASTRO_FILENAME)
        if not cadastro_raw:
            raise ValueError("Pacote sem cadastro.json.")

        cadastro = json.loads(cadastro_raw.decode("utf-8"))
        return manifest, cadastro, files

    def validate_package_integrity(
        self,
        manifest: dict[str, Any],
        files: dict[str, bytes],
    ) -> list[str]:
        errors: list[str] = []
        entries = manifest.get("entries") or {}
        if not isinstance(entries, dict):
            return ["Manifesto inválido: entries ausente."]

        for path, meta in entries.items():
            if not isinstance(meta, dict):
                errors.append(f"Entrada inválida no manifesto: {path}.")
                continue
            expected = meta.get("sha256")
            content = files.get(path)
            if content is None:
                errors.append(f"Arquivo ausente no pacote: {path}.")
                continue
            actual = _sha256_hex(content)
            if expected and actual != expected:
                errors.append(f"Checksum inválido: {path}.")

        for path in files:
            if path in {MANIFEST_FILENAME, CADASTRO_FILENAME}:
                continue
            if path.startswith(EVIDENCE_PREFIX) and path not in entries:
                errors.append(f"Arquivo de evidência não listado no manifesto: {path}.")

        return errors

    def validate_evidence_files(
        self,
        cadastro: dict[str, Any],
        files: dict[str, bytes],
    ) -> list[str]:
        errors: list[str] = []
        for row in cadastro.get(REVISAO_EVIDENCIAS_BUNDLE_KEY) or []:
            if not isinstance(row, dict):
                continue
            stored_name = (row.get("nome_armazenado") or "").strip()
            revisao_id = str(row.get("revisao_id") or "").strip()
            tipo = (row.get("tipo") or "anexo").strip().lower()
            if tipo == "link" or not stored_name:
                continue
            rel_path = evidence_archive_path(revisao_id, stored_name)
            if rel_path not in files:
                label = row.get("nome_arquivo") or stored_name
                errors.append(
                    f"Evidência sem arquivo no pacote: {label} ({rel_path})."
                )
        return errors

    def preview_package(
        self,
        raw: bytes,
        mode: ExportMode,
        import_format: ImportFormat = "auto",
    ) -> dict[str, Any]:
        try:
            manifest, cadastro, files = self.parse_package(raw)
        except (ValueError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
            return {
                "valid": False,
                "errors": [str(exc)],
                "mode": mode,
                "package_format": PACKAGE_FORMAT,
                "format_compatible": False,
            }

        integrity_errors = self.validate_package_integrity(manifest, files)
        evidence_errors = self.validate_evidence_files(cadastro, files)
        errors = integrity_errors + evidence_errors

        cadastro_preview = self._json_backup.preview(cadastro, mode, import_format)
        evidence_files = [
            path for path in files if path.startswith(EVIDENCE_PREFIX)
        ]
        expected_files = sum(
            1
            for row in (cadastro.get(REVISAO_EVIDENCIAS_BUNDLE_KEY) or [])
            if isinstance(row, dict)
            and (row.get("nome_armazenado") or "").strip()
            and (row.get("tipo") or "anexo").strip().lower() != "link"
        )

        result = {
            **cadastro_preview,
            "package_format": PACKAGE_FORMAT,
            "package_version": manifest.get("package_version"),
            "manifest_schema_version": manifest.get("schema_version"),
            "evidence_files": {
                "in_package": len(evidence_files),
                "expected_from_metadata": expected_files,
                "missing_paths": evidence_errors,
            },
        }
        if errors:
            result["valid"] = False
            result["errors"] = _dedupe([*(result.get("errors") or []), *errors])
        return result

    def apply_package(
        self,
        raw: bytes,
        mode: ExportMode,
        import_format: ImportFormat = "auto",
    ) -> dict[str, Any]:
        preview = self.preview_package(raw, mode, import_format)
        if not preview.get("valid"):
            raise ValueError("; ".join(preview.get("errors") or ["Pacote inválido."]))

        manifest, cadastro, files = self.parse_package(raw)
        cadastro_result = self._json_backup.apply(cadastro, mode, import_format)

        if mode == "replace":
            self._clear_evidence_storage()

        restored = self._restore_evidence_files(files)
        return {
            **cadastro_result,
            "package_format": PACKAGE_FORMAT,
            "package_version": manifest.get("package_version"),
            "evidence_files_restored": restored,
        }

    def _restore_evidence_files(self, files: dict[str, bytes]) -> int:
        restored = 0
        for path, content in files.items():
            if not path.startswith(EVIDENCE_PREFIX):
                continue
            parts = path.split("/")
            if len(parts) != 3:
                continue
            revisao_id, stored_name = parts[1], parts[2]
            target_dir = self._storage.base_dir / revisao_id
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / stored_name).write_bytes(content)
            restored += 1
        return restored

    def _clear_evidence_storage(self) -> None:
        base = self._storage.base_dir
        if base.exists():
            shutil.rmtree(base)
        base.mkdir(parents=True, exist_ok=True)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique
