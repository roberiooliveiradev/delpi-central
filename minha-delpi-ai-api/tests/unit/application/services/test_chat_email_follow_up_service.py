from app.application.services.chat_email_follow_up_service import ChatEmailFollowUpService


def test_attach_email_follow_up_metadata():
    metadata: dict = {}
    message = "escreva um e-mail formal para o fornecedor sobre prazo"

    ChatEmailFollowUpService.attach_to_assistant_metadata(
        metadata,
        message=message,
        answer="Assunto: Prazo\n\nOlá.\n\nAtenciosamente,\n\n[Seu nome]",
    )

    labels = [item["label"] for item in metadata.get("emailFollowUpSuggestions") or []]
    assert len(labels) >= 5
    assert "Deixar mais formal" in labels
    assert metadata.get("textTask", {}).get("type") == "email"


def test_operational_draft_via_tool_context():
    metadata: dict = {}
    draft = {
        "text": "Assunto: Teste\n\nCorpo\n\n[Seu nome]",
        "textTask": {"type": "email", "source": "operational_data"},
        "dataSource": {"title": "Estoque", "path": "/stock"},
    }

    ChatEmailFollowUpService.attach_to_assistant_metadata(
        metadata,
        message="escreva e-mail com os dados",
        answer=draft["text"],
        tool_context={"operationalEmailDraft": draft},
    )

    assert metadata.get("emailDataSource", {}).get("path") == "/stock"


def test_no_metadata_for_operational_message():
    metadata: dict = {}
    ChatEmailFollowUpService.attach_to_assistant_metadata(
        metadata,
        message="qual o estoque do produto 10080001?",
    )
    assert "emailFollowUpSuggestions" not in metadata
