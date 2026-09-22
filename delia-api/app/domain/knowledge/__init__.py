"""C3-T6 Knowledge governance + retrieval contracts foundation.

No KnowledgeRepository, VectorStore, RAG, Personal Memory runtime, or ACT.
RetrievalPort deferred — no current Application consumer.
"""

from app.domain.knowledge.model import (
    GOVERNANCE_MUTATION_KEYS,
    KnowledgeCandidate,
    KnowledgeLifecycleStatus,
    KnowledgeOriginClass,
    KnowledgeRetrievalHit,
    KnowledgeRetrievalRequest,
    KnowledgeRetrievalResult,
    OrganizationalKnowledge,
)
from app.domain.knowledge.rules import (
    KnowledgeGovernanceError,
    evaluate_publication_eligibility,
    filter_organizational_retrieval_eligibility,
    publish_organizational_knowledge,
    reject_governance_mutation_from_untrusted_content,
    reject_personal_or_session_auto_promotion,
    reject_self_publication_claim,
)

__all__ = [
    "GOVERNANCE_MUTATION_KEYS",
    "KnowledgeCandidate",
    "KnowledgeGovernanceError",
    "KnowledgeLifecycleStatus",
    "KnowledgeOriginClass",
    "KnowledgeRetrievalHit",
    "KnowledgeRetrievalRequest",
    "KnowledgeRetrievalResult",
    "OrganizationalKnowledge",
    "evaluate_publication_eligibility",
    "filter_organizational_retrieval_eligibility",
    "publish_organizational_knowledge",
    "reject_governance_mutation_from_untrusted_content",
    "reject_personal_or_session_auto_promotion",
    "reject_self_publication_claim",
]
