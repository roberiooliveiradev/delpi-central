"""Resolução manual SB1 de um lote MyWEG — consulta api-delpi, projeta vínculos.

Não altera snapshots V025. Persistência só com semântica comprovada e dry_run=false.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from production_control_app.domain.errors import (
    MyWegNeedsBatchNotFound,
    MyWegNeedsValidationFailed,
)
from production_control_app.domain.myweg_needs_contract import ALLOWED_BRANCH
from production_control_app.domain.services.myweg_sb1_semantics import (
    evaluate_field_semantics,
)
from production_control_app.infrastructure.gateways.delpi_production_gateway import (
    DelpiProductionGateway,
)

logger = logging.getLogger(__name__)

STATUS_UNAVAILABLE = "unavailable"
LOOKUP_SOURCE = "api-delpi.lookup_products_sb1_identity"
LOOKUP_BATCH_SIZE = 400


class MyWegSb1ResolveService:
    def __init__(
        self,
        repository: Any,
        gateway: DelpiProductionGateway | None = None,
    ) -> None:
        self._repository = repository
        self._gateway = gateway or DelpiProductionGateway(
            caller_app="production-control-myweg-sb1-resolve"
        )

    def resolve_batch(
        self,
        *,
        batch_id: str | None = None,
        collection_id: str | None = None,
        dry_run: bool = True,
        caller_app: str | None = None,
    ) -> dict[str, Any]:
        batch = self._load_batch(batch_id=batch_id, collection_id=collection_id)
        records = self._repository.list_all_batch_records(batch_id=batch["id"])
        if not records:
            raise MyWegNeedsValidationFailed(
                "Lote sem registros para resolução SB1.",
                issues=[{"code": "invalid_record", "message": "records vazio", "path": "records"}],
            )

        # Hipótese operacional (rótulo E1 enganoso): codigo_referencia_weg ≈ B1_COD;
        # material_weg_tratado ≈ B1_REFEREN. Validada por evaluate_field_semantics.
        lookup_items = [
            {
                "client_key": str(row["id"]),
                "product_code": (row.get("codigo_referencia_weg") or None),
                "customer_reference": (row.get("material_weg_tratado") or None),
            }
            for row in records
        ]

        lookup_results: list[dict[str, Any]] = []
        try:
            for offset in range(0, len(lookup_items), LOOKUP_BATCH_SIZE):
                chunk = lookup_items[offset : offset + LOOKUP_BATCH_SIZE]
                payload = self._gateway.lookup_products_sb1_identity(
                    branch=ALLOWED_BRANCH,
                    items=chunk,
                )
                data = self._unwrap_gateway_data(payload)
                chunk_results = list(data.get("results") or [])
                lookup_results.extend(chunk_results)
        except Exception as exc:
            logger.exception("Falha na consulta SB1 identity lookup: %s", exc)
            verified_at = datetime.now(timezone.utc)
            unavailable = [
                self._serialize_row(
                    self._unavailable_row(row, verified_at=verified_at, reason=str(exc))
                )
                for row in records
            ]
            counts = self._count_statuses(unavailable)
            return {
                "batchId": batch["id"],
                "collectionId": batch["collection_id"],
                "recordCount": len(records),
                "dryRun": dry_run,
                "persisted": False,
                "semantics": {
                    "proven": False,
                    "architecture_decision_required": True,
                    "notes": "lookup_unavailable",
                },
                "counts": counts,
                "items": unavailable if dry_run else [],
                "error": "protheus_lookup_unavailable",
            }

        by_key = {str(item.get("client_key")): item for item in lookup_results}
        verified_at = datetime.now(timezone.utc)
        projected: list[dict[str, Any]] = []
        for row in records:
            classified = by_key.get(str(row["id"]))
            if classified is None:
                projected.append(
                    self._unavailable_row(
                        row,
                        verified_at=verified_at,
                        reason="missing_lookup_result",
                    )
                )
                continue
            projected.append(
                {
                    "record_id": str(row["id"]),
                    "batch_id": batch["id"],
                    "line_fingerprint": row["line_fingerprint"],
                    "status": str(classified.get("match_status") or STATUS_UNAVAILABLE),
                    "informed_product_code": classified.get("product_code"),
                    "customer_reference": classified.get("customer_reference"),
                    "verified_product_code": classified.get("verified_product_code"),
                    "verified_description": classified.get("verified_description"),
                    "matched_by": classified.get("matched_by"),
                    "reason": classified.get("reason"),
                    "candidates": list(classified.get("candidates") or []),
                    "source": LOOKUP_SOURCE,
                    "verified_at": verified_at,
                }
            )

        semantics = evaluate_field_semantics(lookup_results)
        counts = self._count_statuses(projected)
        public_rows = [self._serialize_row(row) for row in projected]

        response: dict[str, Any] = {
            "batchId": batch["id"],
            "collectionId": batch["collection_id"],
            "recordCount": len(records),
            "dryRun": dry_run,
            "persisted": False,
            "semantics": semantics,
            "counts": counts,
            "itemsSample": public_rows[:25],
        }

        if dry_run:
            response["items"] = public_rows
            return response

        if not semantics.get("proven"):
            raise MyWegNeedsValidationFailed(
                "Semântica dos campos MyWEG×SB1 não comprovada — ARCHITECTURE_DECISION_REQUIRED.",
                issues=[
                    {
                        "code": "architecture_decision_required",
                        "message": semantics.get("notes") or "semantics not proven",
                        "path": "semantics",
                    }
                ],
            )

        run_id = str(uuid4())
        # Commit único: run + vínculos. persisted=true só após retorno sem exceção.
        self._repository.persist_sb1_resolution_batch(
            run_id=run_id,
            batch_id=batch["id"],
            dry_run=False,
            caller_app=caller_app,
            status="completed",
            counts=counts,
            semantics_proven=True,
            semantics_notes=str(semantics.get("notes") or ""),
            rows=projected,
        )
        response["persisted"] = True
        response["resolutionRunId"] = run_id
        return response

    def _load_batch(
        self,
        *,
        batch_id: str | None,
        collection_id: str | None,
    ) -> dict[str, Any]:
        batch = None
        if batch_id:
            batch = self._repository.find_by_id(batch_id)
        elif collection_id:
            batch = self._repository.find_by_collection_id(collection_id)
        if batch is None:
            raise MyWegNeedsBatchNotFound("Coleta MyWEG não encontrada.")
        return batch

    @staticmethod
    def _unwrap_gateway_data(payload: Mapping[str, Any]) -> dict[str, Any]:
        if "results" in payload and "summary" in payload:
            return dict(payload)
        data = payload.get("data")
        if isinstance(data, dict):
            return data
        raise ValueError("Resposta api-delpi sem data/results de SB1 identity.")

    @staticmethod
    def _unavailable_row(
        row: Mapping[str, Any],
        *,
        verified_at: datetime,
        reason: str,
    ) -> dict[str, Any]:
        return {
            "record_id": str(row["id"]),
            "batch_id": str(row["batch_id"]),
            "line_fingerprint": row["line_fingerprint"],
            "status": STATUS_UNAVAILABLE,
            "informed_product_code": row.get("codigo_referencia_weg"),
            "customer_reference": row.get("material_weg_tratado"),
            "verified_product_code": None,
            "verified_description": None,
            "matched_by": None,
            "reason": reason[:500],
            "candidates": [],
            "source": LOOKUP_SOURCE,
            "verified_at": verified_at,
        }

    @staticmethod
    def _serialize_row(row: Mapping[str, Any]) -> dict[str, Any]:
        data = dict(row)
        verified_at = data.get("verified_at")
        if isinstance(verified_at, datetime):
            data["verified_at"] = verified_at.isoformat()
        return data

    @staticmethod
    def _count_statuses(rows: list[Mapping[str, Any]]) -> dict[str, int]:
        counts = {
            "confirmed": 0,
            "pending": 0,
            "not_found": 0,
            "ambiguous": 0,
            "divergent": 0,
            "blocked": 0,
            "unavailable": 0,
        }
        for row in rows:
            status = str(row.get("status") or STATUS_UNAVAILABLE)
            if status not in counts:
                counts[status] = 0
            counts[status] += 1
        return counts
