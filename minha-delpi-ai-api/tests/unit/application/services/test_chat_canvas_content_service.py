from datetime import datetime, timezone
from uuid import uuid4

from app.application.services.chat_canvas_content_service import ChatCanvasContentService
from app.domain.entities.chat_message import ChatMessage


def _assistant_message(content: str, *, metadata=None) -> ChatMessage:
    now = datetime.now(timezone.utc)
    return ChatMessage(
        id=uuid4(),
        session_id=uuid4(),
        role="assistant",
        content=content,
        metadata=metadata,
        created_at=now,
    )


def test_resolve_returns_markdown_from_last_substantive_assistant():
    assistant = _assistant_message("## Perfil\n\nVocê é o analista João.")
    confirmation = _assistant_message(
        "Coloquei «Perfil» na lousa ao lado. Você pode editar, visualizar e salvar o conteúdo quando quiser."
    )

    action = ChatCanvasContentService.resolve(
        "coloque na lousa",
        [assistant, confirmation],
        {"capabilities": {"canvas": True}},
    )

    assert action is not None
    assert action.open_payload is not None
    assert "Perfil" in action.open_payload.title
    assert "João" in action.open_payload.markdown
    assert "lousa" in action.answer.lower()


def test_resolve_without_assistant_history():
    action = ChatCanvasContentService.resolve(
        "coloque em canva",
        [],
        {"capabilities": {"canvas": True}},
    )

    assert action is not None
    assert action.open_payload is None
    assert "ainda não há" in action.answer.lower()


def test_resolve_when_canvas_disabled():
    action = ChatCanvasContentService.resolve(
        "coloque na lousa",
        [_assistant_message("Conteúdo")],
        {"capabilities": {"canvas": False}},
    )

    assert action is not None
    assert action.open_payload is None
    assert "não está habilitada" in action.answer.lower()


def test_operational_update_returns_none_for_early_resolve():
    action = ChatCanvasContentService.resolve(
        "acrescente na lousa a descrição do produto 10080049",
        [_assistant_message("## Perfil\n\nConteúdo anterior.")],
        {"capabilities": {"canvas": True}},
    )

    assert action is None


def test_build_update_from_tools_merges_existing_canvas_and_tool_markdown():
    profile = _assistant_message(
        "## Seu perfil\n\nRobério Oliveira",
        metadata={
            "canvasOpen": {
                "title": "Seu perfil",
                "markdown": "## Seu perfil\n\nRobério Oliveira",
                "sourceMessageId": "profile-id",
            }
        },
    )
    confirmation = _assistant_message(
        "Coloquei «Seu perfil» na lousa ao lado. Você pode editar, visualizar e salvar o conteúdo quando quiser."
    )
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "textPresentation": {
                    "markdown": "### Produto 10080049\n\n**Descrição:** PARAFUSO M8",
                },
            },
        }
    ]

    action = ChatCanvasContentService.build_update_from_tools(
        "acrescente na lousa a descrição do produto 10080049",
        tool_calls,
        [profile, confirmation],
        {"capabilities": {"canvas": True}},
    )

    assert action is not None
    assert action.open_payload is not None
    assert "Robério Oliveira" in action.open_payload.markdown
    assert "PARAFUSO M8" in action.open_payload.markdown
    assert "Atualizei a lousa" in action.answer


def test_resolve_simple_copy_includes_rich_presentations_from_tool_calls():
    assistant = _assistant_message(
        "### Informações completas do produto 90260015\n\n**Destaques**\n\n- Estrutura com 4 itens.",
        metadata={
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "tablePresentations": [
                            {
                                "type": "table",
                                "title": "Produto 90260015",
                                "columns": [
                                    {"key": "campo", "label": "Campo"},
                                    {"key": "valor", "label": "Valor"},
                                ],
                                "rows": [{"campo": "Código", "valor": "90260015"}],
                            }
                        ],
                        "presentation": {
                            "type": "tree",
                            "title": "Estrutura do produto 90260015",
                            "root": {
                                "id": "90260015",
                                "label": "90260015",
                                "subtitle": "CHICOTE DE LIGACAO",
                                "badge": "PA",
                                "meta": {"quantity": 1, "unit": "MI"},
                                "children": [
                                    {
                                        "id": "50210372",
                                        "label": "50210372",
                                        "subtitle": "CA18AZUL",
                                        "badge": "PI",
                                        "meta": {"quantity": 1, "unit": "MI"},
                                        "children": [
                                            {
                                                "id": "10420040",
                                                "label": "10420040",
                                                "subtitle": "CABO PVC",
                                                "badge": "MP",
                                                "meta": {"quantity": 142, "unit": "MT"},
                                            }
                                        ],
                                    }
                                ],
                            },
                        },
                    },
                }
            ]
        },
    )

    action = ChatCanvasContentService.resolve(
        "coloque o resultado acima na lousa",
        [assistant],
        {"capabilities": {"canvas": True}},
    )

    assert action is not None
    assert action.open_payload is not None
    assert "Produto 90260015" in action.open_payload.markdown
    assert "Estrutura do produto 90260015" in action.open_payload.markdown
    assert "#### 90260015" in action.open_payload.markdown
    assert "#### 50210372" in action.open_payload.markdown
    assert "10420040" in action.open_payload.markdown
    assert "Caminho" not in action.open_payload.markdown


def test_content_append_skips_canvas_confirmation_and_merges_existing_canvas():
    profile = _assistant_message(
        "## Seu perfil\n\nRobério Oliveira",
        metadata={
            "canvasOpen": {
                "title": "Seu perfil",
                "markdown": "## Seu perfil\n\nRobério Oliveira",
            }
        },
    )
    confirmation = _assistant_message(
        "Coloquei «Seu perfil» na lousa ao lado. Você pode editar, visualizar e salvar o conteúdo quando quiser."
    )
    follow_up = _assistant_message("## Estoque\n\nSaldo total: 120 unidades.")

    action = ChatCanvasContentService.resolve(
        "acrescente isso na lousa",
        [profile, confirmation, follow_up],
        {"capabilities": {"canvas": True}},
    )

    assert action is not None
    assert action.open_payload is not None
    assert "Robério Oliveira" in action.open_payload.markdown
    assert "Saldo total: 120 unidades." in action.open_payload.markdown
