from uuid import UUID

from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.services.external_actions.external_action_execution_policy import (
    ExternalActionExecutionPolicy,
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
        presentation = self.presenter.build_presentation(sanitized_data, path=action_path)
        chart_presentation = self.presenter.build_chart_presentation(
            sanitized_data, path=action_path,
        )

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
                        "path": action["path"],
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
                "path": action["path"],
                "status_code": result["statusCode"],
                "duration_ms": result["durationMs"],
                "sensitivity": action["sensitivity"],
            },
        )

        return {
            "provider": provider["providerKey"],
            "actionId": action["actionId"],
            "method": action["method"],
            "path": action["path"],
            "statusCode": result["statusCode"],
            "ok": result["ok"],
            "data": sanitized_data,
            "metadata": {
                "durationMs": result["durationMs"],
                "sensitivity": action["sensitivity"],
                "presentation": chart_presentation or presentation,
                "tablePresentation": presentation if chart_presentation else None,
            },
        }

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
