from tm_app.application.services.mail_delivery_content_service import (
    MailDeliveryContentService,
    _content,
)


def setup_function() -> None:
    _content.cache_clear()


def test_all_send_statuses_have_labels():
    for status in MailDeliveryContentService.all_send_statuses():
        label = MailDeliveryContentService.send_status_label(status)
        assert label


def test_all_delivery_statuses_have_labels():
    for status in MailDeliveryContentService.all_delivery_statuses():
        label = MailDeliveryContentService.delivery_status_label(status)
        assert label
