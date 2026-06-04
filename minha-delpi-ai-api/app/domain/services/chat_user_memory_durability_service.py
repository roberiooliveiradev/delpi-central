import re
import unicodedata


class ChatUserMemoryDurabilityService:
    """Decide, de forma conservadora, o que de um turno vale como memória durável.

    Princípio do playbook (§43, anti-padrão #2): NÃO salvar tudo que o usuário
    fala. Só captura afirmações explícitas e estáveis (preferências de estilo e
    dados de perfil declarados), de alta precisão, deixando o resto de fora.
    """

    # Preferências de estilo/idioma/formato declaradas de forma durável.
    _PREFERENCE_PATTERNS = (
        re.compile(
            r"\b(?:de agora em diante|a partir de agora|sempre que possivel|"
            r"daqui (?:pra|para) frente)\b.{0,4}(?P<rest>.{4,160})",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:sempre|por favor sempre)\s+(?P<rest>(?:responda|me responda|"
            r"escreva|formate|use|prefira|evite|fale)\b.{2,160})",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:eu )?(?:prefiro|gosto de|gostaria que voce)\s+(?P<rest>.{4,160})",
            re.IGNORECASE,
        ),
    )

    # Dados de perfil declarados pelo usuário (não sensíveis).
    _PROFILE_PATTERNS = (
        re.compile(
            r"\b(?:meu nome (?:e|é)|pode me chamar de|me chame de)\s+(?P<rest>[A-Za-zÀ-ÿ'\- ]{2,60})",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:meu cargo (?:e|é)|minha funcao (?:e|é)|minha função (?:e|é)|"
            r"eu trabalho (?:no|na|como)|sou (?:do|da|de) (?:setor|departamento|area|área))\s+"
            r"(?P<rest>.{2,80})",
            re.IGNORECASE,
        ),
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

        if len(text) < 6 or len(text) > 400:
            return None

        for pattern in cls._PROFILE_PATTERNS:
            match = pattern.search(text)
            if match:
                content = cls._clean_capture(match.group(0))
                if content:
                    return cls._build("profile", content, 0.7)

        for pattern in cls._PREFERENCE_PATTERNS:
            match = pattern.search(text)
            if match:
                content = cls._clean_capture(match.group(0))
                if content:
                    return cls._build("preference", content, 0.65)

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
