"""Composition root for Helpdesk governed writes.

Builds the BFF adapter once and binds the read + write ports into a
``HelpdeskWriteStack`` for ``GovernedWriteOrchestrator`` — application
code never instantiates infrastructure.
"""

from __future__ import annotations

from tm_app.application.helpdesk.helpdesk_write_port import HelpdeskWriteStack
from tm_app.infrastructure.gateways.helpdesk_bff_gateway import (
    HelpdeskBffGateway,
)
from tm_app.infrastructure.gateways.openai_file_gateway import (
    OpenAIFileGateway,
)


def build_helpdesk_write_stack() -> HelpdeskWriteStack:
    gateway = HelpdeskBffGateway()
    return HelpdeskWriteStack(
        read=gateway, write=gateway, files=OpenAIFileGateway()
    )
