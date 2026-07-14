from __future__ import annotations

from unittest.mock import patch

from app.application.services.audit_5s_portal_notification_service import (
    action_label_for_nc,
    audit_5s_portal_notifications_enabled,
    branch_portal_route,
    build_note_mention_copy,
    build_responsible_assigned_copy,
    format_note_text_html_with_mentions,
    format_note_text_plain_without_at,
    notify_nc_note_mentions,
    notify_nc_responsible_assigned,
    send_audit_5s_portal_notification,
    should_notify_note_mention,
    should_notify_responsible_assignment,
)


def test_audit_5s_portal_notifications_enabled_requires_core_api() -> None:
    with patch("app.application.services.audit_5s_portal_notification_service.settings") as settings:
        settings.AUDIT_5S_NOTIFICATIONS_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = "token"
        assert audit_5s_portal_notifications_enabled() is True


def test_audit_5s_portal_notifications_disabled_without_token() -> None:
    with patch("app.application.services.audit_5s_portal_notification_service.settings") as settings:
        settings.AUDIT_5S_NOTIFICATIONS_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = ""
        assert audit_5s_portal_notifications_enabled() is False


def test_should_notify_skips_same_user_and_self_assign() -> None:
    assert (
        should_notify_responsible_assignment(
            previous_user_id="u1",
            new_user_id="u1",
        )
        is False
    )
    assert (
        should_notify_responsible_assignment(
            previous_user_id=None,
            new_user_id="u1",
            actor_user_id="u1",
        )
        is False
    )
    assert (
        should_notify_responsible_assignment(
            previous_user_id=None,
            new_user_id="u2",
            actor_user_id="u1",
        )
        is True
    )


def test_branch_portal_route() -> None:
    assert branch_portal_route("01") == "/apps/auditoria-5s/filial-01/nc-board/my-pending"
    assert branch_portal_route("02") == "/apps/auditoria-5s/filial-02/nc-board/my-pending"


def test_send_audit_5s_portal_notification_posts_to_core_api() -> None:
    with patch("app.application.services.audit_5s_portal_notification_service.settings") as settings:
        settings.AUDIT_5S_NOTIFICATIONS_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = "token"

        with patch("httpx.Client") as client_cls:
            client = client_cls.return_value.__enter__.return_value
            client.post.return_value.status_code = 201

            sent = send_audit_5s_portal_notification(
                recipient_user_id="user-42",
                title="Você foi designado responsável por uma NC",
                message="Mensagem",
                action_target="/apps/auditoria-5s/filial-01",
                dedupe_key="audit5s:nc_responsible:nc-1:user-42",
                event_type="audit_5s_nc_responsible_assigned",
            )

    assert sent is True
    payload = client.post.call_args.kwargs["json"]
    assert payload["userIds"] == ["user-42"]
    assert payload["sourceApp"] == "auditoria-5s"
    assert payload["category"] == "auditoria_5s"
    assert payload["metadata"]["dedupeKey"] == "audit5s:nc_responsible:nc-1:user-42"


def test_notify_nc_responsible_assigned_skips_unchanged() -> None:
    with patch(
        "app.application.services.audit_5s_portal_notification_service.send_audit_5s_portal_notification"
    ) as send:
        result = notify_nc_responsible_assigned(
            nc_id="nc-1",
            recipient_user_id="user-42",
            branch_code="01",
            previous_user_id="user-42",
            actor_user_id="actor-1",
        )
    assert result is False
    send.assert_not_called()


def test_notify_nc_responsible_assigned_sends_on_change() -> None:
    with patch(
        "app.application.services.audit_5s_portal_notification_service.send_audit_5s_portal_notification",
        return_value=True,
    ) as send:
        result = notify_nc_responsible_assigned(
            nc_id="nc-1",
            recipient_user_id="user-42",
            branch_code="02",
            audit_code="A5S-2026-0001",
            criterion_code="S1-01",
            criterion_description="Ferramentas organizadas",
            area_name="Montagem",
            corrective_action="Comprar ferramentas",
            description="Falta de ferramentas no posto",
            due_date="2026-07-20",
            priority="high",
            previous_user_id=None,
            actor_user_id="actor-1",
            actor_name="Rodrigo",
        )
    assert result is True
    kwargs = send.call_args.kwargs
    assert kwargs["recipient_user_id"] == "user-42"
    assert kwargs["action_target"] == "/apps/auditoria-5s/filial-02/nc-board/my-pending"
    assert "Comprar ferramentas" in kwargs["title"]
    assert "Comprar ferramentas" in kwargs["message"]
    assert "20/07/2026" in kwargs["message"]
    assert "Alta" in kwargs["message"]
    assert kwargs["html_content"]
    assert "notification-note-bubble" in kwargs["html_content"]
    assert kwargs["dedupe_key"] == "audit5s:nc_responsible:nc-1:user-42"


def test_build_responsible_assigned_copy_includes_action_details() -> None:
    title, message, html_content = build_responsible_assigned_copy(
        actor_name="Rodrigo",
        corrective_action="Comprar ferramentas",
        description="Falta de ferramentas",
        area_name="Montagem",
        audit_code="A5S-2026-0001",
        criterion_code="S1-01",
        due_date="2026-07-20",
        priority="high",
    )
    assert 'ação "Comprar ferramentas"' in title
    assert "Rodrigo" in message
    assert "Prioridade: Alta" in message
    assert "Prazo: 20/07/2026" in message
    assert "<ul>" in html_content
    assert "Comprar ferramentas" in html_content


def test_format_note_mentions_strip_at_and_bold() -> None:
    plain = format_note_text_plain_without_at(
        "Mas @Rodrigo Josué isso já está se estendendo demais."
    )
    assert "@" not in plain
    assert "Rodrigo Josué" in plain
    html_note = format_note_text_html_with_mentions(
        "Mas @Rodrigo Josué isso já está se estendendo demais."
    )
    assert "@" not in html_note
    assert "<strong>Rodrigo Josué</strong>" in html_note


def test_action_label_for_nc_prefers_corrective_action() -> None:
    assert (
        action_label_for_nc(
            corrective_action="Comprar ferramentas",
            description="Falta de ferramenta",
        )
        == "Comprar ferramentas"
    )
    assert (
        action_label_for_nc(
            corrective_action=None,
            description="Falta de ferramenta",
        )
        == "Falta de ferramenta"
    )


def test_should_notify_note_mention_skips_self() -> None:
    assert (
        should_notify_note_mention(
            mentioned_user_id="u1",
            actor_user_id="u1",
        )
        is False
    )
    assert (
        should_notify_note_mention(
            mentioned_user_id="u2",
            actor_user_id="u1",
        )
        is True
    )


def test_build_note_mention_copy_includes_full_note() -> None:
    title, message, html_content = build_note_mention_copy(
        actor_name="Rodrigo",
        action_label="Comprar ferramentas",
        note_text="Combinamos prazo até sexta.",
    )
    assert title == "Você foi mencionado por Rodrigo"
    assert 'na ação "Comprar ferramentas"' in message
    assert "Combinamos prazo até sexta." in message
    assert 'class="notification-note-bubble"' in html_content
    assert "Combinamos prazo até sexta." in html_content
    assert "Rodrigo" in html_content


def test_notify_nc_note_mentions_sends_html_payload() -> None:
    with patch(
        "app.application.services.audit_5s_portal_notification_service.send_audit_5s_portal_notification",
        return_value=True,
    ) as send:
        sent = notify_nc_note_mentions(
            nc_id="nc-1",
            action_id="act-9",
            mentioned_user_ids=["user-42", "user-42", "actor-1"],
            note_text="Segue o combinado da visita.",
            branch_code="01",
            action_label="Comprar ferramentas",
            actor_user_id="actor-1",
            actor_name="Rodrigo",
            audit_code="A5S-2026-0001",
        )

    assert sent == 1
    kwargs = send.call_args.kwargs
    assert kwargs["recipient_user_id"] == "user-42"
    assert kwargs["action_target"] == "/apps/auditoria-5s/filial-01/nc-board/my-pending"
    assert kwargs["dedupe_key"] == "audit5s:nc_mention:act-9:user-42"
    assert kwargs["html_content"]
    assert "Segue o combinado da visita." in kwargs["message"]
    assert 'na ação "Comprar ferramentas"' in kwargs["message"]
    assert kwargs["metadata"]["actionId"] == "act-9"


def test_send_audit_5s_portal_notification_includes_html_when_provided() -> None:
    with patch("app.application.services.audit_5s_portal_notification_service.settings") as settings:
        settings.AUDIT_5S_NOTIFICATIONS_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = "token"

        with patch("httpx.Client") as client_cls:
            client = client_cls.return_value.__enter__.return_value
            client.post.return_value.status_code = 201

            sent = send_audit_5s_portal_notification(
                recipient_user_id="user-42",
                title="Você foi mencionado por Rodrigo",
                message="Texto",
                action_target="/apps/auditoria-5s/filial-01/nc-board",
                dedupe_key="audit5s:nc_mention:act-1:user-42",
                event_type="audit_5s_nc_note_mention",
                html_content="<p>oi</p><span class=\"notification-note-bubble\">nota</span>",
            )

    assert sent is True
    payload = client.post.call_args.kwargs["json"]
    assert payload["presentation"] == "html"
    assert payload["htmlContent"] == '<p>oi</p><span class="notification-note-bubble">nota</span>'
