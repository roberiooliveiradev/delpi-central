"""Regras, persistência em memória e arquivos dos relatórios metalográficos."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from PIL import Image

from app.application.services.engineering.metallographic_image_storage import (
    MetallographicImageStorage,
)
from app.application.services.engineering.metallographic_report_service import (
    MetallographicReportService,
)
from app.domain.engineering.metallographic_report import (
    IdempotencyConflictError,
    IdempotencyKeyRequiredError,
    ImageNotFoundError,
    ImageTooLargeError,
    InvalidFilterError,
    InvalidImageError,
    PayloadValidationError,
    PreconditionRequiredError,
    ReportNotFoundError,
    ReportVersionConflictError,
    UnsupportedImageError,
    normalize_create_payload,
)
from app.infrastructure.pdf.metallographic.metallographic_report_pdf_renderer import (
    MetallographicReportPdfRenderer,
)


def _png(color: tuple[int, int, int] = (20, 40, 80)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (32, 24), color).save(buffer, format="PNG")
    return buffer.getvalue()


class MemoryMetallographicRepository:
    def __init__(self) -> None:
        self.reports: dict[str, dict] = {}
        self.images: dict[str, dict[str, dict]] = {}
        self.keys: dict[tuple[str, str, str], tuple[str, str]] = {}
        self.counter = 0
        self.audits: list[dict] = []
        self.fail_put = False

    def create_report(self, *, actor, payload, idempotency_key, request_hash):
        return self._insert(
            actor=actor,
            payload=payload,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            operation="create",
            report_id=str(uuid4()),
            images=[],
        )

    def copy_report(self, *, actor, source_id, report_id, payload, idempotency_key, request_hash, images):
        if self.get_report(source_id) is None:
            raise ReportNotFoundError("Relatório não encontrado.")
        return self._insert(
            actor=actor,
            payload=payload,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            operation="copy",
            report_id=report_id,
            images=images,
        )

    def _insert(self, *, actor, payload, idempotency_key, request_hash, operation, report_id, images):
        replay_key = (actor, operation, idempotency_key)
        existing = self.keys.get(replay_key)
        if existing:
            previous_hash, previous_id = existing
            if previous_hash != request_hash:
                raise IdempotencyConflictError("A Idempotency-Key já foi usada com outro conteúdo.")
            stored = self.get_report(previous_id)
            if stored is None:
                raise IdempotencyConflictError(
                    "A Idempotency-Key já foi usada e o relatório não está mais disponível."
                )
            return stored
        self.counter += 1
        now = datetime.now(timezone.utc).isoformat()
        year = datetime.now().year
        row = {
            "id": report_id,
            "report_number": f"MET-{year}-{self.counter:06d}",
            "report_date": payload.get("report_date"),
            "revision": payload.get("revision") or "00",
            "sample": deepcopy(payload.get("sample") or {}),
            "measurements": deepcopy(payload.get("measurements") or {}),
            "conclusion_result": payload.get("conclusion_result"),
            "conclusion_notes": payload.get("conclusion_notes"),
            "analyst_name": payload.get("analyst_name"),
            "status": "draft",
            "version": 1,
            "created_at": now,
            "updated_at": now,
            "created_by": actor,
            "updated_by": actor,
            "deleted": False,
        }
        self.reports[report_id] = row
        self.images[report_id] = {}
        for image in images:
            self.images[report_id][image["slot"]] = dict(image)
        self.keys[replay_key] = (request_hash, report_id)
        self.audits.append({"report_id": report_id, "operation": operation, "actor": actor})
        return self.get_report(report_id)

    def get_report(self, report_id):
        row = self.reports.get(report_id)
        if row is None or row["deleted"]:
            return None
        return {"public": self._public(row), "files": self._files(report_id)}

    def list_reports(self, *, filters, page, page_size, sort):
        rows = [row for row in self.reports.values() if not row["deleted"]]

        def effective_date(row):
            return row["report_date"] or row["created_at"][:10]

        if filters.get("report_date_from"):
            rows = [row for row in rows if effective_date(row) >= filters["report_date_from"]]
        if filters.get("report_date_to"):
            rows = [row for row in rows if effective_date(row) <= filters["report_date_to"]]
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
            expected = filters.get(field)
            if not expected:
                continue
            needle = expected.casefold()
            rows = [
                row for row in rows
                if needle in str(
                    row["report_number"] if field == "report_number" else row["sample"].get(field) or ""
                ).casefold()
            ]
        if filters.get("conclusion_result"):
            rows = [row for row in rows if row["conclusion_result"] == filters["conclusion_result"]]
        reverse = sort != "report_number_asc" and sort != "created_at_asc"
        if sort == "report_number_asc":
            rows.sort(key=lambda row: (row["report_number"], row["id"]))
        elif sort == "report_date_desc":
            rows.sort(key=lambda row: (row["report_date"] or "", row["id"]), reverse=True)
        elif sort == "created_at_asc":
            rows.sort(key=lambda row: (row["created_at"], row["id"]))
        else:
            rows.sort(key=lambda row: (row["created_at"], row["id"]), reverse=reverse)
        total = len(rows)
        start = (page - 1) * page_size
        page_rows = rows[start:start + page_size]
        return {
            "items": [self._public(row) for row in page_rows],
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": page * page_size < total,
        }

    def update_report(self, *, actor, report_id, expected_version, changes):
        row = self._active(report_id)
        if row["version"] != expected_version:
            raise ReportVersionConflictError("O relatório foi alterado por outra pessoa.")
        if "sample" in changes:
            row["sample"].update(changes["sample"])
        if "measurements" in changes:
            row["measurements"].update(changes["measurements"])
        for key in ("report_date", "revision", "conclusion_result", "conclusion_notes", "analyst_name", "status"):
            if key in changes:
                row[key] = changes[key]
        row["version"] += 1
        row["updated_by"] = actor
        row["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.audits.append({"report_id": report_id, "operation": "update", "fields": sorted(changes)})
        return self.get_report(report_id)

    def soft_delete(self, *, actor, report_id, expected_version):
        row = self._active(report_id)
        if row["version"] != expected_version:
            raise ReportVersionConflictError("O relatório foi alterado por outra pessoa.")
        row["deleted"] = True
        row["version"] += 1
        row["updated_by"] = actor
        self.audits.append({"report_id": report_id, "operation": "delete", "actor": actor})
        return {"id": report_id, "deleted": True, "version": row["version"]}

    def put_image(self, *, actor, report_id, expected_version, image):
        if self.fail_put:
            raise ReportVersionConflictError("falha simulada")
        row = self._active(report_id)
        if row["version"] != expected_version:
            raise ReportVersionConflictError("O relatório foi alterado por outra pessoa.")
        previous = self.images.setdefault(report_id, {}).get(image["slot"])
        self.images[report_id][image["slot"]] = dict(image)
        row["version"] += 1
        row["updated_by"] = actor
        return {
            "previous_stored_name": None if previous is None else previous.get("stored_name"),
            "image": {
                "slot": image["slot"],
                "content_type": image["content_type"],
                "size_bytes": image["size_bytes"],
                "sha256": image["sha256"],
                "version": row["version"],
                "updated_at": row["updated_at"],
            },
        }

    def delete_image(self, *, actor, report_id, slot, expected_version):
        row = self._active(report_id)
        if row["version"] != expected_version:
            raise ReportVersionConflictError("O relatório foi alterado por outra pessoa.")
        current = self.images.get(report_id, {}).pop(slot, None)
        if current is None:
            raise ReportNotFoundError("Imagem não encontrada.")
        row["version"] += 1
        return {"stored_name": current.get("stored_name"), "version": row["version"]}

    def referenced_stored_names(self, report_id):
        return {
            item["stored_name"]
            for item in self.images.get(report_id, {}).values()
            if item.get("stored_name")
        }

    def record_export(self, *, actor, report_id):
        self._active(report_id)
        before = self.reports[report_id]["version"]
        self.audits.append({"report_id": report_id, "operation": "export_pdf", "actor": actor})
        assert self.reports[report_id]["version"] == before

    def _active(self, report_id):
        row = self.reports.get(report_id)
        if row is None or row["deleted"]:
            raise ReportNotFoundError("Relatório não encontrado.")
        return row

    def _files(self, report_id):
        images = self.images.get(report_id, {})
        return {
            slot: None if images.get(slot) is None else images[slot].get("stored_name")
            for slot in ("original", "measured")
        }

    def _public(self, row):
        images = self.images.get(row["id"], {})

        def flag(slot):
            image = images.get(slot)
            if not image:
                return {"present": False, "content_type": None, "sha256": None}
            return {
                "present": True,
                "content_type": image["content_type"],
                "sha256": image["sha256"],
            }

        return {
            "id": row["id"],
            "report_number": row["report_number"],
            "report_date": row["report_date"],
            "revision": row["revision"],
            "sample": deepcopy(row["sample"]),
            "measurements": deepcopy(row["measurements"]),
            "conclusion": {"result": row["conclusion_result"], "notes": row["conclusion_notes"]},
            "analyst": {"name": row["analyst_name"], "user_id": None},
            "images": {"original": flag("original"), "measured": flag("measured")},
            "status": row["status"],
            "version": row["version"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "created_by": row["created_by"],
            "updated_by": row["updated_by"],
        }


def _service(tmp_path: Path) -> tuple[MetallographicReportService, MemoryMetallographicRepository]:
    repository = MemoryMetallographicRepository()
    service = MetallographicReportService(
        repository=repository,  # type: ignore[arg-type]
        storage=MetallographicImageStorage(str(tmp_path)),
        pdf_renderer=MetallographicReportPdfRenderer(),
    )
    return service, repository


def _payload(**overrides):
    body = {
        "report_date": "2026-10-21",
        "revision": "00",
        "sample": {
            "terminal_code": "TERM-1",
            "terminal_part_number": "PN-1",
            "product_harness": "CHICOTE / REV A",
            "cable": "CABO-1",
            "conductor_section": "0.75 mm2",
            "applicator_tool": "APL-1",
            "press_equipment": "PRENSA-1",
            "batch_production_order": "OP-1",
            "sample_identification": "AMOSTRA-01",
        },
        "measurements": {
            "crimp_height_ch": {"criterion": "1.10-1.30", "measured": "1.20"},
            "crimp_width_cb": {"criterion": "2.00-2.20", "measured": "2.10"},
            "void_area_av": {"criterion": "<=5", "measured": "4.5"},
            "left_burr_gh_e": {"criterion": "<=0.10", "measured": "0.08"},
            "right_burr_gh_d": {"criterion": "<=0.10", "measured": "0.07"},
        },
        "conclusion": {"result": "conforming", "notes": "Sem desvio visível."},
        "analyst": {"name": "Analista de exemplo"},
        "status": "draft",
    }
    body.update(overrides)
    return body


def test_create_assigns_unique_numbers_and_preserves_fields(tmp_path: Path) -> None:
    service, _repository = _service(tmp_path)
    first = service.create(actor="user-1", idempotency_key="create-key-01", payload=_payload())
    second = service.create(
        actor="user-1",
        idempotency_key="create-key-02",
        payload=_payload(sample={**_payload()["sample"], "terminal_code": "TERM-2"}),
    )
    assert first["id"] != second["id"]
    assert first["report_number"] != second["report_number"]
    assert first["report_number"].startswith("MET-")
    assert first["sample"]["terminal_code"] == "TERM-1"
    assert first["measurements"]["crimp_height_ch"]["measured"] == "1.20"
    assert first["conclusion"]["result"] == "conforming"
    assert first["created_by"] == "user-1"
    assert first["version"] == 1
    again = service.get(first["id"])
    assert again["report_number"] == first["report_number"]
    assert again["measurements"]["right_burr_gh_d"]["criterion"] == "<=0.10"


def test_idempotent_create_does_not_allocate_a_second_number(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    payload = _payload()
    first = service.create(actor="user-1", idempotency_key="create-key-01", payload=payload)
    replay = service.create(actor="user-1", idempotency_key="create-key-01", payload=payload)
    assert replay["id"] == first["id"]
    assert repository.counter == 1
    with pytest.raises(IdempotencyConflictError):
        service.create(
            actor="user-1",
            idempotency_key="create-key-01",
            payload=_payload(revision="01"),
        )
    with pytest.raises(IdempotencyKeyRequiredError):
        service.create(actor="user-1", idempotency_key=None, payload=payload)


def test_combined_filters_pagination_and_negative_result(tmp_path: Path) -> None:
    service, _repository = _service(tmp_path)
    service.create(actor="user-1", idempotency_key="create-key-01", payload=_payload())
    other = _payload()
    other["sample"] = {**other["sample"], "terminal_code": "OUTRO", "cable": "CABO-9"}
    other["conclusion"] = {"result": "nonconforming", "notes": "desvio"}
    service.create(actor="user-1", idempotency_key="create-key-02", payload=other)
    found = service.list_reports(
        page=1,
        page_size=20,
        sort="report_number_asc",
        filters={"terminal_code": "term-1", "cable": "cabo-1", "conclusion_result": "conforming"},
    )
    assert found["total"] == 1
    assert found["items"][0]["sample"]["terminal_code"] == "TERM-1"
    assert found["has_next"] is False
    empty = service.list_reports(
        page=1,
        page_size=20,
        sort="created_at_desc",
        filters={"terminal_code": "term-1", "conclusion_result": "nonconforming"},
    )
    assert empty["items"] == []
    assert empty["total"] == 0
    with pytest.raises(InvalidFilterError):
        service.list_reports(
            page=1,
            page_size=20,
            sort="created_at_desc",
            filters={"report_date_from": "2026-12-31", "report_date_to": "2026-01-01"},
        )


def test_patch_requires_version_and_keeps_omitted_fields(tmp_path: Path) -> None:
    service, _repository = _service(tmp_path)
    created = service.create(actor="user-1", idempotency_key="create-key-01", payload=_payload())
    with pytest.raises(PreconditionRequiredError):
        service.update(actor="user-2", report_id=created["id"], if_match=None, payload={"revision": "01"})
    with pytest.raises(ReportVersionConflictError):
        service.update(actor="user-2", report_id=created["id"], if_match='"9"', payload={"revision": "01"})
    updated = service.update(
        actor="user-2",
        report_id=created["id"],
        if_match='"1"',
        payload={"revision": "01", "sample": {"cable": "CABO-2"}},
    )
    assert updated["version"] == 2
    assert updated["revision"] == "01"
    assert updated["sample"]["cable"] == "CABO-2"
    assert updated["sample"]["terminal_code"] == "TERM-1"
    assert updated["updated_by"] == "user-2"
    assert updated["measurements"]["void_area_av"]["measured"] == "4.5"


def test_soft_delete_hides_report_and_copy_is_independent(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    created = service.create(actor="user-1", idempotency_key="create-key-01", payload=_payload())
    service.put_image(
        actor="user-1",
        report_id=created["id"],
        slot="original",
        if_match='"1"',
        content=_png(),
        declared_type="image/png",
    )
    current = service.get(created["id"])
    copied = service.copy(actor="user-2", report_id=created["id"], idempotency_key="copy-key-0001")
    assert copied["id"] != created["id"]
    assert copied["report_number"] != created["report_number"]
    assert copied["revision"] == "00"
    assert copied["created_by"] == "user-2"
    assert copied["images"]["original"]["present"] is True
    original_after_copy = service.get(created["id"])
    assert original_after_copy["version"] == current["version"]
    assert original_after_copy["report_number"] == created["report_number"]
    replay = service.copy(actor="user-2", report_id=created["id"], idempotency_key="copy-key-0001")
    assert replay["id"] == copied["id"]
    deleted = service.delete(actor="user-1", report_id=created["id"], if_match=f'"{original_after_copy["version"]}"')
    assert deleted["deleted"] is True
    with pytest.raises(ReportNotFoundError):
        service.get(created["id"])
    listed = service.list_reports(page=1, page_size=20, sort="created_at_desc", filters={})
    assert copied["id"] in {item["id"] for item in listed["items"]}
    assert created["id"] not in {item["id"] for item in listed["items"]}
    assert any(item["operation"] == "delete" for item in repository.audits)


def test_images_round_trip_replace_remove_and_survive_new_storage(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    created = service.create(actor="user-1", idempotency_key="create-key-01", payload=_payload())
    original = service.put_image(
        actor="user-1",
        report_id=created["id"],
        slot="original",
        if_match='"1"',
        content=_png((1, 2, 3)),
        declared_type="image/png",
    )
    measured = service.put_image(
        actor="user-1",
        report_id=created["id"],
        slot="measured",
        if_match=f'"{original["version"]}"',
        content=_png((4, 5, 6)),
        declared_type="image/png",
    )
    reopened = MetallographicReportService(
        repository=repository,  # type: ignore[arg-type]
        storage=MetallographicImageStorage(str(tmp_path)),
        pdf_renderer=MetallographicReportPdfRenderer(),
    )
    loaded = reopened.get_image(report_id=created["id"], slot="original")
    assert loaded["content"][:8] == b"\x89PNG\r\n\x1a\n"
    assert loaded["content_type"] == "image/png"
    replaced = reopened.put_image(
        actor="user-1",
        report_id=created["id"],
        slot="original",
        if_match=f'"{measured["version"]}"',
        content=_png((9, 9, 9)),
        declared_type="image/png",
    )
    assert replaced["sha256"] != original["sha256"]
    removed = reopened.delete_image(
        actor="user-1",
        report_id=created["id"],
        slot="measured",
        if_match=f'"{replaced["version"]}"',
    )
    assert removed["deleted"] is True
    with pytest.raises(ImageNotFoundError):
        reopened.get_image(report_id=created["id"], slot="measured")
    with pytest.raises(UnsupportedImageError):
        reopened.put_image(
            actor="user-1",
            report_id=created["id"],
            slot="original",
            if_match=f'"{removed["version"]}"',
            content=b"GIF89a-not-an-image",
            declared_type="image/gif",
        )
    with pytest.raises(ImageTooLargeError):
        reopened.put_image(
            actor="user-1",
            report_id=created["id"],
            slot="original",
            if_match=f'"{removed["version"]}"',
            content=b"\x89PNG\r\n\x1a\n" + (b"0" * (8 * 1024 * 1024)),
            declared_type="image/png",
        )
    with pytest.raises(InvalidImageError):
        reopened.put_image(
            actor="user-1",
            report_id=created["id"],
            slot="original",
            if_match=f'"{removed["version"]}"',
            content=b"\x89PNG\r\n\x1a\nnot-a-real-png",
            declared_type="image/png",
        )


def test_failed_image_write_removes_orphan_file(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    created = service.create(actor="user-1", idempotency_key="create-key-01", payload=_payload())
    repository.fail_put = True
    with pytest.raises(ReportVersionConflictError):
        service.put_image(
            actor="user-1",
            report_id=created["id"],
            slot="original",
            if_match='"1"',
            content=_png(),
            declared_type="image/png",
        )
    assert list(Path(tmp_path).rglob("*.png")) == []
    assert list(Path(tmp_path).rglob("*.part")) == []


def test_pdf_export_keeps_snapshot_and_sections(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    created = service.create(actor="user-1", idempotency_key="create-key-01", payload=_payload())
    service.put_image(
        actor="user-1",
        report_id=created["id"],
        slot="original",
        if_match='"1"',
        content=_png(),
        declared_type="image/png",
    )
    current = service.get(created["id"])
    exported = service.export_pdf(actor="user-1", report_id=created["id"])
    assert exported["content"].startswith(b"%PDF")
    assert exported["filename"] == f"metalografia-{created['report_number']}.pdf"
    text = exported["content"].decode("latin1", errors="ignore")
    assert created["report_number"] in text
    assert "IDENTIFICA" in text
    assert "CH" in text
    assert "RASCUNHO" in text
    assert "Conforme" in text
    after = service.get(created["id"])
    assert after["version"] == current["version"]
    assert after["revision"] == current["revision"]
    assert any(item["operation"] == "export_pdf" for item in repository.audits)


def test_server_owned_fields_and_numeric_measurement_are_rejected() -> None:
    with pytest.raises(PayloadValidationError):
        normalize_create_payload({"id": "not-allowed", "report_number": "MET-1"})
    with pytest.raises(PayloadValidationError):
        normalize_create_payload({"measurements": {"crimp_height_ch": {"measured": 1.2}}})
    with pytest.raises(PayloadValidationError):
        normalize_create_payload({"status": "approved"})
    draft = normalize_create_payload({})
    assert draft["status"] == "draft"
    assert draft["revision"] == "00"
    assert draft["conclusion_result"] is None


def test_storage_rejects_path_escape(tmp_path: Path) -> None:
    storage = MetallographicImageStorage(str(tmp_path))
    from app.domain.engineering.metallographic_report import ImageStorageError

    with pytest.raises(ImageStorageError):
        storage.save(report_id="../etc", stored_name="abcdefabcdefabcdefabcdefabcdefab.png", content=b"x")
