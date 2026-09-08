import json
from pathlib import Path


def test_features_catalog_documents_field_label_source():
    path = (
        Path(__file__).resolve().parents[3]
        / "app"
        / "content"
        / "pt-BR"
        / "assistant"
        / "features_catalog.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
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
