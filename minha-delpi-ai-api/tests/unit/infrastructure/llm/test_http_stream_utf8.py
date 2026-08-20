from app.infrastructure.llm.http_stream_utf8 import (
    decode_stream_line,
    repair_utf8_mojibake,
)


def test_repair_common_pt_mojibake():
    assert repair_utf8_mojibake("vocÃª") == "você"
    assert repair_utf8_mojibake("posiÃ§Ãµes") == "posições"
    assert repair_utf8_mojibake("disponÃ­vel") == "disponível"
    assert repair_utf8_mojibake("saÃ­das") == "saídas"
    assert repair_utf8_mojibake("sequÃªncia") == "sequência"


def test_repair_leaves_clean_utf8_untouched():
    clean = "até você — posições disponíveis"
    assert repair_utf8_mojibake(clean) == clean


def test_decode_stream_line_empty():
    assert decode_stream_line(None) is None
    assert decode_stream_line(b"") is None
    assert decode_stream_line("") is None
