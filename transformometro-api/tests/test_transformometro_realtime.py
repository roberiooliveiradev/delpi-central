import pytest

from tm_app.application.services.transformometro_realtime_notify import (
    infer_section_key,
    room_key,
)


def test_room_key():
    assert room_key("processo", "abc-123") == "processo:abc-123"


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
