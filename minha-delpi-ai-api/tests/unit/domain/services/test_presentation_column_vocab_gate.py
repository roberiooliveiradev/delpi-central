"""Gate — labels de tabela ≠ key quando discovery está mockada (sem catálogo JSON)."""

from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)
from app.domain.services.presentation_column_label_discovery_service import (
    PresentationColumnLabelDiscoveryService,
)


def test_mocked_discovery_labels_differ_from_technical_keys(monkeypatch):
    def _fake_resolve(cls, keys, **kwargs):
        discovered = {
            "mandatory_cc_pc": "CC obrigatório PC",
            "rohs_indicator": "Indicador ROHS",
        }
        return {key: discovered[key] for key in keys if key in discovered}

    monkeypatch.setattr(
        PresentationColumnLabelDiscoveryService,
        "resolve_labels",
        classmethod(_fake_resolve),
    )

    columns = ExternalActionColumnLabelService().resolve_columns_for_items(
        [{"mandatory_cc_pc": "S", "rohs_indicator": "N"}],
    )
    labels = {
        column["key"]: column["label"]
        for column in columns
        if isinstance(column, dict)
    }

    assert labels["mandatory_cc_pc"] == "CC obrigatório PC"
    assert labels["rohs_indicator"] == "Indicador ROHS"
    assert labels["mandatory_cc_pc"] != "mandatory_cc_pc"
