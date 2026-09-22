"""F3 — executor blocks write without confirmation (defense-in-depth)."""

from __future__ import annotations

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.external_actions.external_action_execution_policy import (
    ExternalActionExecutionPolicy,
)


class _Repo:
    def __init__(self, action: dict):
        self._action = action

    def get_action_for_execution(self, action_id: str):
        return {
            "provider": {"enabled": True, "providerKey": "api_delpi"},
            "action": {**self._action, "actionId": action_id},
        }


class _Gateway:
    def __init__(self):
        self.calls = 0

    def execute(self, **kwargs):
        self.calls += 1
        return {
            "ok": True,
            "statusCode": 200,
            "data": {"ok": True},
            "durationMs": 1,
        }


class _Audit:
    def log(self, **kwargs):
        return None


def _use_case(action: dict, gateway: _Gateway | None = None):
    gw = gateway or _Gateway()
    return (
        ExecuteExternalActionUseCase(
            repository=_Repo(action),
            gateway=gw,
            policy=ExternalActionExecutionPolicy(),
            audit_repository=_Audit(),
        ),
        gw,
    )


def test_executor_blocks_write_without_confirm():
    use_case, gateway = _use_case(
        {
            "enabled": True,
            "method": "POST",
            "path": "/quality/action-plans",
            "sensitivity": "write",
            "parametersSchema": [],
        }
    )
    result = use_case.execute(
        user_id="00000000-0000-0000-0000-000000000001",
        access_token="token",
        action_id="api_delpi.quality.create",
        arguments={"parameters": {}},
    )
    assert result["ok"] is False
    assert result["metadata"]["blockReason"] == "confirmation_required"
    assert result["metadata"]["skippedHttp"] is True
    assert gateway.calls == 0


def test_executor_allows_write_after_confirm_message():
    use_case, gateway = _use_case(
        {
            "enabled": True,
            "method": "POST",
            "path": "/quality/action-plans",
            "sensitivity": "write",
            "parametersSchema": [],
        }
    )
    result = use_case.execute(
        user_id="00000000-0000-0000-0000-000000000001",
        access_token="token",
        action_id="api_delpi.quality.create",
        arguments={"parameters": {"userMessage": "confirmo criar o plano"}},
    )
    assert result["ok"] is True
    assert gateway.calls == 1


def test_executor_allows_write_with_confirmed_flag():
    use_case, gateway = _use_case(
        {
            "enabled": True,
            "method": "DELETE",
            "path": "/records/1",
            "sensitivity": "destructive",
            "parametersSchema": [],
        }
    )
    result = use_case.execute(
        user_id="00000000-0000-0000-0000-000000000001",
        access_token="token",
        action_id="api_delpi.records.delete",
        arguments={"parameters": {"confirmed": True}},
    )
    assert result["ok"] is True
    assert gateway.calls == 1


def test_executor_sql_post_skips_write_confirm_gate():
    use_case, gateway = _use_case(
        {
            "enabled": True,
            "method": "POST",
            "path": "/data/sql",
            "sensitivity": "sql",
            "parametersSchema": [],
        }
    )
    result = use_case.execute(
        user_id="00000000-0000-0000-0000-000000000001",
        access_token="token",
        action_id="api_delpi.data.sql",
        arguments={"parameters": {"sql": "SELECT 1"}},
    )
    assert result["ok"] is True
    assert gateway.calls == 1
