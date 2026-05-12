from uuid import UUID

from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.services.external_actions.external_action_execution_policy import (
    ExternalActionExecutionPolicy,
)


class ExecuteExternalActionUseCase:
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

        self.policy.validate(provider, action, arguments)

        result = self.gateway.execute(
            provider=provider,
            action=action,
            parameters=arguments.get("parameters") or {},
            body=arguments.get("body"),
            access_token=access_token,
        )

        sanitized_data = self.policy.sanitize_response(result["data"])

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
            },
        }
