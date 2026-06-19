"""Entradas de log de atividade para streaming do chat (estilo Cursor)."""

from __future__ import annotations

import time
import uuid
from typing import Any

from app.application.services.chat_composite_direct_answer_service import (
    ChatCompositeDirectAnswerService,
)
from app.domain.services.chat_web_search_direct_answer_service import (
    ChatWebSearchDirectAnswerService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


def _phase_group(phase: str) -> str:
    groups = ChatAssistantContentService.get_mapping("stream", "activity", "phaseGroups")

    return groups.get(
        str(phase or "").strip(),
        ChatAssistantContentService.get("stream", "activity", "defaultPhaseGroup", default="Atividade"),
    )


def _drawing_stage_message(step_key: str) -> str | None:
    stages = ChatAssistantContentService.get_mapping("stream", "activity", "drawingStages")

    return stages.get(str(step_key or "").strip())


class ChatStreamActivityService:
    @classmethod
    def drawing_stage_message(cls, step_key: str) -> str | None:
        return _drawing_stage_message(step_key)

    @classmethod
    def entry(
        cls,
        *,
        verb: str,
        target: str,
        phase: str | None = None,
        level: str = "info",
        state: str = "done",
        detail: str | None = None,
        path: str | None = None,
        status_code: int | None = None,
        action_id: str | None = None,
        message: str | None = None,
        entry_id: str | None = None,
    ) -> dict[str, Any]:
        group = _phase_group(phase)
        summary = message or f"{verb} {target}".strip()

        payload: dict[str, Any] = {
            "id": entry_id or str(uuid.uuid4()),
            "at": time.time(),
            "level": level,
            "phase": phase,
            "group": group,
            "verb": verb,
            "target": target,
            "state": state,
            "message": summary,
        }

        if detail:
            payload["detail"] = detail

        if path:
            payload["path"] = path

        if status_code is not None:
            payload["statusCode"] = status_code

        if action_id:
            payload["actionId"] = action_id

        return payload

    @classmethod
    def think(
        cls,
        *,
        target: str,
        verb: str = "Pensando",
        state: str = "active",
        detail: str | None = None,
        message: str | None = None,
        level: str = "info",
        entry_id: str | None = None,
    ) -> dict[str, Any]:
        return cls.entry(
            verb=verb,
            target=target,
            phase="think",
            state=state,
            level=level,
            detail=detail,
            message=message or f"{verb} {target}".strip(),
            entry_id=entry_id,
        )

    @classmethod
    def plan_step(
        cls,
        *,
        step: int,
        total: int,
        target: str,
        verb: str = "Planejar",
        state: str = "active",
        detail: str | None = None,
        message: str | None = None,
        level: str = "info",
    ) -> dict[str, Any]:
        summary = message or f"{verb} passo {step}/{total}: {target}"

        return cls.entry(
            verb=verb,
            target=target,
            phase="plan",
            state=state,
            level=level,
            detail=detail,
            message=summary,
        )

    @classmethod
    def drawing_analysis_phase(
        cls,
        *,
        target: str = "desenho técnico",
        message: str | None = None,
        state: str = "active",
    ) -> dict[str, Any]:
        return cls.entry(
            verb="Analisando",
            target=target,
            phase="drawing_analysis",
            state=state,
            level="info",
            message=message or "Análise de desenho DELPI em andamento…",
            entry_id="drawing-analysis",
        )

    @classmethod
    def drawing_analysis_step(
        cls,
        *,
        step_key: str,
        message: str,
        state: str = "active",
    ) -> dict[str, Any]:
        return cls.entry(
            verb="Analisando",
            target="desenho técnico",
            phase="drawing_analysis",
            state=state,
            level="info",
            message=message,
            entry_id=f"drawing-analysis-{step_key}",
        )

    @classmethod
    def emit_drawing_analysis_progress(
        cls,
        on_stream_activity,
        *,
        has_pdf: bool,
        phase: str = "start",
    ) -> None:
        if not on_stream_activity:
            return

        if phase == "complete":
            on_stream_activity(
                cls.drawing_analysis_step(
                    step_key="build_report",
                    message=_drawing_stage_message("build_report") or "Gerando relatório…",
                    state="done",
                )
            )
            return

        for step_key, message in ChatAssistantContentService.get_mapping(
            "stream",
            "activity",
            "drawingStages",
        ).items():
            if step_key == "read_pdf" and not has_pdf:
                continue

            on_stream_activity(
                cls.drawing_analysis_step(
                    step_key=step_key,
                    message=message,
                    state="active",
                )
            )

    @classmethod
    def document_vision_step(
        cls,
        *,
        step_key: str,
        message: str,
        state: str = "active",
    ) -> dict[str, Any]:
        return cls.entry(
            verb="Extraindo",
            target="texto do documento",
            phase="document_vision",
            state=state,
            level="info",
            message=message,
            entry_id=f"document-vision-{step_key}",
        )

    @classmethod
    def emit_document_vision_progress(
        cls,
        on_stream_activity,
        *,
        phase: str = "start",
        engine: str | None = None,
        char_count: int | None = None,
    ) -> None:
        if not on_stream_activity:
            return

        if phase == "start":
            on_stream_activity(
                cls.document_vision_step(
                    step_key="start",
                    message="OCR e leitura do anexo…",
                    state="active",
                )
            )
            return

        if phase == "ocr":
            on_stream_activity(
                cls.document_vision_step(
                    step_key="ocr",
                    message="Reconhecendo texto (Tesseract)…",
                    state="active",
                )
            )
            return

        if phase == "complete":
            parts: list[str] = []
            if engine:
                parts.append(f"motor {engine}")
            if char_count is not None and char_count > 0:
                parts.append(f"{char_count} caracteres")
            detail = f" ({', '.join(parts)})" if parts else ""
            on_stream_activity(
                cls.document_vision_step(
                    step_key="complete",
                    message=f"Texto extraído{detail}",
                    state="done",
                )
            )

    @classmethod
    def emit_planned_actions(
        cls,
        on_stream_activity,
        planned_actions: list[dict],
        *,
        prefix: str = "Consulta",
    ) -> None:
        if not on_stream_activity or not planned_actions:
            return

        total = len(planned_actions)

        on_stream_activity(
            cls.plan_step(
                step=1,
                total=max(total, 1),
                target=f"{total} passo(s) na API DELPI",
                verb="Planejando",
                state="active",
                message="Organizando as consultas necessárias...",
                detail="Sequência de consultas definida para esta pergunta.",
            )
        )

        for index, action in enumerate(planned_actions, start=1):
            arguments = action.get("arguments") or {}
            action_id = str(
                arguments.get("actionId") or arguments.get("action_id") or ""
            ).strip()
            parameters = arguments.get("parameters") or {}
            code = ""

            if isinstance(parameters, dict):
                code = str(parameters.get("code") or "").strip()

            label_parts = [part for part in (prefix, action_id, code) if part]
            label = " · ".join(label_parts) if label_parts else f"{prefix} {index}"

            on_stream_activity(
                cls.plan_step(
                    step=index,
                    total=total,
                    target=label,
                    verb="Passo",
                    state="done",
                    detail=str(action.get("reason") or "").strip() or None,
                )
            )

    @classmethod
    def tool_planned(
        cls,
        *,
        index: int,
        total: int,
        path: str | None,
        action_id: str | None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        label = path or action_id or f"consulta {index}"

        return cls.entry(
            verb="Planejando",
            target=label,
            phase="tools",
            state="active",
            detail=reason,
            path=path,
            action_id=action_id,
        )

    @classmethod
    def tool_started(
        cls,
        *,
        index: int,
        total: int,
        path: str | None,
        action_id: str | None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        label = path or action_id or f"consulta {index}"

        progress = f" ({index}/{total})" if total > 1 else ""

        return cls.entry(
            verb="Consultando",
            target=label,
            phase="tools",
            state="active",
            detail=reason or f"Consultando {label}",
            path=path,
            action_id=action_id,
            message=f"Buscando as informações que você pediu...{progress}",
        )

    @classmethod
    def tool_finished(
        cls,
        *,
        index: int,
        total: int,
        metadata: dict,
        path: str | None = None,
        action_id: str | None = None,
        data: object | None = None,
    ) -> dict[str, Any]:
        resolved_path = path or str(metadata.get("path") or "")
        resolved_action = action_id or str(metadata.get("actionId") or "")
        label = resolved_path or resolved_action or f"consulta {index}"

        if not ChatCompositeDirectAnswerService._is_success(metadata):
            detail = ChatCompositeDirectAnswerService._failure_message(metadata)
            status_code = metadata.get("statusCode")

            try:
                code = int(status_code)
            except (TypeError, ValueError):
                code = None

            return cls.entry(
                verb="Falhou",
                target=label,
                phase="tools",
                level="error",
                state="failed",
                detail=detail or f"{label}: falha na consulta",
                path=resolved_path or None,
                action_id=resolved_action or None,
                status_code=code,
                message="Não consegui concluir essa consulta.",
            )

        presenter = ExternalActionResultPresenter()
        humanized = presenter.present(data, path=resolved_path)

        if ChatCompositeDirectAnswerService._is_empty_result(humanized, data):
            return cls.entry(
                verb="Sem dados",
                target=label,
                phase="tools",
                level="warning",
                state="done",
                detail=(
                    "A API respondeu com sucesso, mas não trouxe registros. "
                    "Verifique código, filtros ou permissões."
                ),
                path=resolved_path or None,
                action_id=resolved_action or None,
                status_code=int(metadata.get("statusCode") or 200),
                message="A consulta não trouxe registros.",
            )

        return cls.entry(
            verb="Recebido",
            target=label,
            phase="tools",
            level="success",
            state="done",
            path=resolved_path or None,
            action_id=resolved_action or None,
            status_code=int(metadata.get("statusCode") or 200),
            message="Dados recebidos. Organizando a resposta...",
        )

    @classmethod
    def web_search_started(
        cls,
        *,
        query: str,
        entry_id: str = "web-search",
    ) -> dict[str, Any]:
        cleaned = str(query or "").strip() or "consulta web"

        return cls.entry(
            verb="Buscando",
            target=cleaned,
            phase="web_search",
            state="active",
            message=f"Buscando «{cleaned}» na internet pública",
            entry_id=entry_id,
        )

    @classmethod
    def web_search_finished(
        cls,
        *,
        payload: dict,
        entry_id: str = "web-search",
    ) -> dict[str, Any]:
        query = str(payload.get("query") or "").strip() or "consulta web"
        status = str(payload.get("searchStatus") or "").strip()
        useful = ChatWebSearchDirectAnswerService.extract_useful_results(payload)
        provider = str(payload.get("provider") or "").strip()
        detail_parts = [part for part in (provider, f"{len(useful)} resultado(s)") if part]
        detail = " · ".join(detail_parts) if detail_parts else None

        if status == "no_results" or not useful:
            return cls.entry(
                verb="Sem resultados",
                target=query,
                phase="web_search",
                level="warning",
                state="done",
                detail=detail,
                message=f"Busca web sem resultados úteis para «{query}»",
                entry_id=entry_id,
            )

        return cls.entry(
            verb="Encontrado",
            target=query,
            phase="web_search",
            level="success",
            state="done",
            detail=detail,
            message=f"Busca web: {len(useful)} fonte(s) para «{query}»",
            entry_id=entry_id,
        )

    @classmethod
    def from_tool_calls(cls, tool_calls: list[dict] | None) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        external_calls = [
            item
            for item in (tool_calls or [])
            if str(item.get("name") or "") == "execute_external_action"
        ]
        total = len(external_calls)

        for index, tool_call in enumerate(external_calls, start=1):
            metadata = tool_call.get("metadata") or {}
            arguments = tool_call.get("arguments") or {}
            action_id = str(arguments.get("actionId") or arguments.get("action_id") or "")
            path = str(metadata.get("path") or "")

            entries.append(
                cls.tool_finished(
                    index=index,
                    total=total,
                    metadata=metadata if isinstance(metadata, dict) else {},
                    path=path or None,
                    action_id=action_id or None,
                    data=metadata.get("responsePreview"),
                )
            )

        return entries
