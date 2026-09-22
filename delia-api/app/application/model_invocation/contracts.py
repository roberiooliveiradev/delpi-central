"""Application contracts for C3-T3 model invocation.

Provider SDK objects are forbidden here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from app.domain.evidence.model import (
    AuthorityPolicySnapshot,
    EpistemicClass,
    EvidenceRef,
    ModelRef,
    SourceRef,
)
from app.domain.model_invocation.model import (
    GenerationConfig,
    InstructionLineage,
    InvocationFinishStatus,
    ModelInvocationId,
    ModelInvocationLineage,
    UsageMetadata,
)


@dataclass(frozen=True, slots=True)
class EvalBindRequest:
    """Declare evaluation target identity for lineage binding only.

    Does not execute an evaluator, produce EvalResult, or imply PASS.
    Model/config come from the invocation.
    """

    eval_id: str
    target_sha: str
    fixture_id: str | None = None
    dataset_id: str | None = None


@dataclass(frozen=True, slots=True)
class ModelInvocationRequest:
    invocation_id: ModelInvocationId
    model_ref: ModelRef
    input_text: str
    task_purpose_id: str
    output_schema_id: str
    output_schema_version: str
    expected_fields: tuple[str, ...]
    instruction_lineage: InstructionLineage
    timeout_seconds: float
    evidence_refs: tuple[EvidenceRef, ...] = ()
    source_refs: tuple[SourceRef, ...] = ()
    generation_config: GenerationConfig = field(default_factory=GenerationConfig)
    declared_epistemic_class: EpistemicClass | None = None
    authority_policy: AuthorityPolicySnapshot = field(default_factory=AuthorityPolicySnapshot)
    untrusted_external_metadata: Mapping[str, Any] = field(default_factory=dict)
    eval_bind: EvalBindRequest | None = None


@dataclass(frozen=True, slots=True)
class ProviderInvocationPayload:
    """Neutral adapter payload. Lineage/eval are assembled by the use case, not the provider."""

    structured_output: Mapping[str, Any]
    generated_at: str
    finish_status: InvocationFinishStatus = InvocationFinishStatus.COMPLETED
    usage: UsageMetadata | None = None
    duration_ms: int | None = None


@dataclass(frozen=True, slots=True)
class ModelInvocationResult:
    invocation_id: ModelInvocationId
    model_ref: ModelRef
    structured_output: Mapping[str, Any]
    generated_at: str
    finish_status: InvocationFinishStatus
    lineage: ModelInvocationLineage
    epistemic_class: EpistemicClass
    usage: UsageMetadata | None = None
    duration_ms: int | None = None

    def is_fact(self) -> bool:
        return False

    def authorizes_act(self) -> bool:
        return False
