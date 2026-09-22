"""C3-T5 semantic capability projection model.

CapabilityProjection is a DÉLIA-owned projection of externally owned contract
metadata. It is discovery/planning metadata only: never permission, execution
authority, business approval, or provider credential state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OperationCharacter(str, Enum):
    """Canonical operation-character vocabulary frozen by C0.S5."""

    READ = "READ"
    ADVISE = "ADVISE"
    PREPARE = "PREPARE"
    ACT = "ACT"
    VERIFY = "VERIFY"
    SIGNAL = "SIGNAL"


@dataclass(frozen=True, slots=True)
class SourceContractRef:
    owner: str
    contract_id: str
    version: str
    content_hash: str

    def __post_init__(self) -> None:
        for name, value in (
            ("owner", self.owner),
            ("contract_id", self.contract_id),
            ("version", self.version),
            ("content_hash", self.content_hash),
        ):
            if not value.strip():
                raise ValueError(f"SourceContractRef.{name} is required")


@dataclass(frozen=True, slots=True)
class InputDescriptor:
    name: str
    location: str
    required: bool
    schema_type: str | None = None
    schema_ref: str | None = None


@dataclass(frozen=True, slots=True)
class OutputDescriptor:
    status_code: str
    schema_type: str | None = None
    schema_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ErrorDescriptor:
    status_code: str
    schema_ref: str | None = None


@dataclass(frozen=True, slots=True)
class SecurityRequirementDescriptor:
    """Descriptive OpenAPI security metadata, never effective authorization."""

    scheme: str
    scopes: tuple[str, ...] = ()

    def grants_authorization(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class CapabilityProjection:
    """Projection-only semantic capability metadata.

    The source owner remains authoritative. Current-user authorization is
    intentionally absent and must be resolved live by the proper authorities.
    """

    capability_id: str
    semantic_name: str
    owner: str
    operation_character: OperationCharacter
    source_contract: SourceContractRef
    operation_id: str
    http_method: str
    http_path: str
    inputs: tuple[InputDescriptor, ...] = ()
    outputs: tuple[OutputDescriptor, ...] = ()
    errors: tuple[ErrorDescriptor, ...] = ()
    security_requirements: tuple[SecurityRequirementDescriptor, ...] = ()
    idempotency_semantics: str | None = None
    reversible: bool | None = None
    required_postcondition: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("capability_id", self.capability_id),
            ("semantic_name", self.semantic_name),
            ("owner", self.owner),
            ("operation_id", self.operation_id),
            ("http_method", self.http_method),
            ("http_path", self.http_path),
        ):
            if not value.strip():
                raise ValueError(f"CapabilityProjection.{name} is required")
        if self.owner != self.source_contract.owner:
            raise ValueError("CapabilityProjection owner must match source contract owner")

    def grants_authorization(self) -> bool:
        return False

    def grants_source_access(self) -> bool:
        return False

    def grants_execution(self) -> bool:
        return False

    def authorizes_act(self) -> bool:
        return False
