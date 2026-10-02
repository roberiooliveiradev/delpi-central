"""Governed Product Master read — C4-MCP-GOVERNED-READS-01.

Bounded vertical slice for exactly one governed read:

  user text -> DAVI discover_delpi_information
    -> exactly one candidate with action_id == "search_products"
    -> schema-bounded arguments (model proposal is never authority)
    -> DAVI execute_delpi_information
    -> SpecialistOutcome (epistemic class stays OBSERVATION)

Ownership stays unchanged: DAVI selects eligible candidates and mints
opaque candidate tokens; API DELPI enforces Product Master AuthZ and
the approved projection; DÉLIA only orchestrates, validates bounds,
and records provenance. No direct Product adapter, no generic MCP
proxy, no second Product schema.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any, Mapping

from app.application.interaction.contracts import (
    LIMITATION_RESULT_TRUNCATED,
)
from app.application.interaction.governed_read import (
    GovernedReadAttempt,
    GovernedReadBinding,
    GovernedReadStatus,
    _error_attempt,
    _success_attempt,
)
from app.application.model_invocation.contracts import ModelInvocationRequest
from app.application.model_invocation.errors import ModelInvocationError
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.specialist_interop.contracts import (
    SpecialistInvocationRequest,
)
from app.application.specialist_interop.errors import (
    SpecialistInteropError,
)
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.domain.evidence.model import EpistemicClass, SourceRef
from app.domain.specialist_interop.model import SpecialistOutcome
from app.domain.model_invocation.model import (
    InstructionLineage,
    ModelInvocationId,
)
from app.domain.specialist_interop.rules import (
    GOVERNED_READ_ACTION_ID,
    GOVERNED_READ_DISCOVERY_CAPABILITY,
    GOVERNED_READ_EXECUTE_CAPABILITY,
    GOVERNED_READ_SPECIALIST,
)


# Canonical binding lives in the domain registry (rules.py) — this
# module never names a specialist id literal itself.
SPECIALIST_ID = GOVERNED_READ_SPECIALIST
DISCOVERY_CAPABILITY = GOVERNED_READ_DISCOVERY_CAPABILITY
EXECUTE_CAPABILITY = GOVERNED_READ_EXECUTE_CAPABILITY
GOVERNED_ACTION_ID = GOVERNED_READ_ACTION_ID

# Product Master / API DELPI is the authoritative business source;
# DAVI is only the interoperability specialist (never the source).
PRODUCT_MASTER_SOURCE = SourceRef(
    source_id="product-master",
    source_system="api-delpi",
    provider_name="DAVI",
)

# Static binding identity for this slice.
DAVI_PRODUCT_BINDING = GovernedReadBinding(
    binding_id="davi.search_products",
    specialist_id=GOVERNED_READ_SPECIALIST,
    remote_capability=GOVERNED_READ_EXECUTE_CAPABILITY,
    governed_action_id=GOVERNED_READ_ACTION_ID,
    source=PRODUCT_MASTER_SOURCE,
)

# Bounded argument surface authorized for the search_products action.
# Everything else — including DAVI-internal fields such as
# customer_reference — is rejected even if a model proposes it.
ALLOWED_ARGUMENT_FIELDS = frozenset(
    {"code", "description", "group_code", "page", "page_size"}
)
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50
MAX_TEXT_ARGUMENT_CHARS = 200
MAX_DISCOVERY_QUERY_CHARS = 400

EXTRACTION_INSTRUCTION_ID = "delia.governed_read.product_args"
EXTRACTION_INSTRUCTION_VERSION = "1"
EXTRACTION_INSTRUCTION = """Extract product-search filters from the user message for a
governed DELPI product-catalog search. Respond with JSON containing
exactly the fields "code", "description", and "group_code".

- "code": the exact product code the user asked for, if any.
- "description": the product description/name fragment to search for.
- "group_code": the product group code, if the user specified one.
- Use null for any field the user did not specify.
- Never invent values, never emit any other field, never answer the
  question itself.
"""


def _extraction_lineage() -> InstructionLineage:
    return InstructionLineage(
        instruction_id=EXTRACTION_INSTRUCTION_ID,
        version=EXTRACTION_INSTRUCTION_VERSION,
        content_hash=hashlib.sha256(
            EXTRACTION_INSTRUCTION.encode("utf-8")
        ).hexdigest(),
    )


class GovernedProductRead:
    """Orchestrates the single authorized DAVI Product Master read.

    The model may propose bounded search arguments; deterministic
    validation against the candidate's own schema decides. Discovery,
    model output, and candidate tokens are never authority.
    """

    def __init__(
        self,
        interop: SpecialistInterop,
        invoke_model: InvokeModel | None = None,
        model_ref=None,
    ) -> None:
        self._interop = interop
        self._invoke_model = invoke_model
        self._model_ref = model_ref

    def attempt(
        self, input_text: str, *, correlation_id: str | None = None
    ) -> GovernedReadAttempt:
        """Try the bounded DAVI search_products read; fail closed.

        NOT_APPLICABLE = no read was authorized/needed for this input.
        SOURCE_UNAVAILABLE = a read was applicable or applicability is
        unknown and the authoritative source could not be consulted.
        AUTHZ_DENIED = downstream authority denied the read.
        """
        correlation = correlation_id or str(uuid.uuid4())

        try:
            discovery = self._interop.invoke(
                SpecialistInvocationRequest(
                    specialist_id=SPECIALIST_ID,
                    remote_capability=DISCOVERY_CAPABILITY,
                    correlation_id=correlation,
                    arguments={
                        "query": input_text[:MAX_DISCOVERY_QUERY_CHARS]
                    },
                )
            )
        except SpecialistInteropError as exc:
            # R1: with this slice active, any failure to establish or
            # consult the authoritative source — including an
            # unconfigured or disabled specialist — is a source
            # availability failure, never silent evidence that the
            # question was unrelated. The user-facing result must
            # disclose that current DELPI data was not verified.
            return GovernedReadAttempt(
                status=GovernedReadStatus.SOURCE_UNAVAILABLE,
                correlation_id=correlation,
                error_code=exc.code,
            )

        candidate = self._select_search_products_candidate(
            discovery.structured
        )
        if candidate is None:
            return GovernedReadAttempt(
                status=GovernedReadStatus.NOT_APPLICABLE,
                correlation_id=correlation,
            )

        arguments = self._build_arguments(input_text, candidate)
        if arguments is None:
            return GovernedReadAttempt(
                status=GovernedReadStatus.NOT_APPLICABLE,
                correlation_id=correlation,
            )

        try:
            outcome = self._interop.invoke(
                SpecialistInvocationRequest(
                    specialist_id=SPECIALIST_ID,
                    remote_capability=EXECUTE_CAPABILITY,
                    correlation_id=correlation,
                    governed_action_id=GOVERNED_ACTION_ID,
                    arguments={
                        "candidate_token": candidate["candidate_token"],
                        "arguments": arguments,
                    },
                )
            )
        except SpecialistInteropError as exc:
            return _error_attempt(correlation, exc)

        return _success_attempt(
            correlation_id=correlation,
            binding=DAVI_PRODUCT_BINDING,
            outcome=outcome,
            render=render_product_search,
        )

    def _select_search_products_candidate(
        self, structured: Mapping[str, object] | None
    ) -> Mapping[str, Any] | None:
        """Exactly one eligible search_products candidate or no read.

        Retrieval scores, descriptions, and annotations are relevance
        hints only — only the action_id binding authorizes the read.
        Zero or ambiguous candidates fail closed.
        """
        if not isinstance(structured, Mapping):
            return None
        candidates = structured.get("candidates")
        if not isinstance(candidates, (list, tuple)):
            return None
        matching = [
            candidate
            for candidate in candidates
            if isinstance(candidate, Mapping)
            and candidate.get("action_id") == GOVERNED_ACTION_ID
            and isinstance(candidate.get("candidate_token"), str)
            and candidate["candidate_token"].strip()
        ]
        if len(matching) != 1:
            return None
        return matching[0]

    def _build_arguments(
        self, input_text: str, candidate: Mapping[str, Any]
    ) -> dict[str, Any] | None:
        """Validate model-proposed args against the candidate schema."""
        proposal = self._propose_arguments(input_text)
        if proposal is None:
            return None
        schema = candidate.get("argument_schema")
        schema_properties = (
            schema.get("properties")
            if isinstance(schema, Mapping)
            else None
        )
        required = {
            str(name)
            for name in (candidate.get("required_arguments") or [])
            if isinstance(name, str)
        }

        arguments: dict[str, Any] = {}
        for key, value in proposal.items():
            if key not in ALLOWED_ARGUMENT_FIELDS:
                # Any forbidden/unknown proposal key invalidates the read.
                return None
            if key in ("page", "page_size"):
                if not isinstance(value, int) or isinstance(value, bool):
                    return None
                arguments[key] = value
                continue
            if value is None:
                continue
            if not isinstance(value, str):
                return None
            text = value.strip()
            if not text or len(text) > MAX_TEXT_ARGUMENT_CHARS:
                return None
            arguments[key] = text

        if isinstance(schema_properties, Mapping):
            arguments = {
                key: value
                for key, value in arguments.items()
                if key in schema_properties
            }
        if not required.issubset(arguments):
            return None

        arguments.setdefault("page", DEFAULT_PAGE)
        page_size = arguments.setdefault("page_size", DEFAULT_PAGE_SIZE)
        if page_size < 1 or page_size > MAX_PAGE_SIZE:
            arguments["page_size"] = min(max(page_size, 1), MAX_PAGE_SIZE)
        if arguments["page"] < 1:
            return None
        return arguments

    def _propose_arguments(
        self, input_text: str
    ) -> Mapping[str, Any] | None:
        """Model-assisted proposal; deterministic fallback without one.

        The model output is only a proposal — it is validated field by
        field before any wire call. Without a model the bounded fallback
        is a plain description search over the user's text.
        """
        if self._invoke_model is None or self._model_ref is None:
            return {"description": input_text[:MAX_TEXT_ARGUMENT_CHARS]}
        try:
            result = self._invoke_model.execute(
                ModelInvocationRequest(
                    invocation_id=ModelInvocationId(str(uuid.uuid4())),
                    model_ref=self._model_ref,
                    input_text=input_text,
                    task_purpose_id=EXTRACTION_INSTRUCTION_ID,
                    output_schema_id=EXTRACTION_INSTRUCTION_ID,
                    output_schema_version=EXTRACTION_INSTRUCTION_VERSION,
                    expected_fields=("code", "description", "group_code"),
                    instruction_lineage=_extraction_lineage(),
                    instruction_content=EXTRACTION_INSTRUCTION,
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
        # "limitations" is the canonical model-envelope key, not an
        # argument proposal — it is dropped, never forwarded to the
        # wire. Any other key outside the bounded argument surface —
        # including a model-proposed forbidden field — invalidates the
        # proposal entirely.
        extra_keys = set(proposal) - ALLOWED_ARGUMENT_FIELDS - {"limitations"}
        if extra_keys:
            return None
        return {
            key: value
            for key, value in proposal.items()
            if key in ALLOWED_ARGUMENT_FIELDS
        }


_MAX_DISPLAYED_PRODUCT_ITEMS = 10


def render_product_search(
    outcome: SpecialistOutcome,
) -> tuple[str, tuple[str, ...]]:
    """Bounded deterministic rendering of the authoritative result.

    The remote payload is untrusted content: only the approved
    projected fields are read, item count is display-bounded, and
    truncation is surfaced as an explicit limitation. An empty
    authoritative search is GROUNDED + empty — not a failure.
    """
    structured = (
        outcome.structured if isinstance(outcome.structured, Mapping) else {}
    )
    data = (
        structured.get("data")
        if isinstance(structured.get("data"), Mapping)
        else {}
    )
    raw_items = (
        data.get("items")
        if isinstance(data.get("items"), (list, tuple))
        else []
    )
    items = [item for item in raw_items if isinstance(item, Mapping)]

    limitations = list(outcome.limitations)
    truncated = bool(
        structured.get("truncated")
        or not outcome.is_complete
        or (
            isinstance(data.get("pagination"), Mapping)
            and data["pagination"].get("has_next") is True
        )
    )
    if truncated and LIMITATION_RESULT_TRUNCATED not in limitations:
        limitations.append(LIMITATION_RESULT_TRUNCATED)

    if not items:
        content = (
            "Não encontrei produtos no Cadastro de Produtos DELPI com "
            "esses critérios."
        )
        return content, tuple(limitations)

    lines = []
    for item in items[:_MAX_DISPLAYED_PRODUCT_ITEMS]:
        code = str(item.get("product_code") or "").strip()
        description = str(item.get("description") or "").strip()
        group = str(item.get("group_category") or "").strip()
        label = f"{code} — {description}" if code else description
        if group:
            label = f"{label} (grupo {group})" if label else group
        if label:
            lines.append(f"- {label}")

    header = (
        f"Encontrei {len(items)} produto(s) no Cadastro de Produtos "
        "DELPI:"
    )
    content = header + ("\n" + "\n".join(lines) if lines else "")
    if len(items) > _MAX_DISPLAYED_PRODUCT_ITEMS:
        content += (
            f"\n…e mais {len(items) - _MAX_DISPLAYED_PRODUCT_ITEMS} "
            "item(ns)."
        )
    if truncated:
        content += "\nResultado parcial — pode haver mais itens na fonte."
    return content, tuple(limitations)
