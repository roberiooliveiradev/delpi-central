from app.application.services.chat_structure_comparison_service import (
    ChatStructureComparisonService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


def _structure_assistant_message(
    product_code: str,
    items: list[dict],
    *,
    content_lines: list[str] | None = None,
) -> dict:
    content = ""

    if content_lines:
        content = "Estrutura do produto\n" + "\n".join(content_lines)

    return {
        "role": "assistant",
        "content": content,
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "path": f"/products/{product_code}/structure",
                        "responsePreview": __import__("json").dumps({"items": items}),
                    },
                }
            ]
        },
    }


def test_build_comparison_from_tool_previews():
    messages = [
        {"role": "user", "content": "estrutura do produto 90260077"},
        _structure_assistant_message(
            "90260077",
            [
                {"code": "50230002", "description": "CB14AMAR", "type": "PI", "unit": "MI", "quantity": 1},
                {"code": "50230005", "description": "CB14AZUL", "type": "PI", "unit": "MI", "quantity": 1},
            ],
            content_lines=[
                "50230002 — CB14AMAR (PI) [MI] | Qtd: 1.0",
                "50230005 — CB14AZUL (PI) [MI] | Qtd: 1.0",
            ],
        ),
        {"role": "user", "content": "estrutura do 90260088"},
        _structure_assistant_message(
            "90260088",
            [
                {"code": "50230002", "description": "CB14AMAR", "type": "PI", "unit": "MI", "quantity": 1},
                {"code": "50210053", "description": "CB18AMAR", "type": "PI", "unit": "MI", "quantity": 1},
            ],
            content_lines=[
                "50230002 — CB14AMAR (PI) [MI] | Qtd: 1.0",
                "50210053 — CB18AMAR (PI) [MI] | Qtd: 1.0",
            ],
        ),
    ]

    answer = ChatStructureComparisonService.build_comparison_answer(
        "compare as duas estruturas e traga insights",
        messages,
    )

    assert answer is not None
    assert "90260077" in answer
    assert "90260088" in answer
    assert "50230002" in answer
    assert "50210053" in answer
    assert "**Insights**" in answer
    assert "compra" not in answer.lower()


def test_build_comparison_from_text_only():
    messages = [
        {"role": "user", "content": "estrutura do 90260077"},
        {
            "role": "assistant",
            "content": (
                "Estrutura do produto\n"
                "50230002 — CB14AMAR (PI) [MI] | Qtd: 1.0\n"
                "50230005 — CB14AZUL (PI) [MI] | Qtd: 1.0"
            ),
            "metadata": {},
        },
        {"role": "user", "content": "estrutura do 90260088"},
        {
            "role": "assistant",
            "content": (
                "Estrutura do produto\n"
                "50210053 — CB18AMAR (PI) [MI] | Qtd: 1.0"
            ),
            "metadata": {},
        },
    ]

    answer = ChatStructureComparisonService.build_comparison_answer(
        "comprare as duas estruturas e traga insights",
        messages,
    )

    assert answer is not None
    assert "90260077" in answer
    assert "50230005" in answer


def test_normalize_comprare_does_not_become_compra():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "comprare as duas estruturas"
    )
    assert "compra" not in normalized.split()
    assert "compare" in normalized
