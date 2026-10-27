"""Gestão gerencial de paradas — classificação, triagem e encaminhamento.

O BFF **não** é owner dos fatos: Production Control valida motivo/catálogo,
precondições de concorrência e persiste classificação/triagem; o requests-api
é owner do lifecycle da solicitação. Aqui ficam autorização humana (RBAC +
filial), orquestração das chamadas e allowlist do contrato.

A consulta de tratamento hidrata o status VIVO da solicitação vinculada via
GET /v1/requests/{id} com o Bearer do próprio usuário — quando o usuário
não pode ler a solicitação, a referência continua visível com
requestStatusAvailable=false em vez de esconder o vínculo.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from delpi_mes_app.core.security import (
    MES_ACCESS,
    MES_DOWNTIMES_CLASSIFY,
    MES_DOWNTIMES_TREAT,
    MES_DOWNTIMES_VIEW,
    can,
    is_human_user,
)
from delpi_mes_app.domain.errors import (
    HumanPrincipalRequired,
    MesSourceConflict,
    MesSourceNotFound,
)
from delpi_mes_app.domain.ports.production_control_mes_gateway import (
    ProductionControlMesGatewayPort,
)
from delpi_mes_app.domain.ports.requests_api_gateway import (
    RequestsApiGatewayPort,
)

_PROCESS_ISSUE_TYPE = "process-issue"
_PROCESS_ISSUE_CREATE_PERMISSION = "my-requests.process-issue.create"
_COMPLETED_STATUSES = frozenset({"completed"})

_TREATMENT_FIELDS = (
    "downtimeId", "status", "analysis", "causeKind", "causeNote",
    "actionNeeded", "justification", "requestRef", "linkedAt", "linkedBy",
    "conclusionReason", "concludedAt", "concludedBy", "createdBy",
    "updatedBy", "createdAt", "updatedAt",
)
_CLASSIFICATION_FIELDS = (
    "id", "runId", "reasonCode", "reasonLabel", "category", "note",
    "confirmed", "confirmedAt", "confirmedByType", "confirmedByRef",
    "startedAt", "endedAt", "updatedAt",
)
_HISTORY_FIELDS = (
    "id", "action", "actorType", "actorRef", "occurredAt", "details",
)
_REQUEST_VIEW_FIELDS = (
    "requestId", "requestNumber", "typeCode", "status", "statusAlias",
)


class MesDowntimeManagementService:
    def __init__(
        self,
        mes_gateway: ProductionControlMesGatewayPort,
        requests_gateway: RequestsApiGatewayPort,
    ) -> None:
        self._gateway = mes_gateway
        self._requests = requests_gateway

    # ------------------------------------------------------------------
    # Classificação
    # ------------------------------------------------------------------

    def classify_downtime(
        self,
        user: Any,
        downtime_id: str,
        *,
        branch: str,
        reason_code: str,
        note: str | None,
        expected_updated_at: str,
    ) -> dict[str, Any]:
        branch_code = self._authorize(
            user, branch=branch, permission=MES_DOWNTIMES_CLASSIFY
        )
        actor_ref, actor_name = self._actor(user)
        data = self._gateway.classify_downtime(
            downtime_id,
            {
                "branch": branch_code,
                "reasonCode": reason_code,
                "note": note,
                "expectedUpdatedAt": expected_updated_at,
                "actorRef": actor_ref,
                "actorName": actor_name,
            },
        )
        return self._pick(data, _CLASSIFICATION_FIELDS)

    # ------------------------------------------------------------------
    # Triagem / tratamento
    # ------------------------------------------------------------------

    def get_treatment(
        self, user: Any, downtime_id: str, *, branch: str
    ) -> dict[str, Any]:
        branch_code = self._authorize(
            user, branch=branch, permission=MES_DOWNTIMES_VIEW
        )
        data = self._gateway.get_downtime_treatment(
            downtime_id, branch=branch_code
        )
        treatment = data.get("treatment")
        return {
            "treatment": self._treatment_view(treatment, user)
            if treatment
            else None
        }

    def upsert_treatment(
        self,
        user: Any,
        downtime_id: str,
        *,
        branch: str,
        analysis: str,
        cause_kind: str,
        cause_note: str | None,
        action_needed: bool,
        justification: str,
        expected_updated_at: str | None,
    ) -> dict[str, Any]:
        branch_code = self._authorize(
            user, branch=branch, permission=MES_DOWNTIMES_TREAT
        )
        actor_ref, actor_name = self._actor(user)
        data = self._gateway.upsert_downtime_treatment(
            downtime_id,
            {
                "branch": branch_code,
                "analysis": analysis,
                "causeKind": cause_kind,
                "causeNote": cause_note,
                "actionNeeded": bool(action_needed),
                "justification": justification,
                "expectedUpdatedAt": expected_updated_at,
                "actorRef": actor_ref,
                "actorName": actor_name,
            },
        )
        return {"treatment": self._treatment_view(data, user)}

    def refer_request(
        self,
        user: Any,
        downtime_id: str,
        *,
        branch: str,
        issue_code: str,
        note: str | None,
        idempotency_key: str | None,
    ) -> dict[str, Any]:
        """Encaminha a parada para o dept. de Processos (process-issue).

        Orquestração idempotente: cria a solicitação como o usuário (mesma
        chave → mesma solicitação, sem duplicar) e registra o vínculo no PC
        (mesmo requestId → vínculo estável). O lifecycle permanece no
        requests-api.
        """
        branch_code = self._authorize(
            user, branch=branch, permission=MES_DOWNTIMES_TREAT
        )
        if not can(user, _PROCESS_ISSUE_CREATE_PERMISSION):
            raise PermissionError(
                "Sem permissão para abrir solicitações de problema de processo."
            )
        actor_ref, actor_name = self._actor(user)

        treatment_data = self._gateway.get_downtime_treatment(
            downtime_id, branch=branch_code
        )
        treatment = treatment_data.get("treatment")
        if treatment is None:
            raise MesSourceConflict(
                "Registre a triagem da parada antes de encaminhar."
            )
        if treatment.get("requestRef"):
            raise MesSourceConflict(
                "Esta parada já possui uma solicitação vinculada."
            )
        if treatment.get("status") == "concluded":
            raise MesSourceConflict(
                "O tratamento desta parada já foi concluído."
            )

        downtime = self._downtime_item(user, downtime_id, branch_code)
        key = (idempotency_key or "").strip() or (
            f"delpi-mes-downtime-{downtime_id}-{_PROCESS_ISSUE_TYPE}"
        )
        payload: dict[str, Any] = {
            "source": "delpi_mes",
            "reportedAt": datetime.now(timezone.utc).isoformat(),
            "issue": {
                "code": str(issue_code or "").strip(),
                "note": (note or "").strip() or None,
            },
            "requester": {"name": actor_name},
            "mesDowntime": {
                "downtimeId": downtime_id,
                "branch": branch_code,
                "workCenter": downtime.get("workCenter"),
            },
        }
        if downtime.get("productionOrder") and downtime.get("operationCode"):
            payload["operation"] = {
                "productionOrder": downtime["productionOrder"],
                "operationCode": downtime["operationCode"],
                "reportedWorkCenter": downtime["workCenter"],
            }

        created = self._requests.create_request_as_user(
            access_token=self._access_token(user),
            type_code=_PROCESS_ISSUE_TYPE,
            payload=payload,
            branch=branch_code,
            idempotency_key=key,
        )
        request_id = str(created.get("id") or "").strip()
        if not request_id:
            raise MesSourceConflict(
                "Solicitação criada sem identificador retornado."
            )

        linked = self._gateway.link_downtime_request(
            downtime_id,
            {
                "branch": branch_code,
                "requestId": request_id,
                "requestTypeCode": _PROCESS_ISSUE_TYPE,
                "actorRef": actor_ref,
                "actorName": actor_name,
            },
        )
        return {"treatment": self._treatment_view(linked, user)}

    def conclude_treatment(
        self,
        user: Any,
        downtime_id: str,
        *,
        branch: str,
        reason: str,
    ) -> dict[str, Any]:
        branch_code = self._authorize(
            user, branch=branch, permission=MES_DOWNTIMES_TREAT
        )
        actor_ref, actor_name = self._actor(user)

        treatment_data = self._gateway.get_downtime_treatment(
            downtime_id, branch=branch_code
        )
        treatment = treatment_data.get("treatment")
        if treatment is None:
            raise MesSourceConflict(
                "Registre a triagem da parada antes de concluir."
            )
        linked_completed = False
        request_ref = treatment.get("requestRef") or {}
        request_id = str(request_ref.get("requestId") or "").strip()
        if request_id:
            remote = self._request_status(user, request_id)
            if remote is None:
                raise MesSourceConflict(
                    "Não foi possível confirmar a situação da solicitação "
                    "vinculada; tente novamente."
                )
            if remote.get("status") not in _COMPLETED_STATUSES:
                raise MesSourceConflict(
                    "A solicitação vinculada ainda não foi concluída."
                )
            linked_completed = True

        data = self._gateway.conclude_downtime_treatment(
            downtime_id,
            {
                "branch": branch_code,
                "reason": reason,
                "linkedRequestCompleted": linked_completed,
                "actorRef": actor_ref,
                "actorName": actor_name,
            },
        )
        return {"treatment": self._treatment_view(data, user)}

    def get_history(
        self, user: Any, downtime_id: str, *, branch: str
    ) -> dict[str, Any]:
        branch_code = self._authorize(
            user, branch=branch, permission=MES_DOWNTIMES_VIEW
        )
        data = self._gateway.get_downtime_history(
            downtime_id, branch=branch_code
        )
        return {
            "items": [
                self._pick(item, _HISTORY_FIELDS)
                for item in data.get("items", [])
            ]
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _downtime_item(
        self, user: Any, downtime_id: str, branch: str
    ) -> dict[str, Any]:
        data = self._gateway.get_downtimes(
            branch=branch,
            work_center=None,
            period_from=None,
            period_to=None,
            downtime_id=downtime_id,
            page=1,
            page_size=1,
        )
        items = data.get("items") or []
        if not items:
            raise MesSourceNotFound("Parada não encontrada.")
        return items[0]

    def _request_status(
        self, user: Any, request_id: str
    ) -> dict[str, Any] | None:
        """Status vivo da solicitação; None quando indisponível/negado."""
        try:
            data = self._requests.get_request_as_user(
                access_token=self._access_token(user),
                request_id=request_id,
            )
        except (PermissionError, MesSourceNotFound):
            return None
        status = str(data.get("status") or "").strip()
        if not status:
            return None
        return {
            "requestId": str(data.get("id") or request_id),
            "requestNumber": str(data.get("request_number") or "") or None,
            "typeCode": str(data.get("type_code") or "") or None,
            "status": status,
            "statusAlias": str(data.get("status_alias") or "") or None,
        }

    def _treatment_view(
        self, treatment: dict[str, Any], user: Any
    ) -> dict[str, Any]:
        view = self._pick(treatment, _TREATMENT_FIELDS)
        request_ref = view.get("requestRef") or {}
        request_id = str(request_ref.get("requestId") or "").strip()
        if request_id:
            remote = self._request_status(user, request_id)
            view["request"] = remote
            view["requestStatusAvailable"] = remote is not None
        else:
            view["request"] = None
            view["requestStatusAvailable"] = False
        return view

    @staticmethod
    def _authorize(user: Any, *, branch: str, permission: str) -> str:
        if not is_human_user(user):
            raise HumanPrincipalRequired(
                "A gestão de paradas exige um usuário autenticado."
            )
        if not can(user, MES_ACCESS):
            raise PermissionError("Sem permissão para acessar o Delpi MES.")
        if not can(user, permission):
            raise PermissionError("Sem permissão para esta operação.")
        from delpi_mes_app.application.services.mes_read_service import (
            MesReadService,
        )

        branch_code = MesReadService._valid_branch(str(branch or ""))
        MesReadService._authorize_branch(user, branch_code)
        return branch_code

    @staticmethod
    def _actor(user: Any) -> tuple[str, str]:
        ref = str(getattr(user, "id", "") or "").strip()
        name = str(getattr(user, "name", "") or "").strip()
        if not ref:
            raise HumanPrincipalRequired(
                "Identidade do usuário indisponível para a operação."
            )
        return ref, name or ref

    @staticmethod
    def _access_token(user: Any) -> str:
        token = str(getattr(user, "access_token", "") or "").strip()
        if not token:
            raise HumanPrincipalRequired(
                "Credencial do usuário indisponível para encaminhar."
            )
        return token

    @staticmethod
    def _pick(data: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
        return {field: data.get(field) for field in fields}
