from app.domain.services.chat_product_structure_presentation_service import (
    ChatProductStructurePresentationService,
)


def _sample_90260077():
    return {
        "root": {
            "code": "90260077",
            "description": "CHICOTE DE LIGACAO",
            "type": "PA",
            "unit": "MI",
            "quantity": 1,
        },
        "items": [
            {
                "code": "50230002",
                "description": "CB14AMAR-00180/25/07-0000-0914",
                "type": "PI",
                "unit": "MI",
                "quantity": 1,
                "components": [
                    {
                        "code": "10030048",
                        "description": "CABO EPR 130°C 14AWG AR NBR 9114",
                        "type": "MP",
                        "unit": "MT",
                        "quantity": 180,
                    },
                    {
                        "code": "10080109",
                        "description": "TERM. FASTON 6,30X0,80",
                        "type": "MP",
                        "unit": "PC",
                        "quantity": 1000,
                    },
                ],
            },
            {
                "code": "50230037",
                "description": "CB18PRET-00211/25/06-0000-6314",
                "type": "PI",
                "unit": "MI",
                "quantity": 1,
                "components": [
                    {
                        "code": "10380035",
                        "description": "CABO EPR 125/150°C 18AWG PT",
                        "type": "MP",
                        "unit": "MT",
                        "quantity": 210,
                    },
                ],
            },
        ],
    }


def _sample_90260088():
    return {
        "root": {
            "code": "90260088",
            "description": "CHICOTE EPR SINGELO 270MM",
            "type": "PA",
            "unit": "MI",
            "quantity": 1,
        },
        "items": [
            {
                "code": "50210053",
                "description": "CB18AMAR-00200/20/20-0000-0000",
                "type": "PI",
                "unit": "MI",
                "quantity": 1,
                "components": [
                    {
                        "code": "10380037",
                        "description": "CABO EPR 125/150°C 18AWG AR",
                        "type": "MP",
                        "unit": "MT",
                        "quantity": 230,
                    },
                ],
            },
            {
                "code": "50210125",
                "description": "CB18PRET-00240/20/20-0000-0000",
                "type": "PI",
                "unit": "MI",
                "quantity": 1,
                "components": [
                    {
                        "code": "10380035",
                        "description": "CABO EPR 125/150°C 18AWG PT",
                        "type": "MP",
                        "unit": "MT",
                        "quantity": 240,
                    },
                ],
            },
        ],
    }


def test_format_markdown_includes_hierarchy_sections():
    markdown = ChatProductStructurePresentationService.format_markdown(_sample_90260077())

    assert markdown
    assert "**Produto pai**" in markdown
    assert "**Componentes nível 1**" in markdown
    assert "**Estrutura detalhada**" in markdown
    assert "90260077" in markdown
    assert "50230002" in markdown
    assert "10030048" in markdown
    assert "TERM. FASTON" in markdown


def test_format_markdown_flat_detailed_for_single_mp_per_intermediate():
    markdown = ChatProductStructurePresentationService.format_markdown(_sample_90260088())

    assert "| Pai | Componente |" in markdown
    assert "10380037" in markdown


def test_extract_length_from_intermediate_code():
    length = ChatProductStructurePresentationService.extract_length_from_intermediate(
        "CB18PRET-00211/25/06-0000-6314"
    )

    assert length == 211
