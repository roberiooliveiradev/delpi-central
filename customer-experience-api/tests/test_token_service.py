from cx_app.application.services.token_service import generate_public_token


def test_token_is_unique_and_long():
    tokens = {generate_public_token() for _ in range(500)}
    assert len(tokens) == 500
    for token in tokens:
        # 32 bytes url-safe base64 -> >= 43 caracteres
        assert len(token) >= 43


def test_token_is_url_safe():
    token = generate_public_token()
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
    assert set(token) <= allowed
