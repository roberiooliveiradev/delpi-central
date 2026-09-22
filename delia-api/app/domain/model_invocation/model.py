"""C3-T3 model invocation / eval lineage value objects.

Reuses frozen C0.S3 ModelRef (21 §4). Does not create ModelIdentity,
ProviderRegistry, PromptRegistry, or EvalPlatform.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.evidence.model import (
    EvidenceRef,
    ModelRef,
    SourceRef,
)


class ProviderExposureClass(str, Enum):
    """Where model input would be sent. Not an authorization decision."""

    TEST_ONLY = "TEST_ONLY"
    EXTERNAL_BLOCKED = "EXTERNAL_BLOCKED"


class InvocationFinishStatus(str, Enum):
    COMPLETED = "COMPLETED"
    INVALID_STRUCTURED_OUTPUT = "INVALID_STRUCTURED_OUTPUT"
    TIMEOUT = "TIMEOUT"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_REJECTED = "PROVIDER_REJECTED"
    POLICY_DENIED = "POLICY_DENIED"
    INVALID_REQUEST = "INVALID_REQUEST"
    UNSUPPORTED_MODEL = "UNSUPPORTED_MODEL"


class EvalOutcome(str, Enum):
    """Bounded eval outcome. Not a global intelligence score."""

    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    TEST_NOT_RUN = "TEST_NOT_RUN"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class ModelInvocationId:
    """C3-local invocation identity for lineage/eval/correlation. Not a shared primitive."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("ModelInvocationId.value is required")


@dataclass(frozen=True, slots=True)
class InstructionLineage:
    """Identifies the instruction/policy used. Raw prompt is not stored here."""

    instruction_id: str
    version: str
    content_hash: str

    def __post_init__(self) -> None:
        if not self.instruction_id.strip():
            raise ValueError("InstructionLineage.instruction_id is required")
        if not self.version.strip():
            raise ValueError("InstructionLineage.version is required")
        if not self.content_hash.strip():
            raise ValueError("InstructionLineage.content_hash is required")


@dataclass(frozen=True, slots=True)
class GenerationConfig:
    """Reproducibility-relevant generation bounds. Not a provider parameter dump."""

    max_output_units: int | None = None


@dataclass(frozen=True, slots=True)
class ConfigurationLineage:
    model_ref: ModelRef
    instruction_lineage: InstructionLineage
    output_schema_id: str
    output_schema_version: str
    generation_config: GenerationConfig = GenerationConfig()
    timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        if not self.output_schema_id.strip():
            raise ValueError("ConfigurationLineage.output_schema_id is required")
        if not self.output_schema_version.strip():
            raise ValueError("ConfigurationLineage.output_schema_version is required")


@dataclass(frozen=True, slots=True)
class UsageMetadata:
    """Provider-neutral usage units. Token counts are not Domain cost truth."""

    input_units: int | None = None
    output_units: int | None = None
    unit_kind: str | None = None


@dataclass(frozen=True, slots=True)
class EvalIdentity:
    """Identifies what evaluation target an eval would refer to. Not evidence or outcome."""

    eval_id: str
    target_sha: str
    model_ref: ModelRef
    configuration_id: str
    instruction_version: str | None = None
    fixture_id: str | None = None
    dataset_id: str | None = None

    def __post_init__(self) -> None:
        if not self.eval_id.strip():
            raise ValueError("EvalIdentity.eval_id is required")
        if not self.target_sha.strip():
            raise ValueError("EvalIdentity.target_sha is required")
        if not self.configuration_id.strip():
            raise ValueError("EvalIdentity.configuration_id is required")


@dataclass(frozen=True, slots=True)
class EvalResult:
    identity: EvalIdentity
    outcome: EvalOutcome
    metric_name: str | None = None
    metric_value: float | None = None
    threshold: float | None = None
    failure_category: str | None = None
    observation: str | None = None


@dataclass(frozen=True, slots=True)
class ModelInvocationLineage:
    invocation_id: ModelInvocationId
    model_ref: ModelRef
    evidence_refs: tuple[EvidenceRef, ...]
    source_refs: tuple[SourceRef, ...]
    instruction_lineage: InstructionLineage
    configuration_lineage: ConfigurationLineage
    generated_at: str
    eval_identity: EvalIdentity | None = None

    def grants_authorization(self) -> bool:
        return False

    def grants_source_access(self) -> bool:
        return False

    def grants_act(self) -> bool:
        return False
