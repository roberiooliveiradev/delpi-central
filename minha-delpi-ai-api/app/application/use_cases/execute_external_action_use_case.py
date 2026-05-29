from urllib.parse import quote
from uuid import UUID

from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.services.external_actions.external_action_execution_policy import (
    ExternalActionExecutionPolicy,
)
from app.domain.services.chat_data_coverage_notice_service import (
    ChatDataCoverageNoticeService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


class ExecuteExternalActionUseCase:
    INTERNAL_PARAMETER_NAMES = {
        "message",
        "prompt",
        "question",
        "input",
        "text",
        "queryText",
        "query_text",
        "userMessage",
        "user_message",
    }

    def __init__(
        self,
        repository,
        gateway,
        policy: ExternalActionExecutionPolicy,
        audit_repository: AuditRepositoryPort,
    ):
        self.repository = repository
        self.gateway = gateway
        self.policy = policy
        self.audit_repository = audit_repository
        self.presenter = ExternalActionResultPresenter()

    def execute(
        self,
        user_id: str,
        access_token: str,
        action_id: str,
        arguments: dict,
    ) -> dict:
        action_bundle = self.repository.get_action_for_execution(action_id)

        if not action_bundle:
            raise ValueError("Action not found")

        provider = action_bundle["provider"]
        action = action_bundle["action"]
        arguments = self._normalize_arguments_for_method(action, arguments)
        arguments = self._drop_internal_unknown_parameters(action, arguments)

        self.policy.validate(provider, action, arguments)

        result = self.gateway.execute(
            provider=provider,
            action=action,
            parameters=arguments.get("parameters") or {},
            body=arguments.get("body"),
            access_token=access_token,
        )

        sanitized_data = self.policy.sanitize_response(result["data"])
        action_path = action.get("path") or ""
        resolved_path = self._resolve_action_path(
            action_path,
            arguments.get("parameters") or {},
        )
        text_presentation = self.presenter.build_text_presentation(
            sanitized_data,
            path=resolved_path,
        )
        tree_presentation = self.presenter.build_tree_presentation(
            sanitized_data,
            path=resolved_path,
        )
        presentation = self.presenter.build_presentation(
            sanitized_data,
            path=resolved_path,
            response_schema=action.get("responseSchema"),
        )
        chart_presentation = self.presenter.build_chart_presentation(
            sanitized_data, path=resolved_path,
        )

        table_presentation = None
        if isinstance(presentation, dict) and presentation.get("type") == "markdown":
            if not text_presentation:
                text_presentation = presentation
            presentation = None
        elif isinstance(presentation, dict) and presentation.get("type") == "table":
            table_presentation = presentation
        elif presentation:
            table_presentation = presentation

        self.audit_repository.log(
            user_id=UUID(user_id),
            action="external_action.called",
            context="external_action",
            tool_calls=[
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "provider": provider["providerKey"],
                        "actionId": action["actionId"],
                        "method": action["method"],
                        "path": resolved_path,
                        "statusCode": result["statusCode"],
                        "durationMs": result["durationMs"],
                        "sensitivity": action["sensitivity"],
                    },
                }
            ],
            metadata={
                "provider": provider["providerKey"],
                "action_id": action["actionId"],
                "method": action["method"],
                "path": resolved_path,
                "status_code": result["statusCode"],
                "duration_ms": result["durationMs"],
                "sensitivity": action["sensitivity"],
            },
        )

        available_formats: list[str] = []
        if text_presentation:
            available_formats.append("text")
        if tree_presentation:
            available_formats.append("tree")
        if table_presentation:
            available_formats.append("table")
        if chart_presentation:
            available_formats.append("chart")
        elif table_presentation:
            forced_chart = self.presenter.build_chart_presentation(
                sanitized_data, path=action_path, force=True
            )
            if forced_chart:
                chart_presentation = forced_chart
                available_formats.append("chart")

        path_lower = str(resolved_path or "").lower()
        structure_like = any(
            token in path_lower for token in ("/structure", "/parents", "/analyser")
        )

        if tree_presentation and structure_like:
            primary_presentation = tree_presentation
        elif chart_presentation:
            primary_presentation = chart_presentation
        elif table_presentation:
            primary_presentation = table_presentation
        elif tree_presentation:
            primary_presentation = tree_presentation
        else:
            primary_presentation = None

        preferred_format = None

        if tree_presentation and structure_like:
            preferred_format = "tree"
        elif table_presentation:
            preferred_format = "table"
        elif text_presentation:
            preferred_format = "text"
        elif chart_presentation:
            preferred_format = "chart"

        request_parameters = dict(arguments.get("parameters") or {})
        data_coverage_notice = ChatDataCoverageNoticeService.build(
            sanitized_data,
            path=resolved_path,
            parameters=request_parameters,
            presentation=primary_presentation,
            table_presentation=table_presentation,
        )

        return {
            "provider": provider["providerKey"],
            "actionId": action["actionId"],
            "method": action["method"],
            "path": resolved_path,
            "statusCode": result["statusCode"],
            "ok": result["ok"],
            "data": sanitized_data,
            "metadata": {
                "durationMs": result["durationMs"],
                "sensitivity": action["sensitivity"],
                "presentation": primary_presentation,
                "tablePresentation": (
                    table_presentation
                    if table_presentation is not None
                    and table_presentation is not primary_presentation
                    else None
                ),
                "treePresentation": (
                    tree_presentation
                    if tree_presentation is not None
                    and tree_presentation is not primary_presentation
                    else None
                ),
                "textPresentation": text_presentation,
                "availableFormats": available_formats,
                "preferredFormat": preferred_format,
                "dataCoverageNotice": data_coverage_notice,
            },
        }

    @staticmethod
    def _resolve_action_path(path: str, parameters: dict) -> str:
        resolved = str(path or "")

        for key, value in (parameters or {}).items():
            if value in (None, ""):
                continue

            token = "{" + str(key) + "}"

            if token in resolved:
                resolved = resolved.replace(
                    token,
                    quote(str(value), safe=""),
                )

        return resolved

    def _drop_internal_unknown_parameters(self, action: dict, arguments: dict) -> dict:
        normalized = dict(arguments or {})
        parameters = dict(normalized.get("parameters") or {})

        if not parameters:
            normalized["parameters"] = parameters
            return normalized

        allowed_parameter_names = {
            parameter.get("name")
            for parameter in action.get("parametersSchema") or []
            if parameter.get("name")
        }

        cleaned_parameters = {}

        for key, value in parameters.items():
            if key in allowed_parameter_names:
                cleaned_parameters[key] = value
                continue

            if key in self.INTERNAL_PARAMETER_NAMES:
                continue

            cleaned_parameters[key] = value

        normalized["parameters"] = cleaned_parameters
        return normalized

    def _normalize_arguments_for_method(self, action: dict, arguments: dict) -> dict:
        normalized = dict(arguments or {})
        method = str(action.get("method") or "").upper()

        parameters = dict(normalized.get("parameters") or {})
        body = normalized.get("body")

        if method not in {"GET", "HEAD", "DELETE"}:
            normalized["parameters"] = parameters
            return normalized

        if body in (None, "", {}, []):
            normalized["parameters"] = parameters
            normalized["body"] = None
            return normalized

        if isinstance(body, dict):
            for key, value in body.items():
                if value in (None, ""):
                    continue

                parameters.setdefault(key, value)

        normalized["parameters"] = parameters
        normalized["body"] = None

        return normalized
