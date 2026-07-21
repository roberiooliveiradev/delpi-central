from app.domain.services.chat_presentation_user_format_preference_service import (
    ChatPresentationUserFormatPreferenceService,
)


def test_normalize_from_message_detects_table_hint():
    result = ChatPresentationUserFormatPreferenceService.normalize_from_message(
        None,
        "mostre em tabela os saldos por filial",
    )

    assert result == "table"


def test_normalize_from_message_detects_painel_as_dashboard():
    result = ChatPresentationUserFormatPreferenceService.normalize_from_message(
        None,
        "painel de indicadores da engenharia",
    )

    assert result == "dashboard"


def test_resolve_effective_prefers_explicit_session_format():
    metadata = {"explicitSessionFormat": "table"}

    assert (
        ChatPresentationUserFormatPreferenceService.resolve_effective(metadata, None)
        == "table"
    )
