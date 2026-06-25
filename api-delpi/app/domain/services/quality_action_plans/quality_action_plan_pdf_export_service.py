from __future__ import annotations

import io
from datetime import date, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.domain.services.quality_action_plans.five_whys_service import (
    five_whys_track_lines,
)
from app.domain.services.quality_action_plans.ishikawa_causes_service import (
    ishikawa_category_lines,
)
from app.domain.services.quality_action_plans.rnc_8d_excel_export_service import (
    SUPPLIER_BY_BRANCH,
    _material_label,
)

TITLE_COLOR = colors.HexColor("#013866")
LINE_COLOR = colors.HexColor("#E2E8F0")
MUTED = colors.HexColor("#64748B")

STATUS_LABELS = {
    "draft": "Rascunho",
    "triage": "Triagem",
    "containment": "Contenção",
    "root_cause_analysis": "Análise de causa",
    "action_plan_defined": "Plano definido",
    "in_progress": "Em andamento",
    "waiting_validation": "Aguardando validação",
    "completed": "Concluído",
    "cancelled": "Cancelado",
}

SEVERITY_LABELS = {
    "low": "Baixa",
    "medium": "Média",
    "high": "Alta",
    "critical": "Crítica",
}

SCOPE_LABELS = {
    "internal": "Interna",
    "external": "Externa",
}

EFFECTIVENESS_LABELS = {
    "pending": "Pendente",
    "effective": "Eficaz",
    "partially_effective": "Parcialmente eficaz",
    "ineffective": "Ineficaz",
    "not_verified": "Não verificado",
}

ACTION_TYPE_LABELS = {
    "containment": "Contenção",
    "corrective": "Corretiva",
    "preventive": "Preventiva",
    "verification": "Verificação",
    "standardization": "Padronização",
    "training": "Treinamento",
}

ACTION_STATUS_LABELS = {
    "pending": "Pendente",
    "in_progress": "Em andamento",
    "blocked": "Bloqueada",
    "completed": "Concluída",
    "cancelled": "Cancelada",
    "overdue": "Atrasada",
}

ISHAKAWA_LABELS = {
    "machine": "Máquina",
    "method_process": "Método",
    "material": "Material",
    "manpower": "Mão de obra",
    "measurement": "Medição",
    "environment": "Meio ambiente",
    "notes": "Observações",
}


def _text(value: Any, *, max_len: int = 1500) -> str:
    if value is None:
        return "—"
    text = str(value).strip()
    if not text:
        return "—"
    if len(text) > max_len:
        return f"{text[: max_len - 1]}…"
    return text


def _format_date(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    text = str(value).strip()
    if not text:
        return "—"
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return text[:16]


def plan_pdf_filename(plan: dict[str, Any]) -> str:
    registry = plan.get("code") or str(plan.get("id") or "plano")[:8]
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(registry))
    return f"PAC_{safe}_resumo.pdf"


def rnc_8d_pdf_filename(plan: dict[str, Any]) -> str:
    registry = plan.get("client_nc_registry") or plan.get("code") or str(plan.get("id") or "plano")[:8]
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(registry))
    return f"RNC_{safe}_8D.pdf"


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "PacPdfTitle",
            parent=base["Heading1"],
            fontSize=16,
            textColor=TITLE_COLOR,
            spaceAfter=8,
        ),
        "section": ParagraphStyle(
            "PacPdfSection",
            parent=base["Heading2"],
            fontSize=12,
            textColor=TITLE_COLOR,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "PacPdfBody",
            parent=base["BodyText"],
            fontSize=9,
            leading=12,
        ),
        "muted": ParagraphStyle(
            "PacPdfMuted",
            parent=base["BodyText"],
            fontSize=8,
            textColor=MUTED,
            leading=10,
        ),
    }


def _kv_table(rows: list[tuple[str, str]], *, col_widths: tuple[float, float] = (45 * mm, 125 * mm)) -> Table:
    data = [[Paragraph(f"<b>{label}</b>", _styles()["body"]), Paragraph(_text(value), _styles()["body"])] for label, value in rows]
    table = Table(data, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, LINE_COLOR),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _bullet_list(items: list[str]) -> list[Any]:
    flow: list[Any] = []
    style = _styles()["body"]
    for item in items:
        if item.strip():
            flow.append(Paragraph(f"• {_text(item, max_len=800)}", style))
    return flow


def _append_section(story: list[Any], title: str, blocks: list[Any]) -> None:
    if not blocks:
        return
    story.append(Paragraph(title, _styles()["section"]))
    story.extend(blocks)
    story.append(Spacer(1, 4 * mm))


def _plan_identification_rows(plan: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        ("Código", _text(plan.get("code"))),
        ("Título", _text(plan.get("title"))),
        ("Status", STATUS_LABELS.get(str(plan.get("status") or ""), _text(plan.get("status")))),
        ("Severidade", SEVERITY_LABELS.get(str(plan.get("severity") or ""), _text(plan.get("severity")))),
        ("Escopo NC", SCOPE_LABELS.get(str(plan.get("nonconformity_scope") or ""), _text(plan.get("nonconformity_scope")))),
        ("Filial", _text(plan.get("branch_code"))),
        ("Cliente", _text(plan.get("customer_name"))),
        ("Produto", _material_label(plan)),
        ("Lote", _text(plan.get("batch_number"))),
        ("Departamento", _text(plan.get("department"))),
        ("Modo de falha", _text(plan.get("failure_mode"))),
        ("Categoria do problema", _text(plan.get("problem_category"))),
        ("Causa raiz (categoria)", _text(plan.get("root_cause_category"))),
        ("Responsável", _text(plan.get("owner_user_id"))),
        ("Detectado em", _format_date(plan.get("detected_at"))),
        ("Registrado em", _format_date(plan.get("created_at"))),
    ]

def _ishikawa_items(ishikawa: dict[str, Any] | None) -> list[str]:
    if not ishikawa:
        return []
    items: list[str] = []
    for key, label in ISHAKAWA_LABELS.items():
        for cause in ishikawa_category_lines(ishikawa.get(key)):
            items.append(f"{label}: {cause}")
    notes = ishikawa.get("notes")
    if notes and str(notes).strip():
        items.append(f"Observações: {notes}")
    return items


def _five_whys_items(five_whys: dict[str, Any] | None) -> list[str]:
    if not five_whys:
        return []
    items: list[str] = []
    items.extend(
        five_whys_track_lines(five_whys.get("occurrence_whys"), track_label="Ocorrência")
    )
    items.extend(
        five_whys_track_lines(five_whys.get("detection_whys"), track_label="Detecção")
    )
    root = five_whys.get("root_cause")
    if root and str(root).strip():
        items.append(f"Causa raiz: {root}")
    return items


def _actions_table(actions: list[dict[str, Any]]) -> Table | None:
    if not actions:
        return None
    header = ["Tipo", "Descrição", "Responsável", "Prazo", "Status"]
    rows = [
        [
            ACTION_TYPE_LABELS.get(str(item.get("action_type") or ""), _text(item.get("action_type"))),
            _text(item.get("description"), max_len=500),
            _text(item.get("responsible_name") or item.get("responsible_user_id")),
            _format_date(item.get("due_date")),
            ACTION_STATUS_LABELS.get(str(item.get("status") or ""), _text(item.get("status"))),
        ]
        for item in actions
    ]
    table = Table(
        [header, *rows],
        colWidths=[24 * mm, 68 * mm, 28 * mm, 22 * mm, 22 * mm],
        hAlign="LEFT",
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TITLE_COLOR),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, LINE_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _evidence_items(evidences: list[dict[str, Any]]) -> list[str]:
    items: list[str] = []
    for evidence in evidences:
        label = evidence.get("file_name") or evidence.get("description") or evidence.get("type")
        when = _format_date(evidence.get("created_at"))
        items.append(f"{_text(label)} ({when})")
    return items


def _build_pdf(story: list[Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="PAC Qualidade",
    )
    doc.build(story)
    return buffer.getvalue()


def build_quality_action_plan_pdf(detail: dict[str, Any]) -> bytes:
    plan = detail.get("plan") or {}
    styles = _styles()
    story: list[Any] = [
        Paragraph("Plano de Ação — Qualidade", styles["title"]),
        Paragraph(f"Exportado em {_format_date(datetime.now())}", styles["muted"]),
        Spacer(1, 4 * mm),
    ]

    _append_section(story, "Identificação", [_kv_table(_plan_identification_rows(plan))])

    problem = _text(plan.get("reported_problem"))
    if problem != "—":
        _append_section(story, "Problema relatado", _bullet_list([problem]))

    ishikawa_items = _ishikawa_items(detail.get("ishikawa"))
    _append_section(story, "Ishikawa (6M)", _bullet_list(ishikawa_items))

    five_whys_items = _five_whys_items(detail.get("five_whys"))
    _append_section(story, "5 Porquês", _bullet_list(five_whys_items))

    actions_table = _actions_table(detail.get("actions") or [])
    if actions_table is not None:
        _append_section(story, "Ações", [actions_table])

    effectiveness_status = EFFECTIVENESS_LABELS.get(
        str(plan.get("effectiveness_status") or ""),
        _text(plan.get("effectiveness_status")),
    )
    _append_section(
        story,
        "Eficácia",
        [
            _kv_table(
                [
                    ("Status", effectiveness_status),
                    ("Verificado em", _format_date(plan.get("effectiveness_verified_at"))),
                    ("Observações", _text(plan.get("effectiveness_notes"))),
                ]
            )
        ],
    )

    evidence_items = _evidence_items(detail.get("evidences") or [])
    _append_section(story, "Evidências", _bullet_list(evidence_items))

    return _build_pdf(story)


def build_rnc_8d_pdf(detail: dict[str, Any]) -> bytes:
    plan = detail.get("plan") or {}
    payload = plan.get("template_payload") or {}
    if not isinstance(payload, dict):
        payload = {}

    nc = payload.get("nc_description") or {}
    classification = payload.get("classification") or {}
    effectiveness = payload.get("effectiveness") or {}
    preventive = payload.get("preventive") or {}
    containment_rows = payload.get("containment") or []
    documentation = payload.get("documentation_updates") or []
    team = detail.get("team_members") or []
    five_whys = detail.get("five_whys") or {}
    actions = detail.get("actions") or []

    branch = plan.get("branch_code") or "01"
    styles = _styles()
    story: list[Any] = [
        Paragraph("Relatório 8D — Materiais Adquiridos", styles["title"]),
        Paragraph(f"RNC {_text(plan.get('client_nc_registry'))} · exportado em {_format_date(datetime.now())}", styles["muted"]),
        Spacer(1, 4 * mm),
    ]

    identification_rows = [
        ("Registro NC cliente", _text(plan.get("client_nc_registry"))),
        ("Fornecedor", _text(payload.get("supplier_name") or SUPPLIER_BY_BRANCH.get(branch))),
        ("Material", _material_label(plan)),
        ("Especificação", _text(payload.get("material_specification"))),
        ("Pedido de compra", _text(payload.get("purchase_order"))),
        ("Nota fiscal", _text(payload.get("invoice_number"))),
        ("Quantidade defeituosa", _text(payload.get("defective_quantity"))),
        ("Cliente final", _text(plan.get("customer_name") if classification.get("end_customer") else None)),
        ("Contato", _text(plan.get("customer_contact"))),
        ("Lote cliente", _text(payload.get("client_batch"))),
        ("Lote interno", _text(plan.get("batch_number"))),
        ("Disposição", _text(payload.get("disposition"))),
    ]
    _append_section(story, "D1 — Identificação", [_kv_table(identification_rows)])

    nc_rows = [
        ("Característica", _text(nc.get("characteristic"))),
        ("Especificado", _text(nc.get("specified"))),
        ("Verificado", _text(nc.get("verified") or plan.get("reported_problem"))),
        ("Observações", _text(nc.get("observations") or payload.get("observations"))),
    ]
    _append_section(story, "D2 — Descrição da NC", [_kv_table(nc_rows)])

    team_lines = []
    for member in team:
        role = "Líder" if member.get("is_leader") else "Membro"
        team_lines.append(
            f"{role}: {_text(member.get('member_name'))} · {_text(member.get('department'))}"
        )
    _append_section(story, "D3 — Equipe", _bullet_list(team_lines))

    containment_lines = []
    area_labels = {
        "end_customer": "Cliente final",
        "client_plant": "Planta do cliente",
        "supplier": "Fornecedor",
    }
    for row in containment_rows:
        area = area_labels.get(str(row.get("area") or ""), _text(row.get("area")))
        containment_lines.append(
            f"{area}: qtd {_text(row.get('quantity'))} · ação {_text(row.get('action_plan'))} · "
            f"resp. {_text(row.get('responsible'))} · {_format_date(row.get('date'))}"
        )
    _append_section(story, "D4 — Contenção", _bullet_list(containment_lines))

    _append_section(story, "D4 — Análise de causa", _bullet_list(_five_whys_items(five_whys)))

    corrective = [
        action
        for action in actions
        if action.get("action_type") == "corrective" or action.get("cause_track")
    ]
    actions_table = _actions_table(corrective or actions)
    if actions_table is not None:
        _append_section(story, "D5 — Ações corretivas", [actions_table])

    effectiveness_rows = [
        ("Como foi resolvido", _text(effectiveness.get("resolved_how") or plan.get("effectiveness_notes"))),
        ("Material OK em", _format_date(effectiveness.get("ok_material_date"))),
        ("Identificação peças novas", _text(effectiveness.get("new_parts_identification"))),
        ("Responsável verificação", _text(effectiveness.get("verification_responsible"))),
        ("Data verificação", _format_date(effectiveness.get("verification_date"))),
        (
            "Status PAC",
            EFFECTIVENESS_LABELS.get(
                str(plan.get("effectiveness_status") or ""),
                _text(plan.get("effectiveness_status")),
            ),
        ),
    ]
    _append_section(story, "D6 — Verificação de eficácia", [_kv_table(effectiveness_rows)])

    preventive_rows = [
        ("Como evitar no futuro", _text(preventive.get("how_avoid_future"))),
        ("Outros processos/produtos", _text(preventive.get("other_processes_products"))),
        ("Responsável avaliação", _text(preventive.get("evaluation_responsible"))),
        ("Conclusão avaliação", _format_date(preventive.get("evaluation_completion_date"))),
    ]
    _append_section(story, "D7 — Ação preventiva", [_kv_table(preventive_rows)])

    documentation_lines = [
        f"{_text(item.get('document'))} · resp. {_text(item.get('responsible'))} · {_format_date(item.get('date'))}"
        for item in documentation
        if any(item.get(key) for key in ("document", "responsible", "date"))
    ]
    _append_section(story, "D8 — Padronização / documentação", _bullet_list(documentation_lines))

    evidence_items = _evidence_items(detail.get("evidences") or [])
    _append_section(story, "Anexos / evidências", _bullet_list(evidence_items))

    return _build_pdf(story)
