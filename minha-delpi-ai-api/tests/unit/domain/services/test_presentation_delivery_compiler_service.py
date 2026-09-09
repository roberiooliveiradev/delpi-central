"""delivery.preferCanvas → metadata canvasOpen."""

from app.domain.entities.presentation_spec import PresentationDeliverySpec, PresentationSpec
from app.domain.services.presentation_compilers.presentation_delivery_compiler_service import (
    PresentationDeliveryCompilerService,
)
from app.domain.services.presentation_spec_compiler_service import (
    PresentationSpecCompilerService,
)
from app.domain.services.presentation_data_profile_builder_service import (
    PresentationDataProfileBuilderService,
)


def _table_metadata():
    return {
        "tablePresentation": {
            "type": "table",
            "title": "Estoque por filial",
            "columns": [
                {"key": "branch", "label": "Filial"},
                {"key": "balance", "label": "Saldo"},
            ],
            "rows": [
                {"branch": "01", "balance": 10},
                {"branch": "02", "balance": 5},
            ],
        }
    }


def test_prefer_canvas_from_spec_sets_canvas_open_payload():
    metadata = _table_metadata()
    spec = PresentationSpec(
        view="table",
        delivery=PresentationDeliverySpec(prefer_canvas=True),
    )

    PresentationDeliveryCompilerService.apply(metadata, spec=spec)

    assert metadata.get("deliveryPreferCanvas") is True
    canvas_open = metadata.get("canvasOpen")
    assert isinstance(canvas_open, dict)
    assert canvas_open.get("title") == "Estoque por filial"
    assert "Filial" in str(canvas_open.get("markdown") or "")
    assert "canvasPresentation" not in metadata


def test_prefer_canvas_from_constraints_sets_canvas_open_payload():
    metadata = {
        **_table_metadata(),
        "presentationConstraints": {"preferCanvas": True},
    }

    PresentationDeliveryCompilerService.apply(metadata, spec=None)

    assert metadata.get("deliveryPreferCanvas") is True
    assert isinstance(metadata.get("canvasOpen"), dict)


def test_spec_compiler_wires_delivery_prefer_canvas():
    metadata = _table_metadata()
    rows = metadata["tablePresentation"]["rows"]
    profile = PresentationDataProfileBuilderService.build(rows)
    spec = PresentationSpec(
        view="table",
        delivery=PresentationDeliverySpec(prefer_canvas=True),
    )

    PresentationSpecCompilerService.compile_into_metadata(
        metadata,
        spec=spec,
        profile=profile,
    )

    assert metadata.get("deliveryPreferCanvas") is True
    assert isinstance(metadata.get("canvasOpen"), dict)
    assert isinstance(metadata.get("presentationSpec"), dict)
