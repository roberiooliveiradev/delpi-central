from __future__ import annotations

import re
from functools import lru_cache

from app.domain.services.chat_label_content_service import ChatLabelContentService

_ENGLISH_SUMMARY_PREFIXES = (
    "get ",
    "list ",
    "post ",
    "put ",
    "patch ",
    "delete ",
    "create ",
    "update ",
    "fetch ",
    "retrieve ",
    "search ",
    "execute ",
    "root",
)


@lru_cache(maxsize=1)
def _path_labels() -> tuple[tuple[str, str], ...]:
    data = ChatLabelContentService.load("api_paths")
    items = data.get("pathLabels") or []
    return tuple(
        (str(item["path"]), str(item["label"]))
        for item in items
        if isinstance(item, dict) and item.get("path") and item.get("label")
    )


@lru_cache(maxsize=1)
def _english_exact_summaries() -> dict[str, str]:
    data = ChatLabelContentService.load("api_paths")
    raw = data.get("englishSummaries") or {}
    if not isinstance(raw, dict):
        return {}
    return {str(key).casefold(): str(value) for key, value in raw.items()}


@lru_cache(maxsize=1)
def _default_authorized_query_label() -> str:
    data = ChatLabelContentService.load("api_paths")
    defaults = data.get("defaults") or {}
    if isinstance(defaults, dict) and defaults.get("authorizedQuery"):
        return str(defaults["authorizedQuery"])
    return "Consulta autorizada"


class ChatActionLabelService:
    """Rótulos em pt-BR para actions OpenAPI no catálogo de capacidades."""

    @classmethod
    def humanize(
        cls,
        *,
        path: str,
        method: str,
        summary: str,
        action_id: str = "",
    ) -> str:
        raw = str(summary or "").strip()
        path_key = str(path or "").strip()

        label = cls._label_from_path(path_key)
        if label:
            return label

        english_summaries = _english_exact_summaries()
        lowered = raw.casefold()
        if lowered in english_summaries:
            return english_summaries[lowered]

        if raw and not cls._looks_english(raw):
            return raw

        from_path = cls._label_from_path_tail(path_key, method)
        if from_path:
            return from_path

        translated = cls._translate_english_summary(raw)
        if translated:
            return translated

        if raw:
            return raw

        return action_id or path_key or _default_authorized_query_label()

    @classmethod
    def _label_from_path(cls, path: str) -> str | None:
        if not path:
            return None

        normalized = path.strip().lower().rstrip("/") or "/"
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"

        for pattern, label in _path_labels():
            if cls._path_matches_pattern(normalized, pattern.lower()):
                return label

        return None

    @classmethod
    def _path_matches_pattern(cls, path: str, pattern: str) -> bool:
        def segments(value: str) -> list[str]:
            return [seg for seg in value.strip("/").lower().split("/") if seg]

        path_parts = segments(path)
        pattern_parts = segments(pattern)

        if len(path_parts) != len(pattern_parts):
            return False

        for path_seg, pattern_seg in zip(path_parts, pattern_parts):
            if pattern_seg.startswith("{") and pattern_seg.endswith("}"):
                continue
            if path_seg != pattern_seg:
                return False

        return True

    @classmethod
    def _label_from_path_tail(cls, path: str, method: str) -> str | None:
        if not path:
            return None

        parts = [p for p in path.strip("/").split("/") if p and not p.startswith("{")]
        if not parts:
            return None

        tail = parts[-1].replace("_", " ").replace("-", " ")
        segment_map = {
            "search": "Busca",
            "summary": "Resumo",
            "dashboard": "Painel",
            "series": "Série histórica",
            "charts": "Gráficos",
            "items": "Itens",
            "processes": "Processos",
            "branches": "Filiais",
            "columns": "Colunas",
            "tables": "Tabelas",
        }

        if tail in segment_map:
            prefix = segment_map[tail]
            domain = parts[0] if parts else ""
            domain_pt = {
                "commercial": "comercial",
                "financial": "financeiro",
                "production": "produção",
                "quality": "qualidade",
                "hr": "RH",
                "engineering": "engenharia",
                "supplies": "suprimentos",
                "products": "produto",
                "system": "sistema",
            }.get(domain, domain)
            if domain_pt:
                return f"{prefix} ({domain_pt})"

        return None

    @classmethod
    def _looks_english(cls, text: str) -> bool:
        english_summaries = _english_exact_summaries()
        lowered = text.casefold().strip()
        if not lowered:
            return True

        if lowered in english_summaries:
            return True

        if any(lowered.startswith(prefix) for prefix in _ENGLISH_SUMMARY_PREFIXES):
            return True

        if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$", text.strip()):
            return True

        en_tokens = (
            "customers",
            "suppliers",
            "parents",
            "guide",
            "inspection",
            "invoice",
            "movements",
            "route",
            "billing",
            "pricing",
            "dashboard",
            "public",
        )
        if any(token in lowered for token in en_tokens):
            return True

        return False

    @classmethod
    def _translate_english_summary(cls, summary: str) -> str | None:
        text = summary.strip()
        if not text:
            return None

        lowered = text.casefold()
        for prefix in _ENGLISH_SUMMARY_PREFIXES:
            if lowered.startswith(prefix):
                remainder = text[len(prefix) :].strip()
                return cls._title_to_pt(remainder) or None

        return cls._title_to_pt(text)

    @classmethod
    def _title_to_pt(cls, title: str) -> str | None:
        if not title.strip():
            return None

        words = re.split(r"[\s_/\-]+", title.strip())
        if not words:
            return None

        lexicon = {
            "sales": "vendas",
            "conversion": "conversão",
            "rate": "taxa",
            "branch": "filial",
            "rol": "ROL",
            "target": "meta",
            "pct": "%",
            "head": "matriz",
            "office": "",
            "new": "novos",
            "business": "negócios",
            "clients": "clientes",
            "client": "cliente",
            "average": "média",
            "commercial": "comercial",
            "series": "série",
            "order": "pedido",
            "otd": "OTD",
            "active": "ativos",
            "pdi": "PDI",
            "count": "quantidade",
            "performance": "desempenho",
            "reviews": "avaliações",
            "completion": "conclusão",
            "snapshot": "snapshot",
            "hr": "RH",
            "depreciation": "depreciação",
            "direct": "direta",
            "labor": "mão de obra",
            "cost": "custo",
            "delivery": "entrega",
            "time": "",
            "on": "no",
            "overall": "global",
            "equipment": "equipamentos",
            "effectiveness": "eficiência",
            "production": "produção",
            "ebitda": "EBITDA",
            "fixed": "fixos",
            "pmr": "PMR",
            "audit": "auditoria",
            "kaizen": "kaizen",
            "kaizens": "kaizens",
            "nonconformity": "não conformidade",
            "nonconformities": "não conformidades",
            "external": "externo",
            "internal": "interno",
            "ppm": "PPM",
            "summary": "resumo",
            "excel": "Excel",
            "public": "público",
            "structure": "estrutura",
            "process": "processo",
            "processes": "processos",
            "health": "saúde",
            "root": "raiz",
        }

        translated: list[str] = []
        for word in words:
            key = word.casefold()
            if key in lexicon:
                piece = lexicon[key]
                if piece:
                    translated.append(piece)
            elif word.isupper() and len(word) <= 5:
                translated.append(word)
            else:
                translated.append(word.lower())

        if not translated:
            return None

        phrase = " ".join(translated).strip()
        if not phrase:
            return None

        return phrase[0].upper() + phrase[1:]
