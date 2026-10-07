"""OpenAPI capability provider adapter.

ARCH-DRIFT-DELIA-PROVIDER-NEUTRAL-ORCHESTRATION-01 (ledger §6.130):
OpenAPI is ONE provider family. This adapter consumes the existing
semantic ``CapabilityProjection`` foundation — ``project_openapi_document``
is re-run per turn against the live document, so the surface is always
fresh and semantic identity still comes only from governed
``CapabilityDeclaration``s, never HTTP heuristics.

Authority rules:
- Only ``OperationCharacter.READ`` projections are invocable in the
  interactive phase. Every other declared character (ADVISE, PREPARE,
  ACT, VERIFY, SIGNAL) is projected as ``UNKNOWN``: discoverable but
  never invocable — non-MCP write families remain NOT_AUTHORIZED until
  their own governance boundary is independently authorized.
- All wire mechanics (document fetch, path templating, query
  projection, bearer transport, response shaping) live in per-source
  callables — the orchestrator and this adapter's contract never
  inspect HTTP details.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from typing import Any, Callable, Mapping, Sequence

from app.application.capability_provision.contracts import (
    CapabilityGroup,
    CapabilityProviderError,
    ProviderCapability,
    ProviderSurface,
)
from app.domain.capability_catalog.model import (
    CapabilityProjection,
    OperationCharacter,
)
from app.domain.evidence.model import SourceRef
from app.domain.specialist_interop.model import (
    SpecialistOperationClass,
    SpecialistOutcome,
)

_logger = logging.getLogger(__name__)

# Read-only operation characters are invocable; everything else is
# discoverable-but-unknown — fail closed for non-MCP write families.
_INVOCABLE_OPENAPI_CHARACTERS = frozenset({OperationCharacter.READ})


def _operation_class(
    character: OperationCharacter,
) -> SpecialistOperationClass:
    """Map the declared semantic character to the interactive class.

    Fail closed: only READ is invocable in the interactive phase;
    write/verification characters stay UNKNOWN (discoverable, never
    invocable).
    """
    if character is OperationCharacter.READ:
        return SpecialistOperationClass.READ
    return SpecialistOperationClass.UNKNOWN


def _input_schema_from_inputs(
    projection: CapabilityProjection,
) -> Mapping[str, object] | None:
    """Synthesize a JSON-schema-ish input schema from declared inputs.

    The existing projection's InputDescriptors are the owner-declared
    contract; this synthesizes the same shape the generic argument
    validator consumes — no inference beyond declared name/type/
    required.
    """
    if not projection.inputs:
        return None
    properties: dict[str, object] = {}
    required: list[str] = []
    for descriptor in projection.inputs:
        properties[descriptor.name] = {
            "type": descriptor.schema_type or "string",
            "description": f"{descriptor.location} parameter",
        }
        if descriptor.required:
            required.append(descriptor.name)
    schema: dict[str, object] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required
    return schema


def _capability_from_projection(
    source_id: str, provider_id: str, projection: CapabilityProjection
) -> ProviderCapability:
    return ProviderCapability(
        capability_id=projection.capability_id,
        group_id=source_id,
        provider_id=provider_id,
        remote_name=projection.capability_id,
        owner=projection.owner,
        operation_class=_operation_class(projection.operation_character),
        description=projection.semantic_name,
        input_schema=_input_schema_from_inputs(projection),
        binding={
            "source_id": source_id,
            "operation_id": projection.operation_id,
            "http_method": projection.http_method,
            "http_path": projection.http_path,
            "inputs": tuple(
                {
                    "name": i.name,
                    "location": i.location,
                    "required": i.required,
                }
                for i in projection.inputs
            ),
        },
    )


@dataclass(frozen=True, slots=True)
class OpenApiCapabilitySource:
    """One governed OpenAPI source: document provider + declarations
    + invocation adapter.

    ``projector`` is called per turn and returns the live semantic
    projections (composition wires the governed
    ``project_openapi_document`` + declarations closure); ``invoker``
    is the provider-owned execution closure — it receives the
    capability's opaque binding plus validated arguments and returns a
    normalized SpecialistOutcome.
    """

    source_id: str
    owner_ref: str
    display_name: str
    projector: Callable[[], tuple[CapabilityProjection, ...]]
    invoker: Callable[
        [ProviderCapability, Mapping[str, object]], SpecialistOutcome
    ]

    def grants_authorization(self) -> bool:
        return False


class OpenApiCapabilityProvider:
    """Provider adapter over governed OpenAPI capability sources."""

    provider_id = "openapi"

    def __init__(self, sources: Sequence[OpenApiCapabilitySource]) -> None:
        self._source_by_group = {
            source.source_id: source for source in sources
        }

    def list_groups(
        self,
        *,
        correlation_id: str,
        timeout_seconds: float | None = None,
    ) -> ProviderSurface:
        groups: list[CapabilityGroup] = []
        failures: list[str] = []
        for source in self._source_by_group.values():
            try:
                projections = source.projector()
            except CapabilityProviderError as exc:
                failures.append(exc.code)
                continue
            except Exception as exc:
                _logger.info(
                    "openapi_projection_failed source=%s",
                    source.source_id,
                )
                failures.append("openapi_projection_failed")
                continue
            groups.append(
                CapabilityGroup(
                    provider_id=self.provider_id,
                    group_id=source.source_id,
                    owner_ref=source.owner_ref,
                    display_name=source.display_name,
                    capabilities=tuple(
                        _capability_from_projection(
                            source.source_id,
                            self.provider_id,
                            cap,
                        )
                        for cap in projections
                    ),
                    source=SourceRef(
                        source_id=source.owner_ref,
                        source_system=source.owner_ref,
                        provider_name=source.display_name,
                    ),
                )
            )
        return ProviderSurface(groups=tuple(groups), failures=tuple(failures))

    def invoke(
        self,
        capability: ProviderCapability,
        arguments: Mapping[str, object],
        *,
        correlation_id: str,
        timeout_seconds: float | None = None,
    ) -> SpecialistOutcome:
        source = self._source_by_group.get(capability.group_id)
        if source is None:
            raise CapabilityProviderError(
                "unknown_capability_group",
                "capability does not belong to a known OpenAPI source",
            )
        outcome = source.invoker(capability, dict(arguments))
        # LOOP-03R1 (D09): the turn correlation id is runtime
        # authority — the provider-owned invoker may return an outcome
        # whose provenance carries no/foreign correlation. Stamp the
        # turn id so every outcome joins the request-scoped trace.
        if outcome.provenance.correlation_id != correlation_id:
            outcome = replace(
                outcome,
                provenance=replace(
                    outcome.provenance, correlation_id=correlation_id
                ),
            )
        return outcome
