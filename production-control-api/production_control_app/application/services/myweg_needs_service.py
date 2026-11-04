"""Ingestão e consulta de lotes MyWEG Necessidades (filial 02)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from production_control_app.core.security import (
    PC_ACCESS,
    PC_MYWEG_NEEDS_VIEW,
    PC_VIEW_FILIAL_02,
    can,
)
from production_control_app.domain.errors import (
    BranchAccessDenied,
    MyWegNeedsBatchConflict,
    MyWegNeedsBatchNotFound,
    MyWegNeedsValidationFailed,
)
from production_control_app.domain.myweg_needs_contract import (
    ALLOWED_BRANCH,
    build_idempotency_key,
    decimal_to_canonical_str,
)
from production_control_app.domain.ports.myweg_needs_repository import MyWegNeedsRepositoryPort
from production_control_app.domain.services.myweg_needs_normalization import (
    validate_ingest_batch,
)
from production_control_app.infrastructure.persistence.postgres_myweg_needs_repository import (
    MyWegNeedsCollectionConflict,
)

_SAO_PAULO = ZoneInfo("America/Sao_Paulo")


class MyWegNeedsService:
    def __init__(self, repository: MyWegNeedsRepositoryPort) -> None:
        self._repository = repository

    def ingest_batch(
        self,
        payload: Mapping[str, Any],
        *,
        idempotency_key: str | None,
        caller_app: str | None = None,
    ) -> dict[str, Any]:
        validation = validate_ingest_batch(payload)
        if not validation.ok or validation.batch is None:
            issues = [
                {"code": issue.code, "message": issue.message, "path": issue.path}
                for issue in validation.issues
            ]
            raise MyWegNeedsValidationFailed(
                "Lote MyWEG rejeitado pela validação do contrato.",
                issues=issues,
            )

        batch = validation.batch
        if int(batch["record_count"]) <= 0 or not batch["records"]:
            raise MyWegNeedsValidationFailed(
                "Lote vazio ou incompleto não é aceito.",
                issues=[{"code": "invalid_record", "message": "records vazio", "path": "records"}],
            )

        expected_key = build_idempotency_key(
            collection_id=batch["collection_id"],
            payload_sha256=batch["payload_sha256"],
        )
        provided = (idempotency_key or "").strip()
        if provided and provided != expected_key:
            raise MyWegNeedsValidationFailed(
                "Idempotency-Key diverge de collection_id:payload_sha256.",
                issues=[
                    {
                        "code": "invalid_record",
                        "message": "Idempotency-Key inválida para o lote.",
                        "path": "Idempotency-Key",
                    }
                ],
            )

        existing = self._repository.find_by_collection_id(batch["collection_id"])
        if existing is not None:
            return self._resolve_existing(existing, batch["payload_sha256"], created=False)

        collected_at = datetime.fromisoformat(batch["collected_at"])
        exported_at = datetime.fromisoformat(batch["exported_at"])
        collection_date = self._collection_date(collected_at)

        try:
            stored = self._repository.insert_accepted_batch(
                collection_id=batch["collection_id"],
                branch=ALLOWED_BRANCH,
                myweg_company_code=batch["myweg_company_code"],
                myweg_work_center=batch["myweg_work_center"],
                contract_version=batch["contract_version"],
                collected_at=collected_at,
                exported_at=exported_at,
                collection_date=collection_date,
                payload_sha256=batch["payload_sha256"],
                source_files=batch["source_files"],
                record_count=int(batch["record_count"]),
                total_quantidade_un=Decimal(str(batch["totals"]["quantidade_original_un"])),
                total_quantidade_mi=Decimal(str(batch["totals"]["quantidade_mi"])),
                idempotency_key=expected_key,
                caller_app=(caller_app or "").strip() or None,
                records=batch["records"],
            )
        except MyWegNeedsCollectionConflict:
            raced = self._repository.find_by_collection_id(batch["collection_id"])
            if raced is None:
                raise
            return self._resolve_existing(raced, batch["payload_sha256"], created=False)

        return self._ingest_response(stored, created=True)

    def list_batches(self, user: object | None, *, page: int, page_size: int) -> dict[str, Any]:
        self._assert_can_view(user)
        data = self._repository.list_batches(page=page, page_size=page_size)
        return {
            "branch": ALLOWED_BRANCH,
            "page": data["page"],
            "pageSize": data["pageSize"],
            "total": data["total"],
            "items": [self._batch_summary(item) for item in data["items"]],
        }

    def get_latest_batch(self, user: object | None) -> dict[str, Any]:
        self._assert_can_view(user)
        batch = self._repository.get_latest_batch()
        if batch is None:
            raise MyWegNeedsBatchNotFound("Nenhuma coleta MyWEG aceita encontrada.")
        return self._batch_detail(batch)

    def get_batch(self, user: object | None, *, batch_id: str) -> dict[str, Any]:
        self._assert_can_view(user)
        batch = self._repository.find_by_id(batch_id)
        if batch is None:
            raise MyWegNeedsBatchNotFound("Coleta MyWEG não encontrada.")
        return self._batch_detail(batch)

    def list_batch_items(
        self,
        user: object | None,
        *,
        batch_id: str,
        search: str = "",
        remessa_from: date | None = None,
        remessa_to: date | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        self._assert_can_view(user)
        batch = self._repository.find_by_id(batch_id)
        if batch is None:
            raise MyWegNeedsBatchNotFound("Coleta MyWEG não encontrada.")
        items = self._repository.list_batch_items(
            batch_id=batch_id,
            search=search,
            remessa_from=remessa_from,
            remessa_to=remessa_to,
            page=page,
            page_size=page_size,
        )
        return {
            "branch": ALLOWED_BRANCH,
            "batchId": batch["id"],
            "collectionId": batch["collection_id"],
            "page": items["page"],
            "pageSize": items["pageSize"],
            "total": items["total"],
            "items": items["items"],
        }

    def _resolve_existing(
        self,
        existing: dict[str, Any],
        payload_sha256: str,
        *,
        created: bool,
    ) -> dict[str, Any]:
        if str(existing.get("payload_sha256") or "").lower() != payload_sha256.lower():
            raise MyWegNeedsBatchConflict(
                "Já existe coleta com este collection_id e payload diferente."
            )
        return self._ingest_response(existing, created=created)

    @staticmethod
    def _ingest_response(batch: dict[str, Any], *, created: bool) -> dict[str, Any]:
        return {
            "created": created,
            "id": batch["id"],
            "collectionId": batch["collection_id"],
            "branch": batch["branch"],
            "status": batch["status"],
            "recordCount": int(batch["record_count"]),
            "totals": {
                "quantidade_original_un": decimal_to_canonical_str(
                    Decimal(str(batch["total_quantidade_un"]))
                ),
                "quantidade_mi": decimal_to_canonical_str(
                    Decimal(str(batch["total_quantidade_mi"]))
                ),
            },
            "payloadSha256": batch["payload_sha256"],
            "importedAt": batch["imported_at"],
            "collectionDate": batch["collection_date"],
        }

    @staticmethod
    def _batch_summary(batch: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": batch["id"],
            "collectionId": batch["collection_id"],
            "branch": batch["branch"],
            "status": batch["status"],
            "collectedAt": batch["collected_at"],
            "exportedAt": batch["exported_at"],
            "collectionDate": batch["collection_date"],
            "importedAt": batch["imported_at"],
            "recordCount": int(batch["record_count"]),
            "totals": {
                "quantidade_original_un": decimal_to_canonical_str(
                    Decimal(str(batch["total_quantidade_un"]))
                ),
                "quantidade_mi": decimal_to_canonical_str(
                    Decimal(str(batch["total_quantidade_mi"]))
                ),
            },
            "payloadSha256": batch["payload_sha256"],
        }

    def _batch_detail(self, batch: dict[str, Any]) -> dict[str, Any]:
        summary = self._batch_summary(batch)
        summary["contractVersion"] = batch["contract_version"]
        summary["mywegCompanyCode"] = batch["myweg_company_code"]
        summary["mywegWorkCenter"] = batch["myweg_work_center"]
        summary["sourceFiles"] = batch.get("source_files") or {}
        summary["idempotencyKey"] = batch.get("idempotency_key")
        return summary

    @staticmethod
    def _collection_date(collected_at: datetime) -> date:
        aware = collected_at if collected_at.tzinfo else collected_at.replace(tzinfo=timezone.utc)
        return aware.astimezone(_SAO_PAULO).date()

    @staticmethod
    def _assert_can_view(user: object | None) -> None:
        if not can(user, PC_ACCESS):
            raise PermissionError("Você não tem permissão para acessar o Portal PCP.")
        if not can(user, PC_MYWEG_NEEDS_VIEW):
            raise PermissionError("Você não tem permissão para consultar Necessidades WEG.")
        if not can(user, PC_VIEW_FILIAL_02):
            raise BranchAccessDenied("Sem permissão para a filial 02.")
