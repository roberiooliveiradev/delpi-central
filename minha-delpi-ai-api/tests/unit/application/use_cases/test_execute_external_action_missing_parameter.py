from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.external_actions.external_action_execution_policy import (
    ExternalActionExecutionPolicy,
)


class _Repo:
    def get_action_for_execution(self, action_id: str):
        return {
            "provider": {"enabled": True, "providerKey": "api_delpi"},
            "action": {
                "enabled": True,
                "method": "GET",
                "path": "/products/{code}/drawing",
                "actionId": action_id,
                "sensitivity": "read",
                "parametersSchema": [
                    {"name": "code", "required": True, "in": "path"},
                ],
            },
        }


class _Gateway:
    def execute(self, **kwargs):
        raise AssertionError("HTTP must not run when required parameter is missing")


class _Audit:
    def log(self, **kwargs):
        return None


def test_execute_use_case_skips_http_on_missing_required_parameter():
    use_case = ExecuteExternalActionUseCase(
        repository=_Repo(),
        gateway=_Gateway(),
        policy=ExternalActionExecutionPolicy(),
        audit_repository=_Audit(),
    )

    result = use_case.execute(
        user_id="00000000-0000-0000-0000-000000000001",
        access_token="token",
        action_id="api_delpi.products.get_product_drawing",
        arguments={"parameters": {}},
    )

    assert result["ok"] is False
    assert result["metadata"]["errorKind"] == "missing_required_parameter"
    assert result["metadata"]["missingParameter"] == "code"
    assert result["metadata"]["skippedHttp"] is True
    assert "code" in str(result["metadata"].get("selectionReason") or "")
