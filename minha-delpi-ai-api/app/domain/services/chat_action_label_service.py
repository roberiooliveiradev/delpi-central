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
        provider_key: str = "",
        delpi_metadata: dict | None = None,
        schema_hash: str = "",
    ) -> str:
        from app.domain.services.action_display_label_resolver import (
            ActionDisplayLabelResolver,
        )

        return ActionDisplayLabelResolver.resolve(
            path=path,
            method=method,
            summary=summary,
            action_id=action_id,
            provider_key=provider_key,
            delpi_metadata=delpi_metadata,
            schema_hash=schema_hash,
        ).label

    @classmethod
    def humanize_with_source(
        cls,
        *,
        path: str,
        method: str,
        summary: str,
        action_id: str = "",
        provider_key: str = "",
        delpi_metadata: dict | None = None,
        schema_hash: str = "",
    ):
        from app.domain.services.action_display_label_resolver import (
            ActionDisplayLabelResolver,
        )

        return ActionDisplayLabelResolver.resolve(
            path=path,
            method=method,
            summary=summary,
            action_id=action_id,
            provider_key=provider_key,
            delpi_metadata=delpi_metadata,
            schema_hash=schema_hash,
        )

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
            "stock": "Estoque",
            "purchases": "Compras",
            "structure": "Estrutura",
            "inspection": "Inspeção",
            "guide": "Roteiro",
            "customers": "Clientes",
            "suppliers": "Fornecedores",
            "pricing": "Preços",
            "analyser": "Analisador",
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
        lowered = text.casefold().strip()
        if not lowered:
            return True

        pt_markers = (
            "consultar",
            "listar",
            "buscar",
            "estoque",
            "produto",
            "filial",
            " inventário",
            "inventario",
            "resumo",
            "painel",
            "roteiro",
            "inspeção",
            "inspecao",
            " estrutura",
            " fornecedor",
            " cliente",
            " do ",
            " da ",
            " dos ",
            " das ",
            " por ",
            " para ",
            " com ",
        )
        if any(marker in lowered for marker in pt_markers):
            return False

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
            "production",
            "appointment",
            "appointments",
            "detail",
            "series",
            "schema",
            "complete",
            "snapshot",
            "orders",
            "products",
            "inventory",
            "telemetry",
            "warehouse",
            "widget",
            "widgets",
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
            "customers": "clientes",
            "customer": "cliente",
            "suppliers": "fornecedores",
            "supplier": "fornecedor",
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
            "product": "produto",
            "stock": "estoque",
            "schema": "schema",
            "table": "tabela",
            "dashboard": "painel",
            "fabril": "fabril",
            "eficiencia": "eficiência",
            "things": "itens",
            "widget": "widget",
            "widgets": "widgets",
            "inventory": "inventário",
            "warehouse": "depósito",
            "vehicle": "veículo",
            "telemetry": "telemetria",
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
