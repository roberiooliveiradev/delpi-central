from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class ChatCanvasIntentService:
    """Detecta pedido de enviar conteúdo do chat para a lousa (canvas) do produto."""

    _PLACEMENT_TERMS = (
        "coloque",
        "colocar",
        "coloca",
        "ponha",
        "põe",
        "manda",
        "mandar",
        "envia",
        "enviar",
        "passa",
        "passar",
        "abre",
        "abrir",
        "joga",
        "jogar",
        "leva",
        "levar",
        "transfere",
        "transferir",
        "colocar na",
        "coloque na",
        "coloque no",
        "colocar no",
        "manda para",
        "manda pra",
        "envia para",
        "envia pra",
    )

    _TARGET_TERMS = (
        "lousa",
        "canvas",
        "canva",
    )

    _OPEN_LOUSA_PHRASES = (
        "abrir lousa",
        "abrir a lousa",
        "abrir canvas",
        "abrir o canvas",
        "abrir a canvas",
        "na lousa",
        "para lousa",
        "pra lousa",
        "na canvas",
        "para canvas",
        "pra canvas",
        "em lousa",
        "em canvas",
        "em canva",
    )

    _EXTERNAL_CANVA_BLOCK = (
        "canva.com",
        "www.canva",
        "site da canva",
        "ferramenta canva",
        "design grafico",
        "design gráfico",
        "criar no canva",
        "conta canva",
    )

    @classmethod
    def is_canvas_placement_request(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if any(term in normalized for term in cls._EXTERNAL_CANVA_BLOCK):
            return False

        if any(phrase in normalized for phrase in cls._OPEN_LOUSA_PHRASES):
            return True

        has_target = any(term in normalized for term in cls._TARGET_TERMS)
        has_placement = any(term in normalized for term in cls._PLACEMENT_TERMS)

        return bool(has_target and has_placement)
