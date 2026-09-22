"""C3-T6 Knowledge governance + retrieval contract value objects.

Knowledge candidate != published Organizational Knowledge.
Retrieval contract != RAG / vector / embedding runtime.
Personal Memory != Organizational Knowledge.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.evidence.model import EvidenceRef, SourceRef


class KnowledgeOriginClass(str, Enum):
    """Distinct origin classes — do not collapse into a generic KnowledgeItem."""

    TRANSIENT_RESEARCH = "TRANSIENT_RESEARCH"
    SESSION_EVIDENCE = "SESSION_EVIDENCE"
    PERSONAL_KNOWLEDGE_CANDIDATE = "PERSONAL_KNOWLEDGE_CANDIDATE"
    ORGANIZATIONAL_KNOWLEDGE_CANDIDATE = "ORGANIZATIONAL_KNOWLEDGE_CANDIDATE"
    PUBLISHED_ORGANIZATIONAL_KNOWLEDGE = "PUBLISHED_ORGANIZATIONAL_KNOWLEDGE"


class KnowledgeLifecycleStatus(str, Enum):
    """Minimal knowledge lifecycle. candidate != published."""

    CANDIDATE = "CANDIDATE"
    REVIEWED = "REVIEWED"
    EVALUATED = "EVALUATED"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"
    REVOKED = "REVOKED"


# Untrusted content keys that must not mutate governance metadata.
GOVERNANCE_MUTATION_KEYS = frozenset(
    {
        "system_instruction",
        "policy",
        "rbac",
        "permission",
        "decision_gate",
        "authorization",
        "tool_permission",
        "act_authorized",
        "owner_ref",
        "status",
        "lifecycle_status",
        "publication_status",
        "approved",
        "published",
        "auto_publish",
    }
)


@dataclass(frozen=True, slots=True)
class KnowledgeCandidate:
    """Governed knowledge candidate. Never implies published / FACT / authorization."""

    candidate_id: str
    version: str
    owner_ref: str
    origin_class: KnowledgeOriginClass
    proposed_content_ref: str
    evidence_refs: tuple[EvidenceRef, ...] = ()
    source_refs: tuple[SourceRef, ...] = ()
    reviewer_target_ref: str | None = None
    limitations: tuple[str, ...] = ()
    status: KnowledgeLifecycleStatus = KnowledgeLifecycleStatus.CANDIDATE
    review_completed: bool = False
    publication_evaluation_completed: bool = False
    untrusted_content_metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("candidate_id", self.candidate_id),
            ("version", self.version),
            ("owner_ref", self.owner_ref),
            ("proposed_content_ref", self.proposed_content_ref),
        ):
            if not value.strip():
                raise ValueError(f"KnowledgeCandidate.{name} is required")
        if self.origin_class is KnowledgeOriginClass.PUBLISHED_ORGANIZATIONAL_KNOWLEDGE:
            raise ValueError(
                "KnowledgeCandidate cannot use PUBLISHED_ORGANIZATIONAL_KNOWLEDGE origin"
            )
        if self.status is KnowledgeLifecycleStatus.PUBLISHED:
            raise ValueError("KnowledgeCandidate.status cannot be PUBLISHED")

    def is_published(self) -> bool:
        return False

    def is_fact(self) -> bool:
        return False

    def grants_authorization(self) -> bool:
        return False

    def is_organizational_knowledge(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class OrganizationalKnowledge:
    """Published Organizational Knowledge asset (governance foundation only).

    Not a physical store. Original Domain/source remains authority by default.
    published != globally readable; access remains live AuthZ concern.
    """

    knowledge_id: str
    version: str
    owner_ref: str
    content_ref: str
    status: KnowledgeLifecycleStatus
    evidence_refs: tuple[EvidenceRef, ...] = ()
    source_refs: tuple[SourceRef, ...] = ()
    limitations: tuple[str, ...] = ()
    review_completed: bool = True
    publication_evaluation_completed: bool = True
    origin_candidate_id: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("knowledge_id", self.knowledge_id),
            ("version", self.version),
            ("owner_ref", self.owner_ref),
            ("content_ref", self.content_ref),
        ):
            if not value.strip():
                raise ValueError(f"OrganizationalKnowledge.{name} is required")
        if self.status is not KnowledgeLifecycleStatus.PUBLISHED:
            if self.status not in (
                KnowledgeLifecycleStatus.DEPRECATED,
                KnowledgeLifecycleStatus.REVOKED,
            ):
                raise ValueError(
                    "OrganizationalKnowledge.status must be PUBLISHED, DEPRECATED, or REVOKED"
                )

    def grants_authorization(self) -> bool:
        return False

    def is_globally_readable(self) -> bool:
        return False

    def is_retrievable_for_organizational_scope(self) -> bool:
        return self.status is KnowledgeLifecycleStatus.PUBLISHED


@dataclass(frozen=True, slots=True)
class KnowledgeRetrievalRequest:
    """Provider-neutral retrieval request contract.

    Retrieval Contract != Retrieval Runtime / Vector Search / Embedding / RAG.
    No current Application consumer requires a KnowledgeRetrievalPort — contracts only.
    """

    purpose: str
    knowledge_scope: KnowledgeOriginClass = (
        KnowledgeOriginClass.PUBLISHED_ORGANIZATIONAL_KNOWLEDGE
    )
    owner_filters: tuple[str, ...] = ()
    version_constraint: str | None = None
    max_results: int = 10
    include_unpublished_candidates: bool = False
    include_personal_memory: bool = False
    include_session_evidence: bool = False
    include_revoked_or_deprecated: bool = False

    def __post_init__(self) -> None:
        if not self.purpose.strip():
            raise ValueError("KnowledgeRetrievalRequest.purpose is required")
        if self.max_results < 1:
            raise ValueError("KnowledgeRetrievalRequest.max_results must be >= 1")


@dataclass(frozen=True, slots=True)
class KnowledgeRetrievalHit:
    """Single retrieval hit. Rank/score never imply FACT, Evidence, or permission."""

    knowledge_id: str
    version: str
    status: KnowledgeLifecycleStatus
    origin_class: KnowledgeOriginClass
    evidence_refs: tuple[EvidenceRef, ...] = ()
    source_refs: tuple[SourceRef, ...] = ()
    limitations: tuple[str, ...] = ()
    rank: int | None = None
    score: float | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("knowledge_id", self.knowledge_id),
            ("version", self.version),
        ):
            if not value.strip():
                raise ValueError(f"KnowledgeRetrievalHit.{name} is required")

    def is_fact(self) -> bool:
        return False

    def is_evidence(self) -> bool:
        return False

    def grants_authorization(self) -> bool:
        return False

    def rank_implies_authority(self) -> bool:
        return False

    def score_implies_truth(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class KnowledgeRetrievalResult:
    """Bounded retrieval result contract. Not a RAG engine output."""

    request_purpose: str
    hits: tuple[KnowledgeRetrievalHit, ...] = ()
    limitations: tuple[str, ...] = ()

    def grants_authorization(self) -> bool:
        return False
