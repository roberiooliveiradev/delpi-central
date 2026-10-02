"""TÉO dashboard analyze binding — C4-MCP-GOVERNED-READS-02.

Bounded direct read for exactly one capability:

  user text -> bounded model proposal (applicability + view only)
    -> deterministic validation (view allowlist, no other arguments)
    -> TÉO analyze via SpecialistInterop (direct tools/call — TÉO has
       no DAVI-style candidate flow)
    -> SpecialistOutcome (epistemic class stays OBSERVATION)

Ownership stays unchanged: transformometro-api enforces
transformometro view access and dashboard scope checks; the
authoritative source is the Transformômetro dashboard projection —
TÉO is only the interoperability specialist, never the source.

Only ``view`` is authorized, and only the ``summary`` view — the
frozen use case is a dashboard KPI summary. The full owner analyze
surface (filial/setor/process/revision/family/competencia filters and
``limit``) is intentionally NOT forwarded: the summary view does not
consume them, and least-access binding means they are rejected even
if a model proposes them.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any, Mapping

from app.application.interaction.contracts import (
    LIMITATION_RESULT_TRUNCATED,
)
from app.application.interaction.governed_read import (
    BoundDirectRead,
    GovernedReadBinding,
)
from app.application.model_invocation.contracts import ModelInvocationRequest
from app.application.model_invocation.errors import ModelInvocationError
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.domain.evidence.model import EpistemicClass, SourceRef
from app.domain.model_invocation.model import (
    InstructionLineage,
    ModelInvocationId,
)
from app.domain.specialist_interop.model import SpecialistOutcome
from app.domain.specialist_interop.rules import (
    GOVERNED_READ_TEO_ACTION_ID,
    GOVERNED_READ_TEO_CAPABILITY,
    GOVERNED_READ_TEO_SPECIALIST,
)


# The Transformômetro dashboard is the authoritative business source;
# TÉO is only the interoperability specialist (never the source).
TRANSFORMOMETRO_DASHBOARD_SOURCE = SourceRef(
    source_id="transformometro-dashboard",
    source_system="transformometro-api",
    provider_name="TÉO",
)

TEO_ANALYZE_BINDING = GovernedReadBinding(
    binding_id="teo.analyze",
    specialist_id=GOVERNED_READ_TEO_SPECIALIST,
    remote_capability=GOVERNED_READ_TEO_CAPABILITY,
    governed_action_id=GOVERNED_READ_TEO_ACTION_ID,
    source=TRANSFORMOMETRO_DASHBOARD_SOURCE,
)

# Least-access view surface: only the KPI summary is authorized for
# this slice. The owner contract offers meta|processes|instances|rows,
# which are NOT needed for the frozen use case and stay blocked.
ALLOWED_VIEWS = frozenset({"summary"})
# The summary view does not consume `limit` or any scope filter — the
# forwarded argument surface is exactly {"view"}.
ALLOWED_ARGUMENTS = frozenset({"view"})

PROPOSAL_INSTRUCTION_ID = "delia.governed_read.teo_analyze_args"
PROPOSAL_INSTRUCTION_VERSION = "1"
PROPOSAL_INSTRUCTION = """Decide whether the user message asks for the user's Transformometro
dashboard indicators or KPI summary, and propose bounded arguments for
the governed analyze read. Respond with JSON containing exactly the
fields "applicable" and "view".

- "applicable": true only when the user asks about Transformometro
  dashboard indicators, KPIs, results, savings, or a summary of them.
- "view": must be "summary" when applicable; null otherwise.
- Use null for "applicable" when uncertain.
- Never invent values, never emit any other field, never answer the
  question itself.
"""


def _proposal_lineage() -> InstructionLineage:
    return InstructionLineage(
        instruction_id=PROPOSAL_INSTRUCTION_ID,
        version=PROPOSAL_INSTRUCTION_VERSION,
        content_hash=hashlib.sha256(
            PROPOSAL_INSTRUCTION.encode("utf-8")
        ).hexdigest(),
    )


def _validate_proposal(proposal: Mapping[str, Any]) -> dict[str, Any] | None:
    """Deterministic bound: proposal is never authority.

    Any key outside {applicable, view} — including a model-proposed
    owner-schema field such as filial_id or limit — invalidates the
    proposal entirely. A non-allowlisted view means the read is not
    authorized for this input.
    """
    if set(proposal) - {"applicable", "view", "limitations"}:
        return None
    applicable = proposal.get("applicable")
    if isinstance(applicable, str):
        # Bounded tolerance for the proposal flag only — it decides
        # whether the already-validated read may run, never authority.
        applicable = applicable.strip().lower() == "true"
    if applicable is not True:
        return None
    view = proposal.get("view")
    if view is None:
        view = "summary"
    if not isinstance(view, str):
        return None
    view = view.strip().lower()
    if view not in ALLOWED_VIEWS:
        return None
    return {"view": view}


def render_dashboard_summary(
    outcome: SpecialistOutcome,
) -> tuple[str, tuple[str, ...]]:
    """Bounded deterministic rendering of the authoritative KPI summary.

    Only the owner-projected summary keys are read; values must be
    numeric — the model never sees or alters them. An empty
    authoritative summary is GROUNDED + empty, not a failure.
    """
    labels = {
        "solucoes_implementadas": "Soluções implementadas",
        "economia_bruta_total": "Economia bruta total",
        "economia_liquida_total": "Economia líquida total",
        "investimento_unico_total": "Investimento único total",
        "custo_recorrente_total": "Custo recorrente total",
        "custo_recursos_compartilhados_total": (
            "Custo de recursos compartilhados"
        ),
        "investimento_total": "Investimento total",
        "horas_economizadas_total": "Horas economizadas",
    }
    structured = (
        outcome.structured if isinstance(outcome.structured, Mapping) else {}
    )
    data = (
        structured.get("data")
        if isinstance(structured.get("data"), Mapping)
        else {}
    )
    summary = (
        data.get("summary") if isinstance(data.get("summary"), Mapping) else {}
    )

    limitations = list(outcome.limitations)
    if not outcome.is_complete:
        if LIMITATION_RESULT_TRUNCATED not in limitations:
            limitations.append(LIMITATION_RESULT_TRUNCATED)

    lines = []
    for key, label in labels.items():
        value = summary.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        lines.append(f"- {label}: {value}")

    if not lines:
        content = (
            "Não encontrei indicadores no dashboard do Transformômetro "
            "para o seu escopo."
        )
        return content, tuple(limitations)

    content = (
        "Resumo dos indicadores do seu Transformômetro:\n"
        + "\n".join(lines)
    )
    if not outcome.is_complete:
        content += "\nResultado parcial — pode haver mais dados na fonte."
    return content, tuple(limitations)


def build_teo_dashboard_analyze_read(
    interop: SpecialistInterop,
    *,
    invoke_model: InvokeModel | None = None,
    model_ref=None,
) -> BoundDirectRead:
    """Build the TÉO analyze bound read on the shared direct-read edge.

    Applicability is a model proposal only — deterministic validation
    and the static binding decide; without a model the read is never
    attempted (fail closed to the ordinary interaction path).
    """

    def build_arguments(input_text: str) -> Mapping[str, Any] | None:
        if invoke_model is None or model_ref is None:
            return None
        try:
            result = invoke_model.execute(
                ModelInvocationRequest(
                    invocation_id=ModelInvocationId(str(uuid.uuid4())),
                    model_ref=model_ref,
                    input_text=input_text,
                    task_purpose_id=PROPOSAL_INSTRUCTION_ID,
                    output_schema_id=PROPOSAL_INSTRUCTION_ID,
                    output_schema_version=PROPOSAL_INSTRUCTION_VERSION,
                    expected_fields=("applicable", "view"),
                    instruction_lineage=_proposal_lineage(),
                    instruction_content=PROPOSAL_INSTRUCTION,
                    timeout_seconds=10.0,
                    declared_epistemic_class=EpistemicClass.HYPOTHESIS,
                    untrusted_external_metadata={
                        "interaction_surface": "delia-mfe",
                        "input_kind": "governed_read_args",
                    },
                )
            )
        except ModelInvocationError:
            return None
        proposal = result.structured_output
        if not isinstance(proposal, Mapping):
            return None
        return _validate_proposal(proposal)

    return BoundDirectRead(
        interop,
        TEO_ANALYZE_BINDING,
        build_arguments=build_arguments,
        render=render_dashboard_summary,
    )
