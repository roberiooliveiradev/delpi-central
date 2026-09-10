from __future__ import annotations

from requests_app.application.services.comment_body_policy import (
    assert_comment_body_media_policy,
)
from requests_app.application.errors import ApplicationError
import pytest


def test_comment_body_allows_attachment_href():
    assert_comment_body_media_policy("ola ![x](attachment:pending:abc)")
    assert_comment_body_media_policy("ola ![x](attachment:11111111-2222-3333-4444-555555555555)")


def test_comment_body_rejects_http_and_data_images():
    with pytest.raises(ApplicationError) as exc:
        assert_comment_body_media_policy("![x](https://evil.example/a.png)")
    assert exc.value.code == "comment_media_forbidden"
    with pytest.raises(ApplicationError):
        assert_comment_body_media_policy("![x](data:image/png;base64,aaa)")
