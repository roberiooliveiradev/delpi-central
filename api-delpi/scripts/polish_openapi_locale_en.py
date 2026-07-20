#!/usr/bin/env python3
"""Polimento de textos EN em tv_route_audience + summary nativo do baseline.

- locale.en: remove stubs (= pt-BR) e prefixos PT; humaniza operationId / glossário
- baseline.summary / description: copia locale.en (OpenAPI nativo em inglês)
- openapi_param_locale.json: polishes EN descriptions from pt-BR when stub

Uso:
  python api-delpi/scripts/polish_openapi_locale_en.py --write
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
AUDIENCE_PATH = API_ROOT / "app" / "content" / "tv_route_audience.json"
BASELINE_PATH = API_ROOT / "app" / "content" / "openapi_baseline.json"
PARAM_LOCALE_PATH = API_ROOT / "app" / "content" / "openapi_param_locale.json"

_PT_PREFIX = re.compile(
    r"^(Consulta|Lista paginada|Lista|Indicador|Detalhe|Resumo|Série|Serie|Taxa|Percentual|"
    r"Histórico|Historico|Painel|Relatório|Relatorio|Exportação|Exportacao|Download|"
    r"Propostas|Cadastro|Registros|Consumo|Tempo|OPs)\b"
    r"(?:\s*[—\-–:]\s*|\s+)",
    re.I,
)

_PT_WORD = re.compile(
    r"\b(consulta|listar|lista|paginada|buscar|retorna|indicador|filial|filiais|"
    r"período|periodo|produção|producao|qualidade|estoque|financeiro|percentual|"
    r"histórico|historico|despesas|centro|custo|lancamentos|lançamentos|"
    r"fornecedores|serie|série|inspecoes|inspeções|entrada|pendentes|rejeitadas|"
    r"ensaiador|produto|produtos|detalhe|cadastrado|registros|consumo|validado|"
    r"apontamento|refugo|roteiro|estrutura|tempos|finalizadas|aberto|abertas|"
    r"planejado|propostas|comerciais|carteira|cadastro|operacional|resumo|entrega|"
    r"prazo|suprimentos|componentes|ferramenta|pedidos|venda|tabela|"
    r"consultar|de|da|do|para|com|sem|por|uma|um|os|as|ao|à|dos|das)\b",
    re.I,
)

# Tokens comuns em operationId PT → EN (humanize).
_OID_TOKEN_EN: dict[str, str] = {
    "financeiro": "financial",
    "despesas": "expenses",
    "centro": "center",
    "custo": "cost",
    "serie": "series",
    "série": "series",
    "ranking": "ranking",
    "centros": "centers",
    "fornecedores": "suppliers",
    "lancamentos": "entries",
    "lançamentos": "entries",
    "inspecoes": "inspections",
    "inspeções": "inspections",
    "entrada": "incoming",
    "pendentes": "pending",
    "rejeitadas": "rejected",
    "ensaiador": "tester",
    "produto": "product",
    "produtos": "products",
    "historico": "history",
    "histórico": "history",
    "detalhe": "detail",
    "proposta": "proposal",
    "propostas": "proposals",
    "comercial": "commercial",
    "comerciais": "commercial",
    "cultura": "culture",
    "delpi": "delpi",
    "percentual": "percentage",
    "resumo": "summary",
    "kaizen": "kaizen",
    "record": "record",
    "records": "records",
    "ferramenta": "tool",
    "componentes": "components",
    "abertas": "open",
    "ops": "production orders",
    "pedidos": "orders",
    "venda": "sales",
}

_ACCENT = re.compile(r"[áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ]")

# Substituições ordenadas (frases longas primeiro).
_PHRASE_MAP: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^Indicador\s*[—\-–]\s*", re.I), "Indicator — "),
    (re.compile(r"^Consulta\s*[—\-–]\s*", re.I), ""),
    (re.compile(r"^Lista paginada\s*[—\-–]\s*", re.I), "Paged list — "),
    (re.compile(r"^Lista\s*[—\-–]\s*", re.I), "List — "),
    (re.compile(r"^Taxa de fechamento comercial$", re.I), "Commercial closing rate"),
    (re.compile(r"^Percentual rol de novos negócios$", re.I), "New business ROL percentage"),
    (re.compile(r"^Média de novos clientes$", re.I), "New clients average"),
    (re.compile(r"^Percentual rol de clientes novos$", re.I), "New clients ROL percentage"),
    (re.compile(r"^Série temporal de rol comercial$", re.I), "Commercial ROL time series"),
    (re.compile(r"^Otd de pedidos de venda$", re.I), "Sales order OTD"),
    (re.compile(r"^Detalhe da proposta comercial \(OV\)$", re.I), "Commercial proposal detail (sales order)"),
    (re.compile(r"^Histórico de estágios da proposta comercial$", re.I), "Commercial proposal stage history"),
    (re.compile(r"\bEBITDA percentual \(financeiro\)$", re.I), "Financial EBITDA percentage"),
    (re.compile(r"\bCusto fixo percentual \(financeiro\)$", re.I), "Financial fixed cost percentage"),
    (re.compile(r"\bpercentual \(financeiro\)$", re.I), "percentage (financial)"),
    (re.compile(r"\bpercentual\b", re.I), "percentage"),
    (re.compile(r"\bfinanceiro\b", re.I), "financial"),
    (re.compile(r"\bdespesas\b", re.I), "expenses"),
    (re.compile(r"\blançamentos\b", re.I), "entries"),
    (re.compile(r"\blancamentos\b", re.I), "entries"),
    (re.compile(r"\bcentro custo\b", re.I), "cost center"),
    (re.compile(r"\bfornecedores\b", re.I), "suppliers"),
    (re.compile(r"\branking\b", re.I), "ranking"),
    (re.compile(r"\binspecoes entrada\b", re.I), "incoming inspections"),
    (re.compile(r"\binspeções de entrada\b", re.I), "incoming inspections"),
    (re.compile(r"\bhistorico detalhe\b", re.I), "history detail"),
    (re.compile(r"\bhistórico\b", re.I), "history"),
    (re.compile(r"\bhistorico\b", re.I), "history"),
    (re.compile(r"\bpendentes\b", re.I), "pending"),
    (re.compile(r"\brejeitadas\b", re.I), "rejected"),
    (re.compile(r"\bensaiador\b", re.I), "tester"),
    (re.compile(r"\bfilial\b", re.I), "branch"),
    (re.compile(r"\bfiliais\b", re.I), "branches"),
    (re.compile(r"\bperíodo\b", re.I), "period"),
    (re.compile(r"\bprodução\b", re.I), "production"),
    (re.compile(r"\bqualidade\b", re.I), "quality"),
    (re.compile(r"\bestoque\b", re.I), "stock"),
]


def humanize_operation_id(operation_id: str) -> str:
    text = re.sub(
        r"^(get|list|search|create|update|delete|post|put|patch|download|export)_",
        "",
        operation_id,
    )
    parts = [p for p in text.split("_") if p]
    if not parts:
        return operation_id
    # Merge centro+custo → cost center when adjacent.
    merged: list[str] = []
    i = 0
    while i < len(parts):
        a = parts[i].lower()
        b = parts[i + 1].lower() if i + 1 < len(parts) else ""
        if a == "centro" and b == "custo":
            merged.append("cost center")
            i += 2
            continue
        if a == "custo" and b == "centro":
            merged.append("cost center")
            i += 2
            continue
        merged.append(_OID_TOKEN_EN.get(a, parts[i].replace("-", " ")))
        i += 1
    out = " ".join(merged).strip()
    if not out:
        return operation_id
    return out[:1].upper() + out[1:]


def looks_portuguese(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw:
        return False
    if _ACCENT.search(raw):
        return True
    if _PT_PREFIX.search(raw):
        return True
    hits = _PT_WORD.findall(raw)
    stop = {"de", "da", "do", "os", "as", "um", "uma", "ao", "à", "dos", "das", "com", "sem", "por", "para", "vs"}
    meaningful = [h for h in hits if h.lower() not in stop]
    short = [h for h in hits if h.lower() in stop]
    if meaningful:
        return True
    if len(short) >= 2:
        return True
    return False


def polish_en_text(text: str, *, operation_id: str, field: str) -> str:
    raw = str(text or "").strip()
    if not raw:
        return humanize_operation_id(operation_id) if field == "summary" else raw
    if not looks_portuguese(raw):
        return raw
    out = raw
    for pattern, repl in _PHRASE_MAP:
        out = pattern.sub(repl, out)
    out = re.sub(r"\s+", " ", out).strip(" —-")
    if looks_portuguese(out) and field in {"summary", "label"}:
        return humanize_operation_id(operation_id)
    if looks_portuguese(out) and field == "description":
        return humanize_operation_id(operation_id) + "."
    if looks_portuguese(out) and field == "whenToUse":
        return f"Use for {humanize_operation_id(operation_id).lower()}."
    if not out and field == "summary":
        return humanize_operation_id(operation_id)
    return out or humanize_operation_id(operation_id)


def polish_audience(payload: dict) -> tuple[dict, int]:
    routes = payload.get("routes")
    if not isinstance(routes, dict):
        return payload, 0
    changed = 0
    for oid, entry in routes.items():
        if not isinstance(entry, dict):
            continue
        locale = entry.get("locale") if isinstance(entry.get("locale"), dict) else {}
        pt = dict(locale.get("pt-BR") or {})
        en = dict(locale.get("en") or {})
        updated = False
        for field in ("summary", "description", "whenToUse", "label"):
            pt_val = str(pt.get(field) or "").strip()
            en_val = str(en.get(field) or "").strip()
            needs = (not en_val) or (pt_val and en_val == pt_val) or looks_portuguese(en_val)
            if not needs:
                continue
            source = en_val if en_val and en_val != pt_val else (pt_val or en_val)
            polished = polish_en_text(source, operation_id=str(oid), field=field)
            if polished and polished != en_val:
                en[field] = polished
                updated = True
        if not en.get("summary"):
            en["summary"] = humanize_operation_id(str(oid))
            updated = True
        if updated:
            locale["en"] = en
            if pt:
                locale["pt-BR"] = pt
            entry["locale"] = locale
            routes[oid] = entry
            changed += 1
    payload["routes"] = routes
    return payload, changed


def polish_baseline_native_en(baseline: dict, audience: dict) -> int:
    routes = audience.get("routes") if isinstance(audience.get("routes"), dict) else {}
    changed = 0
    for op in baseline.get("operations") or []:
        if not isinstance(op, dict):
            continue
        oid = str(op.get("operationId") or "")
        entry = routes.get(oid) if isinstance(routes.get(oid), dict) else {}
        locale = entry.get("locale") if isinstance(entry.get("locale"), dict) else {}
        en = locale.get("en") if isinstance(locale.get("en"), dict) else {}
        summary = str(en.get("summary") or "").strip()
        description = str(en.get("description") or summary).strip()
        if summary and op.get("summary") != summary:
            op["summary"] = summary
            changed += 1
        if description and op.get("description") != description:
            op["description"] = description
            changed += 1
    return changed


def polish_param_description(pt: str, label_en: str) -> str:
    text = str(pt or "").strip()
    if not text:
        return f"{label_en} query parameter." if label_en else "Query parameter."
    exact = {
        "Filtra apenas registros ativos (sim) ou inativos (não).": (
            "Filters active (yes) or inactive (no) records only."
        ),
        "Percentual de ajuste aplicado no cálculo.": (
            "Adjustment percentage applied in the calculation."
        ),
        "Identificador da área (ex.: auditoria 5S).": "Area identifier (e.g. 5S audit).",
        "Status da auditoria no fluxo (aberta, concluída etc.).": (
            "Audit status in the workflow (open, completed, etc.)."
        ),
        "Código da filial no Protheus (ex.: 01 ou 02). Vazio usa o consolidado da rota, quando permitido.": (
            "Protheus branch code (e.g. 01 or 02). Empty uses consolidated scope when allowed."
        ),
        "Código da filial no Protheus (ex.: 01 ou 02).": "Protheus branch code (e.g. 01 or 02).",
    }
    if text in exact:
        return exact[text]
    repls: list[tuple[str, str]] = [
        (r"Código da filial", "Branch code"),
        (r"Identificador", "Identifier"),
        (r"Filtro de", "Filter for"),
        (r"Filtro", "Filter"),
        (r"Filtra", "Filters"),
        (r"Percentual", "Percentage"),
        (r"período em dias", "period in days"),
        (r"período", "period"),
        (r"Data de início", "Start date"),
        (r"Data de fim", "End date"),
        (r"data inicial", "start date"),
        (r"data final", "end date"),
        (r"obrigatório", "required"),
        (r"opcional", "optional"),
        (r"quando permitido", "when allowed"),
        (r"no Protheus", "in Protheus"),
        (r"ex\.:", "e.g."),
        (r"Vazio usa o consolidado da rota", "Empty uses the route consolidated scope"),
        (r"Vazio usa", "Empty uses"),
        (r"apenas registros", "records only"),
        (r"registros ativos", "active records"),
        (r"registros", "records"),
        (r"ativos \(sim\) ou inativos \(não\)", "active (yes) or inactive (no)"),
        (r"no fluxo", "in the workflow"),
        (r"aberta, concluída", "open, completed"),
        (r"aplicado no cálculo", "applied in the calculation"),
        (r"de ajuste", "adjustment"),
        (r"produto", "product"),
        (r"produtos", "products"),
        (r"filial", "branch"),
        (r"filiais", "branches"),
        (r"código", "code"),
        (r"Código", "Code"),
        (r"limite", "limit"),
        (r"página", "page"),
        (r"paginação", "pagination"),
        (r"ordenação", "sort order"),
        (r"ordenar por", "sort by"),
        (r"agrupar por", "group by"),
        (r"granularidade", "granularity"),
        (r"dias", "days"),
        (r"mês", "month"),
        (r"ano", "year"),
        (r"departamento", "department"),
        (r"fornecedor", "supplier"),
        (r"cliente", "customer"),
        (r"status", "status"),
        (r"tipo", "type"),
        (r"busca", "search"),
        (r"texto livre", "free text"),
        (r"valor", "value"),
        (r"quantidade", "quantity"),
    ]
    out = text
    for a, b in repls:
        out = re.sub(a, b, out, flags=re.I)
    out = re.sub(r"\s+", " ", out).strip()
    if looks_portuguese(out) or _ACCENT.search(out):
        lab = label_en or "Parameter"
        return f"{lab}."
    return out


def polish_params(payload: dict) -> int:
    params = payload.get("params")
    if not isinstance(params, dict):
        return 0
    changed = 0
    for _name, entry in params.items():
        if not isinstance(entry, dict):
            continue
        locale = entry.get("locale") if isinstance(entry.get("locale"), dict) else {}
        en = dict(locale.get("en") or {})
        pt = dict(locale.get("pt-BR") or {})
        en_desc = str(en.get("description") or "").strip()
        pt_desc = str(pt.get("description") or "").strip()
        label_en = str(en.get("label") or "").strip()
        needs = (
            not en_desc
            or "filter/parameter" in en_desc
            or looks_portuguese(en_desc)
            or (pt_desc and en_desc == pt_desc)
        )
        if not needs:
            continue
        new_desc = polish_param_description(pt_desc, label_en)
        if new_desc and new_desc != en_desc:
            en["description"] = new_desc
            locale["en"] = en
            entry["locale"] = locale
            changed += 1
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    audience = json.loads(AUDIENCE_PATH.read_text(encoding="utf-8"))
    audience, aud_changed = polish_audience(audience)
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    base_changed = polish_baseline_native_en(baseline, audience)
    params_payload = json.loads(PARAM_LOCALE_PATH.read_text(encoding="utf-8"))
    param_changed = polish_params(params_payload)

    print(
        f"audience polished={aud_changed} baseline fields={base_changed} "
        f"param descriptions={param_changed}"
    )
    if not args.write:
        print("Dry-run — use --write para gravar.")
        return 0

    AUDIENCE_PATH.write_text(json.dumps(audience, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    BASELINE_PATH.write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PARAM_LOCALE_PATH.write_text(
        json.dumps(params_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Gravado {AUDIENCE_PATH}")
    print(f"Gravado {BASELINE_PATH}")
    print(f"Gravado {PARAM_LOCALE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
