"""Legacy re-export — use ``presentation_mutation.execution_context``."""

from tv_app.application.services.data.presentation_mutation.execution_context import (  # noqa: F401
    ExecutionContext,
    is_synthetic_id,
    mint_synthetic_id,
)
