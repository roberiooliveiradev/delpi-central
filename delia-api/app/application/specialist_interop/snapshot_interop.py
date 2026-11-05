"""SNAPSHOT_EXPERIMENT catalog source (doc 216, E1/E4).

``SnapshotDiscoverInterop`` is a drop-in SpecialistInterop whose
catalog acquisition reads the ACTIVE persisted snapshot instead of a
live ``tools/list``. Invocation is NOT overridden — the inherited
``invoke`` still re-reads the owner surface live and calls the owner,
so authorization, contract revalidation and availability semantics of
variant A are preserved verbatim.

Fail-closed contract: a missing/invalid/unverified snapshot raises the
typed owner-unavailable error — never a silent live fallback, which
would contaminate the A/B measurement.
"""
from __future__ import annotations

import logging

from app.application.specialist_interop.contracts import (
    RemoteToolDescriptor,
    SpecialistCatalogRequest,
    SpecialistRef,
)
from app.application.specialist_interop.errors import (
    MCP_UNAVAILABLE,
    SpecialistInteropError,
)
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from typing import Callable, Mapping, Protocol, Sequence


class _SnapshotCatalogStore(Protocol):
    """Structural contract for the persisted snapshot store — the
    infrastructure adapter satisfies it; application never imports
    infrastructure directly (boundary fix, doc 263)."""

    def active(
        self, owner_id: str, scope: str
    ) -> Mapping | None: ...

_logger = logging.getLogger(__name__)


class SnapshotDiscoverInterop(SpecialistInterop):
    """Discovery from the persisted snapshot; invoke stays live."""

    def __init__(
        self,
        port,
        store: _SnapshotCatalogStore,
        contract_hash: Callable[[Sequence[Mapping]], str],
        *,
        scope: str = "global",
    ) -> None:
        super().__init__(port)
        self._store = store
        self._contract_hash = contract_hash
        self._scope = scope

    def _remote_tools(
        self,
        specialist: SpecialistRef,
        request: SpecialistCatalogRequest,
    ):
        snap = self._store.active(specialist.specialist_id, self._scope)
        if snap is None:
            raise SpecialistInteropError(
                MCP_UNAVAILABLE,
                "snapshot catalog absent for specialist",
            )
        if self._contract_hash(snap["tools"]) != snap["contract_hash"]:
            raise SpecialistInteropError(
                MCP_UNAVAILABLE,
                "snapshot catalog hash verification failed",
            )
        descriptors: list[RemoteToolDescriptor] = []
        for tool in snap["tools"]:
            name = tool.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            meta = tool.get("_meta")
            descriptors.append(
                RemoteToolDescriptor(
                    remote_name=name.strip(),
                    title=(
                        tool.get("title")
                        if isinstance(tool.get("title"), str)
                        else None
                    ),
                    description=(
                        tool.get("description")
                        if isinstance(tool.get("description"), str)
                        else None
                    ),
                    input_schema=(
                        tool.get("inputSchema")
                        if isinstance(tool.get("inputSchema"), dict)
                        else None
                    ),
                    annotations=(
                        tool.get("annotations")
                        if isinstance(tool.get("annotations"), dict)
                        else None
                    ),
                    operation_class=(
                        meta.get("delpi/toolClass")
                        if isinstance(meta, dict)
                        and isinstance(
                            meta.get("delpi/toolClass"), str
                        )
                        else None
                    ),
                )
            )
        _logger.info(
            "interop catalog_source=snapshot owner=%s version=%s "
            "hash=%s correlation_id=%s",
            specialist.specialist_id,
            snap["catalog_version"],
            snap["contract_hash"][:12],
            request.correlation_id,
        )
        return tuple(descriptors)
