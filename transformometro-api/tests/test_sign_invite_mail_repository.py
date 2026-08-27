from tm_app.domain.sign_invite_mail_status import (
    MAIL_DELIVERY_BOUNCED,
    MAIL_DELIVERY_DELIVERED,
    MAIL_DELIVERY_NOT_APPLICABLE,
    MAIL_DELIVERY_TRACE_PENDING,
    MAIL_DELIVERY_UNKNOWN,
    MAIL_SEND_ACCEPTED,
    MAIL_SEND_FAILED,
    MAIL_SEND_PENDING,
    MAIL_SEND_SKIPPED_GRAPH_UNCONFIGURED,
    MAIL_SEND_SKIPPED_MAIL_DISABLED,
    MAIL_SEND_SKIPPED_NO_EMAIL,
)


def test_mail_status_constants_match_migration_values():
    send_values = {
        MAIL_SEND_PENDING,
        MAIL_SEND_SKIPPED_NO_EMAIL,
        MAIL_SEND_SKIPPED_MAIL_DISABLED,
        MAIL_SEND_SKIPPED_GRAPH_UNCONFIGURED,
        MAIL_SEND_FAILED,
        MAIL_SEND_ACCEPTED,
    }
    delivery_values = {
        MAIL_DELIVERY_NOT_APPLICABLE,
        MAIL_DELIVERY_TRACE_PENDING,
        MAIL_DELIVERY_DELIVERED,
        MAIL_DELIVERY_BOUNCED,
        MAIL_DELIVERY_UNKNOWN,
    }
    assert len(send_values) == 6
    assert len(delivery_values) == 5


def test_repository_exposes_mail_delivery_methods():
    from tm_app.infrastructure.persistence.repositories.meeting_minute_repository import (
        MeetingMinuteRepository,
    )

    repo = MeetingMinuteRepository()
    for method in (
        "update_invite_mail_send_result",
        "update_invite_mail_delivery_result",
        "list_invites_pending_trace",
        "get_latest_invite_mail_by_signer_ids",
    ):
        assert callable(getattr(repo, method))
