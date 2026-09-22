"""Deterministic Knowledge governance rules for C3-T6.

candidate != published
external/user/model content cannot self-publish or mutate governance
Personal Memory / session evidence cannot auto-promote
retrieval eligibility != current-user authorization
"""

from __future__ import annotations

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


class KnowledgeGovernanceError(ValueError):
    """Fail-closed knowledge governance violation."""


def reject_governance_mutation_from_untrusted_content(
    candidate: KnowledgeCandidate,
) -> None:
    for key, _value in candidate.untrusted_content_metadata:
        normalized = key.strip().lower()
        if normalized in GOVERNANCE_MUTATION_KEYS:
            raise KnowledgeGovernanceError(
                f"untrusted content must not mutate governance key '{key}'"
            )


def reject_self_publication_claim(candidate: KnowledgeCandidate) -> None:
    for key, value in candidate.untrusted_content_metadata:
        normalized_key = key.strip().lower()
        normalized_value = value.strip().lower()
        if normalized_key in {"published", "approved", "auto_publish"} and normalized_value in {
            "true",
            "yes",
            "1",
            "published",
            "approved",
        }:
            raise KnowledgeGovernanceError(
                "untrusted content cannot mark itself published/approved"
            )
    if candidate.is_published():
        raise KnowledgeGovernanceError("candidate cannot be treated as published")


def reject_personal_or_session_auto_promotion(candidate: KnowledgeCandidate) -> None:
    if candidate.origin_class in (
        KnowledgeOriginClass.PERSONAL_KNOWLEDGE_CANDIDATE,
        KnowledgeOriginClass.SESSION_EVIDENCE,
        KnowledgeOriginClass.TRANSIENT_RESEARCH,
    ):
        if candidate.status not in (
            KnowledgeLifecycleStatus.CANDIDATE,
            KnowledgeLifecycleStatus.REVIEWED,
            KnowledgeLifecycleStatus.EVALUATED,
        ):
            raise KnowledgeGovernanceError(
                "personal/session/transient origin cannot auto-promote beyond candidate path"
            )
        if candidate.is_organizational_knowledge():
            raise KnowledgeGovernanceError(
                "personal/session origin cannot become Organizational Knowledge automatically"
            )


def evaluate_publication_eligibility(candidate: KnowledgeCandidate) -> None:
    """Canonical publish preconditions — eligibility only, not physical publish."""
    reject_governance_mutation_from_untrusted_content(candidate)
    reject_self_publication_claim(candidate)
    reject_personal_or_session_auto_promotion(candidate)

    if candidate.origin_class is not KnowledgeOriginClass.ORGANIZATIONAL_KNOWLEDGE_CANDIDATE:
        raise KnowledgeGovernanceError(
            "only organizational knowledge candidates are publication-eligible"
        )
    if not candidate.owner_ref.strip():
        raise KnowledgeGovernanceError("publication requires identified owner")
    if not candidate.review_completed:
        raise KnowledgeGovernanceError("publication requires review completed")
    if not candidate.publication_evaluation_completed:
        raise KnowledgeGovernanceError("publication requires publication evaluation completed")
    if not candidate.version.strip():
        raise KnowledgeGovernanceError("publication requires version")
    if not candidate.evidence_refs and not candidate.source_refs:
        raise KnowledgeGovernanceError("publication requires provenance (EvidenceRef or SourceRef)")
    if candidate.status not in (
        KnowledgeLifecycleStatus.REVIEWED,
        KnowledgeLifecycleStatus.EVALUATED,
    ):
        raise KnowledgeGovernanceError(
            "publication eligibility requires REVIEWED or EVALUATED status"
        )


def publish_organizational_knowledge(
    candidate: KnowledgeCandidate,
    *,
    knowledge_id: str,
) -> OrganizationalKnowledge:
    """Create published Organizational Knowledge value object after eligibility passes.

    Not a store write. Physical Knowledge store remains NONE / TO_INVENTORY.
    """
    evaluate_publication_eligibility(candidate)
    return OrganizationalKnowledge(
        knowledge_id=knowledge_id,
        version=candidate.version,
        owner_ref=candidate.owner_ref,
        content_ref=candidate.proposed_content_ref,
        status=KnowledgeLifecycleStatus.PUBLISHED,
        evidence_refs=candidate.evidence_refs,
        source_refs=candidate.source_refs,
        limitations=candidate.limitations,
        review_completed=True,
        publication_evaluation_completed=True,
        origin_candidate_id=candidate.candidate_id,
    )


def filter_organizational_retrieval_eligibility(
    assets: tuple[OrganizationalKnowledge, ...],
    request: KnowledgeRetrievalRequest,
) -> KnowledgeRetrievalResult:
    """Deterministic eligibility filter over in-memory assets (contract test double).

    Not a RetrievalPort, vector store, or RAG runtime.
    retrieval eligibility != current-user authorization.

    NORMAL_RETRIEVAL_SCOPE = PUBLISHED_ORGANIZATIONAL_KNOWLEDGE_ONLY.
    REVOKED/DEPRECATED are EXCLUDED_FROM_NORMAL_RETRIEVAL.
    """
    hits: list[KnowledgeRetrievalHit] = []
    for asset in assets:
        if asset.status is not KnowledgeLifecycleStatus.PUBLISHED:
            continue
        if request.owner_filters and asset.owner_ref not in request.owner_filters:
            continue
        if request.version_constraint and asset.version != request.version_constraint:
            continue
        hits.append(
            KnowledgeRetrievalHit(
                knowledge_id=asset.knowledge_id,
                version=asset.version,
                status=asset.status,
                origin_class=KnowledgeOriginClass.PUBLISHED_ORGANIZATIONAL_KNOWLEDGE,
                evidence_refs=asset.evidence_refs,
                source_refs=asset.source_refs,
                limitations=asset.limitations,
                rank=len(hits) + 1,
            )
        )
        if len(hits) >= request.max_results:
            break

    return KnowledgeRetrievalResult(
        request_purpose=request.purpose,
        hits=tuple(hits),
        limitations=(
            "normal retrieval scope = PUBLISHED_ORGANIZATIONAL_KNOWLEDGE_ONLY",
            "REVOKED/DEPRECATED excluded from normal retrieval",
            "retrieval eligibility != current-user authorization",
            "retrieval hit != FACT",
            "retrieval hit != Evidence automatically",
        ),
    )
