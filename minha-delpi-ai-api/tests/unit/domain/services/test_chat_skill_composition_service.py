from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_skill_composition_service import ChatSkillCompositionService

configure_domain_infrastructure_ports()


def test_without_analysis_keeps_all_enabled():
    loaded = ChatSkillCompositionService.resolve_loaded_skills(
        enabled_skills={"sqlAuthoring": True, "companyKnowledge": True},
        skills_to_load=None,
        analysis_ran=False,
    )
    assert loaded == {"sqlAuthoring": True, "companyKnowledge": True}


def test_analysis_empty_skills_loads_none():
    loaded = ChatSkillCompositionService.resolve_loaded_skills(
        enabled_skills={"sqlAuthoring": True, "companyKnowledge": True},
        skills_to_load=[],
        analysis_ran=True,
    )
    assert loaded == {}


def test_analysis_intersects_enabled_and_caps():
    loaded = ChatSkillCompositionService.resolve_loaded_skills(
        enabled_skills={
            "sqlAuthoring": True,
            "companyKnowledge": True,
            "drawingAnalysis": True,
            "technicalDescription": True,
        },
        skills_to_load=["sql", "company-knowledge", "drawing-analysis", "technical-description"],
        analysis_ran=True,
    )
    assert len(loaded) <= 3
    assert "sqlAuthoring" in loaded
    assert "companyKnowledge" in loaded


def test_drawing_and_norma_loads_drawing_and_company_knowledge():
    loaded = ChatSkillCompositionService.resolve_loaded_skills(
        enabled_skills={
            "sqlAuthoring": True,
            "companyKnowledge": True,
            "drawingAnalysis": True,
        },
        skills_to_load=[],
        analysis_ran=False,
        message="analise o desenho e confira na norma",
    )
    assert loaded.get("drawingAnalysis") is True
    assert loaded.get("companyKnowledge") is True
    assert "sqlAuthoring" not in loaded


def test_stock_message_does_not_load_specialized_skills():
    loaded = ChatSkillCompositionService.resolve_loaded_skills(
        enabled_skills={
            "sqlAuthoring": True,
            "companyKnowledge": True,
            "drawingAnalysis": True,
        },
        skills_to_load=[],
        analysis_ran=False,
        message="estoque do produto 10080022",
    )
    assert "sqlAuthoring" not in loaded
    assert "drawingAnalysis" not in loaded


def test_analysis_ignores_disabled_skill():
    loaded = ChatSkillCompositionService.resolve_loaded_skills(
        enabled_skills={"sqlAuthoring": False, "companyKnowledge": True},
        skills_to_load=["sql", "company-knowledge"],
        analysis_ran=True,
    )
    assert loaded == {"companyKnowledge": True}
