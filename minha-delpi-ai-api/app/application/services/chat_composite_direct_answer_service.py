from __future__ import annotations

from dataclasses import dataclass

from app.domain.services.chat_external_action_direct_answer_service import (
    ChatExternalActionDirectAnswerService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from app.domain.services.external_actions.external_action_sql_capability_service import (
    ExternalActionSqlCapabilityService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)
from app.infrastructure.config.settings import Settings


@dataclass(frozen=True)
class ExternalActionExecutionResult:
    metadata: dict
    data: object
    reason: str | None = None


class ChatCompositeDirectAnswerService:
    """Monta resposta direta única a partir de várias consultas à API."""

    @classmethod
    def build(
        cls,
        message: str,
        executions: list[ExternalActionExecutionResult],
    ) -> str | None:
        if not Settings.CHAT_EXTERNAL_ACTION_DIRECT_RESPONSE_ENABLED:
            return None

        if not executions:
            return None

        presenter = ExternalActionResultPresenter()
        sections: list[str] = []
        issues: list[str] = []

        for index, execution in enumerate(executions, start=1):
            metadata = execution.metadata or {}
            path = str(metadata.get("path") or "")
            action_id = str(metadata.get("actionId") or "")
            label = cls._action_label(path, action_id, index)

            if not cls._is_success(metadata):
                issues.append(
                    f"- **{label}:** {cls._failure_message(metadata, path=path)}"
                )
                continue

            try:
                humanized = presenter.present(
                    ExternalActionSqlCapabilityService.attach_request_sql_to_data(
                        execution.data,
                        metadata=metadata,
                    ),
                    path=path,
                )
            except Exception:
                issues.append(
                    f"- **{label}:** {ExternalActionResponseContentService.get('composite', 'formatFailed')}"
                )
                continue
            body = ChatExternalActionDirectAnswerService.format(
                humanized,
                message=message,
                path=path,
                operation_id=str(metadata.get("operationId") or ""),
            )

            if cls._is_empty_result(humanized, execution.data, path=path):
                if ExternalActionSqlCapabilityService.is_sql_execution_context(
                    path=path,
                    operation_id=str(metadata.get("operationId") or ""),
                    action_id=action_id,
                ) or ExternalActionSqlCapabilityService.is_sql_result_payload(
                    cls._unwrap_payload(execution.data)
                ):
                    body = ChatExternalActionDirectAnswerService.format(
                        humanized,
                        message=message,
                        path=path,
                        operation_id=str(metadata.get("operationId") or ""),
                    )

                    if body:
                        sections.append(body.strip())
                        continue

                issues.append(
                    f"- **{label}:** {ExternalActionResponseContentService.get('composite', 'emptyResult')}"
                )
                continue

            if body:
                if len(executions) > 1:
                    sections.append(f"### {label}\n\n{body.strip()}")
                else:
                    sections.append(body.strip())
            else:
                issues.append(
                    f"- **{label}:** {ExternalActionResponseContentService.get('composite', 'formatFailed')}"
                )

        if not sections and not issues:
            return None

        parts: list[str] = []

        if len(executions) > 1:
            if not issues:
                intro = (
                    cls._build_multi_product_codes_intro(message, executions)
                    or cls._build_multi_route_intro(message, executions)
                )

                if intro:
                    parts.append(intro)
                else:
                    parts.append(
                        ExternalActionResponseContentService.get(
                            "composite",
                            "allSuccessful",
                        )
                    )
            else:
                parts.append(
                    ExternalActionResponseContentService.format(
                        "composite",
                        "multiExecutionSummary",
                        count=len(executions),
                    )
                )
            parts.append("")

        parts.extend(sections)

        if issues:
            parts.append("")
            parts.append(ExternalActionResponseContentService.get("composite", "attentionHeader"))
            parts.extend(issues)

        return "\n".join(parts).strip()

    @classmethod
    def _is_success(cls, metadata: dict) -> bool:
        if not metadata.get("ok"):
            return False

        status_code = metadata.get("statusCode")

        try:
            return 200 <= int(status_code) < 300
        except (TypeError, ValueError):
            return False

    @classmethod
    def _failure_message(cls, metadata: dict, *, path: str = "") -> str:
        from app.domain.services.chat_security_messaging_service import (
            ChatSecurityMessagingService,
        )

        return ChatSecurityMessagingService.resolve_api_failure(
            metadata,
            path=path or str(metadata.get("path") or ""),
        )

    @classmethod
    def _is_empty_result(
        cls,
        humanized: dict,
        data: object,
        *,
        path: str = "",
    ) -> bool:
        lowered_path = str(path or "").lower()

        if cls._has_product_payload(data):
            return False

        linhas = [
            str(line).strip()
            for line in (humanized.get("linhas") or [])
            if str(line).strip()
        ]

        empty_phrases = (
            "nenhum registro",
            "nenhuma ordem",
            "nenhum produto",
            "não retornou registros",
            "não encontrado",
        )

        if linhas and any(phrase in line.lower() for line in linhas for phrase in empty_phrases):
            return True

        if isinstance(data, dict):
            root = data.get("data", data)

            if isinstance(root, dict):
                items = root.get("items")

                if isinstance(items, list) and len(items) == 0:
                    return True

                if "/structure" in lowered_path and "/analyser" not in lowered_path:
                    structure = root.get("structure")

                    if isinstance(structure, dict):
                        structure_items = structure.get("items")

                        if isinstance(structure_items, list) and len(structure_items) == 0:
                            return True

        return len(linhas) == 0 and humanized.get("titulo") is None

    @classmethod
    def _unwrap_payload(cls, data: object) -> dict | None:
        if not isinstance(data, dict):
            return None

        root = data.get("data", data)

        if isinstance(root, dict) and "data" in root and isinstance(root["data"], dict):
            return root["data"]

        if isinstance(root, dict):
            return root

        return None

    @classmethod
    def _has_product_payload(cls, data: object) -> bool:
        if not isinstance(data, dict):
            return False

        root = data.get("data", data)

        if not isinstance(root, dict):
            return False

        product = root.get("product")

        if not isinstance(product, dict):
            return False

        return bool(
            str(product.get("code") or product.get("description") or "").strip()
        )

    @classmethod
    def _build_multi_product_codes_intro(
        cls,
        message: str,
        executions: list[ExternalActionExecutionResult],
    ) -> str | None:
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )
        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )
        from app.domain.services.chat_product_plural_phrasing_service import (
            ChatProductPluralPhrasingService,
        )
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        codes: list[str] = []
        scope_labels: list[str] = []

        for execution in executions:
            metadata = execution.metadata or {}

            if not cls._is_success(metadata):
                continue

            path = str(metadata.get("path") or "").lower()

            if not path.startswith("/products/"):
                continue

            code = ChatProductQueryIntentService.extract_product_code(path)

            if code and code not in codes:
                codes.append(code)

            for label in ChatProductPluralPhrasingService.scope_labels_from_api_path(path):
                if label not in scope_labels:
                    scope_labels.append(label)

        scope_label = ChatProductOperationalContentService.join_list_pt(scope_labels)

        message_codes = ChatAnalysisIntentService.extract_all_product_codes(message)

        for code in message_codes:
            if code not in codes:
                codes.append(code)

        if len(codes) < 2 or not scope_label:
            return None

        return ExternalActionResponseContentService.format(
            "composite",
            "multiProductCodesIntro",
            codes=cls._join_pt_list(codes),
            scope=scope_label,
        )

    @classmethod
    def _build_multi_route_intro(
        cls,
        message: str,
        executions: list[ExternalActionExecutionResult],
    ) -> str | None:
        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        scope_labels: list[str] = []
        product_code: str | None = None

        for execution in executions:
            metadata = execution.metadata or {}

            if not cls._is_success(metadata):
                continue

            path = str(metadata.get("path") or "").lower()

            if not path.startswith("/products/"):
                continue

            if product_code is None:
                product_code = ChatProductQueryIntentService.extract_product_code(
                    message
                ) or ChatProductQueryIntentService.extract_product_code(path)

            for label in ChatProductOperationalContentService.composite_short_scope_labels_from_path(
                path
            ):
                if label not in scope_labels:
                    scope_labels.append(label)

        if len(scope_labels) < 2:
            return None

        code = product_code or ChatProductOperationalContentService.get(
            "composite",
            "informedProductFallback",
            default="informado",
        )
        scopes = ChatProductOperationalContentService.join_list_pt(scope_labels)

        return ExternalActionResponseContentService.format(
            "composite",
            "multiProductRouteIntro",
            code=code,
            scopes=scopes,
        )

    @staticmethod
    def _join_pt_list(items: list[str]) -> str:
        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        return ChatProductOperationalContentService.join_list_pt(items)

    @classmethod
    def _action_label(cls, path: str, action_id: str, index: int) -> str:
        if path:
            from app.application.services.chat_action_label_service import (
                ChatActionLabelService,
            )
            from app.domain.services.chat_product_query_intent_service import (
                ChatProductQueryIntentService,
            )

            label = ChatActionLabelService.humanize(
                path=path,
                method="GET",
                summary="",
                action_id=action_id,
            )

            code = ChatProductQueryIntentService.extract_product_code(path)

            if code and label and label != path and code not in label:
                label = f"{label} — {code}"

            if label and label != path:
                return label

            return path

        if action_id:
            return ExternalActionResponseContentService.format(
                "composite",
                "actionLabel",
                action_id=action_id,
            )

        return ExternalActionResponseContentService.format(
            "composite",
            "queryLabel",
            index=index,
        )
