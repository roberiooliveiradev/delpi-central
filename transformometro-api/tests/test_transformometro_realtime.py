import pytest

from tm_app.application.services.transformometro_realtime_notify import (
    infer_section_key,
    room_key,
)


def test_room_key():
    assert room_key("processo", "abc-123") == "processo:abc-123"


def test_infer_section_key_diagram():
    assert infer_section_key("processo", "diagram.macro.updated") == "diagrama_macro"


def test_infer_section_key_revisao_medicao():
    assert infer_section_key("medicao", "upsert") == "medicao"
