from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_commentary_profile_service import (
    ChatOperationalCommentaryProfileService,
)
from app.domain.services.chat_operational_data_commentary_service import (
    ChatOperationalDataCommentaryService,
)

configure_domain_infrastructure_ports()


def test_structure_exclusivity_profile_skips_template_prose_commentary():
    root = {
        "product": {"product_code": "90260255", "description": "CHICOTE EPR SINGELO 300MM"},
        "summary": {
            "total_components": 12,
            "total_intermediates": 4,
            "total_raw_materials": 8,
            "total_exclusive_raw_materials": 0,
        },
        "items": [{"component_type": "MP", "component_code": "10080098"}],
    }

    commentary = ChatOperationalDataCommentaryService.build("structure_exclusivity", root)

    assert commentary is not None
    assert commentary.get("metadataOnly") is True
    assert commentary.get("highlights") == []
    assert commentary.get("profileKey") == "structure_exclusivity"
    assert "tree" in (commentary.get("visualHints") or [])


def test_structure_exclusivity_highlight_rules_build_verdict_when_not_skipped(monkeypatch):
    monkeypatch.setattr(
        ChatOperationalCommentaryProfileService,
        "should_skip_template_prose_commentary",
        classmethod(lambda cls, profile_key: False),
    )

    root = {
        "product": {"product_code": "90260255", "description": "CHICOTE"},
        "summary": {
            "total_components": 3,
            "total_intermediates": 1,
            "total_raw_materials": 2,
            "total_exclusive_raw_materials": 0,
        },
        "items": [{"component_type": "MP"}],
    }

    highlights = ChatOperationalCommentaryProfileService.build_highlight_rules(
        "structure_exclusivity",
        root,
        format_line=lambda section, key, values: f"{section}:{key}",
    )

    assert any("exclusivityVerdictNo" in line for line in highlights)
    assert any("introWithDescriptionNeutral" in line for line in highlights)


def test_structure_exclusivity_commentary_profile_configured_in_json():
    config = ChatOperationalCommentaryProfileService.profile_config("structure_exclusivity")

    assert config.get("templateProseCommentary") == "skip"
    assert isinstance(config.get("highlightRules"), list)
    assert len(config.get("highlightRules") or []) >= 4
