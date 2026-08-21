import re
import unicodedata

from app.domain.services.chat_memory_intent_content_service import (
    ChatMemoryIntentContentService,
)


class ChatUserMemoryDurabilityService:
    """Decide, de forma conservadora, o que de um turno vale como memória durável.

    Princípio do playbook (§43, anti-padrão #2): NÃO salvar tudo que o usuário
    fala. Só captura afirmações explícitas e estáveis (preferências de estilo e
    dados de perfil declarados), de alta precisão, deixando o resto de fora.
    """

    @classmethod
    def _preference_patterns(cls) -> tuple[re.Pattern[str], ...]:
        return ChatMemoryIntentContentService.compile_pattern_list(
            "durability",
            "preferencePatterns",
        )

    @classmethod
    def _profile_patterns(cls) -> tuple[re.Pattern[str], ...]:
        return ChatMemoryIntentContentService.compile_pattern_list(
            "durability",
            "profilePatterns",
        )

    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""
        stripped = unicodedata.normalize("NFKD", text)
        stripped = "".join(ch for ch in stripped if not unicodedata.combining(ch))
        return re.sub(r"\s+", " ", stripped).strip().lower()

    @classmethod
    def detect(cls, message: str) -> dict | None:
        text = (message or "").strip()
        min_chars = ChatMemoryIntentContentService.limit_int(
            "durability",
            "limits",
            "minMessageChars",
            default=6,
        )
        max_chars = ChatMemoryIntentContentService.limit_int(
            "durability",
            "limits",
            "maxMessageChars",
            default=400,
        )

        if len(text) < min_chars or len(text) > max_chars:
            return None

        profile_confidence = ChatMemoryIntentContentService.limit_float(
            "durability",
            "limits",
            "profileConfidence",
            default=0.7,
        )
        preference_confidence = ChatMemoryIntentContentService.limit_float(
            "durability",
            "limits",
            "preferenceConfidence",
            default=0.65,
        )

        for pattern in cls._profile_patterns():
            match = pattern.search(text)
            if match:
                content = cls._clean_capture(match.group(0))
                if content:
                    return cls._build("profile", content, profile_confidence)

        for pattern in cls._preference_patterns():
            match = pattern.search(text)
            if match:
                content = cls._clean_capture(match.group(0))
                if content:
                    return cls._build("preference", content, preference_confidence)

        return None

    @staticmethod
    def _clean_capture(raw: str) -> str:
        cleaned = re.sub(r"\s+", " ", (raw or "").strip())
        cleaned = cleaned.rstrip(".!?;,")
        # Capitaliza a primeira letra preservando o resto.
        return cleaned[:1].upper() + cleaned[1:] if cleaned else ""

    @classmethod
    def _build(cls, type_: str, content: str, confidence: float) -> dict:
        return {
            "type": type_,
            "content": content,
            "contentNorm": cls.normalize(content),
            "scope": "user",
            "confidence": confidence,
            "source": "turn",
        }
