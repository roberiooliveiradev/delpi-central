"""Task 08 (DELIA-C3-PYDANTICAI-STRUCTURED-DECISION-AB-01):
PydanticAI vs baseline structured-output reliability — isolated
evaluation harness.

Boundary: this file is EVALUATION-ONLY. It reuses the production
``InvokeModel`` use case and the real adapter parse for the baseline
arm, and compares it against (a) strict pydantic validation of the
same raw output (B0) and (b) a PydanticAI direct structured-output
request (B1) — all against the local Ollama evaluation model only.

Hard constraints (pinned by tests):
- pydantic_ai importable only inside function bodies — ``app/`` never
  sees the SDK.
- PYDANTICAI_RETRIES == 0: the framework may never retry; the governed
  DELIA_LLM_CALL_MAX_ATTEMPTS authority is untouched.
- USES_FUNCTION_TOOLS is False: no tool-calling output mode — the
  baseline contract forbids provider tool fields.
- The strict arm never claims semantic authority (``semantic_authority
  is False``): unknown capabilities, forged tokens and authorization
  stay with the existing downstream gates.

Baseline vs strict parity notes (documented contract):
- Baseline parse tolerates ```json fences — the strict arm uses the
  same parse for identical inputs (no false reject divergence).
- Baseline strips surplus keys to allowed_keys — the strict arm uses
  extra="ignore" + the same projection, so benign extras are not
  false rejects. extras_forbidden=True additionally REPORTS what a
  strict-forbid policy would flag, without changing acceptance.
- Baseline coerces unknown native_assessment status → "sufficient"
  (fail-open fallback). The strict arm fails closed — the corpus
  records this as an intentional divergence, not an automatic win.
"""

from __future__ import annotations

import dataclasses
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Mapping

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pydantic import BaseModel, ConfigDict, model_validator

from app.application.model_invocation.contracts import (
    ModelInvocationRequest,
    ProviderInvocationPayload,
)
from app.application.model_invocation.errors import (
    INVALID_STRUCTURED_OUTPUT,
    ModelInvocationError,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.domain.model_invocation.model import (
    EvidenceRef,
    InstructionLineage,
    InvocationFinishStatus,
    ModelInvocationId,
    ModelRef,
    ProviderExposureClass,
    SourceRef,
)
from app.infrastructure.model_invocation.openai_compatible_adapter import (
    OpenAICompatibleModelInvocationAdapter,
)
from datetime import datetime, timezone

PYDANTICAI_RETRIES = 0
USES_FUNCTION_TOOLS = False

# ------------------------------------------------------------------
# Equivalent strict schemas (B0) — same declared contract, typed.
# ------------------------------------------------------------------


class CapabilitySelectionProposal(BaseModel):
    """(applicable, capability_group_id) + optional limitations.

    Baseline passthrough: applicable=false needs no companion id —
    mirrored by the after-validator (required only when True).
    """

    model_config = ConfigDict(extra="ignore")

    applicable: bool
    capability_group_id: str | None = None
    limitations: list[str] | None = None

    @model_validator(mode="after")
    def _group_required_when_applicable(self):
        if self.applicable and not (
            isinstance(self.capability_group_id, str)
            and self.capability_group_id.strip()
        ):
            raise ValueError(
                "capability_group_id required when applicable is true"
            )
        return self


class InteractionAdmissionProposal(BaseModel):
    """requires_owner_surface + interaction_class in governed vocab."""

    model_config = ConfigDict(extra="ignore")

    requires_owner_surface: bool
    interaction_class: Literal[
        "conversation",
        "explanation",
        "hypothetical",
        "operational",
        "surface_inquiry",
        "ambiguous",
    ]
    limitations: list[str] | None = None


class NativeAssessmentProposal(BaseModel):
    """status ∈ governed vocabulary; unknown → fail closed.

    Baseline divergence (documented): unknown status is coerced to
    "sufficient" downstream — this schema exposes that coercion.
    """

    model_config = ConfigDict(extra="ignore")

    status: Literal[
        "sufficient",
        "foreign_evidence_required",
        "corroboration_requested",
    ]
    limitations: list[str] | None = None


SCHEMAS: dict[str, type[BaseModel]] = {
    "capability_selection": CapabilitySelectionProposal,
    "native_assessment": NativeAssessmentProposal,
    "interaction_admission": InteractionAdmissionProposal,
}

# allowed_keys projections, mirroring orchestration._propose contracts
ALLOWED_KEYS: dict[str, frozenset[str]] = {
    "capability_selection": frozenset(
        {"applicable", "capability_group_id", "limitations"}
    ),
    "native_assessment": frozenset({"status", "limitations"}),
    "interaction_admission": frozenset(
        {"requires_owner_surface", "interaction_class", "limitations"}
    ),
}


@dataclass(frozen=True)
class Verdict:
    accepted: bool
    projected: dict[str, Any] | None
    error_code: str | None = None
    # The strict arm NEVER claims semantic authority: unknown
    # capabilities, forged candidate tokens, authorization and
    # business semantics stay with the existing downstream gates.
    semantic_authority: bool = False
    extras_flagged: tuple[str, ...] = ()


@dataclass(frozen=True)
class CorpusCase:
    case_id: str
    raw: str
    expected_fields: tuple[str, ...]
    schema_key: str


@dataclass(frozen=True)
class LiveResult:
    arm: str
    scenario_id: str
    provider_requests: int
    input_tokens: int | None
    output_tokens: int | None
    token_source: str
    latency_ms: int
    invalid_output: bool
    structured_valid: bool
    error_code: str | None
    projected: dict[str, Any] | None


CORPUS: tuple[CorpusCase, ...] = (
    CorpusCase(
        "valid_selection",
        '{"applicable": true, "capability_group_id": "davi"}',
        ("applicable", "capability_group_id"),
        "capability_selection",
    ),
    CorpusCase(
        "malformed_json",
        '{"applicable": true, "capability_group_id": ',
        ("applicable", "capability_group_id"),
        "capability_selection",
    ),
    CorpusCase(
        "missing_required_field",
        '{"applicable": true}',
        ("applicable", "capability_group_id"),
        "capability_selection",
    ),
    CorpusCase(
        "wrong_field_type",
        '{"applicable": true, "capability_group_id": 5}',
        ("applicable", "capability_group_id"),
        "capability_selection",
    ),
    CorpusCase(
        "invalid_enum",
        '{"status": "maybe_foreign"}',
        ("status",),
        "native_assessment",
    ),
    CorpusCase(
        "extra_unexpected_properties",
        '{"applicable": true, "capability_group_id": "davi",'
        ' "hack": "x"}',
        ("applicable", "capability_group_id"),
        "capability_selection",
    ),
    CorpusCase(
        "non_object_output",
        '["applicable", "davi"]',
        ("applicable", "capability_group_id"),
        "capability_selection",
    ),
    CorpusCase(
        "applicable_false_passthrough",
        '{"applicable": false}',
        ("applicable", "capability_group_id"),
        "capability_selection",
    ),
    CorpusCase(
        "semantically_invalid_capability",
        '{"applicable": true, "capability_group_id": "no_such_group"}',
        ("applicable", "capability_group_id"),
        "capability_selection",
    ),
    CorpusCase(
        "fenced_json",
        '```json\n{"applicable": true, "capability_group_id": "davi"}\n```',
        ("applicable", "capability_group_id"),
        "capability_selection",
    ),
    CorpusCase(
        "forged_candidate_token",
        '{"applicable": true, "capability_group_id": "davi"}',
        ("applicable", "capability_group_id"),
        "capability_selection",
    ),
    CorpusCase(
        "empty_content",
        "   ",
        ("applicable", "capability_group_id"),
        "capability_selection",
    ),
)


# ------------------------------------------------------------------
# Baseline arm — REAL InvokeModel over a canned-response TEST_ONLY
# port; parse via the REAL adapter static (fence recovery included).
# ------------------------------------------------------------------


def _model_ref() -> ModelRef:
    return ModelRef(
        model_id="eval-structured-output",
        version="eval",
        owner_ref="DELPI",
        provider_ref="eval",
    )


def _request(expected_fields: tuple[str, ...]) -> ModelInvocationRequest:
    return ModelInvocationRequest(
        invocation_id=ModelInvocationId("eval-inv"),
        model_ref=_model_ref(),
        input_text="eval fixture",
        task_purpose_id="task08.structured_output",
        output_schema_id="task08.schema",
        output_schema_version="1",
        expected_fields=expected_fields,
        instruction_lineage=InstructionLineage(
            instruction_id="task08.instruction",
            version="1",
            content_hash="sha256:eval",
        ),
        timeout_seconds=5.0,
        evidence_refs=(EvidenceRef("ev-eval"),),
        source_refs=(SourceRef(source_id="src", source_system="eval"),),
        eval_bind=None,
    )


class _CannedResponsePort:
    """TEST_ONLY port returning the REAL-adapter parse of a canned
    raw string — exercises InvokeModel's real validation path."""

    ADAPTER_KIND = "TEST_ONLY"

    def __init__(self, raw: str) -> None:
        self._raw = raw

    @property
    def adapter_kind(self) -> str:
        return self.ADAPTER_KIND

    @property
    def exposure_class(self) -> ProviderExposureClass:
        return ProviderExposureClass.TEST_ONLY

    @property
    def context_window_tokens(self):
        return None

    @property
    def default_max_output_units(self):
        return None

    def invoke(self, request: ModelInvocationRequest) -> ProviderInvocationPayload:
        structured = OpenAICompatibleModelInvocationAdapter._parse_structured_output(
            self._raw
        )
        return ProviderInvocationPayload(
            structured_output=structured,
            generated_at=datetime.now(timezone.utc).isoformat(),
            finish_status=InvocationFinishStatus.COMPLETED,
            usage=None,
            duration_ms=0,
        )


def baseline_verdict(
    raw: str, *, expected: tuple[str, ...], schema_key: str | None = None
) -> Verdict:
    """REAL path: adapter parse → InvokeModel → expected-fields →
    allowed_keys projection (the _propose contract)."""
    try:
        result = InvokeModel(_CannedResponsePort(raw)).execute(
            _request(expected)
        )
    except ModelInvocationError as exc:
        return Verdict(
            accepted=False, projected=None, error_code=exc.code
        )
    proposal = dict(result.structured_output)
    key = schema_key or "capability_selection"
    projected = {
        k: v for k, v in proposal.items() if k in ALLOWED_KEYS[key]
    }
    applicable = projected.get("applicable")
    if isinstance(applicable, str):
        applicable = applicable.strip().lower() == "true"
    if applicable is False and "applicable" in expected:
        return Verdict(accepted=True, projected=projected)
    missing = [f for f in expected if f not in projected]
    if missing:
        return Verdict(
            accepted=False,
            projected=None,
            error_code="invalid_structured_output",
        )
    return Verdict(accepted=True, projected=projected)


def strict_verdict(
    raw: str, *, schema: str, extras_forbidden: bool = False
) -> Verdict:
    """B0: identical parse tolerance → strict pydantic schema →
    same projection contract. semantic_authority stays False."""
    try:
        parsed = OpenAICompatibleModelInvocationAdapter._parse_structured_output(raw)
    except ModelInvocationError as exc:
        return Verdict(
            accepted=False, projected=None, error_code=exc.code
        )
    model_cls = SCHEMAS[schema]
    extras = tuple(sorted(set(parsed) - set(model_cls.model_fields)))
    try:
        if extras_forbidden and extras:
            raise ValueError(f"unexpected properties: {extras}")
        proposal = model_cls.model_validate(parsed)
    except Exception:
        return Verdict(
            accepted=False,
            projected=None,
            error_code="invalid_structured_output",
            extras_flagged=extras,
        )
    return Verdict(
        accepted=True,
        projected={
            k: v
            for k, v in proposal.model_dump().items()
            if k in ALLOWED_KEYS[schema] and v is not None
        },
        extras_flagged=extras,
    )


# ------------------------------------------------------------------
# Live arms — local Ollama evaluation model only. Never wired into
# app/; every real provider request is counted.
# ------------------------------------------------------------------

OLLAMA_BASE_URL = "http://localhost:11434/v1"
EVAL_MODEL = "delia-json:latest"


def _directive(expected: tuple[str, ...]) -> str:
    fields = ", ".join(f'"{n}"' for n in expected)
    return (
        "Respond ONLY with a single JSON object. No prose, no markdown "
        f"fences. Required fields: {fields}. Use JSON types that match "
        "each field (string, number, boolean, object, or array). "
        'You MAY include "limitations": an array of short strings '
        "describing what could not be verified — omit it when the "
        "required fields alone answer the schema."
    )


def run_baseline_live(
    input_text: str,
    instruction: str,
    expected: tuple[str, ...],
    schema_key: str,
    *,
    base_url: str = OLLAMA_BASE_URL,
    model: str = EVAL_MODEL,
    scenario_id: str = "live",
) -> LiveResult:
    """Arm A — the real adapter + InvokeModel against local Ollama."""
    adapter = OpenAICompatibleModelInvocationAdapter(
        base_url=base_url,
        api_key="local-eval",
        model=model,
        timeout_seconds=60.0,
    )
    t0 = time.monotonic()
    try:
        # The real adapter performs provider call + parse; validation
        # then flows through the same canned-port path used by
        # baseline_verdict so the verdict contract is identical.
        payload = adapter.invoke(
            dataclasses.replace(
                _request(expected),
                input_text=input_text,
                instruction_content=instruction,
            )
        )
        verdict = baseline_verdict(
            json.dumps(payload.structured_output),
            expected=expected,
            schema_key=schema_key,
        )
        invalid = False
        error_code = None
    except ModelInvocationError as exc:
        verdict = Verdict(
            accepted=False, projected=None, error_code=exc.code
        )
        payload = None
        invalid = True
        error_code = exc.code
    latency = int((time.monotonic() - t0) * 1000)
    usage = getattr(payload, "usage", None)
    return LiveResult(
        arm="baseline",
        scenario_id=scenario_id,
        provider_requests=1,
        input_tokens=getattr(usage, "input_units", None),
        output_tokens=getattr(usage, "output_units", None),
        token_source="PROVIDER_REPORTED",
        latency_ms=latency,
        invalid_output=invalid,
        structured_valid=verdict.accepted,
        error_code=error_code,
        projected=verdict.projected,
    )


def run_pydanticai_live(
    input_text: str,
    instruction: str,
    expected: tuple[str, ...],
    schema_key: str,
    *,
    base_url: str = OLLAMA_BASE_URL,
    model: str = EVAL_MODEL,
    scenario_id: str = "live",
) -> LiveResult:
    """Arm B1 — PydanticAI direct request, native output mode, zero
    framework retries, zero function tools. SDK import is confined
    to this function."""
    from pydantic_ai import ModelRequest
    from pydantic_ai.direct import model_request_sync
    from pydantic_ai.output import OutputObjectDefinition
    from pydantic_ai.models import ModelRequestParameters
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    provider = OpenAIProvider(base_url=base_url, api_key="local-eval")
    params = ModelRequestParameters(
        output_mode="native",
        output_object=OutputObjectDefinition(
            json_schema=SCHEMAS[schema_key].model_json_schema(),
            name=SCHEMAS[schema_key].__name__,
            strict=True,
        ),
        allow_text_output=False,
    )
    t0 = time.monotonic()
    try:
        response = model_request_sync(
            OpenAIChatModel(model, provider=provider),
            [
                ModelRequest(
                    parts=[],
                    instructions=f"{instruction}\n\n{_directive(expected)}",
                ),
                ModelRequest.user_text_prompt(input_text),
            ],
            model_request_parameters=params,
        )
        raw = response.text or ""
        invalid = False
        error_code = None
        usage = response.usage
    except Exception as exc:  # provider/model errors stay typed
        raw = ""
        invalid = True
        error_code = type(exc).__name__
        usage = None
    latency = int((time.monotonic() - t0) * 1000)
    verdict = strict_verdict(raw, schema=schema_key) if raw else Verdict(
        accepted=False,
        projected=None,
        error_code=error_code or "invalid_structured_output",
    )
    return LiveResult(
        arm="pydanticai_native",
        scenario_id=scenario_id,
        provider_requests=1,
        input_tokens=getattr(usage, "input_tokens", None),
        output_tokens=getattr(usage, "output_tokens", None),
        token_source="PROVIDER_REPORTED",
        latency_ms=latency,
        invalid_output=invalid or not verdict.accepted,
        structured_valid=verdict.accepted,
        error_code=verdict.error_code or error_code,
        projected=verdict.projected,
    )


def run_corpus_eval() -> list[dict[str, Any]]:
    rows = []
    for case in CORPUS:
        base = baseline_verdict(
            case.raw,
            expected=case.expected_fields,
            schema_key=case.schema_key,
        )
        strict = strict_verdict(case.raw, schema=case.schema_key)
        forbid = strict_verdict(
            case.raw, schema=case.schema_key, extras_forbidden=True
        )
        rows.append(
            {
                "case_id": case.case_id,
                "schema_key": case.schema_key,
                "baseline": {
                    "accepted": base.accepted,
                    "error_code": base.error_code,
                    "projected": base.projected,
                },
                "strict": {
                    "accepted": strict.accepted,
                    "error_code": strict.error_code,
                    "projected": strict.projected,
                    "extras_flagged": strict.extras_flagged,
                },
                "strict_extras_forbidden": forbid.accepted,
            }
        )
    return rows


def main() -> int:
    rows = run_corpus_eval()
    print(json.dumps(rows, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
