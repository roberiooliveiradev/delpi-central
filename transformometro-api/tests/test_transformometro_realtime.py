import pytest

from tm_app.application.services.transformometro_realtime_notify import (
    _related_rooms,
    catalog_room,
    infer_section_key,
    room_key,
)


def test_room_key():
    assert room_key("processo", "abc-123") == "processo:abc-123"
    assert catalog_room("processo") == "catalog:processo"


def test_infer_section_key_diagram_and_decomposition():
    assert infer_section_key("processo", "diagram.macro.updated") == "diagrama_macro"
    assert infer_section_key("processo", "diagram.macro.imported_bpmn") == "diagrama_macro"
    assert infer_section_key("processo", "decomposition.updated") == "decomposicao"
    assert infer_section_key("processo_instancia", "decomposition.scope.updated") == "decomposicao_escopo"
    assert infer_section_key("revisao", "decomposition.overlay.updated") == "decomposicao_overlay"


def test_infer_section_key_revisao_medicao():
    assert infer_section_key("medicao", "upsert") == "medicao"


def test_infer_section_key_processo_arquivos():
    assert infer_section_key("processo", "processo.arquivo.created") == "arquivos"
    assert infer_section_key("processo", "processo.arquivo.deleted") == "arquivos"


def test_infer_section_key_evidencias_and_matriz():
    assert infer_section_key("revisao", "revisao.evidencia.created") == "evidencias"
    assert infer_section_key("revisao", "revisao.evidencia.deleted") == "evidencias"
    assert infer_section_key("revisao", "matrix.updated") == "matriz"


def test_infer_section_key_crud_by_entity():
    assert infer_section_key("processo_instancia", "create") == "instancia"
    assert infer_section_key("revisao", "create") == "vigencia"
    assert infer_section_key("investimento", "delete") == "investimentos"


def test_related_rooms_revisao_fans_out_to_processo():
    rooms = _related_rooms(
        "revisao",
        "rev-1",
        {"processo_id": "proc-1", "instancia_id": "inst-1"},
    )
    assert room_key("revisao", "rev-1") in rooms
    assert room_key("processo", "proc-1") in rooms
    assert room_key("processo_instancia", "inst-1") in rooms
    assert catalog_room("processo") in rooms
    assert catalog_room("dashboard") in rooms


def test_related_rooms_instancia_fans_out_to_processo():
    rooms = _related_rooms(
        "processo_instancia",
        "inst-1",
        {"processo_id": "proc-1"},
    )
    assert room_key("processo", "proc-1") in rooms
    assert catalog_room("processo") in rooms


def test_related_rooms_investimento_fans_out_to_revisao():
    rooms = _related_rooms(
        "investimento",
        "inv-1",
        {"revisao_id": "rev-1"},
    )
    assert room_key("revisao", "rev-1") in rooms
    assert catalog_room("dashboard") in rooms


def test_related_rooms_medicao_fans_out_to_processo_and_instancia():
    rooms = _related_rooms(
        "medicao",
        "med-1",
        {
            "revisao_id": "rev-1",
            "instancia_id": "inst-1",
            "processo_id": "proc-1",
        },
    )
    assert room_key("medicao", "med-1") in rooms
    assert room_key("revisao", "rev-1") in rooms
    assert room_key("processo_instancia", "inst-1") in rooms
    assert room_key("processo", "proc-1") in rooms
    assert catalog_room("dashboard") in rooms


def test_related_rooms_investimento_with_scope_fans_out_to_processo():
    rooms = _related_rooms(
        "investimento",
        "inv-1",
        {
            "revisao_id": "rev-1",
            "instancia_id": "inst-1",
            "processo_id": "proc-1",
        },
    )
    assert room_key("processo", "proc-1") in rooms
    assert room_key("processo_instancia", "inst-1") in rooms


def test_enrich_realtime_scope_payload_revisao_looks_up_processo(monkeypatch):
    from tm_app.application.services import transformometro_realtime_notify as mod

    class FakeRepo:
        def get(self, _rid):
            return {"processo_id": "proc-9", "instancia_id": "inst-9"}

    monkeypatch.setattr(
        "tm_app.infrastructure.persistence.repositories.revisao_repository.RevisaoRepository",
        FakeRepo,
    )
    body = mod.enrich_realtime_scope_payload("revisao", "rev-9", {"overrides": 2})
    assert body["processo_id"] == "proc-9"
    assert body["instancia_id"] == "inst-9"


def test_enrich_realtime_scope_payload_instancia_looks_up_processo(monkeypatch):
    from tm_app.application.services import transformometro_realtime_notify as mod

    class FakeRepo:
        def get(self, _iid):
            return {"processo_id": "proc-8"}

    monkeypatch.setattr(
        "tm_app.infrastructure.persistence.repositories.processo_instancia_repository.ProcessoInstanciaRepository",
        FakeRepo,
    )
    body = mod.enrich_realtime_scope_payload(
        "processo_instancia", "inst-8", {"inherit_all": True}
    )
    assert body["processo_id"] == "proc-8"


def test_related_rooms_recurso_custo_fans_out_to_recurso():
    rooms = _related_rooms(
        "recurso_custo",
        "custo-1",
        {"recurso_compartilhado_id": "rec-1"},
    )
    assert room_key("recurso", "rec-1") in rooms
    assert catalog_room("recurso") in rooms


def test_related_rooms_json_backup_fans_out_all_catalogs():
    rooms = _related_rooms("json_backup", "00000000-0000-0000-0000-000000000000", {})
    assert catalog_room("processo") in rooms
    assert catalog_room("filial") in rooms
    assert catalog_room("setor") in rooms
    assert catalog_room("recurso") in rooms
    assert catalog_room("dashboard") in rooms
