"""Application contracts for C3-T4 Structured Understanding.

Provider SDK objects are forbidden here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from app.application.model_invocation.contracts import EvalBindRequest
from app.domain.evidence.model import (
    AuthorityPolicySnapshot,
    EpistemicClass,
    EvidenceRef,
    ModelRef,
    SourceRef,
)
from app.domain.model_invocation.model import (
    InstructionLineage,
    ModelInvocationId,
    ModelInvocationLineage,
)
from app.domain.structured_understanding.model import (
    StructuredUnderstandingContent,
    StructuredUnderstandingId,
)


@dataclass(frozen=True, slots=True)
class StructuredUnderstandingRequest:
    """Bounded source-observation extraction request.

    source_text is a TEST FIXTURE / bounded input — not authoritative Domain SoT.
    Epistemic class is fixed by capability semantics (OBSERVATION), not caller preference.
    source_refs must be exactly one SourceRef for this slice.
    evidence_refs are request/result/lineage context only — not per-observation support claims.
    """

    understanding_id: StructuredUnderstandingId
    invocation_id: ModelInvocationId
    model_ref: ModelRef
    source_text: str
    task_purpose_id: str
    output_schema_id: str
    output_schema_version: str
    instruction_lineage: InstructionLineage
    timeout_seconds: float
    source_refs: tuple[SourceRef, ...]
    evidence_refs: tuple[EvidenceRef, ...] = ()
    authority_policy: AuthorityPolicySnapshot = field(default_factory=AuthorityPolicySnapshot)
    untrusted_external_metadata: Mapping[str, Any] = field(default_factory=dict)
    eval_bind: EvalBindRequest | None = None


@dataclass(frozen=True, slots=True)
class StructuredUnderstandingResult:
    understanding_id: StructuredUnderstandingId
    schema_id: str
    schema_version: str
    content: StructuredUnderstandingContent
    epistemic_class: EpistemicClass
    evidence_refs: tuple[EvidenceRef, ...]
    source_refs: tuple[SourceRef, ...]
    model_ref: ModelRef
    lineage: ModelInvocationLineage
    generated_at: str

    def is_fact(self) -> bool:
        return False

    def is_world_fact(self) -> bool:
        return False

    def authorizes_act(self) -> bool:
        return False

    def has_eval_result(self) -> bool:
        return False
