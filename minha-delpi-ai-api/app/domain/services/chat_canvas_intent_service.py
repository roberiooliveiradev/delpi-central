from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatCanvasIntentService:
    """Detecta pedido de enviar ou atualizar conteúdo na lousa (canvas) do produto."""

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

    _UPDATE_TERMS = (
        "acrescente",
        "acrescentar",
        "adicione",
        "adicionar",
        "adiciona",
        "inclua",
        "incluir",
        "inclui",
        "atualize",
        "atualizar",
        "atualiza",
        "anexe",
        "anexar",
        "anexa",
        "complemente",
        "complementar",
        "agregue",
        "agregar",
        "some",
        "somar",
        "insira",
        "inserir",
        "insere",
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

    _OPERATIONAL_DATA_TERMS = (
        "descricao",
        "descrição",
        "estoque",
        "saldo",
        "estrutura",
        "ficha",
        "resumo",
        "vendas",
        "venda",
        "compras",
        "compra",
        "analise",
        "análise",
        "analyser",
        "onde e usado",
        "onde é usado",
        "produto",
        "item",
        "codigo",
        "código",
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

    _TRANSFORM_VERBS = (
        "transforme",
        "transformar",
        "converter",
        "converta",
        "virar",
        "vire",
        "reformate",
        "reformatar",
    )

    _LOUSA_CONTENT_TERMS = (
        "lousa",
        "canvas",
        "canva",
        "conteudo da lousa",
        "conteúdo da lousa",
        "texto da lousa",
    )

    @classmethod
    def is_canvas_request(cls, message: str) -> bool:
        return cls.is_canvas_placement_request(message) or cls.is_canvas_update_request(
            message
        )

    @classmethod
    def is_canvas_placement_request(cls, message: str) -> bool:
        normalized = cls._normalize(message)

        if not normalized:
            return False

        if any(term in normalized for term in cls._EXTERNAL_CANVA_BLOCK):
            return False

        if cls.is_canvas_update_request(message):
            return False

        if any(phrase in normalized for phrase in cls._OPEN_LOUSA_PHRASES):
            return True

        has_target = any(term in normalized for term in cls._TARGET_TERMS)
        has_placement = any(term in normalized for term in cls._PLACEMENT_TERMS)

        return bool(has_target and has_placement)

    @classmethod
    def is_canvas_update_request(cls, message: str) -> bool:
        normalized = cls._normalize(message)

        if not normalized:
            return False

        if any(term in normalized for term in cls._EXTERNAL_CANVA_BLOCK):
            return False

        has_target = any(
            term in normalized
            for term in (*cls._TARGET_TERMS, *cls._OPEN_LOUSA_PHRASES)
        )
        has_update = any(term in normalized for term in cls._UPDATE_TERMS)

        return bool(has_target and has_update)

    @classmethod
    def is_canvas_operational_update_request(cls, message: str) -> bool:
        if not cls.is_canvas_update_request(message):
            return False

        normalized = cls._normalize(message)

        if ChatProductQueryIntentService.extract_product_code(message):
            return True

        return any(term in normalized for term in cls._OPERATIONAL_DATA_TERMS)

    @classmethod
    def is_canvas_transform_request(cls, message: str) -> bool:
        from app.domain.services.chat_canvas_transform_service import (
            ChatCanvasTransformService,
        )

        normalized = cls._normalize(message)

        if not normalized:
            return False

        if any(term in normalized for term in cls._EXTERNAL_CANVA_BLOCK):
            return False

        if not ChatCanvasTransformService.detect_kind(message):
            return False

        has_transform = any(term in normalized for term in cls._TRANSFORM_VERBS)
        has_canvas_ref = any(term in normalized for term in cls._LOUSA_CONTENT_TERMS)

        return bool(has_transform and has_canvas_ref)

    @classmethod
    def blocks_external_action_selection(cls, message: str) -> bool:
        if cls.is_canvas_transform_request(message):
            return True

        return cls.is_canvas_request(message) and not cls.is_canvas_operational_update_request(
            message
        )

    @classmethod
    def _normalize(cls, message: str) -> str:
        return ChatMessageNormalizationService.normalize_for_matching(message)
