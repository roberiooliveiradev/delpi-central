"""Playbook 08 — sinais de confiança."""

from app.domain.services.chat_trust_signals_service import ChatTrustSignalsService


def test_authorized_data_when_tool_ok():
    signals = ChatTrustSignalsService.build(
        message="estoque do produto 10080001",
        answer="Segue o estoque.",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"ok": True, "path": "/products/10080001/stock"},
            }
        ],
        sources=[],
    )
    ids = {item["id"] for item in signals}

    assert "authorized_data" in ids


def test_draft_for_text_task():
    signals = ChatTrustSignalsService.build(
        message="reescreva o e-mail",
        answer="Segue o rascunho.",
        tool_calls=[],
        sources=[],
        workspace_context={"textTaskCategory": "email"},
    )

    assert any(item["id"] == "draft" for item in signals)


def test_permission_limited_on_forbidden():
    signals = ChatTrustSignalsService.build(
        message="consulta restrita",
        answer="Sem acesso.",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"ok": False, "statusCode": 403, "detail": "forbidden"},
            }
        ],
        sources=[],
    )
    ids = {item["id"] for item in signals}

    assert "permission_limited" in ids
    assert "api_unavailable" in ids
