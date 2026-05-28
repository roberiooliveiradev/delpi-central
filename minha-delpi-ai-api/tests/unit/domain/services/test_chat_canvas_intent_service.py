from app.domain.services.chat_canvas_intent_service import ChatCanvasIntentService


def test_detects_coloque_na_lousa():
    assert ChatCanvasIntentService.is_canvas_placement_request("coloque na lousa")


def test_detects_coloque_em_canva_as_lousa():
    assert ChatCanvasIntentService.is_canvas_placement_request("coloque em canva")


def test_detects_manda_para_canvas():
    assert ChatCanvasIntentService.is_canvas_placement_request("manda isso para o canvas")


def test_ignores_external_canva_site():
    assert not ChatCanvasIntentService.is_canvas_placement_request(
        "como criar um post no canva.com?"
    )


def test_ignores_unrelated_message():
    assert not ChatCanvasIntentService.is_canvas_placement_request(
        "qual o estoque do produto 10080001?"
    )
