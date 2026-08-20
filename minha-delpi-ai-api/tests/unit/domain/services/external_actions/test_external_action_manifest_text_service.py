from app.domain.services.external_actions.external_action_manifest_text_service import (
    ExternalActionManifestTextService,
)
from app.application.services.external_actions.external_action_selection_support_service import (
    ExternalActionSelectionSupportService,
)


def test_manifest_includes_params_enums_and_returns():
    text = ExternalActionManifestTextService.build(
        {
            "method": "GET",
            "path": "/production/otd",
            "summary": "OTD production",
            "description": "On-time delivery detail",
            "operationId": "get_production_otd",
            "tags": ["production"],
            "parametersSchema": [
                {
                    "name": "status",
                    "description": "Filter by delivery status",
                    "schema": {"type": "string", "enum": ["late", "on_time", "all"]},
                },
                {"name": "branch", "schema": {"type": "string"}},
            ],
            "delpiMetadata": {
                "entity": "production_otd",
                "shape": "playbook_report",
            },
            "responseSchema": {
                "200": {
                    "content": {
                        "application/json": {
                            "example": {
                                "meta": {
                                    "fields": [
                                        {"name": "late_ops"},
                                        {"name": "otd_pct"},
                                    ]
                                }
                            }
                        }
                    }
                }
            },
        }
    )

    assert "GET" in text
    assert "/production/otd" in text
    assert "get_production_otd" in text
    assert "params:" in text
    assert "status" in text
    assert "enums=late|on_time|all" in text
    assert "returns:" in text
    assert "entity=production_otd" in text
    assert "shape=playbook_report" in text
    assert "fields=late_ops,otd_pct" in text


def test_manifest_respects_max_chars_from_json():
    text = ExternalActionManifestTextService.build(
        {
            "method": "GET",
            "path": "/x",
            "summary": "s" * 5000,
        }
    )
    assert len(text) <= 4000


def test_lexical_overlap_uses_manifest_enums():
    action = {
        "method": "GET",
        "path": "/production/otd",
        "summary": "OTD",
        "operationId": "get_production_otd",
        "parametersSchema": [
            {
                "name": "status",
                "schema": {"enum": ["late", "on_time"]},
            }
        ],
    }
    score = ExternalActionSelectionSupportService.lexical_overlap_score(
        "listar otd status late",
        action,
    )
    assert score > 0
    lexical_text = ExternalActionManifestTextService.build_for_lexical(action)
    assert "late" in lexical_text
    assert "playbook" not in lexical_text


def test_build_for_lexical_excludes_shape_playbook():
    text = ExternalActionManifestTextService.build_for_lexical(
        {
            "method": "GET",
            "path": "/production/otd",
            "summary": "OTD produção",
            "operationId": "get_production_otd",
            "delpiMetadata": {
                "entity": "production_otd",
                "shape": "playbook_report",
            },
            "parametersSchema": [
                {
                    "name": "branch",
                    "description": "all (no branch filter)",
                    "schema": {"enum": ["all", "01"]},
                }
            ],
        }
    )
    assert "playbook" not in text.lower()
    assert "no branch" not in text.lower()
    assert "production_otd" in text or "otd" in text.lower()
    assert "branch" in text
    assert "all" in text

