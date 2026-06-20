"""Testes do modo de resposta do chat (rápida / normal / pensador)."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_response_mode_service import ChatResponseModeService

configure_domain_infrastructure_ports()


def test_normalize_aliases():
    assert ChatResponseModeService.normalize("rapida") == "fast"
    assert ChatResponseModeService.normalize("pensador") == "thinker"
    assert ChatResponseModeService.normalize(None) == "normal"
    assert ChatResponseModeService.normalize("unknown") == "normal"


def test_fast_mode_uses_smaller_limits(monkeypatch):
    monkeypatch.setenv("CHAT_RESPONSE_MODE_FAST_MODEL", "qwen2.5:1.5b")
    monkeypatch.setenv("CHAT_RESPONSE_MODE_FAST_MAX_TOKENS", "256")
    config = ChatResponseModeService.resolve("fast")
    assert config.response_mode == "fast"
    assert config.model == "qwen2.5:1.5b"
    assert config.max_tokens == 256


def test_thinker_mode_expands_context(monkeypatch):
    monkeypatch.setenv("CHAT_RESPONSE_MODE_THINKER_NUM_CTX", "4096")
    config = ChatResponseModeService.resolve("thinker")
    assert config.response_mode == "thinker"
    assert config.num_ctx == 4096


def test_list_modes_when_enabled(monkeypatch):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)
    modes = ChatResponseModeService.list_modes()
    assert len(modes) == 3
    assert {item["id"] for item in modes} == {"fast", "normal", "thinker"}


def test_apply_turn_direct_answer_policy_overview_fast_forces_brief_llm():
    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="me fale do produto 10080045",
        response_mode="fast",
        direct_answer="### Produto\n\nRelatório.",
        skip_rag=True,
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"ok": True},
            }
        ],
    )

    assert direct is None
    assert skip_rag is False
    assert effect == "llm_synthesis_brief"


def test_apply_turn_direct_answer_policy_overview_thinker_forces_llm():
    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="me fale do produto 10080045",
        response_mode="thinker",
        direct_answer="### Produto\n\nRelatório.",
        skip_rag=True,
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"ok": True},
            }
        ],
    )

    assert direct is None
    assert skip_rag is False
    assert effect == "llm_synthesis"


def test_normal_mode_uses_bounded_limits(monkeypatch):
    monkeypatch.setenv("CHAT_RESPONSE_MODE_NORMAL_MAX_TOKENS", "512")
    monkeypatch.setenv("CHAT_RESPONSE_MODE_NORMAL_NUM_CTX", "1536")
    config = ChatResponseModeService.resolve("normal")
    assert config.response_mode == "normal"
    assert config.max_tokens == 512
    assert config.num_ctx == 1536


def test_apply_turn_direct_answer_policy_overview_normal_forces_llm():
    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="me fale do produto 10080045",
        response_mode="normal",
        direct_answer="### Produto\n\nRelatório.",
        skip_rag=True,
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"ok": True},
            }
        ],
    )

    assert direct is None
    assert skip_rag is False
    assert effect == "llm_synthesis"


def test_apply_turn_direct_answer_policy_stock_narrative_forces_llm():
    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="como está o estoque do produto 10080045?",
        response_mode="normal",
        direct_answer="### Estoque\n\nResumo.",
        skip_rag=True,
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/products/10080045/stock",
                    "presentationDecision": {
                        "selected": "text",
                        "layoutMode": "stack",
                    },
                    "stackPresentationPlan": {
                        "presentationProfile": "product_stock",
                    },
                    "textPresentation": {
                        "type": "markdown",
                        "markdown": "### Estoque\n\nResumo.",
                    },
                },
            }
        ],
    )

    assert direct is None
    assert skip_rag is False
    assert effect == "llm_synthesis"


def test_apply_turn_direct_answer_policy_stock_factual_uses_llm_when_everywhere(monkeypatch):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)

    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="estoque do produto 10080045 filial 01 quantidade",
        response_mode="normal",
        direct_answer="| Filial | Qtd |",
        skip_rag=True,
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/products/10080045/stock",
                    "presentationDecision": {
                        "selected": "text",
                        "layoutMode": "stack",
                    },
                    "stackPresentationPlan": {
                        "presentationProfile": "product_stock",
                    },
                },
            }
        ],
    )

    assert direct is None
    assert skip_rag is False
    assert effect == "llm_synthesis"


def test_apply_turn_direct_answer_policy_stock_stays_operational_direct_when_everywhere_off(
    monkeypatch,
):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)

    from app.domain.services.chat_presentation_prose_delivery_content_service import (
        ChatPresentationProseDeliveryContentService,
    )

    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "llm_prose_everywhere",
        lambda: False,
    )

    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="estoque do produto 10080045",
        response_mode="thinker",
        direct_answer="| Filial | Qtd |",
        skip_rag=True,
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"ok": True},
            }
        ],
    )

    assert direct == "| Filial | Qtd |"
    assert skip_rag is True
    assert effect == "operational_direct"


def test_apply_turn_direct_answer_policy_playbook_uses_llm_when_everywhere(monkeypatch):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)

    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="quais os top itens de consumo na produção?",
        response_mode="normal",
        direct_answer="### Top itens\n\nLista.",
        skip_rag=True,
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/production/consumption/top-items",
                    "apiDelpiResponseMeta": {
                        "entity": "production_consumption_top_items",
                    },
                    "presentationDecision": {
                        "selected": "table",
                        "layoutMode": "single",
                    },
                    "textPresentation": {
                        "type": "markdown",
                        "markdown": "### Top itens\n\nLista.",
                    },
                },
            }
        ],
    )

    assert direct is None
    assert skip_rag is False
    assert effect == "llm_synthesis"


def test_apply_turn_direct_answer_policy_playbook_template_stays_direct_when_everywhere_off(
    monkeypatch,
):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)

    from app.domain.services.chat_presentation_prose_delivery_content_service import (
        ChatPresentationProseDeliveryContentService,
    )

    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "llm_prose_everywhere",
        lambda: False,
    )

    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="quais os top itens de consumo na produção?",
        response_mode="normal",
        direct_answer="### Top itens\n\nLista.",
        skip_rag=True,
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/production/consumption/top-items",
                    "apiDelpiResponseMeta": {
                        "entity": "production_consumption_top_items",
                    },
                    "presentationDecision": {
                        "selected": "table",
                        "layoutMode": "single",
                    },
                    "textPresentation": {
                        "type": "markdown",
                        "markdown": "### Top itens\n\nLista.",
                    },
                },
            }
        ],
    )

    assert direct == "### Top itens\n\nLista."
    assert skip_rag is True
    assert effect == "operational_direct"


def test_apply_turn_direct_answer_policy_never_operational_direct_when_everywhere(
    monkeypatch,
):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)

    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="estoque do produto 10080045",
        response_mode="normal",
        direct_answer="| Filial | Qtd |",
        skip_rag=True,
        tool_calls=None,
    )

    assert direct is None
    assert skip_rag is False
    assert effect == "llm_synthesis"


def test_list_modes_loads_json_labels(monkeypatch):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)
    modes = ChatResponseModeService.list_modes()

    assert modes[1]["label"] == "Normal"
    assert "narrativa" in modes[1]["description"].lower()
