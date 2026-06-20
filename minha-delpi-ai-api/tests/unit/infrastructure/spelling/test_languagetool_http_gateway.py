from unittest.mock import MagicMock, patch

from app.infrastructure.spelling.languagetool_http_gateway import LanguageToolHttpGateway


def test_gateway_parses_matches():
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "matches": [
            {
                "offset": 2,
                "length": 4,
                "message": "Possível erro de ortografia.",
                "replacements": [{"value": "está"}],
                "rule": {"id": "MORFOLOGIK_RULE_PT_BR", "category": {"id": "TYPOS"}},
            }
        ]
    }

    with patch(
        "app.infrastructure.spelling.languagetool_http_gateway.requests.post",
        return_value=response,
    ) as post:
        issues = LanguageToolHttpGateway().check("o estoque esta baixo", language="pt-BR")

    assert len(issues) == 1
    assert issues[0]["replacements"] == ["está"]
    assert issues[0]["ruleId"] == "MORFOLOGIK_RULE_PT_BR"
    post.assert_called_once()


def test_gateway_returns_empty_on_http_error():
    with patch(
        "app.infrastructure.spelling.languagetool_http_gateway.requests.post",
        side_effect=TimeoutError("timeout"),
    ):
        issues = LanguageToolHttpGateway().check("texto", language="pt-BR")

    assert issues == []
