import json
from pathlib import Path


def _catalog() -> dict:
    path = (
        Path(__file__).resolve().parents[3]
        / "app"
        / "content"
        / "pt-BR"
        / "assistant"
        / "features_catalog.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_features_catalog_documents_field_label_source():
    payload = _catalog()
    features = {item["id"]: item for item in payload["features"]}

    overview = features["capabilities_overview"]
    chart = features["chart"]

    overview_help = " ".join(overview.get("howToUse") or []).casefold()
    chart_help = " ".join(chart.get("howToUse") or []).casefold()

    assert "catálogo" in overview_help or "catalogo" in overview_help
    assert "meta" in overview_help
    assert "rótulos" in overview_help or "rotulos" in overview_help
    assert "catálogo" in chart_help or "catalogo" in chart_help
    assert chart.get("howToUse")


def test_features_catalog_documents_consolidated_multi_scope_product_lookup():
    payload = _catalog()
    features = {item["id"]: item for item in payload["features"]}
    product = features["product_lookup"]
    help_text = " ".join(product.get("howToUse") or []).casefold()
    examples = " ".join(product.get("examples") or []).casefold()

    assert "vários aspectos" in help_text or "varios aspectos" in help_text
    assert "consolida" in help_text
    assert "painel" in help_text or "painéis" in help_text or "paineis" in help_text
    assert "visão integrada" in examples or "visao integrada" in examples
    assert "estrutura" in examples and "estoque" in examples


def test_features_catalog_documents_numeric_value_formatting():
    payload = _catalog()
    features = {item["id"]: item for item in payload["features"]}
    composer = features["presentation_composer"]
    help_text = " ".join(composer.get("howToUse") or []).casefold()

    assert "pt-br" in help_text or "moeda" in help_text
    assert "códigos" in help_text or "codigos" in help_text
