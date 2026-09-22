"""Canonical PresentationMutation — typed ops for VISTA / future DÉLIA.

Owner of TvPresentationPatchV1. Persistence remains ``TvPresentationWriteService``.
"""

from __future__ import annotations

from tv_app.application.services.data.presentation_mutation.execution_context import (
    ExecutionContext,
    is_synthetic_id,
    mint_synthetic_id,
)
from tv_app.application.services.data.presentation_mutation.merge import (
    BLOCK_DEEP_MERGE_KEYS,
    deep_merge_dicts,
    merge_block_patch,
    merge_data_binding,
    merge_native_config_key,
)
from tv_app.application.services.data.presentation_mutation.patch_service import (
    PresentationPatchError,
    PresentationPatchService,
)
from tv_app.application.services.data.presentation_mutation.plan_compiler import (
    CompiledPlan,
    PlanCompileError,
    compile_presentation_plan,
)

__all__ = [
    "BLOCK_DEEP_MERGE_KEYS",
    "CompiledPlan",
    "ExecutionContext",
    "PlanCompileError",
    "PresentationPatchError",
    "PresentationPatchService",
    "compile_presentation_plan",
    "deep_merge_dicts",
    "is_synthetic_id",
    "merge_block_patch",
    "merge_data_binding",
    "merge_native_config_key",
    "mint_synthetic_id",
]
