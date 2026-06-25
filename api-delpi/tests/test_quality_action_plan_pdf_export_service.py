from __future__ import annotations

from app.domain.services.quality_action_plans.quality_action_plan_pdf_export_service import (
    build_quality_action_plan_pdf,
    build_rnc_8d_pdf,
    plan_pdf_filename,
    rnc_8d_pdf_filename,
)


def _sample_detail() -> dict:
    return {
        "plan": {
            "id": "plan-001",
            "code": "PAC-2026-001",
            "title": "Oxidação em chicote silicone",
            "status": "in_progress",
            "severity": "high",
            "nonconformity_scope": "external",
            "branch_code": "01",
            "customer_name": "Cliente industrial",
            "product_code": "14297268",
            "product_description": "CHICOTE 3 SILICONE 150mm",
            "batch_number": "90262776",
            "reported_problem": "Falha visual na pintura do terminal.",
            "effectiveness_status": "pending",
            "created_at": "2026-06-01T10:00:00+00:00",
        },
        "ishikawa": {"method_process": "Parâmetro de forno incorreto"},
        "five_whys": {"why_1": "Pintura descascando", "root_cause": "Tempo de cura insuficiente"},
        "actions": [
            {
                "action_type": "corrective",
                "description": "Revisar receita de pintura",
                "responsible_name": "Qualidade",
                "due_date": "2026-06-15",
                "status": "in_progress",
            }
        ],
        "evidences": [{"file_name": "foto-nc.png", "created_at": "2026-06-02T12:00:00+00:00"}],
        "history": [],
    }


def test_plan_pdf_filename_sanitizes_code():
    assert plan_pdf_filename({"code": "PAC/001"}) == "PAC_PAC_001_resumo.pdf"


def test_rnc_8d_pdf_filename_prefers_client_registry():
    assert rnc_8d_pdf_filename({"client_nc_registry": "215571003"}) == "RNC_215571003_8D.pdf"


def test_build_quality_action_plan_pdf_returns_pdf_bytes():
    content = build_quality_action_plan_pdf(_sample_detail())
    assert content.startswith(b"%PDF")
    assert len(content) > 1500


def test_build_rnc_8d_pdf_returns_pdf_bytes():
    detail = _sample_detail()
    detail["plan"]["client_nc_registry"] = "215571003"
    detail["plan"]["customer_template"] = "rnc_8d"
    detail["plan"]["template_payload"] = {
        "purchase_order": "5500044658",
        "nc_description": {"characteristic": "Dimensional"},
        "containment": [{"area": "client_plant", "quantity": "120", "action_plan": "Segregar lote"}],
    }
    detail["team_members"] = [{"member_name": "Ana", "department": "Qualidade", "is_leader": True}]

    content = build_rnc_8d_pdf(detail)
    assert content.startswith(b"%PDF")
    assert len(content) > 1500
