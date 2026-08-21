from app.application.services.chat_intelligence_metadata_service import (
    ChatIntelligenceMetadataService,
)


def test_metadata_exposes_skills_loaded_from_heuristics():
    metadata = ChatIntelligenceMetadataService.build(
        sources=[],
        tool_context={
            "skills": {
                "sqlAuthoring": True,
                "companyKnowledge": True,
                "drawingAnalysis": True,
            },
            "userMessage": "analise o desenho e confira na norma",
            "turnAnalysis": {"decision": "execute"},
            "turnAnalysisSkillsToLoad": [],
        },
    )

    assert "drawing-analysis" in (metadata.get("skillsLoaded") or [])
    assert "company-knowledge" in (metadata.get("skillsLoaded") or [])
    assert "sql" not in (metadata.get("skillsLoaded") or [])
