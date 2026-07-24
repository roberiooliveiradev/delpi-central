"""Gate: rotas HTTP mutáveis do Transformômetro disparam notify realtime."""

from __future__ import annotations

from pathlib import Path

ROUTES_DIR = Path(__file__).resolve().parents[1] / "tm_app" / "interface" / "http" / "routes"

# Arquivos de rota com mutações de negócio que devem notificar WS.
MUTATING_ROUTE_FILES = (
    "crud_routes.py",
    "diagram_routes.py",
    "decomposition_routes.py",
    "dashboard_routes.py",
    "json_backup_routes.py",
    "processo_arquivo_routes.py",
    "revisao_evidence_routes.py",
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
