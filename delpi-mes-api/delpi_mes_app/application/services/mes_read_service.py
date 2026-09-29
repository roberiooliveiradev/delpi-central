from __future__ import annotations

from datetime import datetime
from typing import Any

from delpi_mes_app.core.security import BRANCH_VIEW_PERMISSIONS, MES_ACCESS, can, is_human_user
from delpi_mes_app.domain.errors import BranchAccessDenied, HumanPrincipalRequired, InvalidBranch
from delpi_mes_app.domain.ports.production_control_mes_gateway import (
    ProductionControlMesGatewayPort,
)

_MONITORING_SUMMARY_FIELDS = (
    "activeRuns", "producing", "stopped", "paused", "unclassifiedDowntimes",
)
_TIMELINE_SUMMARY_FIELDS = (
    "elapsedSeconds", "producingSeconds", "stoppedSeconds", "stopCount",
)
_MONITORING_ITEM_FIELDS = (
    "branch", "workCenter", "runId", "runStatus", "operationalState",
    "stateStartedAt", "stateSource", "integrityStatus", "productionOrder",
    "operationCode", "operatorCode", "operatorName", "piecesTotal", "targetPieces",
    "lastCountActivityAt", "downtime",
)
_TIMELINE_FIELDS = ("runId", "branch", "workCenter", "status", "referenceAt", "summary")
_TIMELINE_ITEM_FIELDS = (
    "id", "state", "startedAt", "endedAt", "durationSeconds", "source", "downtime",
)
_DOWNTIME_FIELDS = (
    "id", "startedAt", "source", "reasonCode", "reasonLabel", "category", "confirmed", "note",
)
_DOWNTIME_ITEM_FIELDS = (
    "id", "runId", "workCenter", "productionOrder", "operationCode", "startedAt",
    "endedAt", "source", "reasonCode", "reasonLabel", "category", "confirmed", "note",
)


class MesReadService:
    def __init__(self, gateway: ProductionControlMesGatewayPort) -> None:
        self._gateway = gateway

    def get_monitoring(self, user: Any, *, branch: str, permission: str) -> dict[str, Any]:
        code = self._authorize(user, branch=branch, permission=permission)
        data = self._gateway.get_monitoring(branch=code)
        return {
            "branch": data.get("branch"),
            "referenceAt": data.get("referenceAt"),
            "summary": self._pick(data.get("summary") or {}, _MONITORING_SUMMARY_FIELDS),
            "items": [self._monitoring_item(item) for item in data.get("items", [])],
        }

    def get_timeline(self, user: Any, run_id: str, *, permission: str) -> dict[str, Any]:
        self._authorize_product(user, permission)
        data = self._gateway.get_timeline(run_id)
        branch = self._valid_branch(str(data.get("branch") or ""))
        self._authorize_branch(user, branch)
        result = self._pick(data, _TIMELINE_FIELDS)
        result["summary"] = self._pick(data.get("summary") or {}, _TIMELINE_SUMMARY_FIELDS)
        result["items"] = [self._timeline_item(item) for item in data.get("items", [])]
        return result

    def get_downtimes(
        self,
        user: Any,
        *,
        branch: str,
        work_center: str | None,
        period_from: datetime | None,
        period_to: datetime | None,
        page: int,
        page_size: int,
        permission: str,
    ) -> dict[str, Any]:
        code = self._authorize(user, branch=branch, permission=permission)
        self._validate_period(period_from, period_to)
        if page_size < 1 or page_size > 100:
            raise ValueError("pageSize deve estar entre 1 e 100.")
        data = self._gateway.get_downtimes(
            branch=code,
            work_center=work_center,
            period_from=period_from,
            period_to=period_to,
            page=page,
            page_size=page_size,
        )
        return {
            "branch": data.get("branch"),
            "referenceAt": data.get("referenceAt"),
            "page": data.get("page"),
            "pageSize": data.get("pageSize"),
            "total": data.get("total"),
            "items": [self._pick(item, _DOWNTIME_ITEM_FIELDS) for item in data.get("items", [])],
        }

    def _authorize(self, user: Any, *, branch: str, permission: str) -> str:
        self._authorize_product(user, permission)
        code = self._valid_branch(branch)
        self._authorize_branch(user, code)
        return code

    @staticmethod
    def _authorize_product(user: Any, permission: str) -> None:
        if not is_human_user(user):
            raise HumanPrincipalRequired("Acesso gerencial exige um usuário autenticado.")
        if not can(user, MES_ACCESS):
            raise PermissionError("Sem permissão para acessar o Delpi MES.")
        if not can(user, permission):
            raise PermissionError("Sem permissão para esta consulta do Delpi MES.")

    @staticmethod
    def _valid_branch(branch: str) -> str:
        code = branch.strip()
        if code not in BRANCH_VIEW_PERMISSIONS:
            raise InvalidBranch("Filial inválida. Use 01 ou 02.")
        return code

    @staticmethod
    def _authorize_branch(user: Any, branch: str) -> None:
        if not can(user, BRANCH_VIEW_PERMISSIONS[branch]):
            raise BranchAccessDenied("Sem permissão para esta filial.")

    @staticmethod
    def _validate_period(period_from: datetime | None, period_to: datetime | None) -> None:
        for name, value in (("from", period_from), ("to", period_to)):
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{name} deve incluir timezone.")
        if period_from and period_to and period_from >= period_to:
            raise ValueError("O início do período deve ser anterior ao fim.")

    @classmethod
    def _monitoring_item(cls, data: dict[str, Any]) -> dict[str, Any]:
        item = cls._pick(data, _MONITORING_ITEM_FIELDS)
        if isinstance(data.get("downtime"), dict):
            item["downtime"] = cls._pick(data["downtime"], _DOWNTIME_FIELDS)
        return item

    @classmethod
    def _timeline_item(cls, data: dict[str, Any]) -> dict[str, Any]:
        item = cls._pick(data, _TIMELINE_ITEM_FIELDS)
        if isinstance(data.get("downtime"), dict):
            item["downtime"] = cls._pick(data["downtime"], _DOWNTIME_FIELDS)
        return item

    @staticmethod
    def _pick(data: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
        return {field: data.get(field) for field in fields}
