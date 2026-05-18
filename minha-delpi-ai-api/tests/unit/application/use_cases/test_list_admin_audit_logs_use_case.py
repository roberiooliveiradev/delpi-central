from uuid import uuid4

from app.application.use_cases.list_admin_audit_logs_use_case import ListAdminAuditLogsUseCase
from app.domain.ports.audit_repository_port import AuditLogQuery


class FakeAuditRepository:
    def __init__(self):
        self.last_query = None

    def log(self, **kwargs):
        return None

    def list_logs_page(self, query):
        self.last_query = query
        return (
            [
                {
                    "id": 1,
                    "userId": str(uuid4()),
                    "action": "chat.message.sent",
                    "promptHash": "abc",
                    "context": "chat",
                    "toolCalls": [],
                    "metadata": {},
                    "createdAt": "2026-05-18T10:00:00+00:00",
                }
            ],
            1,
        )

    def get_log(self, log_id):
        if log_id == 1:
            return {
                "id": 1,
                "promptHash": "abc",
                "action": "chat.message.sent",
            }
        return None

    def list_by_prompt_hash(self, *, prompt_hash, limit=20, exclude_id=None):
        return [{"id": 2, "action": "chat.tool.called", "promptHash": prompt_hash}]


def test_list_admin_audit_logs_returns_pagination():
    repository = FakeAuditRepository()
    use_case = ListAdminAuditLogsUseCase(repository)

    result = use_case.execute(limit=20, offset=0, action="chat.message")

    assert len(result["items"]) == 1
    assert result["pagination"]["total"] == 1
    assert result["pagination"]["hasNext"] is False
    assert repository.last_query.action == "chat.message"


def test_export_admin_audit_logs():
    use_case = ListAdminAuditLogsUseCase(FakeAuditRepository())

    result = use_case.execute_export(action="chat")

    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert "exportedAt" in result


def test_get_audit_log_detail_with_related():
    use_case = ListAdminAuditLogsUseCase(FakeAuditRepository())

    result = use_case.execute_detail(1)

    assert result is not None
    assert result["log"]["id"] == 1
    assert len(result["relatedLogs"]) == 1
