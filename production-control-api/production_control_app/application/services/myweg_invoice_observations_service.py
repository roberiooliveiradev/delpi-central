"""Ingestão e consulta de observações MyWEG NF Emitidas (filial 02)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Mapping

from production_control_app.core.security import (
    PC_ACCESS,
    PC_MYWEG_NEEDS_VIEW,
    PC_VIEW_FILIAL_02,
    can,
)
from production_control_app.domain.errors import (
    BranchAccessDenied,
    MyWegInvoiceObservationConflict,
    MyWegInvoiceObservationNotFound,
    MyWegInvoiceObservationValidationFailed,
)
from production_control_app.domain.myweg_invoice_observations_contract import (
    ALLOWED_BRANCH,
    build_idempotency_key,
    decimal_to_canonical_str,
)
from production_control_app.domain.ports.myweg_invoice_observations_repository import (
    MyWegInvoiceObservationsRepositoryPort,
)
from production_control_app.domain.services.myweg_invoice_observations_normalization import (
    validate_ingest_observation,
)
from production_control_app.infrastructure.persistence.postgres_myweg_invoice_observations_repository import (
    MyWegInvoiceObservationCollectionConflict,
)


class MyWegInvoiceObservationsService:
    def __init__(self, repository: MyWegInvoiceObservationsRepositoryPort) -> None:
        self._repository = repository

    def ingest_observation(
        self,
        payload: Mapping[str, Any],
        *,
        idempotency_key: str | None,
        caller_app: str | None = None,
    ) -> dict[str, Any]:
        validation = validate_ingest_observation(payload)
        if not validation.ok or validation.batch is None:
            issues = [
                {"code": issue.code, "message": issue.message, "path": issue.path}
                for issue in validation.issues
            ]
            raise MyWegInvoiceObservationValidationFailed(
                "Observação MyWEG NF rejeitada pela validação do contrato.",
                issues=issues,
            )

        batch = validation.batch
        expected_key = build_idempotency_key(
            collection_id=batch["collection_id"],
            payload_sha256=batch["payload_sha256"],
        )
        provided = (idempotency_key or "").strip()
        if provided and provided != expected_key:
            raise MyWegInvoiceObservationValidationFailed(
                "Idempotency-Key diverge de collection_id:payload_sha256.",
                issues=[
                    {
                        "code": "invalid_record",
                        "message": "Idempotency-Key inválida para a observação.",
                        "path": "Idempotency-Key",
                    }
                ],
            )

        existing = self._repository.find_by_collection_id(batch["collection_id"])
        if existing is not None:
            return self._resolve_existing(existing, batch["payload_sha256"], created=False)

        observed_at = (
            datetime.fromisoformat(batch["observed_at"])
            if batch.get("observed_at")
            else None
        )
        source_prepared_at = datetime.fromisoformat(batch["source_prepared_at"])
        document_date = date.fromisoformat(batch["document_date"])

        try:
            stored = self._repository.insert_accepted_observation(
                collection_id=batch["collection_id"],
                branch=ALLOWED_BRANCH,
                myweg_company_code=batch["myweg_company_code"],
                myweg_work_center=batch["myweg_work_center"],
                myweg_supplier_code=batch["myweg_supplier_code"],
                contract_version=batch["contract_version"],
                document_date=document_date,
                observation_status=batch["observation_status"],
                observed_at=observed_at,
                source_prepared_at=source_prepared_at,
                source_sha256=batch.get("source_sha256"),
                payload_sha256=batch["payload_sha256"],
                semantic_sha256=batch["semantic_sha256"],
                record_count=int(batch["record_count"]),
                total_quantity_un=Decimal(str(batch["total_quantity_un"])),
                manifesto=batch.get("manifesto") or {},
                idempotency_key=expected_key,
                caller_app=(caller_app or "").strip() or None,
                records=batch["records"],
            )
        except MyWegInvoiceObservationCollectionConflict:
            raced = self._repository.find_by_collection_id(batch["collection_id"])
            if raced is None:
                raise
            return self._resolve_existing(raced, batch["payload_sha256"], created=False)

        return self._ingest_response(stored, created=True)

    def list_observations(
        self,
        user: object | None,
        *,
        document_date: date | None,
        observation_status: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        self._assert_can_view(user)
        data = self._repository.list_observations(
            document_date=document_date,
            observation_status=observation_status,
            page=page,
            page_size=page_size,
        )
        return {
            "branch": ALLOWED_BRANCH,
            "page": data["page"],
            "pageSize": data["pageSize"],
            "total": data["total"],
            "items": [self._observation_summary(item) for item in data["items"]],
        }

    def get_observation(
        self, user: object | None, *, observation_id: str
    ) -> dict[str, Any]:
        self._assert_can_view(user)
        observation = self._repository.find_by_id(observation_id)
        if observation is None:
            raise MyWegInvoiceObservationNotFound(
                "Observação MyWEG NF não encontrada."
            )
        return self._observation_detail(observation)

    def list_observation_items(
        self,
        user: object | None,
        *,
        observation_id: str,
        search: str = "",
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        self._assert_can_view(user)
        observation = self._repository.find_by_id(observation_id)
        if observation is None:
            raise MyWegInvoiceObservationNotFound(
                "Observação MyWEG NF não encontrada."
            )
        items = self._repository.list_observation_items(
            observation_id=observation_id,
            search=search,
            page=page,
            page_size=page_size,
        )
        return {
            "branch": ALLOWED_BRANCH,
            "observationId": observation["id"],
            "collectionId": observation["collection_id"],
            "documentDate": observation["document_date"],
            "observationStatus": observation["observation_status"],
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
            raise MyWegInvoiceObservationConflict(
                "Já existe observação com este collection_id e payload diferente."
            )
        return self._ingest_response(existing, created=created)

    def _ingest_response(
        self, observation: dict[str, Any], *, created: bool
    ) -> dict[str, Any]:
        equivalent = self._repository.count_by_semantic_sha256(
            semantic_sha256=observation["semantic_sha256"],
            exclude_collection_id=observation["collection_id"],
        )
        return {
            "created": created,
            "id": observation["id"],
            "collectionId": observation["collection_id"],
            "branch": observation["branch"],
            "status": observation["status"],
            "observationStatus": observation["observation_status"],
            "documentDate": observation["document_date"],
            "recordCount": int(observation["record_count"]),
            "totalQuantityUn": decimal_to_canonical_str(
                Decimal(str(observation["total_quantity_un"]))
            ),
            "sourceSha256": observation.get("source_sha256"),
            "payloadSha256": observation["payload_sha256"],
            "semanticSha256": observation["semantic_sha256"],
            "equivalentObservationCount": int(equivalent),
            "importedAt": observation["imported_at"],
        }

    def _observation_summary(self, observation: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": observation["id"],
            "collectionId": observation["collection_id"],
            "branch": observation["branch"],
            "status": observation["status"],
            "observationStatus": observation["observation_status"],
            "documentDate": observation["document_date"],
            "observedAt": observation.get("observed_at"),
            "sourcePreparedAt": observation.get("source_prepared_at"),
            "importedAt": observation.get("imported_at"),
            "recordCount": int(observation["record_count"]),
            "totalQuantityUn": decimal_to_canonical_str(
                Decimal(str(observation["total_quantity_un"]))
            ),
            "sourceSha256": observation.get("source_sha256"),
            "payloadSha256": observation["payload_sha256"],
            "semanticSha256": observation["semantic_sha256"],
        }

    def _observation_detail(self, observation: dict[str, Any]) -> dict[str, Any]:
        summary = self._observation_summary(observation)
        summary["contractVersion"] = observation["contract_version"]
        summary["mywegCompanyCode"] = observation["myweg_company_code"]
        summary["mywegWorkCenter"] = observation["myweg_work_center"]
        summary["mywegSupplierCode"] = observation["myweg_supplier_code"]
        summary["manifesto"] = observation.get("manifesto") or {}
        summary["idempotencyKey"] = observation.get("idempotency_key")
        summary["equivalentObservationCount"] = self._repository.count_by_semantic_sha256(
            semantic_sha256=observation["semantic_sha256"],
            exclude_collection_id=observation["collection_id"],
        )
        return summary

    @staticmethod
    def _assert_can_view(user: object | None) -> None:
        # E1: reutiliza PC_MYWEG_NEEDS_VIEW (mesma superfície MyWEG filial 02).
        # Política mais restrita para números de NF exigiria ownership no Core.
        if not can(user, PC_ACCESS):
            raise PermissionError("Você não tem permissão para acessar o Portal PCP.")
        if not can(user, PC_MYWEG_NEEDS_VIEW):
            raise PermissionError(
                "Você não tem permissão para consultar observações MyWEG."
            )
        if not can(user, PC_VIEW_FILIAL_02):
            raise BranchAccessDenied("Sem permissão para a filial 02.")
