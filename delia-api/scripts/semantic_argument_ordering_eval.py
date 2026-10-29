"""Task 14 (DELIA-C3-SEMANTIC-ARGUMENT-AND-ORDERING-REMEDIATION-01):

stage-local semantic eval — turn_goal + capability arguments against
the REAL governed instruction resource and the REAL TÉO ``record_read``
contract (inputSchema captured from the production container's own
list_tools()). Arms:

  baseline:   instruction file passed via --instructions (v25),
              schema file passed via --schema (undescribed params),
              NO declared_requirements projection (current behavior)
  correction: instruction file v26, schema with owner param
              descriptions, declared_requirements projected into the
              argument block — mirroring the corrected code path

Runs the real OpenAI-compatible adapter against the local Ollama
evaluation model. No production endpoints. The argument stage is
chained: business_subject/answer_requirements come from the SAME
case's real turn_goal output (the real pipeline feeds goal → args).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.application.model_invocation.contracts import (
    ModelInvocationRequest,
    ModelInvocationId,
    ProviderInvocationPayload,
)
from app.domain.evidence.model import (
    ModelRef,
    SourceRef,
)
from app.domain.model_invocation.model import (
    EvidenceRef,
    InstructionLineage,
)
from app.infrastructure.model_invocation.openai_compatible_adapter import (
    OpenAICompatibleModelInvocationAdapter,
)

OLLAMA_BASE_URL = "http://localhost:11434/v1"
EVAL_MODEL = "delia-json:latest"


def _model_ref() -> ModelRef:
    return ModelRef(
        model_id="eval-semantic-args",
        version="eval",
        owner_ref="DELPI",
        provider_ref="eval",
    )


def _request(
    input_text: str,
    block_tag: str,
    block_payload: str,
    instruction: str,
    instruction_id: str,
    expected_fields: tuple[str, ...],
    version: str,
) -> ModelInvocationRequest:
    return ModelInvocationRequest(
        invocation_id=ModelInvocationId("eval-t14"),
        model_ref=_model_ref(),
        input_text=(
            "<user_message>\n"
            + input_text
            + "\n</user_message>\n<"
            + block_tag
            + ">\n"
            + block_payload
            + "\n</"
            + block_tag
            + ">"
        ),
        task_purpose_id=instruction_id,
        output_schema_id=instruction_id,
        output_schema_version=version,
        expected_fields=expected_fields,
        instruction_lineage=InstructionLineage(
            instruction_id=instruction_id,
            version=version,
            content_hash="sha256:eval",
        ),
        instruction_content=instruction,
        timeout_seconds=60.0,
        evidence_refs=(EvidenceRef("ev-eval"),),
        source_refs=(SourceRef(source_id="src", source_system="eval"),),
        eval_bind=None,
    )


def _invoke(
    adapter,
    req: ModelInvocationRequest,
    allowed_keys: frozenset[str],
) -> tuple[dict[str, Any] | None, Any]:
    payload: ProviderInvocationPayload = adapter.invoke(req)
    structured = payload.structured_output
    if not isinstance(structured, Mapping):
        return None, payload.usage
    return (
        {k: v for k, v in structured.items() if k in allowed_keys},
        payload.usage,
    )


GOAL_INSTRUCTION_ID = "delia.capability_orchestration.turn_goal"
ARGUMENTS_INSTRUCTION_ID = "delia.capability_orchestration.arguments"

GOAL_KEYS = frozenset(
    {
        "goal_class",
        "comparison_requested",
        "output_mode",
        "execution_bound",
        "business_subject",
        "scope_constraints",
        "answer_requirements",
        "prior_evidence_sufficient",
        "contract_subject",
    }
)
ARG_KEYS = frozenset(
    {"arguments", "missing_inputs", "limitations", "selections"}
)


def _goal_block(input_text: str, descriptor: Mapping) -> str:
    """turn_goal receives no capability block — the instruction
    classifies the message alone (real contract)."""
    return "{}"


def _arguments_block(
    descriptor: Mapping[str, Any],
    business_subject: str | None,
    declared: Mapping[str, Any] | None,
) -> str:
    """Mirrors orchestration._build_arguments block construction —
    capability name + bounded description + verbatim input_schema +
    business_subject; the correction arm adds declared_requirements
    exactly as the fix projects them."""
    block: dict[str, Any] = {
        "capability": descriptor["remote_name"],
        "description": descriptor["description"],
        "input_schema": descriptor["input_schema"],
    }
    if business_subject:
        block["business_subject"] = business_subject
    if declared:
        block["declared_requirements"] = dict(declared)
    return json.dumps(block, ensure_ascii=False, default=str)


@dataclass(frozen=True)
class Case:
    case_id: str
    user_text: str
    # expected goal-stage semantics
    want_ordering: str | None = None  # newest_first | oldest_first
    want_min_items: int | None = None
    # expected argument-stage semantics
    q_should_be: str = "absent"  # absent | present | any
    want_action: str | None = None  # search | get
    note: str = ""


CORPUS: tuple[Case, ...] = (
    Case(
        "e2_incident",
        "Qual o último processo do Transforma+?",
        want_ordering="newest_first",
        q_should_be="absent",
        want_action="search",
        note="original incident — Transforma+ is the platform, "
        "not record content",
    ),
    Case(
        "latest_process",
        "Qual o último processo cadastrado?",
        want_ordering="newest_first",
        q_should_be="absent",
        want_action="search",
    ),
    Case(
        "latest_request",
        "Qual a solicitação mais recente?",
        want_ordering="newest_first",
        q_should_be="absent",
    ),
    Case(
        "three_recent",
        "Quais os três registros mais recentes?",
        want_ordering="newest_first",
        want_min_items=3,
        q_should_be="absent",
    ),
    Case(
        "recent_updated",
        "Mostre os processos atualizados recentemente.",
        want_ordering="newest_first",
        q_should_be="absent",
    ),
    Case(
        "count_processes",
        "Quantos processos existem?",
        q_should_be="absent",
    ),
    Case(
        "text_search",
        "Procure processos que contenham a palavra melhoria.",
        q_should_be="present",
        want_action="search",
        note="legitimate text filter — must NOT regress",
    ),
    Case(
        "by_id",
        "Mostre o processo com identificação 12345.",
        want_action="get",
        q_should_be="absent",
        note="identifier path — get, not text search",
    ),
    Case(
        "oldest_record",
        "Qual o registro mais antigo?",
        want_ordering="oldest_first",
        q_should_be="absent",
    ),
    Case(
        "list_all",
        "Liste os registros disponíveis.",
        q_should_be="absent",
        want_action="search",
    ),
)


def run_corpus(
    *,
    adapter,
    instructions: Mapping[str, str],
    version: str,
    descriptor: Mapping[str, Any],
    project_requirements: bool,
) -> dict[str, Any]:
    goal_text = instructions[GOAL_INSTRUCTION_ID]
    args_text = instructions[ARGUMENTS_INSTRUCTION_ID]
    cri_clause = instructions.get("_cri_clause")
    if cri_clause:
        goal_text = goal_text + cri_clause
    rows: list[dict[str, Any]] = []
    totals = {"calls": 0, "in_tok": 0, "out_tok": 0, "ms": 0}
    for case in CORPUS:
        started = time.monotonic()
        # --- stage 1: turn_goal (real instruction, real contract)
        greq = _request(
            case.user_text,
            "goal_context",
            _goal_block(case.user_text, descriptor),
            goal_text,
            GOAL_INSTRUCTION_ID,
            ("goal_class",),
            version,
        )
        goal, gu = _invoke(adapter, greq, GOAL_KEYS)
        # --- stage 2: arguments (real instruction + real block)
        reqs = None
        subject = None
        if goal:
            reqs = goal.get("answer_requirements")
            subject = goal.get("business_subject")
            if not isinstance(reqs, Mapping) or not reqs:
                reqs = None
        declared = (
            dict(reqs) if (project_requirements and reqs) else None
        )
        areq = _request(
            case.user_text,
            "schema",
            _arguments_block(descriptor, subject, declared),
            args_text,
            ARGUMENTS_INSTRUCTION_ID,
            ("arguments",),
            version,
        )
        args, au = _invoke(adapter, areq, ARG_KEYS)
        elapsed = int((time.monotonic() - started) * 1000)
        arguments = (
            args.get("arguments") if isinstance(args, Mapping) else None
        )
        q_val = (
            arguments.get("q")
            if isinstance(arguments, Mapping)
            else None
        )
        declared_obs = (
            dict(reqs) if isinstance(reqs, Mapping) else {}
        )
        ordering_ok = (
            case.want_ordering is None
            or declared_obs.get("ordering") == case.want_ordering
        )
        min_items_ok = (
            case.want_min_items is None
            or declared_obs.get("min_items") == case.want_min_items
        )
        q_ok = (
            case.q_should_be == "any"
            or (case.q_should_be == "absent" and not q_val)
            or (case.q_should_be == "present" and bool(q_val))
        )
        action_ok = (
            case.want_action is None
            or (
                isinstance(arguments, Mapping)
                and arguments.get("action") == case.want_action
            )
        )
        row = {
            "case": case.case_id,
            "goal": goal,
            "arguments": arguments,
            "missing_inputs": (
                args.get("missing_inputs") if args else None
            ),
            "checks": {
                "ordering": ordering_ok,
                "min_items": min_items_ok,
                "q": q_ok,
                "action": action_ok,
            },
            "ok": all(
                [ordering_ok, min_items_ok, q_ok, action_ok]
            ),
            "ms": elapsed,
        }
        for usage in (gu, au):
            totals["calls"] += 1
            if usage is not None:
                totals["in_tok"] += int(
                    getattr(usage, "input_tokens", 0) or 0
                )
                totals["out_tok"] += int(
                    getattr(usage, "output_tokens", 0) or 0
                )
        totals["ms"] += elapsed
        rows.append(row)
    passed = sum(1 for r in rows if r["ok"])
    return {
        "cases": rows,
        "summary": {
            "passed": passed,
            "total": len(rows),
            **totals,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instructions", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument(
        "--cri-clause",
        default=None,
        help="governed CRI requirements clause file appended to "
        "turn_goal exactly as the production orchestrator does when "
        "CRI is enabled",
    )
    parser.add_argument(
        "--project-requirements",
        action="store_true",
        help="correction arm: project declared_requirements",
    )
    parser.add_argument("--descriptor-name", default="record_read")
    args = parser.parse_args()

    instructions = json.loads(
        Path(args.instructions).read_text(encoding="utf-8")
    )["instructions"]
    if args.cri_clause:
        instructions["_cri_clause"] = json.loads(
            Path(args.cri_clause).read_text(encoding="utf-8")
        )["instruction_text"].strip()
    schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    descriptor = {
        "remote_name": args.descriptor_name,
        "description": schema["description"],
        "input_schema": schema["input_schema"],
    }
    adapter = OpenAICompatibleModelInvocationAdapter(
        base_url=OLLAMA_BASE_URL,
        api_key="local-eval",
        model=EVAL_MODEL,
        timeout_seconds=60.0,
    )
    result = run_corpus(
        adapter=adapter,
        instructions=instructions,
        version=args.version,
        descriptor=descriptor,
        project_requirements=args.project_requirements,
    )
    print(json.dumps(result, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
