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
    "get_ppm_external_series": "PPM externo — série temporal",
    "get_ppm_internal_series": "PPM interno — série temporal",
    "get_nonconformity_series_quality_nonconformities_series_get": "Não conformidades — série temporal",
    "list_ppm_external": "PPM externo — listagem",
    "list_ppm_internal": "PPM interno — listagem",
    "list_nonconformity_route_quality_nonconformities_get": "Não conformidades — listagem",
    "download_nc_attachment_quality_audit_5s_nonconformities__nc_id__attachments__attachment_id__file_get": "Auditoria 5S — download de anexo da NC",
    "download_kaizen_evidence_quality_kaizens_records__record_id__evidences__evidence_id__file_get": "Kaizen — download de evidência",
    "export_proposta_comercial_pdf_route_propostas_comerciais__proposta_interna__pdf_get": "Proposta comercial — exportar PDF",
    "get_quality_action_plans_dashboard": "PAC Qualidade — painel",
    "list_labels_quality_labels_get": "Etiquetas de qualidade — listagem",
    "list_audit_events_quality_labels_audit_events_get": "Etiquetas — eventos de auditoria",
    "list_checklist_template_quality_labels_checklist_template_get": "Etiquetas — modelo de checklist",
    "get_my_inspector_quality_labels_inspectors_me_get": "Meu perfil de inspetor",
    "get_my_signature_quality_labels_inspectors_me_signature_get": "Minha assinatura de inspetor",
    "get_label_quality_labels__label_id__get": "Etiqueta de qualidade — detalhe",
    "get_certificate_quality_labels__label_id__certificate_get": "Etiqueta — certificado",
    "get_label_qr_quality_labels__label_id__qr_get": "Etiqueta — QR Code",
    "get_produced_quantity": "Quantidade produzida",
    "list_bookings_scheduling_bookings_get": "Agendamentos — reservas",
    "list_resources_scheduling_resources_get": "Agendamentos — recursos",
}

# Prefixos EN genéricos → PT
_EN_PREFIXES = (
    (re.compile(r"^Get\s+", re.I), ""),
    (re.compile(r"^List\s+", re.I), ""),
    (re.compile(r"^Search\s+", re.I), ""),
    (re.compile(r"^Create\s+", re.I), ""),
    (re.compile(r"^Update\s+", re.I), ""),
    (re.compile(r"^Delete\s+", re.I), ""),
    (re.compile(r"^Post\s+", re.I), ""),
    (re.compile(r"^Download\s+", re.I), ""),
    (re.compile(r"^Export\s+", re.I), ""),
    (re.compile(r"^Consultar\s+", re.I), ""),
    (re.compile(r"^Listar\s+", re.I), ""),
)

# Tokens EN remanescentes no rótulo (após prefixo)
_EN_TOKEN_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bNonconformity\b", re.I), "não conformidades"),
    (re.compile(r"\bExternal\s+Ppm\b", re.I), "PPM externo"),
    (re.compile(r"\bInternal\s+Ppm\b", re.I), "PPM interno"),
    (re.compile(r"\bPpm\b", re.I), "PPM"),
    (re.compile(r"\bSeries\b", re.I), "série temporal"),
    (re.compile(r"\bAttachment\b", re.I), "anexo"),
    (re.compile(r"\bAttachments\b", re.I), "anexos"),
    (re.compile(r"\bEvidence\b", re.I), "evidência"),
    (re.compile(r"\bEvidences\b", re.I), "evidências"),
    (re.compile(r"\bRoute\b", re.I), ""),
    (re.compile(r"\bQuality\s+action\s+plan\s+dashboard\b", re.I), "PAC Qualidade — painel"),
    (re.compile(r"\bKaizen\b", re.I), "Kaizen"),
    (re.compile(r"\bNc\b"), "NC"),
    (re.compile(r"\b5s\b", re.I), "5S"),
    (re.compile(r"\bId\b"), "ID"),
    (re.compile(r"\bPdf\b", re.I), "PDF"),
)

_SHAPE_LEAD = {
    "scalar": "Indicador numérico",
    "paged_list": "Listagem paginada",
    "hierarchy": "Visão hierárquica",
    "playbook_report": "Relatório operacional",
    "composite_analysis": "Análise composta",
}


def _looks_english(label: str) -> bool:
    """Detecta rótulos ainda em inglês ou híbridos (ex.: Consultar External Ppm Series)."""
    text = label.strip()
    if re.match(r"^(Get|List|Search|Create|Update|Delete|Post|Download|Export)\b", text, re.I):
        return True
    # Híbridos do enrich anterior: prefixo PT + resto EN
    if re.match(r"^(Consultar|Listar|Buscar|Criar|Atualizar|Excluir|Enviar)\s+", text, re.I):
        return bool(
            re.search(
                r"\b(External|Internal|Nonconformity|Attachment|Evidence|Route|Series|Ppm|"
                r"Customers|Inspection|Kaizen|Quality|Action|Plan|Dashboard|Pdf)\b",
                text,
                re.I,
            )
        )
    return False


def _title_case_pt(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip(" —–-")
    if not text:
        return text
    # Capitaliza só a primeira letra (resto já vem do glossário)
    return text[0].upper() + text[1:] if text else text


def _humanize_en_label(label: str) -> str:
    text = label.strip()
    for pattern, _repl in _EN_PREFIXES:
        if pattern.match(text):
            text = pattern.sub("", text).strip()
            break
    for pattern, repl in _EN_TOKEN_REPLACEMENTS:
        text = pattern.sub(repl, text)
    text = re.sub(r"\s+", " ", text).strip(" —–-")
    # "PPM externo série temporal" → "PPM externo — série temporal"
    text = re.sub(r"\b(PPM (?:externo|interno))\s+(série temporal)\b", r"\1 — \2", text, flags=re.I)
    text = re.sub(r"\b(não conformidades)\s+(série temporal)\b", r"\1 — \2", text, flags=re.I)
    return _title_case_pt(text)


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
