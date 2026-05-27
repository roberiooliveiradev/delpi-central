from __future__ import annotations

import re

# Padrões de path (minúsculo) → rótulo em pt-BR. Ordem: mais específico primeiro.
_PATH_LABELS: tuple[tuple[str, str], ...] = (
    ("/products/{code}/stock", "Estoque do produto por filial e local"),
    ("/products/{code}/suppliers", "Fornecedores do produto"),
    ("/products/{code}/customers", "Clientes do produto"),
    ("/products/{code}/purchases", "Histórico de compras do produto"),
    ("/products/{code}/sales/billing", "Resumo de faturamento do produto"),
    ("/products/{code}/sales/open-orders", "Carteira de pedidos de venda em aberto"),
    ("/products/{code}/sales", "Resumo de vendas do produto"),
    ("/products/{code}/structure/excel", "Exportar estrutura (BOM) em Excel"),
    ("/products/{code}/structure", "Estrutura (BOM) do produto"),
    ("/products/{code}/parents", "Onde o produto é usado (produtos pai)"),
    ("/products/{code}/guide", "Roteiro de produção do produto"),
    ("/products/{code}/inspection", "Plano de inspeção do produto"),
    ("/products/{code}/internal-movements", "Movimentações internas do produto"),
    ("/products/{code}/inbound-invoice-items", "Itens de notas fiscais de entrada"),
    ("/products/{code}/outbound-invoice-items", "Itens de notas fiscais de saída"),
    ("/products/{code}/analyser", "Ficha completa do produto (analisador)"),
    ("/products/{code}/pricing", "Preços comerciais do produto"),
    ("/products/{code}/summary", "Resumo consolidado do produto"),
    ("/products/{code}", "Descrição e dados cadastrais do produto"),
    ("/products/search", "Buscar produtos no Protheus"),
    ("/data/sql", "Executar consulta SQL somente leitura"),
    ("/supplies/stock-value", "Valor total de estoque (suprimentos)"),
    ("/supplies/inventory-turnover", "Giro de estoque / IDD (suprimentos)"),
    ("/supplies/cpv", "CPV — custo de produto vendido (suprimentos)"),
    ("/supplies/otd", "OTD — entrega no prazo (suprimentos)"),
    ("/engineering/lmps/dashboard/charts", "Gráficos do painel de LMPs"),
    ("/engineering/lmps/dashboard/items", "Itens do painel de LMPs"),
    ("/engineering/lmps/dashboard/summary", "Resumo do painel de LMPs"),
    ("/engineering/lmps/dashboard", "Painel (dashboard) de LMPs"),
    ("/engineering/lmps/{sale_number}", "Detalhe da LMP por ordem de venda"),
    ("/engineering/lmps", "Listar LMPs (ordens especiais / amostras)"),
    ("/engineering/transforma-mais/processes/summary", "Resumo dos processos Transforma Mais"),
    ("/engineering/transforma-mais/processes", "Listar processos Transforma Mais"),
    ("/system/columns/search", "Buscar colunas por descrição (SX3)"),
    ("/system/tables/search", "Buscar tabelas por descrição (SX2)"),
    ("/system/tables/{tablename}/columns/search", "Buscar colunas de uma tabela por texto"),
    ("/system/tables/{tablename}/columns", "Listar colunas de tabela com paginação"),
    ("/system/tables/{tablename}", "Consultar informações de tabela"),
    ("/commercial/sales-order-otd", "OTD de ordens de venda (comercial)"),
    ("/commercial/closing-rate", "Taxa de conversão de vendas"),
    ("/commercial/branch_rol_target_pct", "Meta ROL por filial (%)"),
    ("/commercial/head_office_rol_target_pct", "Meta ROL matriz (%)"),
    ("/commercial/new-business-rol-pct", "ROL de novos negócios (%)"),
    ("/commercial/new-clients-average", "Média de novos clientes"),
    ("/commercial/new-clients-rol-pct", "ROL de novos clientes (%)"),
    ("/commercial/rol/series", "Série histórica de ROL comercial"),
    ("/financial/ebitda_pct", "EBITDA (%)"),
    ("/financial/fixed_cost_pct", "Custos fixos (%)"),
    ("/financial/pmr", "PMR — prazo médio de recebimento"),
    ("/financial/rol", "ROL financeiro"),
    ("/finacial/ebitda_pct", "EBITDA (%) — rota legada"),
    ("/finacial/fixed_cost_pct", "Custos fixos (%) — rota legada"),
    ("/finacial/pmr", "PMR — rota legada"),
    ("/finacial/rol", "ROL — rota legada"),
    ("/production/depreciation_pct", "Depreciação (%) — produção"),
    ("/production/direct_labor_cost_pct", "Custo de mão de obra direta (%)"),
    ("/production/on_time_delivery_pct", "Entrega no prazo (%) — produção"),
    ("/production/overall_equipment_effectiveness_pct", "OEE — eficiência global dos equipamentos (%)"),
    ("/production/production_cost_pct", "Custo de produção (%)"),
    ("/hr/active-pdi-count", "PDIs ativos (RH)"),
    ("/hr/branches", "Filiais (RH)"),
    ("/hr/performance-reviews-completion", "Conclusão de avaliações de desempenho"),
    ("/hr/snapshot", "Snapshot de indicadores de RH"),
    ("/quality/audit-5s/summary", "Resumo da auditoria 5S"),
    ("/quality/branches", "Filiais (qualidade)"),
    ("/quality/kaizens/summary", "Resumo de kaizens"),
    ("/quality/nonconformities/series", "Série de não conformidades"),
    ("/quality/nonconformities", "Não conformidades"),
    ("/quality/ppm/external/series", "Série de PPM externo"),
    ("/quality/ppm/external/summary", "Resumo de PPM externo"),
    ("/quality/ppm/external", "PPM externo"),
    ("/quality/ppm/internal/series", "Série de PPM interno"),
    ("/quality/ppm/internal/summary", "Resumo de PPM interno"),
    ("/quality/ppm/internal", "PPM interno"),
    ("/sales/", "Listar ordens de venda"),
    ("/health", "Verificar saúde da API"),
)

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

_ENGLISH_EXACT_SUMMARIES: dict[str, str] = {
    "customers": "Clientes do produto",
    "suppliers": "Fornecedores do produto",
    "parents": "Onde o produto é usado (produtos pai)",
    "guide": "Roteiro de produção do produto",
    "inspection": "Plano de inspeção do produto",
    "internal movements": "Movimentações internas do produto",
    "inbound invoice items": "Itens de notas fiscais de entrada",
    "outbound invoice items": "Itens de notas fiscais de saída",
    "structure excel public": "Exportar estrutura (BOM) em Excel",
    "product commercial pricing": "Preços comerciais do produto",
    "product billing summary": "Resumo de faturamento do produto",
    "list processes": "Listar processos Transforma Mais",
    "get process summary": "Resumo dos processos Transforma Mais",
    "root": "Verificar saúde da API",
    "lmps dashboard charts route": "Gráficos do painel de LMPs",
    "lmps dashboard items route": "Itens do painel de LMPs",
    "lmps dashboard summary route": "Resumo do painel de LMPs",
}

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

        lowered = raw.casefold()
        if lowered in _ENGLISH_EXACT_SUMMARIES:
            return _ENGLISH_EXACT_SUMMARIES[lowered]

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

        return action_id or path_key or "Consulta autorizada"

    @classmethod
    def _label_from_path(cls, path: str) -> str | None:
        if not path:
            return None

        normalized = path.strip().lower().rstrip("/") or "/"
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"

        for pattern, label in _PATH_LABELS:
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
        lowered = text.casefold().strip()
        if not lowered:
            return True

        if lowered in _ENGLISH_EXACT_SUMMARIES:
            return True

        if any(lowered.startswith(prefix) for prefix in _ENGLISH_SUMMARY_PREFIXES):
            return True

        # CamelCase ou muitas palavras ASCII típicas de OpenAPI
        if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$", text.strip()):
            return True

        # Poucos caracteres acentuados e palavras comuns em EN
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
