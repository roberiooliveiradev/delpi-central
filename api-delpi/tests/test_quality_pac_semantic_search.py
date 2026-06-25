from app.domain.services.quality_action_plans.case_similarity_embedding_service import (
    CaseSimilarityEmbeddingService,
)
from app.domain.services.quality_action_plans.case_similarity_scoring_service import (
    CaseSimilarityScoringService,
    IndexedCaseCandidate,
    SimilarCaseQuery,
)
from app.infrastructure.embeddings.null_case_similarity_embedding_gateway import (
    NullCaseSimilarityEmbeddingGateway,
)
from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_intelligence_repository import (
    PostgresQualityIntelligenceRepository,
)


def test_semantic_similarity_boosts_ranking():
    scoring = CaseSimilarityScoringService()
    query = SimilarCaseQuery(
        problem_description="oxidação em parafusos do chicote",
        product_code="14297268",
    )
    semantic = IndexedCaseCandidate(
        plan_id="uuid-1",
        plan_code="PAC-2026-0001",
        search_text="corrosão metálica em fixadores",
        product_code="14297268",
        failure_mode="oxidação",
        root_cause_category="processo",
        symptom_tags=["oxidação"],
        problem_summary="Oxidação em parafusos",
        root_cause="Tratamento superficial",
        effectiveness_status="effective",
        closed_at="2026-01-01",
        effective_actions=["Revisar tratamento"],
        semantic_similarity=0.92,
    )
    lexical_only = IndexedCaseCandidate(
        plan_id="uuid-2",
        plan_code="PAC-2026-0002",
        search_text="etiqueta ilegível",
        product_code="14297268",
        failure_mode="etiqueta",
        root_cause_category="processo",
        symptom_tags=[],
        problem_summary="Etiqueta",
        root_cause="Impressão",
        effectiveness_status="effective",
        closed_at="2026-01-01",
        effective_actions=["Trocar ribbon"],
        semantic_similarity=None,
    )

    assert scoring.score(query, semantic) > scoring.score(query, lexical_only)


def test_merge_similar_case_candidates_preserves_semantic_score():
    merged = PostgresQualityIntelligenceRepository._merge_similar_case_candidates(
        [{"plan_id": "plan-1", "plan_code": "PAC-1", "semantic_similarity": None}],
        [
            {"plan_id": "plan-1", "plan_code": "PAC-1", "semantic_similarity": 0.81},
            {"plan_id": "plan-2", "plan_code": "PAC-2", "semantic_similarity": 0.77},
        ],
    )
    by_id = {row["plan_id"]: row for row in merged}
    assert by_id["plan-1"]["semantic_similarity"] == 0.81


def test_null_embedding_gateway_is_disabled():
    gateway = NullCaseSimilarityEmbeddingGateway()
    assert gateway.is_enabled() is False
    assert CaseSimilarityEmbeddingService.embed_search_text(gateway, "texto") is None
