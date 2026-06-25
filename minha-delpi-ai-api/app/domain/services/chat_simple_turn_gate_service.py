"""Gate de turno simples (Playbook de Inteligência, seções 4 a 8).

Problema corrigido: perguntas simples (identidade, saudação, agradecimento, hora/data,
capacidades, "não entendi") disparavam etapas técnicas visíveis (carregando contexto,
histórico pronto, intenção e rota OpenAPI, planejamento de ferramentas) antes de
qualquer resposta — uma experiência artificial.

Este serviço é a **fonte única** que decide, *antes de qualquer streaming técnico*, se o
turno é simples. Quando é, o chamador (ex.: stream use case) suprime as atividades
técnicas; a resposta direta continua sendo montada pelos serviços já existentes
(small talk, identidade, utilidades, capacidades, fallback honesto).

Importante: este gate **não** altera a resposta — apenas classifica e controla a
visibilidade das etapas. Por isso é seguro: no pior caso, um turno simples mostra
brevemente uma etapa técnica, nunca uma resposta errada.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_unclear_request_service import ChatUnclearRequestService


# Termos que desqualificam o turno como "simples": indicam consulta operacional,
# dados, ferramentas, anexos, lousa ou web (Playbook, seção 8).
_DISQUALIFIERS: tuple[str, ...] = (
    "produto",
    "estoque",
    "saldo",
    "fornecedor",
    "cliente",
    "pedido",
    "venda",
    "compra",
    "preco",
    "estrutura",
    "roteiro",
    "inspecao",
    "componente",
    "sql",
    "select",
    "anexo",
    "pdf",
    "arquivo",
    "desenho",
    "grafico",
    "tabela",
    "lousa",
    "canvas",
    "web",
    "internet",
    "consultar",
    "consulte",
    "listar",
    "liste",
    "buscar",
    "busque",
    "mostrar",
    "mostre",
    "pesquisar",
    "pesquise",
)


@dataclass(frozen=True)
class SimpleTurnDecision:
    matched: bool
    intent: str | None = None
    sub_intent: str | None = None
    requires_tool: bool = False
    requires_rag: bool = False
    requires_llm: bool = False
    hide_activity: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "matched": self.matched,
            "intent": self.intent,
            "subIntent": self.sub_intent,
            "requiresTool": self.requires_tool,
            "requiresRag": self.requires_rag,
            "requiresLlm": self.requires_llm,
            "hideActivity": self.hide_activity,
        }


class ChatSimpleTurnGateService:
    """Resolve turnos simples antes de qualquer atividade técnica/ferramenta/RAG/LLM."""

    @classmethod
    def evaluate(
        cls,
        *,
        message: str,
        workspace_context: dict | None = None,
        previous_messages: list | None = None,
        attachment_ids: list[str] | None = None,
    ) -> SimpleTurnDecision:
        text = str(message or "").strip()

        if not text:
            return SimpleTurnDecision(matched=False)

        # Anexos sempre exigem leitura/ferramenta — nunca é turno simples.
        if attachment_ids:
            return SimpleTurnDecision(matched=False)

        normalized = ChatMessageNormalizationService.normalize_for_matching(text) or ""

        if ChatMessageNormalizationService.contains_any(normalized, _DISQUALIFIERS):
            return SimpleTurnDecision(matched=False)

        # Importações tardias para evitar ciclos de importação no domínio.
        from app.domain.services.chat_assistant_identity_service import (
            ChatAssistantIdentityService,
        )
        from app.domain.services.chat_capabilities_detection_service import (
            ChatCapabilitiesDetectionService,
        )
        from app.domain.services.chat_utility_direct_answer_service import (
            ChatUtilityDirectAnswerService,
        )
        from app.domain.services.chat_small_talk_pattern_service import (
            ChatSmallTalkPatternService,
        )

        identity_category = ChatAssistantIdentityService.classify(text)

        if identity_category:
            return cls._matched("assistant_identity", identity_category)

        small_talk_category = ChatSmallTalkPatternService.match_category(text)

        if small_talk_category:
            return cls._matched("small_talk", small_talk_category)

        utility_category = ChatUtilityDirectAnswerService.classify(text)

        if utility_category:
            return cls._matched("utility", utility_category)

        if ChatCapabilitiesDetectionService.is_capabilities_question(text):
            return cls._matched("capabilities", None)

        unclear_category = ChatUnclearRequestService.classify(
            text,
            previous_messages=previous_messages,
        )

        if unclear_category:
            return cls._matched("unclear_request", unclear_category)

        return SimpleTurnDecision(matched=False)

    @classmethod
    def is_simple_turn(
        cls,
        *,
        message: str,
        workspace_context: dict | None = None,
        previous_messages: list | None = None,
        attachment_ids: list[str] | None = None,
    ) -> bool:
        return cls.evaluate(
            message=message,
            workspace_context=workspace_context,
            previous_messages=previous_messages,
            attachment_ids=attachment_ids,
        ).hide_activity

    @staticmethod
    def _matched(intent: str, sub_intent: str | None) -> SimpleTurnDecision:
        return SimpleTurnDecision(
            matched=True,
            intent=intent,
            sub_intent=sub_intent,
            requires_tool=False,
            requires_rag=False,
            requires_llm=False,
            hide_activity=True,
        )
