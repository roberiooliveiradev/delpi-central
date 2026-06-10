from app.domain.services.chat_presentation_story_service import (
    ChatPresentationStoryService,
)


def test_build_story_from_data_answer_metadata():
    metadata = {
        "path": "/products/90269001/stock",
        "dataAnswer": {
            "profileKey": "stock",
            "summary": {
                "answer": "Saldo confortável em duas filiais.",
                "meaning": "não há ruptura aparente",
                "riskLevel": "ok",
                "nextAction": "Conferir posição com disponível negativo.",
                "attention": ["Uma posição com empenho acima do físico."],
            },
            "facts": [{"text": "Total disponível: **150** un."}],
            "analysis": ["Concentração em Fil.01."],
            "recommendations": [
                {
                    "label": "Ver concentração por filial",
                    "query": "Mostrar concentração de estoque por filial",
                    "reason": "Priorizar onde o saldo está",
                }
            ],
            "limitations": ["Esta análise considera apenas os registros desta página."],
        },
        "textPresentation": {
            "markdown": "### Estoque do produto — 90269001\n\nResumo.",
        },
    }

    assert ChatPresentationStoryService.enrich_metadata(metadata) is True

    story = metadata.get("storyPresentation")

    assert isinstance(story, dict)
    assert story["type"] == "story"
    assert story["title"] == "Estoque do produto — 90269001"
    assert story["blocks"][0]["kind"] == "verdict"
    assert story["blocks"][0]["status"] == "ok"
    assert any(block.get("kind") == "recommendation" and block.get("query") for block in story["blocks"])
    assert any(block.get("kind") == "limitation" for block in story["blocks"])


def test_skips_story_when_data_answer_missing():
    metadata = {"path": "/products/90269001/stock"}

    assert ChatPresentationStoryService.enrich_metadata(metadata) is False
    assert "storyPresentation" not in metadata
