from app.application.services.chat_grounded_narrate_answer_service import (
    ChatGroundedNarrateAnswerService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()


def _structure_tool_meta():
    return {
        "ok": True,
        "path": "/products/90260149/structure",
        "humanizedSummary": {
            "titulo": "Estrutura do produto 90260149",
            "linhas": [
                "6 itens intermediários (PI) na estrutura.",
                "Cada PI usa cabo CB16 em cor distinta.",
            ],
        },
    }


def test_build_answer_from_humanized_summary_when_grounded_narrate():
    previous = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": _structure_tool_meta(),
                    }
                ]
            },
        }
    ]
    workspace = {
        "turnGrounding": {"status": "grounded"},
        "workingMemory": {
            "lastResultExcerpt": {
                "title": "Resultado da consulta",
                "rowCount": 6,
                "topKeys": ["50230130", "50230131"],
            }
        },
    }
    tool_context = {
        "groundedNarrate": True,
        "turnGrounding": workspace["turnGrounding"],
    }

    answer = ChatGroundedNarrateAnswerService.build_answer(
        "o que me diz sobre os itens?",
        previous,
        workspace_context=workspace,
        tool_context=tool_context,
    )

    assert answer
    assert "6 itens" in answer.lower() or "estrutura" in answer.lower()
    assert "reformular" not in answer.lower()


def test_build_answer_from_excerpt_top_keys_fallback():
    workspace = {
        "workingMemory": {
            "lastResultExcerpt": {
                "title": "Resultado da consulta",
                "rowCount": 6,
                "topKeys": ["50230130", "50230131", "50230132"],
            }
        },
    }

    answer = ChatGroundedNarrateAnswerService.build_answer(
        "o que me diz sobre os itens?",
        [],
        workspace_context=workspace,
        tool_context={"groundedNarrate": True},
    )

    assert answer
    assert "50230130" in answer
    assert "6" in answer
    assert "reformular" not in answer.lower()
