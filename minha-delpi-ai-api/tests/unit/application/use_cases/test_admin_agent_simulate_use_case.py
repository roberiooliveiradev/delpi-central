from unittest.mock import Mock

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.application.services.admin_guideline_prompt_service import AdminGuidelinePromptService
from app.application.use_cases.admin_agent_simulate_use_case import AdminAgentSimulateUseCase
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.services.chat_response_mode_service import ChatResponseModeService

configure_domain_infrastructure_ports()


def _make_use_case(**kwargs) -> AdminAgentSimulateUseCase:
    return AdminAgentSimulateUseCase(
        rag_context_service=kwargs.get("rag_context_service", FakeRagContextService()),
        guideline_prompt_service=kwargs.get(
            "guideline_prompt_service",
            AdminGuidelinePromptService(FakeGuidelineRepository()),
        ),
        chat_agent_repository=kwargs.get("chat_agent_repository", Mock(spec=ChatAgentRepositoryPort)),
        chat_session_repository=kwargs.get(
            "chat_session_repository",
            Mock(spec=ChatSessionRepositoryPort),
        ),
        chat_tool_context_service=kwargs.get("chat_tool_context_service"),
    )


class FakeGuidelineRepository:
    def list_active(self, environment=None, categories=None):
        return [
            {
                "id": "g1",
                "title": "Tom formal",
                "category": "behavior",
                "status": "active",
                "description": "Respostas formais",
                "content": "Use linguagem formal.",
            }
        ]


class FakeRagContextService:
    def build_context(self, query, filters=None):
        return {
            "context": f"[Fonte 1]\nTítulo: Manual\nTrecho: conteúdo sobre {query}",
            "sources": [
                {
                    "id": "doc-1",
                    "documentId": "doc-1",
                    "title": "Manual",
                    "sourceType": "markdown",
                    "score": 0.82,
                }
            ],
        }


class FakeChatToolContextService:
    def build_context(self, user_id, access_token, message, actions_enabled=True, **kwargs):
        return {
            "context": "Ferramenta get_current_user: Nome: Usuário Real; E-mail: real@delpi.com.br",
            "toolCalls": [
                {
                    "name": "get_current_user",
                    "arguments": {},
                    "reason": "A pergunta solicita dados do usuário autenticado.",
                    "metadata": {"source": "core-api:/me", "ok": True},
                }
            ],
        }


class FakeFactoryStatusToolContextService:
    def build_context(self, user_id, access_token, message, actions_enabled=True, **kwargs):
        return {
            "context": "Status fabril consolidado.",
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "arguments": {},
                    "reason": "Consulta status fabril.",
                    "metadata": {
                        "ok": True,
                        "path": "/products/90269002/factory-status",
                        "presentationDecision": {
                            "selected": "text",
                            "layoutMode": "stack",
                            "presentationMode": "summary_then_evidence",
                        },
                        "stackPresentationPlan": {
                            "presentationProfile": "product_factory_status",
                            "humanizedSections": True,
                        },
                        "textPresentation": {
                            "type": "markdown",
                            "markdown": "### Status fabril\n\nSituação consolidada.",
                        },
                        "humanizedSummary": {
                            "titulo": "Status fabril",
                            "linhas": ["- OP em andamento."],
                        },
                    },
                }
            ],
        }


def test_admin_agent_simulate_builds_prompt_and_comparison():
    use_case = _make_use_case()

    result = use_case.execute(question="Como funciona o chat?")

    assert result["question"] == "Como funciona o chat?"
    assert len(result["appliedGuidelines"]) == 1
    assert len(result["chunks"]) == 1
    assert result["finalPrompt"]["systemPrompt"]
    assert result["comparison"]["withRag"]["enabled"] is True
    assert result["comparison"]["withGuidelines"]["enabled"] is True
    assert "Prévia estrutural" in result["answerPreview"]


def test_admin_agent_simulate_executes_tools_with_access_token():
    use_case = _make_use_case(chat_tool_context_service=FakeChatToolContextService())

    result = use_case.execute(
        question="Quem sou eu?",
        user_id="00000000-0000-0000-0000-000000000001",
        access_token="token-test",
        execute_tools_in_sandbox=True,
    )

    assert result["plannedToolCalls"][0]["name"] == "get_current_user"
    assert result["plannedToolCalls"][0]["status"] == "executed"
    assert "get_current_user" in result["finalPrompt"]["systemPrompt"]
    assert result["debugContext"]["toolsExecuted"] is True


def test_admin_agent_simulate_applies_prose_delivery_on_sandbox_tools(monkeypatch):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)
    use_case = _make_use_case(
        chat_tool_context_service=FakeFactoryStatusToolContextService(),
    )

    result = use_case.execute(
        question="qual o status do produto 90269002 na fabrica hoje?",
        user_id="00000000-0000-0000-0000-000000000001",
        access_token="token-test",
        execute_tools_in_sandbox=True,
    )

    metadata = result["plannedToolCalls"][0]["metadata"]
    assert metadata.get("llmProseDecoupled") is True
    assert str((metadata.get("textPresentation") or {}).get("markdown") or "").strip() == ""


def test_admin_agent_simulate_rejects_empty_question():
    use_case = _make_use_case()

    try:
        use_case.execute(question="   ")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "question" in str(exc)
