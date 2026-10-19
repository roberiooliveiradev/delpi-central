from app.application.services.integrations.protheus_secret_redaction import (
    redact_text,
    redact_url,
)


def test_redact_url_strips_password_and_username() -> None:
    url = (
        "https://host/rest/api/oauth2/v1/token"
        "?grant_type=password&username=tech.user&password=super-secret"
    )
    redacted = redact_url(url)
    assert "super-secret" not in redacted
    assert "tech.user" not in redacted
    assert "password=" in redacted
    assert "username=" in redacted
    assert "grant_type=password" in redacted
    # urlencode may percent-encode the mask
    assert "***" in redacted or "%2A%2A%2A" in redacted


def test_redact_text_strips_bearer_and_json_tokens() -> None:
    text = 'Bearer abc.def.ghi {"access_token":"tok123","refresh_token":"ref456"}'
    redacted = redact_text(text)
    assert "abc.def.ghi" not in redacted
    assert "tok123" not in redacted
    assert "ref456" not in redacted
