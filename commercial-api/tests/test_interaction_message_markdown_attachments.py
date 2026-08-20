from __future__ import annotations

from commercial_app.domain.services.interaction_message_markdown_attachments_service import (
    InteractionMessageMarkdownAttachmentsService,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)


def test_lists_ids_and_pending() -> None:
    InteractionRoomContentService.clear_cache()
    body = (
        "a ![one](attachment:pending:p1) b "
        "![two](attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee) "
        "![dup](attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)"
    )
    assert InteractionMessageMarkdownAttachmentsService.list_pending_ids(body) == ("p1",)
    assert InteractionMessageMarkdownAttachmentsService.list_attachment_ids(body) == (
        "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    )


def test_rewrite_pending() -> None:
    InteractionRoomContentService.clear_cache()
    body = "x ![s](attachment:pending:local-1) y"
    out = InteractionMessageMarkdownAttachmentsService.rewrite_pending_to_attachment(
        body, {"local-1": "11111111-2222-3333-4444-555555555555"}
    )
    assert (
        out
        == "x ![s](attachment:11111111-2222-3333-4444-555555555555) y"
    )
    assert InteractionMessageMarkdownAttachmentsService.list_pending_ids(out) == ()
