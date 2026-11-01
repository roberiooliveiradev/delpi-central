"""DI-1 — professional guidance reaches the runtime via the canonical
knowledge delivery path (no parallel registry)."""
from __future__ import annotations

from tv_app.application.services.data import design_intelligence_service as m


def test_professional_guidance_loaded():
    dm = m._document()["designMethodology"]
    pg = dm.get("professionalGuidance")
    assert pg is not None
    assert pg["version"] == "prof-guidance-v1"
    assert pg["sources"], "fontes atribuidas exigidas"
    assert pg["chartSelection"]["temporal"]["recommended"] == "line"
    assert pg["chartSelection"]["ranking"]["recommended"] == "horizontal_bar"
    assert pg["tvConstraints"]["max_kpis_per_slide"] == 4


def test_guidance_aligned_with_recommendation_rules():
    """Knowledge prescritivo bate com as regras de _recommend."""
    from tv_app.application.services.data.design_intelligence_service import (
        DesignIntelligenceService as D,
    )
    pg = m._document()["designMethodology"]["professionalGuidance"]
    cs = pg["chartSelection"]
    temporal = D.visual_recommendation(
        D.semantic_digest([{"dia": "01", "qty": 1}, {"dia": "02", "qty": 2}])
    )
    goal = D.visual_recommendation(
        D.semantic_digest([{"nome": "oee", "real": 1, "meta": 2}])
    )
    assert temporal["recommendedType"] == cs["temporal"]["recommended"]
    assert goal["recommendedType"] == cs["goal_progress"]["recommended"]


def test_catalog_projection_includes_methodology():
    cat = m.DesignIntelligenceService.catalog_projection()
    assert "designMethodology" in cat
    dm = cat["designMethodology"]
    # Guidance completa fica no documento (canal knowledge/raciocínio);
    # a projeção compacta expõe apenas o escopo (budget de catálogo).
    assert dm.get("professionalGuidanceScope")
