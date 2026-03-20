# app/application/use_cases/external_nc/export_nonconformity_report_use_case.py
from __future__ import annotations
from datetime import datetime, timezone
from app.domain.ports.external_nc.external_nc_export_repository import (
    ExternalNcExportRepositoryPort,
)


class ExportNonconformityReportUseCase:
    def __init__(
        self,
        export_repository: ExternalNcExportRepositoryPort,
    ) -> None:
        self._export_repository = export_repository

    def execute(self, nonconformity_id: str) -> dict:
        if not nonconformity_id or not nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")

        payload = self._export_repository.get_nonconformity_export_payload(
            nonconformity_id.strip()
        )
        if payload is None:
            raise ValueError("Não conformidade externa não encontrada.")

        return {
            "report_type": "external_nonconformity",
            "generated_format": "json",
            "generated_at": datetime.now(timezone.utc),
            "data": payload,
        }