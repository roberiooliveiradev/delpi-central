from app.domain.services.chat_learning_safety_guard import ChatLearningSafetyGuard
from app.domain.services.chat_term_extraction_service import ChatTermExtractionService


class ChatWebMeaningResearchService:
    """Decide se/como pesquisar o significado de um termo na web (playbook §12, §35).

    Puro/sem rede: decide elegibilidade (termo público, não sensível) e monta a
    query. A execução HTTP fica na camada de aplicação, que reaproveita o gateway
    de web search existente.
    """

    @staticmethod
    def is_eligible(term: str, *, message: str | None = None) -> bool:
        candidate = (term or "").strip()

        if not candidate:
            return False

        # Termo público/técnico apenas (sigla, técnico, código de produto).
        if not ChatTermExtractionService.is_web_researchable(candidate):
            return False

        # Nunca pesquisar quando o termo ou a mensagem carregam dado sensível
        # (preço/cliente/pedido/PII/segredo) — playbook §12, §35.
        if not ChatLearningSafetyGuard.is_safe_to_learn(candidate):
            return False

        if message and not ChatLearningSafetyGuard.is_safe_to_learn(message):
            return False

        return True

    @staticmethod
    def build_query(term: str) -> str:
        return f"o que significa {term.strip()}"

    @staticmethod
    def build_permission_prompt(term: str) -> str:
        return (
            f'Não encontrei "{term.strip()}" no glossário interno. '
            "Posso pesquisar fontes públicas para tentar entender o significado?"
        )
