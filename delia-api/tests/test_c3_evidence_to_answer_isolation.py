"""DELIA-C3 — evidence-to-answer isolation.

Bounded coverage for
DELIA-C3-EVIDENCE-TO-ANSWER-CAUSAL-REMEDIATION-AND-ISOLATION-01
(production incidents E1 ``fa4f6444`` / E2 ``a5283249``).

Proven defect (deterministic replay against real owner payload
shapes): capability-catalog descriptors returned by
``discover_delpi_information`` project through the business-record
channel. ``_resolver_entities`` prefers the ``candidates`` collection
(also a legitimate entity-resolution key), and the descriptor filter
vocabulary never covered the owner-published candidate shape
(``candidate_token``/``action_id``/``argument_schema``/
``semantic_hints``/``retrieval_score``/``required_arguments``/
``pagination_hints``). Consequences:

* ``_activity_outcome_summary`` emitted ``record_count`` for a
  DISCOVERY invocation — the "N registro(s) localizado(s)" activity
  observed in E1 was capability descriptors, never product records;
* ``outcome_facts`` marked ``has_business_evidence`` on a DISCOVERY
  outcome and suppressed the ``contract_facts`` fallback.

These tests pin the corrected boundary: descriptor-shaped entries are
never business records at any extraction site, while genuine
business/entity-resolution payloads keep projecting.
"""

from __future__ import annotations

from app.application.capability_provision.orchestration import (
    _activity_outcome_summary,
    _synthesis_records,
)
from app.application.capability_provision.outcome_assessment import (
    OUTCOME_CONTRACT_FACTS,
    assess_outcome,
    outcome_facts,
)
from app.application.capability_provision.paginated_result_semantics import (
    extract_pagination_envelope,
)
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)


def _outcome(
    group_id,
    remote_name,
    text,
    structured=None,
    status=SpecialistResultStatus.COMPLETED,
):
    return SpecialistOutcome(
        status=status,
        provenance=SpecialistResultProvenance(
            specialist_id=group_id,
            remote_name=remote_name,
            protocol=InteropProtocol.MCP,
            correlation_id="c",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text=text,
        structured=structured,
    )


def _facts(outcome, operation_class):
    return outcome_facts(
        outcome, operation_class, record_resolver=_synthesis_records
    )


# ------------------------------------------------------------------
# Real owner payload shapes (sanitized) captured by deterministic
# replay of the live DAVI/TÉO surfaces, 2026-10-29.
# ------------------------------------------------------------------

_DAVI_CANDIDATE = {
    "candidate_token": "<opaque>",
    "description": "Search products",
    "semantic_hints": {
        "entity": "product_search",
        "shape": "paged_list",
        "tags": ["products"],
    },
    "required_arguments": [],
    "argument_schema": {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "description": {"type": "string"},
        },
    },
    "pagination_hints": {"supports_page": True},
    "retrieval_score": 0.7196,
    "action_id": "search_products",
}

_DAVI_DISCOVER_STRUCTURED = {
    "query": "terminal bala",
    "top_k": 5,
    "candidate_count": 2,
    "eligible_action_count": 94,
    "candidates": [
        _DAVI_CANDIDATE,
        dict(_DAVI_CANDIDATE, action_id="get_product_stock"),
    ],
    "capability_surface": {
        "agent_directives": {"version": "2026.10.27.1"},
        "entities": {"product": {"filterable_fields": ["description"]}},
    },
}

_DAVI_EXECUTE_STRUCTURED = {
    "action_id": "search_products",
    "status": "ok",
    "entity": "product_search",
    "shape": "paged_list",
    "projection": "approved_fields",
    "data": {
        "items": [
            {
                "product_code": "10080092",
                "description": "TERM. BALA 0,50-2,27MM2 ESTANHADO",
                "group_category": "1008",
            },
            {
                "product_code": "10081004",
                "description": "TERM. BALA 1,00-2,50MM2 NIQUELADO",
                "group_category": "1008",
            },
        ],
        "page": 1,
        "page_size": 50,
        "total_pages": 1,
        "total": 2,
        "is_complete": True,
        "truncated": False,
    },
    "truncated": False,
    "is_complete": True,
    "response_bytes": 900,
}

_TEO_RECORD_READ_STRUCTURED = {
    "success": True,
    "message": "Registros.",
    "data": {
        "total": 2,
        "items": [
            {
                "processo_id": "p-1",
                "nome_processo": "Processo A",
                "updated_at": "2026-10-16T11:58:19-03:00",
            },
            {
                "processo_id": "p-2",
                "nome_processo": "Processo B",
                "updated_at": "2026-10-15T09:00:00-03:00",
            },
        ],
    },
}


# ------------------------------------------------------------------
# Incident E1/E2 — descriptor isolation (RED before the owner fix)
# ------------------------------------------------------------------


def test_discovery_candidates_never_project_as_business_records():
    """DAVI ``candidates`` are capability descriptors, not records.

    E1 replay: the "2 registro(s) localizado(s)" activity was this
    projection leaking catalog entries into the record channel.
    """
    outcome = _outcome(
        "davi",
        "discover_delpi_information",
        "Discovery completed.",
        structured=_DAVI_DISCOVER_STRUCTURED,
    )
    facts = _facts(outcome, SpecialistOperationClass.DISCOVERY)
    assert facts.records == ()
    assert facts.has_business_evidence is False


def test_synthesis_records_empty_for_discovery_payload():
    """The shared synthesis projection excludes descriptor entries —
    the descriptor filter, not the collection key, is the gate."""
    assert _synthesis_records(_DAVI_DISCOVER_STRUCTURED) == ()


def test_activity_summary_carries_no_record_count_for_discovery():
    """SOURCE_QUERY_COMPLETED may classify the call but must never
    count capability candidates as located business records."""
    outcome = _outcome(
        "davi",
        "discover_delpi_information",
        "Discovery completed.",
        structured=_DAVI_DISCOVER_STRUCTURED,
    )
    ref = _activity_outcome_summary(outcome)
    assert ref is not None
    assert ref.get("record_count") is None


def test_discovery_outcome_keeps_contract_facts_path():
    """With descriptors excluded, a DISCOVERY outcome carrying owner
    contract vocabulary projects ``contract_facts`` instead of
    pretending business evidence."""
    outcome = _outcome(
        "davi",
        "discover_delpi_information",
        "Discovery completed.",
        structured=_DAVI_DISCOVER_STRUCTURED,
    )
    facts = _facts(outcome, SpecialistOperationClass.DISCOVERY)
    assert facts.has_business_evidence is False
    assert any(
        "filterable_fields" in row for row in facts.contract_facts
    )
    # Contract rows never substitute for an undeclared intent — but
    # with the declared contract hypothesis they are the real answer.
    assert assess_outcome(facts).decision != OUTCOME_CONTRACT_FACTS
    verdict = assess_outcome(facts, contract_subject=True)
    assert verdict.decision == OUTCOME_CONTRACT_FACTS


def test_sparse_candidate_entry_still_excluded():
    """A lone ``candidate_token`` field already marks descriptor
    vocabulary — sparse entries cannot slip through."""
    outcome = _outcome(
        "davi",
        "discover_delpi_information",
        "Discovery completed.",
        structured={"candidates": [{"candidate_token": "<opaque>"}]},
    )
    facts = _facts(outcome, SpecialistOperationClass.DISCOVERY)
    assert facts.has_business_evidence is False


# ------------------------------------------------------------------
# Proven-correct projections — regression locks (stay GREEN)
# ------------------------------------------------------------------


def test_execute_products_envelope_projects_business_records():
    """E1 terminal shape: ``{action_id,status,data:{items,...}}``
    projects every product — an empty presentation proves the owner
    itself returned no items."""
    outcome = _outcome(
        "davi",
        "execute_delpi_information",
        "Execution completed.",
        structured=_DAVI_EXECUTE_STRUCTURED,
    )
    envelope = extract_pagination_envelope(outcome.structured)
    assert envelope is not None
    assert len(envelope.items) == 2
    facts = _facts(outcome, SpecialistOperationClass.READ)
    assert facts.has_business_evidence is True
    assert len(facts.records) == 2
    assert facts.records[0]["product_code"] == "10080092"


def test_teo_record_read_envelope_projects_business_records():
    """E2 shape: ``{success,message,data:{total,items}}`` projects —
    the owner surface is envelope-compatible."""
    outcome = _outcome(
        "teo",
        "record_read",
        "Registros.",
        structured=_TEO_RECORD_READ_STRUCTURED,
    )
    facts = _facts(outcome, SpecialistOperationClass.READ)
    assert facts.has_business_evidence is True
    assert facts.total_count == 2
    assert facts.records[0]["nome_processo"] == "Processo A"


def test_authoritative_empty_owner_page_stays_distinguishable():
    """Case A stays case A: a proven-empty owner page is explicit
    empty, not a projection failure."""
    outcome = _outcome(
        "teo",
        "record_read",
        "Registros.",
        structured={
            "success": True,
            "message": "Registros.",
            "data": {"total": 0, "items": []},
        },
    )
    facts = _facts(outcome, SpecialistOperationClass.READ)
    assert facts.records == ()
    assert facts.has_business_evidence is False
    assert facts.explicit_empty is True
    assert facts.total_count == 0


def test_dense_business_record_with_homonymous_fields_preserved():
    """A real business record whose fields merely share vocabulary
    fragments (``action_id`` as data) keeps its eligibility — the
    descriptor shape, not a single key, is the criterion."""
    record = {
        "processo_id": "p-1",
        "action_id": "instalar-sensor",
        "nome_processo": "Linha 3",
        "setor": "Producao",
        "quantidade": 12,
        "updated_at": "2026-10-16T11:58:19-03:00",
    }
    outcome = _outcome(
        "teo",
        "record_read",
        "Registros.",
        structured={"data": {"total": 1, "items": [record]}},
    )
    facts = _facts(outcome, SpecialistOperationClass.READ)
    assert facts.has_business_evidence is True
    assert facts.records[0]["nome_processo"] == "Linha 3"


def test_entity_resolution_candidates_still_project():
    """``candidates`` stays a preferred collection for genuine
    entity-resolution payloads — entries that are NOT descriptor-
    shaped remain resolvable entities."""
    outcome = _outcome(
        "teo",
        "record_read",
        "Registros.",
        structured={
            "candidates": [
                {"processo_id": "p-1", "nome_processo": "Proc A"},
                {"processo_id": "p-2", "nome_processo": "Proc B"},
            ]
        },
    )
    facts = _facts(outcome, SpecialistOperationClass.READ)
    assert facts.has_business_evidence is True
    assert len(facts.records) == 2
