import re

# Playbook §7, §26: o que NÃO deve ser aprendido automaticamente.
# Bloqueia segredos, dados pessoais sensíveis e dados operacionais restritos
# antes de qualquer candidato ser persistido.

_SECRET_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"(?i)\b(senha|password|passwd|secret|api[_-]?key|token|bearer)\b"),
    re.compile(r"(?i)\bsk-[a-z0-9]{12,}\b"),
    re.compile(r"(?i)\bghp_[a-z0-9]{20,}\b"),
    re.compile(r"(?i)\beyj[a-z0-9_\-]{10,}\."),  # JWT-like
    re.compile(r"\b[a-f0-9]{32,}\b"),  # long hex / hash
)

_PII_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),  # CPF
    re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"),  # CNPJ
    re.compile(r"(?i)\b[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}\b"),  # e-mail
    re.compile(r"(?<!\d)(?:\+?55\s?)?\(?\d{2}\)?\s?9?\d{4}-?\d{4}(?!\d)"),  # telefone
)

# Termos que sinalizam dado operacional restrito (preço/cliente/pedido).
_OPERATIONAL_SENSITIVE_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"(?i)\b(pre[cç]o|custo|margem|fatur)\w*\b"),
    re.compile(r"(?i)\b(cliente|fornecedor|pedido)\b"),
    re.compile(r"r\$\s?\d", re.IGNORECASE),
)

_LONG_DIGIT_RUN = re.compile(r"\d{5,}")


class ChatLearningSafetyGuard:
    """Bloqueia aprendizado tóxico/sensível (playbook §26 — ChatLearningSafetyGuard)."""

    @classmethod
    def inspect(cls, text: str, *, candidate_type: str | None = None) -> dict:
        """Retorna {allowed, riskLevel, reason} para um texto candidato."""
        content = str(text or "").strip()

        if not content:
            return {"allowed": False, "riskLevel": "high", "reason": "empty"}

        for pattern in _SECRET_PATTERNS:
            if pattern.search(content):
                return {"allowed": False, "riskLevel": "high", "reason": "secret_detected"}

        for pattern in _PII_PATTERNS:
            if pattern.search(content):
                return {"allowed": False, "riskLevel": "high", "reason": "pii_detected"}

        # Candidatos de vocabulário/normalização não devem carregar códigos operacionais.
        if candidate_type in {"vocabulary", "normalization_rule", "typo"}:
            if _LONG_DIGIT_RUN.search(content):
                return {
                    "allowed": False,
                    "riskLevel": "medium",
                    "reason": "operational_code",
                }

        for pattern in _OPERATIONAL_SENSITIVE_PATTERNS:
            if pattern.search(content):
                return {
                    "allowed": False,
                    "riskLevel": "medium",
                    "reason": "operational_sensitive",
                }

        return {"allowed": True, "riskLevel": "low", "reason": None}

    @classmethod
    def is_safe_to_learn(cls, text: str, *, candidate_type: str | None = None) -> bool:
        return cls.inspect(text, candidate_type=candidate_type)["allowed"]
