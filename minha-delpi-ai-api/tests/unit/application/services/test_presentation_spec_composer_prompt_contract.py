"""Contract: PresentationSpec composer prompt never includes raw rows or sensitive keys."""

import json

from app.application.services.presentation_spec_composer_application_service import (
    PresentationSpecComposerApplicationService,
)


def _profile_with_sensitive() -> dict:
    return {
        "dimensionCandidates": ["product_code", "cpf", "branch"],
        "measureCandidates": ["balance", "salary"],
        "fields": [
            {
                "key": "product_code",
                "semanticType": "nominal",
                "cardinalityBand": "medium",
                "displayLabel": "Produto",
                "isDimensionCandidate": True,
                "isMeasureCandidate": False,
                "sensitive": False,
            },
            {
                "key": "cpf",
                "semanticType": "identifier",
                "cardinalityBand": "high",
                "displayLabel": "CPF",
                "isDimensionCandidate": True,
                "isMeasureCandidate": False,
                "sensitive": True,
            },
            {
                "key": "salary",
                "semanticType": "quantitative",
                "cardinalityBand": "high",
                "displayLabel": "Salário",
                "isDimensionCandidate": False,
                "isMeasureCandidate": True,
                "sensitive": True,
            },
            {
                "key": "balance",
                "semanticType": "quantitative",
                "cardinalityBand": "medium",
                "displayLabel": "Saldo",
                "isDimensionCandidate": False,
                "isMeasureCandidate": True,
                "sensitive": False,
            },
        ],
        # Adversarial: raw payload must never leak into compose payload.
        "rows": [{"cpf": "123", "salary": 9000, "balance": 10}],
        "sampleRows": [{"cpf": "999"}],
    }


def test_compose_payload_excludes_rows_and_sensitive_keys():
    """Positive: payload só com stats seguros."""
    payload = PresentationSpecComposerApplicationService.build_compose_payload(
        intent={"view": "table"},
        profile=_profile_with_sensitive(),
        excerpt="mostre a tabela",
    )
    assert "rows" not in payload
    assert "sampleRows" not in payload
    keys = {item["key"] for item in payload["fields"]}
    assert keys == {"product_code", "balance"}
    assert "cpf" not in payload["dimensionCandidates"]
    assert "salary" not in payload["measureCandidates"]
    assert "product_code" in payload["dimensionCandidates"]
    assert "balance" in payload["measureCandidates"]


def test_compose_prompt_json_has_no_row_literals():
    """Sibling: string do prompt não carrega rows/sensitive."""
    prompt = PresentationSpecComposerApplicationService._build_prompt(
        intent={"view": "chart", "mark": "bar"},
        profile=_profile_with_sensitive(),
        excerpt="gráfico de barras",
    )
    parsed = json.loads(prompt)
    assert "rows" not in parsed
    blob = json.dumps(parsed, ensure_ascii=False)
    assert '"cpf"' not in blob
    assert '"salary"' not in blob
    assert "123" not in blob
    assert "9000" not in blob


def test_compose_payload_negative_empty_profile():
    """Negative: profile vazio não inventa rows."""
    payload = PresentationSpecComposerApplicationService.build_compose_payload(
        intent={},
        profile={},
        excerpt=None,
    )
    assert payload["fields"] == []
    assert payload["dimensionCandidates"] == []
    assert payload["measureCandidates"] == []
    assert "rows" not in payload
