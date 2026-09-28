"""Composition root for the Diagnostic governed-write stack.

Single place that wires concrete authorities into the application ports —
interface layers call this instead of instantiating repositories inline.
"""

from __future__ import annotations

from tm_app.application.governed_writes.diagnostic_capabilities import (
    DiagnosticWriteStack,
)
from tm_app.application.use_cases.diagnostic_write import DiagnosticWriteUseCase
from tm_app.infrastructure.persistence.repositories.diagnostic_readers import (
    EvidenceReaderAdapter,
    RevisionReaderAdapter,
)
from tm_app.infrastructure.persistence.repositories.diagnostic_repository import (
    DiagnosticRepository,
)
from tm_app.infrastructure.security.diagnostic_authorization import (
    FreshAuthorizationAdapter,
)


def build_diagnostic_write_stack() -> DiagnosticWriteStack:
    return DiagnosticWriteStack(
        use_case=DiagnosticWriteUseCase(
            diagnostics=DiagnosticRepository(),
            revisions=RevisionReaderAdapter(),
            evidence=EvidenceReaderAdapter(),
            authorization=FreshAuthorizationAdapter(),
        ),
        diagnostics=DiagnosticRepository(),
        revisions=RevisionReaderAdapter(),
        evidence=EvidenceReaderAdapter(),
    )
