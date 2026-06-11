"""Gate — vocabulário interno cobre chaves das fixtures tier A."""

from tests.fixtures.presentation_column_vocab_gate import validate_column_vocab_for_ci


def test_api_fixture_column_keys_exist_in_column_labels_fields():
    report = validate_column_vocab_for_ci()

    assert report["ok"] is True, "\n".join(report.get("missingKeys") or [])
