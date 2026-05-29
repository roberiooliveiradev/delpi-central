"""Perguntas sobre descrição técnica de matérias-primas (Normas_Tecnicas_DELPI.md)."""

from __future__ import annotations

import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)

_GUIDANCE_VERBS = (
    "como descrever",
    "como descrevo",
    "como escrever",
    "como escrevo",
    "como montar",
    "como elaborar",
    "como cadastrar",
    "como registrar",
    "como preencher",
    "como formatar",
    "como padronizar",
    "como funciona a descricao",
    "como funciona a descrição",
    "como funciona o cadastro da descricao",
    "como funciona o cadastro da descrição",
    "como pesquisar por descricao",
    "como pesquisar por descrição",
    "como buscar por descricao",
    "como buscar por descrição",
)

_NORMAS_MARKERS = (
    "normas tecnicas",
    "norma tecnica",
    "normas delpi",
    "normas_tecnicas",
    "normas-tecnicas",
    "normas técnicas",
    "norma técnica",
)

_DESCRIPTION_GUIDANCE_MARKERS = (
    "descricao tecnica",
    "descrição técnica",
    "descricao padrao",
    "descrição padrão",
    "modelo de descricao",
    "modelo de descrição",
    "estrutura da descricao",
    "estrutura da descrição",
    "campos da descricao",
    "campos da descrição",
    "sequencia da descricao",
    "sequência da descrição",
    "materia prima",
    "matéria-prima",
    "materia-prima",
    "materias primas",
    "matérias-primas",
    "cadastro de descricao",
    "cadastro de descrição",
    "padrao de descricao",
    "padrão de descrição",
    "exemplo de descricao",
    "exemplo de descrição",
)

_FIELD_MEANING_MARKERS = (
    "o que significa",
    "significado do campo",
    "significado da coluna",
    "para que serve o campo",
    "para que serve a coluna",
    "o que e o campo",
    "o que é o campo",
)

_DESCRIPTION_FIELDS = (
    "material",
    "bitola",
    "secao",
    "seção",
    "cor",
    "isolacao",
    "isolação",
    "temperatura",
    "norma",
    "rohs",
    "bitola awg",
    "awg",
    "mm2",
    "mm²",
)

_MATERIAL_GROUPS: tuple[tuple[str, ...], str, str] = (
    (("terminal", "terminais", "pino", "forquilha", "ilhos", "ilhós", "lingueta", "faston", "olhal", "anzol", "luva", "emenda"), "1008", "terminais"),
    (("cabo", "cabos", "fio", "fios", "pp com plug"), "1001-1005", "cabos"),
    (("isolador", "isoladores"), "1009", "isoladores"),
    (("inserto", "insertos"), "1009", "inserto"),
    (("conector", "conectores"), "1009", "conectores"),
    (("etiqueta", "etiquetas"), "1011", "etiquetas"),
    (("tubo isolante", "tubo corrugado", "tubo flexivel", "tubo flexível"), "1012", "tubo isolante"),
    (("termoencolhivel", "termoencolhível", "termo retratil", "termo-retratil"), "1013", "termoencolhível"),
    (("prensa cabo", "prensa-cabo", "prensa cabos"), "1015", "prensa cabos"),
    (("resistor", "resistores"), "1016", "resistores"),
    (("termistor", "termistores"), "1025", "termistores"),
)

_PRODUCT_LOOKUP_MARKERS = (
    "descricao do produto",
    "descrição do produto",
    "qual a descricao",
    "qual a descrição",
    "qual e a descricao",
    "qual é a descrição",
    "descricao do item",
    "descrição do item",
    "descricao do codigo",
    "descrição do código",
    "me fale sobre o produto",
    "informacoes do produto",
    "informações do produto",
    "dados cadastrais do produto",
)


class ChatTechnicalDescriptionIntentService:
    @classmethod
    def requires_normas_knowledge(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if ChatProductQueryIntentService.extract_product_code(message or ""):
            return False

        if any(marker in normalized for marker in _PRODUCT_LOOKUP_MARKERS):
            return False

        if any(marker in normalized for marker in _NORMAS_MARKERS):
            return True

        if any(marker in normalized for marker in _GUIDANCE_VERBS):
            if any(marker in normalized for marker in _DESCRIPTION_GUIDANCE_MARKERS):
                return True
            if cls.resolve_material_group(normalized):
                return True
            if "descricao" in normalized:
                return True

        if any(marker in normalized for marker in _DESCRIPTION_GUIDANCE_MARKERS):
            if cls.resolve_material_group(normalized):
                return True
            if "grupo " in normalized and re.search(r"\b10\d{2}\b", normalized):
                return True

        if any(marker in normalized for marker in _FIELD_MEANING_MARKERS):
            if any(field in normalized for field in _DESCRIPTION_FIELDS):
                return True
            if any(marker in normalized for marker in _DESCRIPTION_GUIDANCE_MARKERS):
                return True

        if re.search(r"\bgrupo\s+10\d{2}\b", normalized) and (
            "descricao" in normalized or "estrutura" in normalized or "campo" in normalized
        ):
            return True

        return False

    @classmethod
    def resolve_material_group(cls, normalized_message: str | None) -> tuple[str, str, str] | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(normalized_message)

        if not normalized:
            return None

        for keywords, group_code, label in _MATERIAL_GROUPS:
            if any(keyword in normalized for keyword in keywords):
                return group_code, label, keywords[0]

        group_match = re.search(r"\bgrupo\s+(10\d{2})\b", normalized)
        if group_match:
            code = group_match.group(1)
            return code, f"grupo {code}", code

        return None

    @classmethod
    def build_rag_query(cls, message: str | None) -> str:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        parts = [
            "normas técnicas DELPI",
            "Normas_Tecnicas_DELPI",
            "descrição técnica matéria-prima",
            "estrutura da descrição campos exemplo",
            "cadastro TOTVS Protheus",
        ]

        group = cls.resolve_material_group(normalized)
        if group:
            group_code, label, _keyword = group
            parts.extend(
                [
                    f"grupo {group_code}",
                    label,
                    "objetivo abrangência estrutura campos",
                ]
            )

        if normalized:
            parts.append(normalized)

        return " ".join(dict.fromkeys(part for part in parts if part))
