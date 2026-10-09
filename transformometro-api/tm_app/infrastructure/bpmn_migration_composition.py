"""Composition root for the G8 migration governed capability.

Mirrors diagnostic_composition / helpdesk_composition: interface layer
wires concrete repositories + use cases into the application's
MigrationWriteStack — application never instantiates infrastructure.
"""

from __future__ import annotations

from tm_app.application.governed_writes.bpmn_migration_capability import (
    MigrationWriteStack,
)
from tm_app.application.use_cases.manage_process_bpmn_document import (
    ProcessBpmnDocumentUseCases,
)
from tm_app.application.use_cases.migrate_legacy_diagram_to_bpmn import (
    MigrateLegacyDiagramToBpmnUseCase,
)
from tm_app.infrastructure.persistence.repositories.process_bpmn_document_repository import (
    ProcessBpmnDocumentRepository,
)
from tm_app.infrastructure.persistence.repositories.process_bpmn_migration_repository import (
    ProcessBpmnMigrationRepository,
)
from tm_app.infrastructure.persistence.repositories.process_bpmn_reference_repository import (
    ProcessBpmnReferenceRepository,
)


def build_migration_write_stack() -> MigrationWriteStack:
    docs = ProcessBpmnDocumentRepository()
    refs = ProcessBpmnReferenceRepository()
    migrations = ProcessBpmnMigrationRepository()
    return MigrationWriteStack(
        use_case=MigrateLegacyDiagramToBpmnUseCase(
            docs=docs,
            refs=refs,
            migrations=migrations,
            document_use_cases=ProcessBpmnDocumentUseCases(docs, refs),
        ),
        docs=docs,
        refs=refs,
        migrations=migrations,
    )
