from app.application.services.audit_csv_exporter_service import AuditCsvExporterService


def test_export_rows_includes_header_and_trace_id():
    service = AuditCsvExporterService()

    csv_content = service.export_rows(
        [
            {
                "id": 1,
                "createdAt": "2026-05-18T10:00:00+00:00",
                "traceId": "trace-abc",
                "action": "chat.message.sent",
                "context": "chat",
                "userId": "user-1",
                "promptHash": "hash",
                "metadata": {"session_id": "sess-1"},
                "toolCalls": [],
            }
        ]
    )

    lines = csv_content.strip().splitlines()

    assert lines[0].startswith("id,createdAt,traceId")
    assert "trace-abc" in lines[1]
    assert "chat.message.sent" in lines[1]
