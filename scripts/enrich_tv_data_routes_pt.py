"""Curadoria PT-BR: labels EN para PT e description em todas as rotas TV.

Idempotente — reexecutar preserva descriptions ja manuais com --only-missing.

Uso:
  python3 scripts/enrich_tv_data_routes_pt.py --write
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "tv-dashboard-api" / "tv_app" / "content" / "tv_data_routes.json"

# Labels EN explícitos (operationId → label PT)
LABEL_OVERRIDES: dict[str, str] = {
    "get_cultura_delpi_content_cultura_delpi_content_get": "Conteúdo Cultura Delpi",
    "search_customers_route_customers_search_get": "Busca de clientes",
    "get_dashboard_department_idd_dashboard_department_idd_get": "Dashboard departamental (IDD)",
    "get_public_inspection_public_quality_labels_inspection__token__get": "Inspeção pública (etiqueta)",
    "get_audit_5s_dashboard_quality_audit_5s_analytics_dashboard_get": "Auditoria 5S — painel analítico",
    "list_areas_quality_audit_5s_areas_get": "Auditoria 5S — áreas",
    "list_audits_quality_audit_5s_audits_get": "Auditoria 5S — listagem",
    "get_audit_quality_audit_5s_audits__audit_id__get": "Auditoria 5S — detalhe",
    "list_audit_nc_attachments_quality_audit_5s_audits__audit_id__nc_attachments_get": "Auditoria 5S — anexos de NC da auditoria",
    "list_nc_candidates_quality_audit_5s_audits__audit_id__nc_candidates_get": "Auditoria 5S — candidatos a NC",
    "list_audit_nonconformities_quality_audit_5s_audits__audit_id__nonconformities_get": "Auditoria 5S — não conformidades",
    "list_criteria_quality_audit_5s_criteria_get": "Auditoria 5S — critérios",
    "list_nc_actions_quality_audit_5s_nonconformities__nc_id__actions_get": "Auditoria 5S — ações da NC",
    "list_nc_attachments_quality_audit_5s_nonconformities__nc_id__attachments_get": "Auditoria 5S — anexos da NC",
    "get_audit_5s_summary_quality_audit_5s_summary_get": "Auditoria 5S — resumo",
    "root_health_get": "Saúde da API (root)",
}

# Prefixos EN genéricos → PT
_EN_PREFIXES = (
    (re.compile(r"^Get\s+", re.I), "Consultar "),
    (re.compile(r"^List\s+", re.I), "Listar "),
    (re.compile(r"^Search\s+", re.I), "Buscar "),
    (re.compile(r"^Create\s+", re.I), "Criar "),
    (re.compile(r"^Update\s+", re.I), "Atualizar "),
    (re.compile(r"^Delete\s+", re.I), "Excluir "),
    (re.compile(r"^Post\s+", re.I), "Enviar "),
)

_SHAPE_LEAD = {
    "scalar": "Indicador numérico",
    "paged_list": "Listagem paginada",
    "hierarchy": "Visão hierárquica",
    "playbook_report": "Relatório operacional",
    "composite_analysis": "Análise composta",
}


def _looks_english(label: str) -> bool:
    return bool(re.match(r"^(Get|List|Search|Create|Update|Delete|Post)\b", label.strip(), re.I))


def _humanize_en_label(label: str) -> str:
    text = label.strip()
    for pattern, repl in _EN_PREFIXES:
        if pattern.match(text):
            rest = pattern.sub("", text).strip()
            # Nc → NC, 5s → 5S
            rest = re.sub(r"\bNc\b", "NC", rest)
            rest = re.sub(r"\b5s\b", "5S", rest, flags=re.I)
            rest = re.sub(r"\bId\b", "ID", rest)
            return f"{repl}{rest}".strip()
    return text


def _description_for(route: dict) -> str:
    label = str(route.get("label") or "").strip()
    shape = str(route.get("metaShape") or "")
    lead = _SHAPE_LEAD.get(shape, "Consulta operacional")
    # Evitar "Indicador numérico: Indicador — …"
    clean = re.sub(r"^Indicador\s*[—\-–]\s*", "", label, flags=re.I).strip() or label
    if shape == "scalar":
        return f"{lead} para «{clean}»."
    if shape == "paged_list":
        return f"{lead} de «{clean}» para uso em tabela ou gráfico no TV."
    if shape == "hierarchy":
        return f"{lead} de «{clean}»."
    return f"{lead}: «{clean}»."


def enrich(routes: list[dict], *, only_missing: bool) -> tuple[int, int]:
    labels_fixed = 0
    descriptions_added = 0
    for route in routes:
        op = str(route.get("operationId") or "")
        if op in LABEL_OVERRIDES:
            if route.get("label") != LABEL_OVERRIDES[op]:
                route["label"] = LABEL_OVERRIDES[op]
                labels_fixed += 1
        elif _looks_english(str(route.get("label") or "")):
            route["label"] = _humanize_en_label(str(route["label"]))
            labels_fixed += 1

        if only_missing and route.get("description"):
            continue
        desc = _description_for(route)
        if route.get("description") != desc:
            route["description"] = desc
            descriptions_added += 1
    return labels_fixed, descriptions_added


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--only-missing", action="store_true", help="Não sobrescreve description existente")
    args = parser.parse_args()

    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    routes = data.get("routes") or []
    labels_fixed, descriptions_added = enrich(routes, only_missing=args.only_missing)
    print(f"routes={len(routes)} labels_fixed={labels_fixed} descriptions_set={descriptions_added}")

    if args.write:
        CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {CATALOG}")


if __name__ == "__main__":
    main()
