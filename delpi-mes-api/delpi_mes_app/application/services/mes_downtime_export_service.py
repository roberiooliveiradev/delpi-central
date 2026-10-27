"""Exportações e relatórios gerenciais de paradas (Etapa 5).

O BFF não é owner dos fatos nem dos agregados: Production Control aplica
o mesmo universo elegível da listagem/painel e devolve fatos completos
(sem paginação) e indicadores; aqui ficam a autorização humana (RBAC +
filial), a serialização do arquivo e os metadados de extração.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from delpi_mes_app.core.security import (
    BRANCH_VIEW_PERMISSIONS,
    MES_ACCESS,
    MES_DOWNTIMES_EXPORT,
    can,
    is_human_user,
)
from delpi_mes_app.domain.errors import (
    BranchAccessDenied,
    HumanPrincipalRequired,
    InvalidBranch,
)
from delpi_mes_app.domain.ports.production_control_mes_gateway import (
    ProductionControlMesGatewayPort,
)
from delpi_mes_app.infrastructure.export.downtime_files import (
    CSV_MIME,
    PDF_MIME,
    XLSX_MIME,
    build_executive_pdf,
    build_occurrences_csv,
    build_occurrences_xlsx,
)

_FACTORY_TZ = ZoneInfo("America/Sao_Paulo")
_TABULAR_FORMATS = frozenset({"csv", "xlsx"})


class MesDowntimeExportService:
    def __init__(self, gateway: ProductionControlMesGatewayPort) -> None:
        self._gateway = gateway

    def export_occurrences(
        self,
        user: Any,
        *,
        branch: str,
        export_format: str,
        pendency: bool = False,
        work_center: str | None = None,
        period_from: datetime | None = None,
        period_to: datetime | None = None,
        reason_code: str | None = None,
        source: str | None = None,
        classification: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        code = self._authorize(user, branch=branch)
        fmt = (export_format or "").strip().lower()
        if fmt not in _TABULAR_FORMATS:
            raise ValueError("format deve ser 'csv' ou 'xlsx'.")
        self._validate_period(period_from, period_to)
        data = self._gateway.export_downtimes(
            branch=code,
            work_center=(work_center or "").strip() or None,
            period_from=period_from,
            period_to=period_to,
            reason_code=(reason_code or "").strip() or None,
            source=(source or "").strip() or None,
            classification=(classification or "").strip() or None,
            status=(status or "").strip() or None,
            pendency=pendency,
        )
        data["generatedAt"] = datetime.now(timezone.utc).isoformat()
        title = (
            "Relatório de pendências de paradas"
            if pendency
            else "Exportação de paradas"
        )
        stamp = datetime.now(_FACTORY_TZ).strftime("%Y%m%d-%H%M%S")
        base = (
            f"delpi-mes-pendencias-paradas-{code}-{stamp}"
            if pendency
            else f"delpi-mes-paradas-{code}-{stamp}"
        )
        if fmt == "xlsx":
            return {
                "content": build_occurrences_xlsx(data, title=title),
                "contentType": XLSX_MIME,
                "filename": base + ".xlsx",
                "total": data.get("total"),
                "capped": bool(data.get("capped")),
            }
        return {
            "content": build_occurrences_csv(data, title=title),
            "contentType": CSV_MIME,
            "filename": base + ".csv",
            "total": data.get("total"),
            "capped": bool(data.get("capped")),
        }

    def export_executive_report(
        self,
        user: Any,
        *,
        branch: str,
        period_from: datetime,
        period_to: datetime | None = None,
        work_center: str | None = None,
        reason_code: str | None = None,
        source: str | None = None,
        classification: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        code = self._authorize(user, branch=branch)
        self._validate_period(period_from, period_to)
        data = self._gateway.get_downtime_analytics(
            branch=code,
            period_from=period_from,
            period_to=period_to,
            work_center=(work_center or "").strip() or None,
            reason_code=(reason_code or "").strip() or None,
            source=(source or "").strip() or None,
            classification=(classification or "").strip() or None,
            status=(status or "").strip() or None,
        )
        data["generatedAt"] = datetime.now(timezone.utc).isoformat()
        data["total"] = (data.get("summary") or {}).get("occurrencesCount")
        stamp = datetime.now(_FACTORY_TZ).strftime("%Y%m%d-%H%M%S")
        return {
            "content": build_executive_pdf(
                data, title="Relatório executivo de paradas — Delpi MES"
            ),
            "contentType": PDF_MIME,
            "filename": f"delpi-mes-relatorio-executivo-paradas-{code}-{stamp}.pdf",
            "capped": bool(
                (data.get("quality") or {}).get("partial")
            ),
        }

    def _authorize(self, user: Any, *, branch: str) -> str:
        if not is_human_user(user):
            raise HumanPrincipalRequired(
                "A exportação exige um usuário autenticado."
            )
        if not can(user, MES_ACCESS):
            raise PermissionError("Sem permissão para acessar o Delpi MES.")
        if not can(user, MES_DOWNTIMES_EXPORT):
            raise PermissionError("Sem permissão para exportar paradas.")
        code = branch.strip()
        if code not in BRANCH_VIEW_PERMISSIONS:
            raise InvalidBranch("Filial inválida. Use 01 ou 02.")
        if not can(user, BRANCH_VIEW_PERMISSIONS[code]):
            raise BranchAccessDenied("Sem permissão para esta filial.")
        return code

    @staticmethod
    def _validate_period(
        period_from: datetime | None, period_to: datetime | None
    ) -> None:
        for name, value in (("from", period_from), ("to", period_to)):
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{name} deve incluir timezone.")
        if period_from and period_to and period_from >= period_to:
            raise ValueError("O início do período deve ser anterior ao fim.")
