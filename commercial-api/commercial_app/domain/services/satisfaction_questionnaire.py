"""Immutable canonical questionnaire for the customer satisfaction survey."""

from __future__ import annotations

from typing import Any

QUESTIONNAIRE_VERSION = (
    "delpi.commercial.satisfaction-survey.canonical-15@2026-11-11"
)

DIMENSION_KEYS: tuple[str, ...] = (
    "quality",
    "delivery_deadline",
    "service",
    "agility",
    "communication",
    "technical_support",
    "commercial_support",
    "flexibility",
    "reliability",
    "partnership",
)

SCALE_1_5_LABELS: dict[int, str] = {
    1: "Muito insatisfeito",
    2: "Insatisfeito",
    3: "Neutro",
    4: "Satisfeito",
    5: "Muito satisfeito",
}

# Literal texts from the official Word plan (Q09 fidelity gate).
_DIMENSION_ITEMS: tuple[dict[str, Any], ...] = (
    {
        "order": 1,
        "key": "quality",
        "title": "Qualidade",
        "prompt": (
            "Como você avalia a qualidade dos produtos fornecidos pela Delpi?"
        ),
        "kind": "dimension",
        "allows_not_applicable": True,
        "required": True,
        "scale_min": 1,
        "scale_max": 5,
    },
    {
        "order": 2,
        "key": "delivery_deadline",
        "title": "Prazo de entrega",
        "prompt": "Como você avalia o cumprimento dos prazos acordados?",
        "kind": "dimension",
        "allows_not_applicable": True,
        "required": True,
        "scale_min": 1,
        "scale_max": 5,
    },
    {
        "order": 3,
        "key": "service",
        "title": "Atendimento",
        "prompt": "Como você avalia o atendimento da equipe Delpi?",
        "kind": "dimension",
        "allows_not_applicable": True,
        "required": True,
        "scale_min": 1,
        "scale_max": 5,
    },
    {
        "order": 4,
        "key": "agility",
        "title": "Agilidade",
        "prompt": (
            "Como você avalia a velocidade de resposta às suas solicitações?"
        ),
        "kind": "dimension",
        "allows_not_applicable": True,
        "required": True,
        "scale_min": 1,
        "scale_max": 5,
    },
    {
        "order": 5,
        "key": "communication",
        "title": "Comunicação",
        "prompt": (
            "Como você avalia a clareza e efetividade da comunicação?"
        ),
        "kind": "dimension",
        "allows_not_applicable": True,
        "required": True,
        "scale_min": 1,
        "scale_max": 5,
    },
    {
        "order": 6,
        "key": "technical_support",
        "title": "Suporte técnico",
        "prompt": (
            "Como você avalia o suporte técnico oferecido pela Delpi?"
        ),
        "kind": "dimension",
        "allows_not_applicable": True,
        "required": True,
        "scale_min": 1,
        "scale_max": 5,
    },
    {
        "order": 7,
        "key": "commercial_support",
        "title": "Suporte comercial",
        "prompt": (
            "Como você avalia o suporte comercial oferecido pela Delpi?"
        ),
        "kind": "dimension",
        "allows_not_applicable": True,
        "required": True,
        "scale_min": 1,
        "scale_max": 5,
    },
    {
        "order": 8,
        "key": "flexibility",
        "title": "Flexibilidade",
        "prompt": (
            "Como você avalia a capacidade da Delpi de atender "
            "necessidades específicas?"
        ),
        "kind": "dimension",
        "allows_not_applicable": True,
        "required": True,
        "scale_min": 1,
        "scale_max": 5,
    },
    {
        "order": 9,
        "key": "reliability",
        "title": "Confiabilidade",
        "prompt": (
            "Quanto você considera a Delpi confiável como fornecedora?"
        ),
        "kind": "dimension",
        "allows_not_applicable": True,
        "required": True,
        "scale_min": 1,
        "scale_max": 5,
    },
    {
        "order": 10,
        "key": "partnership",
        "title": "Parceria",
        "prompt": (
            "Como você avalia a Delpi como parceira de longo prazo?"
        ),
        "kind": "dimension",
        "allows_not_applicable": True,
        "required": True,
        "scale_min": 1,
        "scale_max": 5,
    },
)

_GENERAL_ITEMS: tuple[dict[str, Any], ...] = (
    {
        "order": 11,
        "key": "overall_score",
        "title": "Satisfação geral",
        "prompt": (
            "De forma geral, qual é o seu nível de satisfação com a Delpi "
            "como fornecedor?"
        ),
        "kind": "overall",
        "allows_not_applicable": False,
        "required": True,
        "scale_min": 1,
        "scale_max": 5,
    },
    {
        "order": 12,
        "key": "recommendation_score",
        "title": "Recomendação",
        "prompt": (
            "Em uma escala de 0 a 10, o quanto você recomendaria a Delpi "
            "para outra empresa que busca um fornecedor de chicotes "
            "elétricos e componentes?"
        ),
        "kind": "recommendation",
        "allows_not_applicable": False,
        "required": True,
        "scale_min": 0,
        "scale_max": 10,
    },
)

_OPEN_ITEMS: tuple[dict[str, Any], ...] = (
    {
        "order": 13,
        "key": "strengths",
        "title": "Pontos fortes",
        "prompt": (
            "O que a Delpi faz bem e você considera importante manter?"
        ),
        "kind": "open",
        "allows_not_applicable": False,
        "required": False,
    },
    {
        "order": 14,
        "key": "improvements",
        "title": "Oportunidades de melhoria",
        "prompt": (
            "O que a Delpi poderia melhorar para atender melhor sua empresa?"
        ),
        "kind": "open",
        "allows_not_applicable": False,
        "required": False,
    },
    {
        "order": 15,
        "key": "unmet_needs",
        "title": "Necessidades não atendidas",
        "prompt": (
            "Existe alguma necessidade ou expectativa que a Delpi ainda "
            "não esteja atendendo?"
        ),
        "kind": "open",
        "allows_not_applicable": False,
        "required": False,
    },
)

DEFAULT_INVITE_SUBJECT = "Pesquisa de satisfação Delpi — {nome_empresa}"
DEFAULT_INVITE_BODY = (
    "Olá,\n\n"
    "Convidamos a empresa {nome_empresa} a participar da nossa pesquisa "
    "de satisfação.\n\n"
    "Acesse o formulário exclusivo pelo link:\n"
    "{link_pesquisa}\n\n"
    "Agradecemos a colaboração.\n"
    "Equipe Delpi"
)

INVITE_PLACEHOLDERS: tuple[str, ...] = ("{nome_empresa}", "{link_pesquisa}")


def get_questionnaire_catalog() -> dict[str, Any]:
    items = list(_DIMENSION_ITEMS) + list(_GENERAL_ITEMS) + list(_OPEN_ITEMS)
    return {
        "questionnaire_version": QUESTIONNAIRE_VERSION,
        "scale_1_5_labels": SCALE_1_5_LABELS,
        "dimension_keys": list(DIMENSION_KEYS),
        "items": items,
        "invite_placeholders": list(INVITE_PLACEHOLDERS),
    }


def validate_dimensions_payload(dimensions: Any) -> dict[str, int | None]:
    if not isinstance(dimensions, dict):
        raise ValueError("dimensions deve ser um objeto com as 10 chaves canônicas.")
    missing = [key for key in DIMENSION_KEYS if key not in dimensions]
    if missing:
        raise ValueError(
            "dimensions incompleto; faltam chaves: " + ", ".join(missing)
        )
    extra = [key for key in dimensions.keys() if key not in DIMENSION_KEYS]
    if extra:
        raise ValueError(
            "dimensions contém chaves inválidas: " + ", ".join(sorted(extra))
        )
    normalized: dict[str, int | None] = {}
    for key in DIMENSION_KEYS:
        value = dimensions[key]
        if value is None:
            normalized[key] = None
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(
                f"Dimensão {key}: informe nota 1–5 ou null (Não se aplica)."
            )
        if value < 1 or value > 5:
            raise ValueError(
                f"Dimensão {key}: nota deve estar entre 1 e 5."
            )
        normalized[key] = value
    return normalized
