"""Casos de uso dos relatórios metalográficos."""

from __future__ import annotations

import hashlib
from io import BytesIO
from typing import Any
from uuid import uuid4

from PIL import Image

from app.application.services.engineering.metallographic_image_storage import (
    MetallographicImageStorage,
    new_stored_name,
)
from app.domain.engineering.metallographic_report import (
    CONCLUSION_RESULTS,
    IMAGE_SLOTS,
    SORT_VALUES,
    ImageNotFoundError,
    ImageStorageError,
    InvalidFilterError,
    ReportNotFoundError,
    etag_for,
    normalize_create_payload,
    normalize_patch_payload,
    parse_filter_date,
    parse_if_match,
    request_hash,
    require_idempotency_key,
    validate_slot,
)
from app.infrastructure.pdf.metallographic.metallographic_report_pdf_renderer import (
    MetallographicReportPdfRenderer,
)
from app.infrastructure.persistence.plugins.repositories.engineering.postgres_metallographic_report_repository import (
    PostgresMetallographicReportRepository,
)
from app.utils.logger import log_error, log_info, log_warning


class MetallographicReportService:
    def __init__(
        self,
        repository: PostgresMetallographicReportRepository | None = None,
        storage: MetallographicImageStorage | None = None,
        pdf_renderer: MetallographicReportPdfRenderer | None = None,
    ) -> None:
        self.repository = repository or PostgresMetallographicReportRepository()
        self.storage = storage or MetallographicImageStorage()
        self.pdf_renderer = pdf_renderer or MetallographicReportPdfRenderer()

    def create(self, *, actor: str, idempotency_key: str | None, payload: dict[str, Any]) -> dict[str, Any]:
        key = require_idempotency_key(idempotency_key)
        normalized = normalize_create_payload(payload)
        stored = self.repository.create_report(
            actor=actor,
            payload=normalized,
            idempotency_key=key,
            request_hash=request_hash(normalized),
        )
        report = stored["public"]
        self._log("create", actor, report["id"], "ok")
        return report

    def list_reports(
        self,
        *,
        page: int,
        page_size: int,
        sort: str,
        filters: dict[str, Any],
    ) -> dict[str, Any]:
        if sort not in SORT_VALUES:
            raise InvalidFilterError("Ordenação não permitida.")
        date_from = parse_filter_date(filters.get("report_date_from"), label="report_date_from")
        date_to = parse_filter_date(filters.get("report_date_to"), label="report_date_to")
        if date_from and date_to and date_from > date_to:
            raise InvalidFilterError("report_date_from não pode ser posterior a report_date_to.")
        result = filters.get("conclusion_result")
        if result and result not in CONCLUSION_RESULTS:
            raise InvalidFilterError("conclusion_result inválido.")
        clean: dict[str, Any] = {
            "report_date_from": date_from,
            "report_date_to": date_to,
            "conclusion_result": result or None,
        }
        for field in (
            "report_number",
            "terminal_code",
            "terminal_part_number",
            "product_harness",
            "cable",
            "conductor_section",
            "applicator_tool",
            "press_equipment",
            "batch_production_order",
            "sample_identification",
        ):
            value = filters.get(field)
            if value is None or not str(value).strip():
                continue
            text = str(value).strip()
            if len(text) > 240:
                raise InvalidFilterError(f"{field} excede 240 caracteres.")
            clean[field] = text
        page_result = self.repository.list_reports(
            filters=clean,
            page=page,
            page_size=page_size,
            sort=sort,
        )
        self._log("list", "authorized", "-", "ok")
        return page_result

    def get(self, report_id: str) -> dict[str, Any]:
        return self._require(report_id)["public"]

    def update(
        self,
        *,
        actor: str,
        report_id: str,
        if_match: str | None,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        version = parse_if_match(if_match)
        changes = normalize_patch_payload(payload)
        stored = self.repository.update_report(
            actor=actor,
            report_id=report_id,
            expected_version=version,
            changes=changes,
        )
        report = stored["public"]
        self._log("update", actor, report["id"], "ok")
        return report

    def delete(self, *, actor: str, report_id: str, if_match: str | None) -> dict[str, Any]:
        version = parse_if_match(if_match)
        deleted = self.repository.soft_delete(
            actor=actor,
            report_id=report_id,
            expected_version=version,
        )
        self._log("delete", actor, report_id, "ok")
        return deleted

    def copy(
        self,
        *,
        actor: str,
        report_id: str,
        idempotency_key: str | None,
    ) -> dict[str, Any]:
        key = require_idempotency_key(idempotency_key)
        source = self._require(report_id)
        public = source["public"]
        payload = {
            "report_date": public.get("report_date"),
            "revision": "00",
            "sample": public.get("sample") or {},
            "measurements": public.get("measurements") or {},
            "conclusion_result": (public.get("conclusion") or {}).get("result"),
            "conclusion_notes": (public.get("conclusion") or {}).get("notes"),
            "analyst_name": (public.get("analyst") or {}).get("name"),
            "status": "draft",
        }
        new_id = str(uuid4())
        prepared: list[dict[str, Any]] = []
        try:
            for slot in IMAGE_SLOTS:
                stored_name = (source.get("files") or {}).get(slot)
                if not stored_name:
                    continue
                content = self.storage.read(report_id=report_id, stored_name=stored_name)
                with Image.open(BytesIO(content)) as image:
                    width, height = image.size
                extension = "png" if str(stored_name).endswith(".png") else "jpg"
                name = new_stored_name(extension)
                self.storage.save(report_id=new_id, stored_name=name, content=content)
                content_type = (public.get("images") or {}).get(slot, {}).get("content_type")
                prepared.append({
                    "slot": slot,
                    "content_type": content_type or ("image/png" if extension == "png" else "image/jpeg"),
                    "size_bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "stored_name": name,
                    "width": width,
                    "height": height,
                })
            stored = self.repository.copy_report(
                actor=actor,
                source_id=report_id,
                report_id=new_id,
                payload=payload,
                idempotency_key=key,
                request_hash=request_hash({"source_id": report_id}),
                images=prepared,
            )
        except Exception:
            self._discard_new_files(new_id)
            raise
        if stored["public"]["id"] != new_id:
            self._discard_new_files(new_id)
        self._log("copy", actor, stored["public"]["id"], "ok")
        return stored["public"]

    def put_image(
        self,
        *,
        actor: str,
        report_id: str,
        slot: str,
        if_match: str | None,
        content: bytes,
        declared_type: str | None,
    ) -> dict[str, Any]:
        validate_slot(slot)
        version = parse_if_match(if_match)
        self._require(report_id)
        normalized = self.storage.validate_and_normalize(content, declared_type=declared_type)
        stored_name = new_stored_name(str(normalized["extension"]))
        self.storage.save(
            report_id=report_id,
            stored_name=stored_name,
            content=normalized["content"],  # type: ignore[arg-type]
        )
        try:
            saved = self.repository.put_image(
                actor=actor,
                report_id=report_id,
                expected_version=version,
                image={
                    "slot": slot,
                    "content_type": normalized["content_type"],
                    "size_bytes": normalized["size_bytes"],
                    "sha256": normalized["sha256"],
                    "stored_name": stored_name,
                    "width": normalized["width"],
                    "height": normalized["height"],
                },
            )
        except Exception:
            self.storage.delete(report_id=report_id, stored_name=stored_name)
            raise
        previous = saved.get("previous_stored_name")
        if previous and previous != stored_name:
            try:
                self.storage.delete(report_id=report_id, stored_name=previous)
            except ImageStorageError:
                log_warning(
                    f"metallographic_report operation=put_image actor={actor} "
                    f"report_id={report_id} outcome=orphan_cleanup_failed"
                )
        self._cleanup_orphans(report_id)
        self._log("put_image", actor, report_id, "ok")
        return saved["image"]

    def get_image(self, *, report_id: str, slot: str) -> dict[str, Any]:
        validate_slot(slot)
        stored = self._require(report_id)
        stored_name = (stored.get("files") or {}).get(slot)
        if not stored_name:
            raise ImageNotFoundError("Imagem não encontrada.")
        content = self.storage.read(report_id=report_id, stored_name=stored_name)
        meta = stored["public"]["images"][slot]
        return {
            "content": content,
            "content_type": meta.get("content_type") or "application/octet-stream",
            "etag": etag_for(stored["public"]["version"]),
            "filename": f"{slot}.jpg" if "jpeg" in str(meta.get("content_type")) else f"{slot}.png",
        }

    def delete_image(
        self,
        *,
        actor: str,
        report_id: str,
        slot: str,
        if_match: str | None,
    ) -> dict[str, Any]:
        validate_slot(slot)
        version = parse_if_match(if_match)
        removed = self.repository.delete_image(
            actor=actor,
            report_id=report_id,
            slot=slot,
            expected_version=version,
        )
        try:
            self.storage.delete(report_id=report_id, stored_name=removed.get("stored_name"))
            self._cleanup_orphans(report_id)
        except ImageStorageError:
            log_warning(
                f"metallographic_report operation=delete_image actor={actor} "
                f"report_id={report_id} outcome=file_cleanup_failed"
            )
        self._log("delete_image", actor, report_id, "ok")
        return {"slot": slot, "deleted": True, "version": removed["version"]}

    def export_pdf(self, *, actor: str, report_id: str) -> dict[str, Any]:
        stored = self._require(report_id)
        images: dict[str, bytes] = {}
        for slot in IMAGE_SLOTS:
            stored_name = (stored.get("files") or {}).get(slot)
            if not stored_name:
                continue
            images[slot] = self.storage.read(report_id=report_id, stored_name=stored_name)
        pdf = self.pdf_renderer.render(stored["public"], images)
        self.repository.record_export(actor=actor, report_id=report_id)
        number = stored["public"]["report_number"]
        self._log("export_pdf", actor, report_id, "ok")
        return {
            "content": pdf,
            "filename": f"metalografia-{number}.pdf",
            "etag": etag_for(stored["public"]["version"]),
        }

    def _require(self, report_id: str) -> dict[str, Any]:
        stored = self.repository.get_report(report_id)
        if stored is None:
            raise ReportNotFoundError("Relatório não encontrado.")
        return stored

    def _cleanup_orphans(self, report_id: str) -> None:
        referenced = self.repository.referenced_stored_names(report_id)
        self.storage.drop_unreferenced(report_id=report_id, referenced=referenced)

    def _discard_new_files(self, report_id: str) -> None:
        try:
            self.storage.drop_unreferenced(report_id=report_id, referenced=set())
        except ImageStorageError:
            log_error(
                f"metallographic_report operation=copy report_id={report_id} "
                "outcome=orphan_cleanup_failed"
            )

    def _log(self, operation: str, actor: str, report_id: str, outcome: str) -> None:
        log_info(
            "metallographic_report "
            f"operation={operation} actor={actor} report_id={report_id} outcome={outcome}"
        )

