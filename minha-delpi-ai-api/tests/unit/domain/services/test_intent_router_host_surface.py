"""Superfície do host na classificação de intenção.

No editor TV, «escreva um texto "Bem-vindos"» é comando de slide, não redação.
Sem o hostContext no classify, o roteador marcava text_task e o turno nunca
chegava à tool do copiloto.
"""

from __future__ import annotations

import pytest

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_intent_router_service import ChatIntentRouterService

configure_domain_infrastructure_ports()

_TV_WORKSPACE = {
    "skills": {"tvDashboardCopilot": True},
    "tvDashboardHostContext": {
        "surface": "tv-dashboard",
        "playlistId": "pl-1",
        "slideId": "sl-1",
    },
}


@pytest.mark.parametrize(
    "message",
    [
        'escreva um texto "Bem-vindos"',
        "crie um texto de boas-vindas",
        "crie uma seção nova",
    ],
)
def test_editor_surface_does_not_classify_command_as_text_task(message: str):
    assert ChatIntentRouterService.classify(message).intent in {
        "text_task",
        "email_task",
    }, "sem host o roteador trata como redação (baseline do teste)"

    route = ChatIntentRouterService.classify(message, workspace_context=_TV_WORKSPACE)

    assert route.intent not in {"text_task", "email_task"}


def test_explicit_email_stays_text_task_even_on_editor_surface():
    route = ChatIntentRouterService.classify(
        "escreva um email para o cliente sobre o atraso",
        workspace_context=_TV_WORKSPACE,
    )

    assert route.intent == "email_task"
