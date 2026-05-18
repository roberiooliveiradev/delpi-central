from datetime import datetime, timezone

from app.infrastructure.persistence.postgres_admin_metrics_repository import (
    PostgresAdminMetricsRepository,
)


class FakeAuditRow:
    def __init__(self, metadata):
        self.audit_metadata = metadata


def test_rag_test_metrics_computes_assertiveness_rate(monkeypatch):
    repository = PostgresAdminMetricsRepository()
    since = datetime.now(timezone.utc)

    fake_rows = [
        FakeAuditRow({"assertive": True, "score": 0.9, "chunk_count": 3}),
        FakeAuditRow({"assertive": False, "score": 0.1, "chunk_count": 0}),
    ]

    class FakeQuery:
        def filter(self, *_args, **_kwargs):
            return self

        def all(self):
            return fake_rows

    monkeypatch.setattr(
        "app.infrastructure.persistence.postgres_admin_metrics_repository.db.session.query",
        lambda *_args, **_kwargs: FakeQuery(),
    )

    result = repository._rag_test_metrics_24h(since=since)

    assert result["totalTests"] == 2
    assert result["assertiveTests"] == 1
    assert result["assertivenessRate"] == 0.5
