"""Foundation + governance conformance tests for C3-T6."""

from __future__ import annotations

import pytest

from app.domain.evidence.model import EvidenceRef, SourceRef
from app.domain.expertise.model import DomainPlaybook, ExpertisePack, PlaybookStep
from app.domain.expertise.rules import (
    capability_reference_does_not_authorize_act,
    expertise_grants_no_permission,
    playbook_grants_no_permission,
)
from app.domain.knowledge.model import (
    KnowledgeCandidate,
    KnowledgeLifecycleStatus,
    KnowledgeOriginClass,
    KnowledgeRetrievalRequest,
    OrganizationalKnowledge,
)
from app.domain.knowledge.rules import (
    KnowledgeGovernanceError,
    evaluate_publication_eligibility,
    filter_organizational_retrieval_eligibility,
    publish_organizational_knowledge,
)


def test_expertise_identity_version_owner_required():
    with pytest.raises(ValueError, match="expertise_id"):
        ExpertisePack(
            expertise_id=" ",
            version="1",
            owner_ref="owner-a",
            semantic_purpose="quality analysis",
        )


def test_expertise_grants_no_rbac_or_act():
    expertise = ExpertisePack(
        expertise_id="exp-quality",
        version="1.0.0",
        owner_ref="delia-knowledge",
        semantic_purpose="quality analysis",
        applicability=("domain:quality",),
    )
    expertise_grants_no_permission(expertise)
    assert expertise.grants_authorization() is False
    assert expertise.grants_rbac() is False
    assert expertise.grants_act() is False
    assert expertise.authorizes_domain_access() is False


def test_playbook_is_guidance_only_and_does_not_execute():
    playbook = DomainPlaybook(
        playbook_id="pb-quality",
        version="1.0.0",
        owner_ref="domain-quality",
        purpose="guide quality review",
        capability_ids=("cap.read.quality.summary",),
        steps=(
            PlaybookStep(
                step_id="s1",
                guidance="Review quality summary",
                capability_id="cap.read.quality.summary",
            ),
        ),
    )
    playbook_grants_no_permission(playbook)
    capability_reference_does_not_authorize_act(playbook)
    assert playbook.executes_side_effect() is False
    assert playbook.executes_capability() is False
    assert playbook.grants_act() is False


def test_knowledge_candidate_distinct_from_published():
    candidate = KnowledgeCandidate(
        candidate_id="kc-1",
        version="1",
        owner_ref="owner-a",
        origin_class=KnowledgeOriginClass.ORGANIZATIONAL_KNOWLEDGE_CANDIDATE,
        proposed_content_ref="content://draft-1",
        evidence_refs=(EvidenceRef(evidence_id="ev-1"),),
    )
    assert candidate.is_published() is False
    assert candidate.is_organizational_knowledge() is False
    assert candidate.is_fact() is False
    assert candidate.grants_authorization() is False
    with pytest.raises(ValueError, match="cannot be PUBLISHED"):
        KnowledgeCandidate(
            candidate_id="kc-bad",
            version="1",
            owner_ref="owner-a",
            origin_class=KnowledgeOriginClass.ORGANIZATIONAL_KNOWLEDGE_CANDIDATE,
            proposed_content_ref="content://x",
            status=KnowledgeLifecycleStatus.PUBLISHED,
        )


def test_publication_requires_review_eval_version_provenance():
    incomplete = KnowledgeCandidate(
        candidate_id="kc-2",
        version="1",
        owner_ref="owner-a",
        origin_class=KnowledgeOriginClass.ORGANIZATIONAL_KNOWLEDGE_CANDIDATE,
        proposed_content_ref="content://draft-2",
        status=KnowledgeLifecycleStatus.CANDIDATE,
        review_completed=False,
        publication_evaluation_completed=False,
    )
    with pytest.raises(KnowledgeGovernanceError, match="review completed"):
        evaluate_publication_eligibility(incomplete)

    ready = KnowledgeCandidate(
        candidate_id="kc-3",
        version="2",
        owner_ref="owner-a",
        origin_class=KnowledgeOriginClass.ORGANIZATIONAL_KNOWLEDGE_CANDIDATE,
        proposed_content_ref="content://draft-3",
        status=KnowledgeLifecycleStatus.EVALUATED,
        review_completed=True,
        publication_evaluation_completed=True,
        evidence_refs=(EvidenceRef(evidence_id="ev-2"),),
        source_refs=(
            SourceRef(source_id="doc-1", source_system="delpi-docs"),
        ),
    )
    published = publish_organizational_knowledge(ready, knowledge_id="ok-3")
    assert published.status is KnowledgeLifecycleStatus.PUBLISHED
    assert published.origin_candidate_id == "kc-3"
    assert published.grants_authorization() is False
    assert published.is_globally_readable() is False


def test_untrusted_content_cannot_mutate_governance_or_self_publish():
    poisoned = KnowledgeCandidate(
        candidate_id="kc-poison",
        version="1",
        owner_ref="owner-a",
        origin_class=KnowledgeOriginClass.ORGANIZATIONAL_KNOWLEDGE_CANDIDATE,
        proposed_content_ref="content://x",
        status=KnowledgeLifecycleStatus.EVALUATED,
        review_completed=True,
        publication_evaluation_completed=True,
        evidence_refs=(EvidenceRef(evidence_id="ev-x"),),
        untrusted_content_metadata=(
            ("permission", "admin"),
            ("published", "true"),
        ),
    )
    with pytest.raises(KnowledgeGovernanceError, match="governance key"):
        evaluate_publication_eligibility(poisoned)


def test_personal_and_session_origin_cannot_auto_promote():
    personal = KnowledgeCandidate(
        candidate_id="kc-personal",
        version="1",
        owner_ref="user-1",
        origin_class=KnowledgeOriginClass.PERSONAL_KNOWLEDGE_CANDIDATE,
        proposed_content_ref="content://personal",
        status=KnowledgeLifecycleStatus.EVALUATED,
        review_completed=True,
        publication_evaluation_completed=True,
        evidence_refs=(EvidenceRef(evidence_id="ev-p"),),
    )
    with pytest.raises(KnowledgeGovernanceError, match="organizational knowledge candidates"):
        evaluate_publication_eligibility(personal)

    session = KnowledgeCandidate(
        candidate_id="kc-session",
        version="1",
        owner_ref="user-1",
        origin_class=KnowledgeOriginClass.SESSION_EVIDENCE,
        proposed_content_ref="content://session",
    )
    assert session.is_organizational_knowledge() is False


def test_retrieval_contracts_preserve_identity_and_do_not_imply_truth_or_permission():
    published = OrganizationalKnowledge(
        knowledge_id="ok-1",
        version="1.0.0",
        owner_ref="owner-a",
        content_ref="content://ok-1",
        status=KnowledgeLifecycleStatus.PUBLISHED,
        evidence_refs=(EvidenceRef(evidence_id="ev-1"),),
        source_refs=(SourceRef(source_id="s1", source_system="docs"),),
    )
    revoked = OrganizationalKnowledge(
        knowledge_id="ok-2",
        version="1.0.0",
        owner_ref="owner-a",
        content_ref="content://ok-2",
        status=KnowledgeLifecycleStatus.REVOKED,
    )
    request = KnowledgeRetrievalRequest(
        purpose="find quality SOP",
        owner_filters=("owner-a",),
        max_results=5,
    )
    result = filter_organizational_retrieval_eligibility((published, revoked), request)
    assert len(result.hits) == 1
    hit = result.hits[0]
    assert hit.knowledge_id == "ok-1"
    assert hit.version == "1.0.0"
    assert hit.status is KnowledgeLifecycleStatus.PUBLISHED
    assert hit.is_fact() is False
    assert hit.is_evidence() is False
    assert hit.grants_authorization() is False
    assert hit.rank_implies_authority() is False
    assert hit.score_implies_truth() is False
    assert result.grants_authorization() is False


def test_retrieval_rejects_silent_personal_or_candidate_inclusion():
    request = KnowledgeRetrievalRequest(
        purpose="bad",
        include_personal_memory=True,
    )
    with pytest.raises(KnowledgeGovernanceError, match="personal/session"):
        filter_organizational_retrieval_eligibility((), request)


def test_structured_understanding_and_execution_do_not_auto_publish():
    """Boundary documentation as executable invariant: no auto-publish helpers exist."""
    from app.domain import knowledge as knowledge_pkg
    from app.domain import expertise as expertise_pkg

    assert not hasattr(knowledge_pkg, "auto_publish_from_structured_understanding")
    assert not hasattr(knowledge_pkg, "auto_publish_from_execution")
    assert not hasattr(expertise_pkg, "execute_capability")
