"""Operator Feedback no cockpit público — orquestração da C2.

Confiança: o operador só escolhe OP/operação/tipo/motivo/nota. Identidade,
filial e posto vêm SEMPRE da bench session; o contexto da OP é congelado a
partir da fila PUBLISHED (mesma fonte do cockpit — nunca WORKING nem TOTVS);
run_id é capturado por leitura leve do repositório (sem Pulse).

Segurança de enumeração: operação inexistente e operação publicada em outro
posto recebem a MESMA resposta 404 — o link anônimo não vira oráculo de fila.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from production_control_app.application.services.machine_load_service import (
    MachineLoadService,
)
from production_control_app.application.services.operator_feedback_service import (
    OperatorFeedbackService,
)
from production_control_app.domain.errors import (
    InvalidOperatorFeedbackMaterials,
    SnapshotNotFound,
)
from production_control_app.domain.operator_feedback import (
    OperatorFeedbackReason,
)

logger = logging.getLogger(__name__)

_OPERATION_UNAVAILABLE = (
    "Esta operação não está disponível neste posto na fila publicada."
)


def _iso(value: Any) -> Any:
    return value.isoformat() if hasattr(value, "isoformat") else value


def _to_public_material(row: dict[str, Any]) -> dict[str, Any]:
    """Material no DTO público: só o que o operador precisa acompanhar —
    sem autoria interna (picked_by/delivered_by ficam para o PCP)."""
    return {
        "productCode": row.get("product_code"),
        "description": row.get("description"),
        "unit": row.get("unit"),
        "status": row.get("status"),
    }


def _to_public_item(
    row: dict[str, Any],
    materials: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """DTO público: sem sessão, sem autoria PCP, sem internals do banco."""
    return {
        "id": row.get("id"),
        "productionOrder": row.get("production_order"),
        "operationCode": row.get("operation_code"),
        "reportedWorkCenter": row.get("reported_work_center"),
        "feedbackType": row.get("feedback_type"),
        "reasonCode": row.get("reason_code"),
        "note": row.get("note"),
        "status": row.get("status"),
        "createdAt": _iso(row.get("created_at")),
        "acknowledgedAt": _iso(row.get("acknowledged_at")),
        "resolvedAt": _iso(row.get("resolved_at")),
        "materials": [
            _to_public_material(item)
            for item in (materials if materials is not None else row.get("materials") or [])
        ],
    }


class PublicOperatorFeedbackService:
    def __init__(
        self,
        *,
        run_service: Any,
        machine_load: MachineLoadService,
        feedbacks: OperatorFeedbackService,
        run_lookup: Callable[..., dict[str, Any] | None],
        notify: Callable[..., None] | None = None,
        operation_materials: Any | None = None,
        feedback_materials: Any | None = None,
        notifications: Any | None = None,
    ) -> None:
        self._run_service = run_service
        self._machine_load = machine_load
        self._feedbacks = feedbacks
        self._run_lookup = run_lookup
        self._notify = notify
        # C5: catálogo SD4 da OP (PublicOperationMaterialsService) e a port
        # dos materiais gravados (para devolver status no list_active).
        self._operation_materials = operation_materials
        self._feedback_materials = feedback_materials
        # C6: Minha DELPI via Core API — camada de atenção, nunca bloqueante.
        self._notifications = notifications

    def report(
        self,
        *,
        session_token: str | None,
        production_order: str,
        operation_code: str,
        feedback_type: str,
        reason_code: str,
        note: str | None = None,
        material_codes: list[str] | None = None,
    ) -> dict[str, Any]:
        session = self._run_service.resolve_bench_session(session_token)
        branch = str(session.get("branch") or "").strip()
        work_center = str(session.get("work_center") or "").strip()
        context = self._published_context(
            branch=branch,
            work_center=work_center,
            production_order=production_order,
            operation_code=operation_code,
        )
        run_id = self._matching_run_id(
            branch=branch, work_center=work_center, context=context
        )
        materials = self._resolve_materials(
            branch=branch,
            context=context,
            reason_code=reason_code,
            material_codes=material_codes,
        )
        row = self._feedbacks.report(
            feedback_type=feedback_type,
            reason_code=reason_code,
            branch=branch,
            production_order=context["production_order"],
            operation_code=context["operation_code"],
            reported_work_center=work_center,
            operator_code=str(session.get("operator_code") or "").strip(),
            operator_name=str(session.get("operator_name") or "").strip(),
            bench_session_id=session.get("id"),
            run_id=run_id,
            note=note,
            product_code=context.get("product_code"),
            product_description=context.get("product_description"),
            pa_product_code=context.get("pa_product_code"),
            due_date=context.get("due_date"),
            materials=materials,
        )
        self._notify_created(branch=branch, feedback=row)
        self._notify_minha_delpi(feedback=row, materials=materials)
        return _to_public_item(row)

    def list_active(
        self,
        *,
        session_token: str | None,
        production_order: str,
        operation_code: str,
    ) -> dict[str, Any]:
        """Feedbacks ativos (open|acknowledged) da OP/operação neste posto.

        O lookup é pela identidade funcional — sem filtro de
        reported_work_center — então o cockpit do CT destino continua vendo o
        impedimento reportado no CT de origem após transferência.
        """
        session = self._run_service.resolve_bench_session(session_token)
        branch = str(session.get("branch") or "").strip()
        work_center = str(session.get("work_center") or "").strip()
        context = self._published_context(
            branch=branch,
            work_center=work_center,
            production_order=production_order,
            operation_code=operation_code,
        )
        rows = self._feedbacks.list_active_for_operation(
            branch=branch,
            production_order=context["production_order"],
            operation_code=context["operation_code"],
        )
        grouped = self._materials_for(rows)
        return {
            "items": [
                _to_public_item(row, grouped.get(row.get("id"), []))
                for row in rows
            ]
        }

    def _resolve_materials(
        self,
        *,
        branch: str,
        context: dict[str, Any],
        reason_code: str,
        material_codes: list[str] | None,
    ) -> list[dict[str, Any]] | None:
        """C5: missing_material exige seleção estruturada; o backend revalida
        cada código contra os materiais oficiais da OP (SD4) e congela o
        snapshot — o navegador nunca é autoridade sobre descrição/quantidade.

        Outros motivos ignoram a lista (não é erro mandar vazia).
        """
        reason = str(reason_code or "").strip()
        if reason != OperatorFeedbackReason.MISSING_MATERIAL.value:
            return None
        codes = [
            str(code or "").strip() for code in (material_codes or [])
        ]
        codes = [code for code in codes if code]
        if not codes:
            raise InvalidOperatorFeedbackMaterials(
                "Selecione pelo menos um material que está impedindo a produção."
            )
        if self._operation_materials is None:
            raise InvalidOperatorFeedbackMaterials(
                "Consulta de materiais indisponível."
            )
        official = self._operation_materials.list_for_feedback(
            branch=branch,
            production_order=context["production_order"],
            operation_code=context["operation_code"],
        )
        by_code = {
            str(item.get("product_code") or "").strip(): item
            for item in official
        }
        missing = [code for code in codes if code not in by_code]
        if missing:
            raise InvalidOperatorFeedbackMaterials(
                "Um ou mais materiais selecionados não pertencem a esta operação."
            )
        # Dedup preservando a ordem enviada; o snapshot é do item oficial.
        seen: set[str] = set()
        snapshots: list[dict[str, Any]] = []
        for code in codes:
            if code in seen:
                continue
            seen.add(code)
            item = by_code[code]
            snapshots.append(
                {
                    "product_code": item["product_code"],
                    "description": item.get("description") or "",
                    "unit": item.get("unit") or "",
                    "original_qty": item.get("original_qty") or 0,
                    "open_qty": item.get("open_qty") or 0,
                    "consumed_qty": item.get("consumed_qty") or 0,
                    "commitment_count": item.get("commitment_count") or 0,
                }
            )
        return snapshots

    def _materials_for(
        self, rows: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        if self._feedback_materials is None or not rows:
            return {}
        ids = [str(row["id"]) for row in rows if row.get("id")]
        return self._feedback_materials.list_for_feedbacks(ids)

    def _published_context(
        self,
        *,
        branch: str,
        work_center: str,
        production_order: str,
        operation_code: str,
    ) -> dict[str, Any]:
        context = self._machine_load.public_operation_feedback_context(
            branch=branch,
            production_order=production_order,
            operation_code=operation_code,
        )
        # Ausência na PUBLISHED e publicação em outro posto: mesma resposta —
        # um link anônimo não pode mapear a fila dos outros centros.
        if context is None or context.get("work_center") != work_center:
            raise SnapshotNotFound(_OPERATION_UNAVAILABLE)
        return context

    def _matching_run_id(
        self, *, branch: str, work_center: str, context: dict[str, Any]
    ) -> str | None:
        """run_id é contexto opcional: só vínculo quando o run ativo do posto é
        exatamente desta OP/operação. Leitura leve do repositório — sem Pulse,
        sem telemetria, sem efeitos colaterais."""
        run = self._run_lookup(branch=branch, work_center=work_center)
        if not run:
            return None
        same_order = (
            str(run.get("production_order") or "").strip().upper()
            == context["production_order"].upper()
        )
        same_op = (
            str(run.get("operation_code") or "").strip().lstrip("0") or "0"
        ) == (context["operation_code"].lstrip("0") or "0")
        if same_order and same_op:
            return run.get("id")
        return None

    def _notify_created(self, *, branch: str, feedback: dict[str, Any]) -> None:
        """Realtime é best-effort: persistência já aconteceu, falha no socket
        nunca transforma a criação salva em erro para o operador."""
        if self._notify is None:
            return
        try:
            self._notify(branch=branch, reason="created", feedback=feedback)
        except Exception:  # noqa: BLE001
            logger.warning("operator_feedback_notify_failed", exc_info=True)

    def _notify_minha_delpi(
        self,
        *,
        feedback: dict[str, Any],
        materials: list[dict[str, Any]] | None,
    ) -> None:
        """C6: dispara a atenção Minha DELPI DEPOIS do commit — a notificação
        jamais anuncia impedimento rollbackado. Best-effort: qualquer falha
        é logada dentro do service e não chega ao operador."""
        if self._notifications is None:
            return
        try:
            self._notifications.notify_feedback_created(
                feedback=feedback,
                material_count=len(materials or []),
            )
        except Exception:  # noqa: BLE001 — defesa extra além do service
            logger.warning(
                "operator_feedback_minha_delpi_notify_failed", exc_info=True
            )
