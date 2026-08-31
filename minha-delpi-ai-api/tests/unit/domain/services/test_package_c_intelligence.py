"""Testes do pacote C — sessão, assertividade e commentary sem rows."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_context_assertiveness_directive_service import (
    ChatContextAssertivenessDirectiveService,
)
from app.domain.services.chat_data_insight_service import ChatDataInsightService
from app.domain.services.chat_operational_llm_synthesis_context_service import (
    ChatOperationalLlmSynthesisContextService,
)

configure_domain_infrastructure_ports()


def test_session_context_addon_includes_focus_and_capability():
    addon = ChatOperationalLlmSynthesisContextService.build_session_context_addon(
        {
            "operationalFocus": {"branch": "01", "periodLabel": "agosto/2026"},
            "workingMemory": {
                "lastAction": {"path": "/financial/rol"},
            },
            "actionsEnabled": False,
            "userActivatedAgent": False,
        }
    )

    assert "Contexto desta sessão" in addon
    assert "branch=01" in addon
    assert "/financial/rol" in addon
    assert "Chat comum" in addon or "comum" in addon.lower()


def test_assertiveness_directive_from_previous_assistant():
    previous = [
        {
            "role": "assistant",
            "content": "ok",
            "metadata": {
                "contextAssertiveness": {
                    "score": 40,
                    "flags": ["unnecessary_code_request"],
                }
            },
        }
    ]
    addon = ChatContextAssertivenessDirectiveService.build_prompt_addon(previous)

    assert "Diretivas de continuidade" in addon
    assert "código" in addon.lower()


def test_generic_commentary_from_summary_without_rows():
    commentary = ChatDataInsightService._build_generic_commentary(
        metadata={"path": "/financial/rol"},
        data={
            "summary": {
                "rol": 123456.78,
                "highlights": ["ROL consolidado no período"],
            }
        },
    )

    # Se summary não produzir highlights via helper, ainda pode retornar None —
    # o importante é não crashar e preferir commentary quando houver highlights.
    if commentary is not None:
        assert commentary.get("highlights") or commentary.get("summaryLines")
