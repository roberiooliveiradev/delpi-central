"""Gate: rotas HTTP mutáveis do Transformômetro disparam notify realtime."""

from __future__ import annotations

from pathlib import Path

ROUTES_DIR = Path(__file__).resolve().parents[1] / "tm_app" / "interface" / "http" / "routes"

# Arquivos de rota com mutações de negócio que devem notificar WS.
MUTATING_ROUTE_FILES = (
    "crud_routes.py",
    # diagram_routes.py is intentionally absent: all legacy flowchart_v1
    # writes are locked (LEGACY_DIAGRAM_READ_ONLY), so the module no
    # longer mutates business state.
    "decomposition_routes.py",
    "dashboard_routes.py",
    "json_backup_routes.py",
    "process_file_routes.py",
    "process_document_routes.py",
    "revision_evidence_routes.py",
    # meeting_minutes_routes.py intentionally omitted: notify is owned by
    # MeetingMinutesService (shared Portal/TÉO/public path). See
    # test_meeting_minute_realtime_notify.py.
)

SERVICE_NOTIFY_OWNERS = (
    (
        "application/services/meeting_minutes_service.py",
        ("notify_entity_updated(",),
    ),
)

NOTIFY_MARKERS = (
    "notify_from_audit(",
    "notify_entity_updated(",
    "notify_catalog_updated(",
)


def test_mutating_route_modules_call_realtime_notify():
    missing: list[str] = []
    for name in MUTATING_ROUTE_FILES:
        path = ROUTES_DIR / name
        assert path.is_file(), f"arquivo de rota ausente: {name}"
        text = path.read_text(encoding="utf-8")
        if not any(marker in text for marker in NOTIFY_MARKERS):
            missing.append(name)
    assert not missing, (
        "Rotas mutáveis sem notify realtime: "
        + ", ".join(missing)
        + ". Toda mutação deve chamar notify_from_audit / notify_entity_updated / notify_catalog_updated."
    )


def test_service_owned_realtime_notify_modules():
    app_root = Path(__file__).resolve().parents[1] / "tm_app"
    missing: list[str] = []
    for relative, markers in SERVICE_NOTIFY_OWNERS:
        path = app_root / relative
        assert path.is_file(), f"serviço ausente: {relative}"
        text = path.read_text(encoding="utf-8")
        if not any(marker in text for marker in markers):
            missing.append(relative)
    assert not missing, (
        "Serviços donos de mutação sem notify realtime: " + ", ".join(missing)
    )


def test_crud_audit_passes_actor_client_id():
    text = (ROUTES_DIR / "crud_routes.py").read_text(encoding="utf-8")
    assert "client_id_from_request" in text
    assert "actor_client_id=" in text


def test_section_key_overlay_aligned_with_mfe():
    from tm_app.application.services.transformometro_realtime_notify import (
        infer_section_key,
    )

    assert infer_section_key("revisao", "decomposition.overlay.updated") == "decomposicao_revisao"
    assert infer_section_key("revisao", "diagram.overlay.updated") == "diagrama_revisao"
