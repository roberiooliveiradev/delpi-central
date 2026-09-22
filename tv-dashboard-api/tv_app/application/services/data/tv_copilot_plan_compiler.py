"""Legacy re-export — use ``presentation_mutation.plan_compiler``."""

from tv_app.application.services.data.presentation_mutation.plan_compiler import (  # noqa: F401
    CompiledPlan,
    PlanCompileError,
    compile_copilot_plan,
)
