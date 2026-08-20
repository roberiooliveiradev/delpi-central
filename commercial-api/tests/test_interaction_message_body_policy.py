from __future__ import annotations

import pytest

from commercial_app.domain.services.interaction_message_body_policy_service import (
    InteractionMessageBodyPolicyService,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)


def test_allows_markdown_and_inline_u_span() -> None:
    assert not InteractionMessageBodyPolicyService.contains_raw_html("**oi** e `x`")
    assert not InteractionMessageBodyPolicyService.contains_raw_html("a <u>b</u> c")
    assert not InteractionMessageBodyPolicyService.contains_raw_html(
        '<span style="font-size: 18px">a</span>'
    )


def test_rejects_raw_html() -> None:
    assert InteractionMessageBodyPolicyService.contains_raw_html("<p>oi</p>")
    assert InteractionMessageBodyPolicyService.contains_raw_html("<script>x</script>")
    with pytest.raises(ValueError) as exc:
        InteractionMessageBodyPolicyService.assert_markdown_body("<div>x</div>")
    assert str(exc.value) == InteractionRoomContentService.error("bodyHtmlNotAllowed")
