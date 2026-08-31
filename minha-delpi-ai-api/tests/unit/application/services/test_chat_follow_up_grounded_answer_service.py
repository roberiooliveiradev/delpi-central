from app.application.services.chat_follow_up_grounded_answer_service import (
    ChatFollowUpGroundedAnswerService,
)


_EXCERPT = {
    "title": "ROL do mês",
    "preview": "ROL consolidado: R$ 1.000.000,00",
    "rowCount": 1,
}


def test_challenge_answer_uses_excerpt_without_asking_period():
    answer = ChatFollowUpGroundedAnswerService.build_challenge_answer(
        workspace_context={
            "turnGrounding": {"stage": "grounded_challenge_result", "excerpt": _EXCERPT},
            "workingMemory": {
                "lastResultExcerpt": _EXCERPT,
                "lastAction": {
                    "path": "/financial/rol",
                    "params": {"start_date": "01-08-2026", "end_date": "28-08-2026"},
                },
            },
        }
    )
    assert answer
    assert "1.000.000" in answer or "ROL" in answer or "consolidado" in answer.lower()
    assert "preciso" not in answer.lower()
    assert ChatFollowUpGroundedAnswerService.challenge_suggestion_items()


def test_challenge_contrasts_consolidated_vs_branch_with_numbers():
    previous = [
        {
            "role": "assistant",
            "content": "ROL consolidado: R$ 10.000.000,00",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {"parameters": {}},
                        "metadata": {
                            "ok": True,
                            "kpiPresentation": {
                                "cards": [
                                    {"key": "rol", "label": "ROL", "value": 10000000.0}
                                ]
                            },
                        },
                    }
                ]
            },
        },
        {
            "role": "assistant",
            "content": "ROL filial 01: R$ 2.500.000,00",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {"parameters": {"branch": "01"}},
                        "metadata": {
                            "ok": True,
                            "kpiPresentation": {
                                "cards": [
                                    {"key": "rol", "label": "ROL", "value": 2500000.0}
                                ]
                            },
                        },
                    }
                ]
            },
        },
    ]
    answer = ChatFollowUpGroundedAnswerService.build_challenge_answer(
        workspace_context={
            "turnGrounding": {"stage": "grounded_challenge_result", "excerpt": _EXCERPT},
            "workingMemory": {
                "lastResultExcerpt": _EXCERPT,
                "lastAction": {
                    "path": "/financial/rol",
                    "params": {
                        "branch": "01",
                        "start_date": "01-08-2026",
                        "end_date": "28-08-2026",
                    },
                },
            },
        },
        previous_messages=previous,
    )
    assert answer
    assert "10.000.000" in answer
    assert "2.500.000" in answer
    assert "01" in answer
    assert "não" in answer.lower() or "nao" in answer.lower()


def test_challenge_contrasts_from_entity_like_previous_messages():
    """Histórico do chat chega como entidade (não dict) no prepare/finalize."""

    class _Msg:
        def __init__(self, role, content, metadata=None):
            self.role = role
            self.content = content
            self.metadata = metadata or {}

    previous = [
        _Msg("assistant", "**ROL:** R$ 4.229.441,28"),
        _Msg(
            "assistant",
            "Consulta filtrada pela filial 01.\n\n**ROL:** R$ 676.062,44",
            {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {"parameters": {"branch": "01"}},
                        "metadata": {"ok": True, "path": "/financial/rol"},
                    }
                ]
            },
        ),
    ]
    answer = ChatFollowUpGroundedAnswerService.build_challenge_answer(
        workspace_context={
            "turnGrounding": {
                "stage": "grounded_challenge_result",
                "excerpt": {"title": "ROL", "preview": "**ROL:** R$ 676.062,44"},
            },
            "workingMemory": {
                "lastAction": {
                    "path": "/financial/rol",
                    "params": {"branch": "01", "start_date": "01-08-2026", "end_date": "31-08-2026"},
                }
            },
        },
        previous_messages=previous,
    )
    assert answer
    assert "4.229.441" in answer
    assert "676.062" in answer
    """Histórico live costuma trazer só prosa — lastAction.branch marca o valor recente."""
    previous = [
        {"role": "assistant", "content": "**ROL:** R$ 4.229.441,28"},
        {
            "role": "assistant",
            "content": "Consulta filtrada pela filial 01.\n\n**ROL:** R$ 676.062,44",
        },
    ]
    answer = ChatFollowUpGroundedAnswerService.build_challenge_answer(
        workspace_context={
            "turnGrounding": {
                "stage": "grounded_challenge_result",
                "excerpt": {"title": "ROL", "preview": "**ROL:** R$ 676.062,44"},
            },
            "workingMemory": {
                "lastAction": {
                    "path": "/financial/rol",
                    "params": {"branch": "01", "start_date": "01-08-2026", "end_date": "31-08-2026"},
                }
            },
        },
        previous_messages=previous,
    )
    assert answer
    assert "4.229.441" in answer
    assert "676.062" in answer
    assert "01" in answer
    answer = ChatFollowUpGroundedAnswerService.build_clarify_answer(
        workspace_context={
            "turnGrounding": {
                "stage": "grounded_clarify_slot",
                "followUp": {"clarifySlot": "branch"},
            }
        }
    )
    assert answer
    assert "filial" in answer.lower()


def test_revise_ack_mentions_branch():
    ack = ChatFollowUpGroundedAnswerService.build_revise_ack(
        parameters={"branch": "01", "start_date": "01-08-2026", "end_date": "28-08-2026"}
    )
    assert ack
    assert "01" in ack
    assert "mantido" in ack.lower()


def test_revise_ack_marks_period_changed():
    ack = ChatFollowUpGroundedAnswerService.build_revise_ack(
        parameters={"branch": "01", "start_date": "01-08-2026", "end_date": "31-08-2026"},
        baseline_parameters={"start_date": "01-08-2025", "end_date": "28-08-2025"},
    )
    assert ack
    assert "ajustado" in ack.lower()


def test_period_compare_answer_builds_delta_and_next_steps():
    tool_calls = [
        {
            "name": "execute_external_action",
            "periodCompareRole": "baseline",
            "arguments": {
                "parameters": {
                    "start_date": "01-08-2026",
                    "end_date": "28-08-2026",
                    "branch": "01",
                },
                "selectionDiagnostics": {"periodCompareRole": "baseline"},
            },
            "metadata": {
                "ok": True,
                "kpiPresentation": {
                    "cards": [{"key": "rol", "label": "ROL", "value": 3000000.0}]
                },
            },
        },
        {
            "name": "execute_external_action",
            "periodCompareRole": "prior",
            "arguments": {
                "parameters": {
                    "start_date": "01-08-2025",
                    "end_date": "28-08-2025",
                    "branch": "01",
                },
                "selectionDiagnostics": {"periodCompareRole": "prior"},
            },
            "metadata": {
                "ok": True,
                "kpiPresentation": {
                    "cards": [{"key": "rol", "label": "ROL", "value": 2500000.0}]
                },
            },
        },
    ]
    workspace: dict = {}
    answer = ChatFollowUpGroundedAnswerService.build_period_compare_answer(
        tool_calls=tool_calls,
        workspace_context=workspace,
    )
    assert answer
    assert "2026" in answer and "2025" in answer
    assert "3.000.000" in answer
    assert "2.500.000" in answer
    assert "Variação" in answer or "alta" in answer.lower()
    assert "Próximos passos" in answer
    assert workspace.get("followUpSuggestions")


def test_period_compare_prior_label_follows_slot_kind():
    tool_calls = [
        {
            "name": "execute_external_action",
            "periodCompareRole": "baseline",
            "arguments": {
                "parameters": {
                    "start_date": "01-08-2026",
                    "end_date": "31-08-2026",
                    "branch": "01",
                },
            },
            "metadata": {
                "ok": True,
                "kpiPresentation": {
                    "cards": [{"key": "rol", "label": "ROL", "value": 100.0}]
                },
            },
        },
        {
            "name": "execute_external_action",
            "periodCompareRole": "prior",
            "arguments": {
                "parameters": {
                    "start_date": "01-07-2026",
                    "end_date": "31-07-2026",
                    "branch": "01",
                },
            },
            "metadata": {
                "ok": True,
                "kpiPresentation": {
                    "cards": [{"key": "rol", "label": "ROL", "value": 80.0}]
                },
            },
        },
    ]
    workspace = {
        "turnGrounding": {
            "followUp": {"slotDelta": {"period": "previous_period"}},
        }
    }
    answer = ChatFollowUpGroundedAnswerService.build_period_compare_answer(
        tool_calls=tool_calls,
        workspace_context=workspace,
    )
    assert answer
    assert "período anterior" in answer.lower()
    assert "ano anterior" not in answer.lower()

    yoy_workspace = {
        "turnGrounding": {
            "followUp": {"slotDelta": {"period": "previous_year_same_range"}},
        }
    }
    yoy_calls = [
        {
            **tool_calls[0],
            "arguments": {
                "parameters": {
                    "start_date": "01-08-2026",
                    "end_date": "28-08-2026",
                    "branch": "01",
                }
            },
        },
        {
            **tool_calls[1],
            "arguments": {
                "parameters": {
                    "start_date": "01-08-2025",
                    "end_date": "28-08-2025",
                    "branch": "01",
                }
            },
        },
    ]
    yoy = ChatFollowUpGroundedAnswerService.build_period_compare_answer(
        tool_calls=yoy_calls,
        workspace_context=yoy_workspace,
    )
    assert yoy
    assert "ano anterior" in yoy.lower()
