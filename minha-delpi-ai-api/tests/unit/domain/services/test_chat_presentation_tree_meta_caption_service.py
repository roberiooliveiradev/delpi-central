from app.domain.services.chat_presentation_tree_meta_caption_service import (
    ChatPresentationTreeMetaCaptionService,
)


def test_enrich_builds_meta_caption_from_column_labels():
    presentation = {
        "type": "tree",
        "root": {
            "id": "branch:01",
            "label": "Filial 01",
            "meta": {
                "available_quantity": 80.0,
                "current_quantity": 100.0,
                "committed_quantity": 20.0,
            },
            "children": [
                {
                    "id": "wh:01:01",
                    "label": "Armazém 01",
                    "meta": {
                        "available_quantity": 80.0,
                        "current_quantity": 100.0,
                        "committed_quantity": 20.0,
                    },
                }
            ],
        },
    }

    ChatPresentationTreeMetaCaptionService.enrich(presentation)

    branch_caption = presentation["root"]["metaCaption"]
    warehouse_caption = presentation["root"]["children"][0]["metaCaption"]

    assert "Qtd. disponível:" in branch_caption
    assert "Qtd. atual:" in warehouse_caption
    assert presentation["root"]["meta"]["quantity"] == 80.0
    assert presentation["root"]["meta"]["unit"] == "un."


def test_enrich_preserves_existing_meta_caption():
    presentation = {
        "type": "tree",
        "root": {
            "id": "node",
            "label": "Nó",
            "metaCaption": "Legenda customizada",
            "meta": {"available_quantity": 1.0},
        },
    }

    ChatPresentationTreeMetaCaptionService.enrich(presentation)

    assert presentation["root"]["metaCaption"] == "Legenda customizada"
