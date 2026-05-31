from app.application.services.chat_email_operational_composer_service import (
    ChatEmailOperationalComposerService,
)
from app.application.services.chat_email_follow_up_service import ChatEmailFollowUpService


def test_operational_draft_structure():
    summary = {
        "titulo": "Estoque do produto",
        "path": "/products/10080001/stock",
        "linhas": ["Filial 01: 100 un.", "Filial 02: 50 un."],
    }
    message = "consulte estoque do 10080001 e escreva um e-mail para compras"

    draft = ChatEmailOperationalComposerService.build_from_summary(summary, message)

    assert draft is not None
    text = draft["text"]
    assert text.startswith("Assunto:")
    assert "10080001" in text
    assert "Filial 01" in text
    assert "[Seu nome]" in text
    assert "Fonte dos dados" in text
    assert "/products/10080001/stock" in text
    assert draft["textTask"]["source"] == "operational_data"
    assert draft["dataSource"]["productCode"] == "10080001"


def test_follow_up_metadata_from_operational_draft():
    draft = ChatEmailOperationalComposerService.build_from_summary(
        {
            "titulo": "Estoque",
            "linhas": ["Filial 01: 10 un."],
            "path": "/products/10080001/stock",
        },
        "escreva um e-mail com os dados da tabela",
    )
    metadata: dict = {}

    ChatEmailFollowUpService.attach_to_assistant_metadata(
        metadata,
        message="escreva um e-mail com os dados da tabela",
        answer=draft["text"],
        tool_context={"operationalEmailDraft": draft},
    )

    assert metadata.get("textTask", {}).get("source") == "operational_data"
    assert metadata.get("emailDataSource", {}).get("path") == "/products/10080001/stock"
    assert len(metadata.get("emailFollowUpSuggestions") or []) >= 3
