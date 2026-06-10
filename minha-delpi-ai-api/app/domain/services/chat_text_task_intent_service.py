"""Classifica tarefas administrativas/textuais (sem consulta ERP)."""

from __future__ import annotations

import re

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatTextTaskIntentService:
    _CATEGORY_PATTERNS: dict[str, tuple[str, ...]] = {
        "correct": (
            r"\bcorrij",
            r"\brevise\b",
            r"\bortografia\b",
            r"\barrume\s+o\s+portugu",
            r"\bgramática\b",
            r"\bgramatica\b",
        ),
        "review": (
            r"\bavalie\s+se\b",
            r"\bestá\s+bom\b",
            r"\besta\s+bom\b",
            r"\btexto\s+está\s+bom\b",
            r"\btexto\s+esta\s+bom\b",
            r"\brevisão\s+de\s+qualidade\b",
            r"\brevise\s+o\s+texto\b",
            r"\brevise\s+este\s+texto\b",
        ),
        "to_table": (
            r"\bem\s+tabela\b",
            r"\bcoloque\s+em\s+tabela\b",
            r"\btransforme\s+em\s+tabela\b",
            r"\bformato\s+tabela\b",
            r"\btabela\s+markdown\b",
        ),
        "memorandum": (r"\bmemorando\b",),
        "conversation_transform": (
            r"\btransforme\s+(?:essa|esta)\s+conversa\b",
            r"\btransformar\s+(?:essa|esta)\s+conversa\b",
            r"\bconversa\s+em\s+ata\b",
            r"\bconversa\s+em\s+relat",
            r"\bconversa\s+em\s+comunicado\b",
            r"\bhistórico\s+em\s+ata\b",
        ),
        "rewrite": (
            r"\breescrev",
            r"\bmelhor(e|ar)\b",
            r"\bdeixe\s+mais\s+formal",
            r"\bmais\s+profissional",
            r"\bmais\s+educad",
            r"\bmais\s+diret",
            r"\bmais\s+simples",
        ),
        "translate": (r"\btraduza\b", r"\btraduzir\b", r"\bpasse\s+para\s+ingl", r"\bpasse\s+para\s+espan"),
        "summarize": (r"\bresuma\b", r"\bresumo\b", r"\bpontos\s+principais\b", r"\bsíntese\b", r"\bsintese\b"),
        "structure": (
            r"\bchecklist\b",
            r"\bata\b",
            r"\bem\s+tópicos\b",
            r"\bem\s+topicos\b",
            r"\blista\s+de\s+pend",
        ),
        "email": (
            r"\be-?mail\b",
            r"\bassunto\b",
            r"\bcobrança\b",
            r"\bcobranca\b",
            r"\bcomunicado\s+por\s+e-?mail\b",
            r"\bmensagem\s+formal\b",
            r"\bresponda\s+este\s+e-?mail\b",
            r"\bmelhore\s+este\s+e-?mail\b",
            r"\brevise\s+este\s+e-?mail\b",
            r"\bfaça\s+um\s+e-?mail\b",
            r"\bfaca\s+um\s+e-?mail\b",
        ),
        "message": (r"\bwhatsapp\b", r"\bteams\b", r"\bmensagem\s+curta\b"),
        "write": (r"\bescreva\b", r"\bredija\b", r"\bmonte\b", r"\bcrie\b", r"\bgere\b", r"\belabore\b"),
        "tone_adjust": (
            r"\bdeixe\s+mais\s+formal\b",
            r"\bdeixe\s+menos\s+formal\b",
            r"\bdeixe\s+mais\s+cordial\b",
            r"\bdeixe\s+mais\s+firme\b",
            r"\bdeixe\s+mais\s+direto\b",
            r"\bdeixe\s+mais\s+humano\b",
            r"\bdeixe\s+mais\s+t[eé]cnic",
            r"\bdeixe\s+mais\s+simples\b",
            r"\bdeixe\s+mais\s+executiv",
            r"\bdeixe\s+mais\s+comercial\b",
            r"\bdeixe\s+mais\s+educad",
            r"\bdeixe\s+mais\s+curto\b",
            r"\bdeixe\s+mais\s+detalhad",
            r"\bmenos\s+agressiv",
            r"\bajuste\s+o\s+tom\b",
        ),
        "extract_decisions": (
            r"\bdecis[oõ]es\b",
            r"\bextraia\s+decis",
            r"\blistar\s+decis",
        ),
        "extract_actions": (r"\bpendências\b", r"\bpendencias\b", r"\bpróximos\s+passos\b", r"\bproximos\s+passos\b"),
        "letter": (
            r"\bcarta\b",
            r"\bcarta\s+formal\b",
            r"\bcarta\s+comercial\b",
            r"\bcarta\s+de\s+solicita",
        ),
        "report": (
            r"\brelatório\b",
            r"\brelatorio\b",
            r"\btransforme\s+em\s+relat",
            r"\bgerar\s+relat",
        ),
        "documentation": (
            r"\bdocumentação\b",
            r"\bdocumentacao\b",
            r"\bdocumentação\s+técnica\b",
            r"\bdocumentacao\s+tecnica\b",
            r"\btransforme.*documentação\b",
            r"\btransforme.*documentacao\b",
            r"\bmanual\b",
            r"\binstrução\s+de\s+trabalho\b",
            r"\binstrucao\s+de\s+trabalho\b",
            r"\bfaq\b",
            r"\bglossário\b",
            r"\bglossario\b",
            r"\brelease\s+notes\b",
            r"\bchangelog\b",
        ),
        "explain": (
            r"\bexplique\b",
            r"\bexplicação\b",
            r"\bexplicacao\b",
            r"\bexplicar\s+melhor\b",
            r"\bexplicar\s+esse\b",
        ),
        "eli5": (
            r"\beli5\b",
            r"\bcomo\s+se\s+eu\s+tivesse\s+5\s+anos\b",
            r"\bcomo\s+se\s+eu\s+tivesse\s+cinco\s+anos\b",
            r"\bexplain\s+like\b",
        ),
        "action_plan": (
            r"\bplano\s+de\s+ação\b",
            r"\bplano\s+de\s+acao\b",
            r"\bextraia\s+um\s+plano\b",
        ),
        "adapt_audience": (
            r"\badapte\s+para\b",
            r"\badaptar\s+para\b",
            r"\bversão\s+para\s+diretoria\b",
            r"\bversao\s+para\s+diretoria\b",
            r"\bpara\s+produção\b",
            r"\bpara\s+cliente\b",
            r"\bpara\s+fornecedor\b",
        ),
        "document": (r"\bcomunicado\b", r"\bprocedimento\b", r"\bmemorando\b"),
        "minutes": (r"\bata\b", r"\bata de reuni", r"\banotações em ata\b", r"\bnotas em ata\b"),
        "announcement": (r"\bcomunicado interno\b", r"\bcrise um comunicado\b", r"\bmonte um comunicado\b"),
        "compare": (r"\bcompare\b", r"\bcomparar\b", r"\bqual está melhor\b", r"\bo que mudou\b"),
        "organize": (r"\borganize\b", r"\borganizar\b", r"\bem tópicos\b", r"\bem topicos\b"),
        "simplify": (r"\bexplique de forma simples\b", r"\bsimplifique\b", r"\bdeixe fácil\b"),
    }

    _OPERATIONAL_COMMAND_PATTERNS = (
        r"\bconsulte\b",
        r"\bconsultar\b",
        r"\bliste\s+produtos\b",
        r"\bqual\s+o\s+estoque\b",
        r"\bme\s+fale\s+do\s+produto\b",
        r"\bmostre\s+(o\s+)?faturamento\b",
        r"\bmostre\s+o\s+estoque\b",
        r"\bver\s+estoque\b",
        r"\bestoque\s+do\b",
        r"\bexecute\s+(a\s+)?sql\b",
        r"\bbusque\s+produto\b",
        r"\bverifique\s+o\s+estoque\b",
    )

    _MIXED_CONNECTORS = (
        " e escreva",
        " e redija",
        " e monte",
        " e gere",
        " e depois escreva",
        " e depois redija",
    )

    @classmethod
    def classify(cls, message: str | None) -> str | None:
        normalized = (message or "").strip().lower()

        if len(normalized) < 4:
            return None

        priority = (
            "review",
            "correct",
            "compare",
            "conversation_transform",
            "to_table",
            "eli5",
            "documentation",
            "explain",
            "adapt_audience",
            "memorandum",
            "letter",
            "minutes",
            "announcement",
            "email",
            "translate",
            "summarize",
            "action_plan",
            "report",
            "simplify",
            "structure",
            "organize",
            "rewrite",
            "document",
            "message",
            "write",
            "tone_adjust",
            "extract_decisions",
            "extract_actions",
        )

        for category in priority:
            patterns = cls._CATEGORY_PATTERNS.get(category, ())

            if any(re.search(pattern, normalized) for pattern in patterns):
                return category

        return None

    @classmethod
    def is_pure_text_task(
        cls,
        message: str | None,
        *,
        previous_messages: list | None = None,
    ) -> bool:
        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService

        normalized = (message or "").strip().lower()

        from app.domain.services.chat_presentation_format_refinement_service import (
            ChatPresentationFormatRefinementService,
        )

        if ChatPresentationFormatRefinementService.looks_like_format_refinement(message):
            return False

        category = cls.classify(message)

        if cls._is_session_preference_declaration(message):
            return True

        if not category:
            return False

        if previous_messages:
            from app.domain.services.chat_analysis_intent_service import (
                ChatAnalysisIntentService,
            )

            if ChatAnalysisIntentService.is_email_from_operational_data_request(
                message,
                previous_messages,
            ):
                return False

        if ChatSqlIntentService.is_sql_conversation_turn(message):
            return False

        if cls._is_linguistic_only_turn(normalized, category):
            return True

        if cls.is_mixed_text_and_operational(message):
            return False

        if cls._starts_with_text_lead(normalized):
            return True

        if any(re.search(pattern, normalized) for pattern in cls._OPERATIONAL_COMMAND_PATTERNS):
            return False

        if ChatProductQueryIntentService.extract_product_code(message) and category not in {
            "correct",
            "rewrite",
            "translate",
            "summarize",
            "simplify",
        }:
            return False

        return True

    @classmethod
    def is_mixed_text_and_operational(cls, message: str | None) -> bool:
        normalized = (message or "").strip().lower()

        if not normalized:
            return False

        has_operational = any(
            re.search(pattern, normalized) for pattern in cls._OPERATIONAL_COMMAND_PATTERNS
        )

        if not has_operational:
            return False

        if any(connector in normalized for connector in cls._MIXED_CONNECTORS):
            return True

        if cls.classify(message) and not cls._starts_with_text_lead(normalized):
            return True

        return False

    @classmethod
    def _is_linguistic_only_turn(cls, normalized: str, category: str) -> bool:
        if any(re.search(pattern, normalized) for pattern in cls._OPERATIONAL_COMMAND_PATTERNS):
            return False

        if any(connector in normalized for connector in cls._MIXED_CONNECTORS):
            return False

        if category not in {
            "correct",
            "review",
            "rewrite",
            "translate",
            "summarize",
            "simplify",
            "email",
            "letter",
            "memorandum",
            "minutes",
            "announcement",
            "documentation",
            "explain",
            "eli5",
            "structure",
            "organize",
            "compare",
            "adapt_audience",
            "action_plan",
            "report",
            "to_table",
            "conversation_transform",
            "document",
            "tone_adjust",
            "extract_actions",
            "extract_decisions",
            "message",
            "write",
        }:
            return False

        return bool(
            re.search(
                r"\b(texto|portugu|ortografia|gramática|gramatica|e-?mail|carta|ata|comunicado|traduza|resuma|documentação|documentacao|explique|eli5|formal|autoriza|corrij|reescrev|glossário|glossario|faq|memorando|pendências|pendencias|decis)\b",
                normalized,
            )
        )

    @classmethod
    def _is_session_preference_declaration(cls, message: str | None) -> bool:
        from app.domain.services.chat_text_task_preference_service import (
            ChatTextTaskPreferenceService,
        )

        normalized = (message or "").strip().lower()

        if not normalized:
            return False

        if not ChatTextTaskPreferenceService.detect_from_message(message):
            return False

        return any(
            re.search(pattern, normalized)
            for pattern in ChatTextTaskPreferenceService._PERSISTENT_MARKERS
        )

    @classmethod
    def _starts_with_text_lead(cls, normalized: str) -> bool:
        leads = (
            "corrija",
            "corrigir",
            "traduza",
            "traduzir",
            "resuma",
            "resumir",
            "escreva",
            "escrever",
            "redija",
            "melhore",
            "deixe",
            "revise",
            "explique",
            "adapte",
            "transforme",
        )

        return any(normalized.startswith(lead) for lead in leads)
