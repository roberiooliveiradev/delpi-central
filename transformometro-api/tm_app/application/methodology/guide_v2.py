"""TÉO methodology intelligence V2 — structured canonical definition.

``teo-method-playbooks-v2`` adds intent routing, method applicability,
readiness, soft composition, sufficiency/stop conditions, next-question
metadata and epistemic constraints on top of the V1 editorial playbooks.

One semantic authority: this module is the ONLY structured source for V2
routing/applicability/readiness. Human guidance prose stays owned by
``guide.py`` (V1 playbook entries) — V2 projects both from the same method
ids; it never restates V1 prose as a second editable truth.

Methodology = guidance, not source of truth: read_only, no writes, no
persistence, no authorization, no domain state.
"""

from __future__ import annotations

from typing import Any, Mapping

from tm_app.application.methodology.guide import (
    AUTHORITY,
    EVIDENCE_STATES,
    INVARIANTS,
    _METHODS,
    _norm,
    _resolve_method,
    list_method_ids,
)

GUIDE_VERSION_V1 = "teo-method-playbooks-v1"
GUIDE_VERSION_V2 = "teo-method-playbooks-v2"
SUPPORTED_GUIDE_VERSIONS = (GUIDE_VERSION_V1, GUIDE_VERSION_V2)
WIRE_DEFAULT_GUIDE_VERSION = GUIDE_VERSION_V1
RECOMMENDED_GUIDE_VERSION = GUIDE_VERSION_V2

INTENT_IDS = (
    "discover",
    "map",
    "diagnose",
    "redesign",
    "measure",
    "prioritize",
    "interview",
    "strategic_analysis",
    "improve",
)

READINESS_STATES = ("READY", "PARTIAL", "NOT_READY", "UNKNOWN")
SUFFICIENCY_STATES = ("SUFFICIENT", "NOT_SUFFICIENT", "UNKNOWN")
STOP_REASONS = (
    "PURPOSE_ACHIEVED",
    "REMAINING_UNKNOWN_NON_BLOCKING",
    "NEXT_QUESTION_LOW_MATERIALITY",
    "SPECULATION_RISK",
    "BETTER_METHOD_AVAILABLE",
)
QUESTION_KINDS = ("clarifying", "readiness", "evidence", "deepening")

# Closed vocabulary of process-context facts the router may consult.
# Tri-state/epistemic values — never new domain fields (spec §22).
CONTEXT_FACTS = (
    "organization_context",
    "macroprocess_known",
    "process_identified",
    "boundary_known",
    "as_is_known",
    "flow_known",
    "problem_defined",
    "candidate_cause",
    "candidates_known",
    "multiple_cause_families",
    "causes_open",
    "waste_symptoms",
    "operational_cause_focus",
    "objective_known",
    "future_state_proposed",
    "future_defined",
    "redesign_desired",
    "measurement_available",
    "strategic_question",
    "scope_defined",
    "horizon_defined",
)

_YES = frozenset({"yes", "true", "present", "known", "observed", "informed", "calculated"})
_NO = frozenset({"no", "false", "missing", "absent"})


def _fact_token(value: Any) -> str:
    """Normalize a context fact to a state token.

    True → ``yes``; False → ``no``; absent/unknown-ish → ``unknown``;
    epistemic strings keep their token (``inferred``, ``proposed``,
    ``partial``) so per-method ``accepts`` rules decide adequacy.
    """
    if value is None:
        return "unknown"
    if isinstance(value, bool):
        return "yes" if value else "no"
    token = _norm(str(value)) or "unknown"
    if token in _YES:
        return "yes"
    if token in _NO:
        return "no"
    if token in ("inferred", "proposed", "partial"):
        return token
    return "unknown"


def _req(fact: str, *accepts: str) -> dict[str, Any]:
    return {"fact": fact, "accepts": list(accepts) or ["yes"]}


def _gap(fact: str, text: str) -> dict[str, Any]:
    return {
        "id": f"gap_{fact}",
        "text": text,
        "kind": "readiness",
        "resolves": fact,
    }


_METHOD_SEMANTICS: dict[str, dict[str, Any]] = {
    "macroprocess": {
        "intents": ("discover",),
        "minimum_information": [],
        "epistemic_constraints": (
            "Candidate macroprocesses stay INFERRED until user-validated.",
            "Value-chain categories are a lens, not company facts.",
        ),
        "sufficiency": {
            "stop_when": (
                "Value chain is coherent and MECE enough to proceed.",
                "Further drilling would need domain facts not yet available.",
            ),
            "not_sufficient_when": ("Major overlaps or uncovered scopes remain.",),
        },
        "gap_questions": (
            _gap("organization_context", "What does the organization deliver, and to whom?"),
        ),
    },
    "key_process": {
        "intents": ("discover",),
        "minimum_information": [_req("macroprocess_known")],
        "favored_all": ("macroprocess_known",),
        "epistemic_constraints": (
            "Key-process candidates stay PROPOSED until validated.",
        ),
        "sufficiency": {
            "stop_when": ("Key processes produce distinct outcomes and are validated.",),
            "not_sufficient_when": ("The macroprocess itself is not established.",),
        },
        "gap_questions": (
            _gap("macroprocess_known", "Which macroprocess does this improvement belong to?"),
        ),
    },
    "sipoc": {
        "intents": ("map", "interview"),
        "minimum_information": [_req("process_identified")],
        # Boundary/supplier UNKNOWNs are the reason SIPOC exists — never blockers.
        "favored_all": ("process_identified",),
        "disfavored_when": ("boundary_known", "future_defined"),
        "epistemic_constraints": (
            "AS-IS entries must not embed improvement proposals.",
            "Unknown suppliers/inputs stay UNKNOWN — never invented.",
        ),
        "sufficiency": {
            "stop_when": (
                "Boundary, phases and handoffs are consistent enough for the next method.",
                "Remaining gaps are recorded UNKNOWN without blocking.",
            ),
            "not_sufficient_when": ("The process itself is not identified.",),
        },
        "gap_questions": (
            _gap("process_identified", "Which process or work should be framed?"),
        ),
    },
    "end_to_end": {
        "intents": ("map",),
        "minimum_information": [_req("process_identified"), _req("boundary_known")],
        "favored_all": ("process_identified", "boundary_known"),
        "epistemic_constraints": (
            "Missing stages stay UNKNOWN — not invented.",
        ),
        "sufficiency": {
            "stop_when": ("Trigger-to-outcome flow with handoffs is stable.",),
            "not_sufficient_when": ("Trigger or final outcome still unknown.",),
        },
        "gap_questions": (
            _gap("boundary_known", "What event starts this process and what outcome ends it?"),
        ),
    },
    "as_is": {
        "intents": ("map",),
        "minimum_information": [_req("process_identified")],
        "favored_all": ("process_identified", "flow_known"),
        "epistemic_constraints": (
            "AS-IS stays OBSERVED/INFORMED and separate from PROPOSED.",
            "A draft AS-IS is DRAFT — never ACTIVE state.",
        ),
        "sufficiency": {
            "stop_when": ("Current state is described well enough for the declared goal.",),
            "not_sufficient_when": ("Observed and proposed statements are still mixed.",),
        },
        "gap_questions": (
            _gap("process_identified", "Which current process should be described?"),
        ),
    },
    "lean": {
        "intents": ("diagnose",),
        "minimum_information": [_req("flow_known", "yes", "partial")],
        "favored_all": ("flow_known",),
        "favored_any": ("waste_symptoms", "operational_cause_focus"),
        "epistemic_constraints": (
            "Pattern recognition stays INFERRED — a Lean label is not a measured gain.",
        ),
        "sufficiency": {
            "stop_when": (
                "Waste hypotheses are labelled with evidence state and next lens adds no value.",
            ),
            "not_sufficient_when": ("The current flow is not known enough.",),
        },
        "gap_questions": (
            _gap("flow_known", "How does the work flow today, from start to finish?"),
            _gap("waste_symptoms", "Where does the work wait, return or get redone?"),
        ),
    },
    "ishikawa": {
        "intents": ("diagnose",),
        "minimum_information": [_req("problem_defined")],
        "favored_all": ("problem_defined",),
        "favored_any": ("multiple_cause_families", "causes_open"),
        "epistemic_constraints": (
            "TÉO-suggested causes stay INFERRED until evidence validates them.",
            "suggested cause != proven cause.",
        ),
        "sufficiency": {
            "stop_when": (
                "Cause families are MECE enough and a candidate line is selected.",
            ),
            "not_sufficient_when": ("The effect is not yet defined.",),
        },
        "gap_questions": (
            _gap("problem_defined", "What exactly is the problem or effect, and how is it recognized?"),
        ),
    },
    "five_whys": {
        "intents": ("diagnose",),
        "minimum_information": [
            _req("problem_defined"),
            _req("candidate_cause", "yes", "inferred", "proposed"),
        ],
        "favored_all": ("problem_defined", "candidate_cause"),
        "epistemic_constraints": (
            "INFERRED candidate satisfies 'candidate causal line' but is never "
            "promoted to validated cause by this method.",
            "5th why != proven root cause — stop when the next why is UNKNOWN.",
        ),
        "sufficiency": {
            "stop_when": (
                "The chain reaches a testable candidate or UNKNOWN without ritual 'five'.",
                "Continuing would require speculation.",
            ),
            "not_sufficient_when": ("No candidate causal line exists yet.",),
        },
        "gap_questions": (
            _gap("problem_defined", "What is the defined effect the chain should explain?"),
            _gap("candidate_cause", "Which single cause or family should be deepened first?"),
        ),
    },
    "ctp": {
        "intents": ("prioritize",),
        "minimum_information": [_req("candidates_known")],
        "favored_all": ("candidates_known",),
        "epistemic_constraints": (
            "Suggested scores stay PROPOSED until corrected by the user.",
        ),
        "sufficiency": {
            "stop_when": ("Priorities separate criticality from implementability.",),
            "not_sufficient_when": ("No candidate factors are on the table.",),
        },
        "gap_questions": (
            _gap("candidates_known", "Which candidate causes or factors should be prioritized?"),
        ),
    },
    "tdr": {
        "intents": ("redesign",),
        "minimum_information": [_req("as_is_known", "yes", "partial")],
        "favored_all": ("as_is_known", "redesign_desired"),
        "disfavored_when": ("future_defined",),
        "epistemic_constraints": (
            "Redesign proposals stay PROPOSED; automation opportunity != authorization.",
        ),
        "sufficiency": {
            "stop_when": (
                "Each relevant step was challenged and a PROPOSED TO-BE exists.",
            ),
            "not_sufficient_when": ("AS-IS is still mostly unknown.",),
        },
        "gap_questions": (
            _gap("as_is_known", "How does the process work today — steps, handoffs, rules?"),
        ),
    },
    "to_be": {
        "intents": ("redesign",),
        "minimum_information": [_req("as_is_known", "yes", "partial")],
        "favored_any": ("future_state_proposed", "future_defined"),
        "epistemic_constraints": (
            "PROPOSED TO-BE never becomes ACTIVE without a governed write.",
            "TDR is not a mandatory prerequisite of TO-BE.",
        ),
        "sufficiency": {
            "stop_when": ("The PROPOSED future flow and its delta vs AS-IS are stated.",),
            "not_sufficient_when": ("The future definition is still absent and AS-IS is weak.",),
        },
        "gap_questions": (
            _gap("as_is_known", "What does the current flow look like before redesigning it?"),
        ),
    },
    "kpi": {
        "intents": ("measure",),
        "minimum_information": [_req("objective_known")],
        "favored_all": ("objective_known",),
        "epistemic_constraints": (
            "TÉO-proposed targets stay PROPOSED; API results stay CALCULATED.",
        ),
        "sufficiency": {
            "stop_when": ("Indicator has definition, source and evidence states.",),
            "not_sufficient_when": ("There is nothing conceptually measurable yet.",),
        },
        "gap_questions": (
            _gap("objective_known", "Which objective, outcome or critical factor should the indicator reflect?"),
        ),
    },
    "swot": {
        "intents": ("strategic_analysis",),
        "minimum_information": [
            _req("strategic_question", "yes", "inferred", "proposed"),
            _req("scope_defined"),
            _req("horizon_defined"),
        ],
        "favored_all": ("strategic_question",),
        "disfavored_when": ("operational_cause_focus",),
        "epistemic_constraints": (
            "Perceptions stay labelled; wishes are not opportunities.",
            "SWOT does not substitute a causal or flow diagnosis.",
        ),
        "sufficiency": {
            "stop_when": ("The strategic matrix informs the declared decision.",),
            "not_sufficient_when": ("No decision, scope or horizon is set.",),
        },
        "gap_questions": (
            _gap("strategic_question", "What decision should this analysis inform?"),
            _gap("scope_defined", "What is the scope of the analysis — unit, process, product?"),
            _gap("horizon_defined", "What horizon or context should the analysis consider?"),
        ),
    },
}

# Soft composition — optional methodological transitions, never a pipeline.
COMPOSITION_EDGES = (
    {
        "source_method": "ishikawa",
        "target_method": "five_whys",
        "purpose": "Deepen one selected causal line after families are separated.",
        "condition": "A single candidate cause is chosen from the Ishikawa set.",
        "rationale": "Ishikawa opens families; 5 Whys tests one chain.",
        "mandatory": False,
    },
    {
        "source_method": "sipoc",
        "target_method": "end_to_end",
        "purpose": "Turn a clarified boundary into a start-to-finish flow.",
        "condition": "Trigger and outcome become identifiable.",
        "rationale": "SIPOC frames; end-to-end maps the path.",
        "mandatory": False,
    },
    {
        "source_method": "sipoc",
        "target_method": "as_is",
        "purpose": "Describe the current state once the boundary is framed.",
        "condition": "The work itself needs a narrative description, not only a frame.",
        "rationale": "Framing feeds a richer current-state description.",
        "mandatory": False,
    },
    {
        "source_method": "end_to_end",
        "target_method": "as_is",
        "purpose": "Attach evidence states to the mapped flow.",
        "condition": "The mapped flow needs OBSERVED vs missing detail.",
        "rationale": "Flow structure becomes a described current state.",
        "mandatory": False,
    },
    {
        "source_method": "as_is",
        "target_method": "lean",
        "purpose": "Inspect a described flow for waste and flow breaks.",
        "condition": "The current flow is known enough to discuss value and waste.",
        "rationale": "AS-IS description feeds waste lenses.",
        "mandatory": False,
    },
    {
        "source_method": "as_is",
        "target_method": "tdr",
        "purpose": "Challenge the described design toward a TO-BE.",
        "condition": "Redesign is desired and AS-IS is sufficiently known.",
        "rationale": "Tear-down requires a current design to challenge.",
        "mandatory": False,
    },
    {
        "source_method": "tdr",
        "target_method": "to_be",
        "purpose": "Explicit the future state produced by the redesign.",
        "condition": "The redesign produced a draft future flow.",
        "rationale": "TDR output is stated as a PROPOSED TO-BE.",
        "mandatory": False,
    },
    {
        "source_method": "to_be",
        "target_method": "kpi",
        "purpose": "Define measurement for the proposed future state.",
        "condition": "The TO-BE defines an outcome worth measuring.",
        "rationale": "A proposal needs a measurable success indicator.",
        "mandatory": False,
    },
)

_COMPOSITION_BY_SOURCE: dict[str, list[dict[str, Any]]] = {}
for _edge in COMPOSITION_EDGES:
    _COMPOSITION_BY_SOURCE.setdefault(_edge["source_method"], []).append(_edge)

# Meta-routing rules for intent=improve — ordered; first satisfied wins.
_IMPROVE_RULES = (
    {
        "when": {"strategic_question": ("yes", "inferred", "proposed")},
        "resolves_intent": "strategic_analysis",
        "note": "Strategic question detected — route to strategic_analysis.",
    },
    {
        "when": {"problem_defined": ("yes",)},
        "any_of": (("multiple_cause_families",), ("causes_open",)),
        "resolves_intent": "diagnose",
        "candidate_hint": "ishikawa",
        "note": "Defined problem with open causal families — diagnose via Ishikawa.",
    },
    {
        "when": {"problem_defined": ("yes",), "candidate_cause": ("yes", "inferred", "proposed")},
        "resolves_intent": "diagnose",
        "candidate_hint": "five_whys",
        "note": "Defined effect plus one candidate line — diagnose via 5 Whys.",
    },
    {
        "when": {"flow_known": ("yes", "partial"), "waste_symptoms": ("yes",)},
        "resolves_intent": "diagnose",
        "candidate_hint": "lean",
        "note": "Known flow with waste/delay/rework symptoms — Lean lens.",
    },
    {
        "when": {"as_is_known": ("yes", "partial"), "redesign_desired": ("yes",)},
        "resolves_intent": "redesign",
        "candidate_hint": "tdr",
        "note": "Known AS-IS plus redesign intent — tear-down and redesign.",
    },
    {
        "when": {"future_defined": ("yes",)},
        "any_of": (("future_state_proposed",),),
        "resolves_intent": "redesign",
        "candidate_hint": "to_be",
        "note": "Future state already defined — explicitate as PROPOSED TO-BE.",
    },
    {
        "when_any_unknown": ("process_identified", "boundary_known", "as_is_known"),
        "resolves_intent": "map",
        "candidate_hint": "sipoc",
        "note": "Process little known — map/frame first.",
    },
)


def _satisfied(req: Mapping[str, Any], context: Mapping[str, Any]) -> str:
    """One of: satisfied | missing | unknown."""
    token = _fact_token(context.get(req["fact"]))
    if token == "unknown":
        return "unknown"
    if token == "no":
        return "missing"
    if token == "yes" or token in req["accepts"]:
        return "satisfied"
    return "missing"


def evaluate_readiness(method_id: str, context: Mapping[str, Any] | None) -> dict[str, Any]:
    """Tri-state-plus readiness for one method. UNKNOWN != NOT_READY."""
    method_id = _resolve_method(method_id)
    semantics = _METHOD_SEMANTICS[method_id]
    context = context or {}
    unmet: list[str] = []
    missing: list[str] = []
    satisfied = 0
    requirements = semantics["minimum_information"]
    for req in requirements:
        state = _satisfied(req, context)
        if state == "satisfied":
            satisfied += 1
        elif state == "missing":
            missing.append(req["fact"])
            unmet.append(req["fact"])
        else:
            unmet.append(req["fact"])
    if missing:
        verdict = "NOT_READY"
    elif requirements and satisfied == len(requirements):
        verdict = "READY"
    elif satisfied > 0:
        verdict = "PARTIAL"
    elif not requirements:
        verdict = "READY"
    else:
        verdict = "UNKNOWN"
    return {
        "readiness": verdict,
        "satisfied": satisfied,
        "requirements": len(requirements),
        "unmet_facts": unmet,
        "missing_facts": missing,
    }


def _signal_active(fact: str, context: Mapping[str, Any], accepts=("yes",)) -> bool:
    return _fact_token(context.get(fact)) in accepts


def _candidate_rank(method_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    semantics = _METHOD_SEMANTICS[method_id]
    context = context or {}
    favored_all = semantics.get("favored_all", ())
    favored_any = semantics.get("favored_any", ())
    disfavored = semantics.get("disfavored_when", ())
    matched = [f for f in favored_all + favored_any if _signal_active(f, context, ("yes", "partial", "inferred", "proposed"))]
    against = [f for f in disfavored if _signal_active(f, context)]
    favored = (
        all(_signal_active(f, context, ("yes", "partial", "inferred", "proposed")) for f in favored_all)
        and (not favored_any or any(_signal_active(f, context, ("yes", "partial", "inferred", "proposed")) for f in favored_any))
        and not against
    )
    return {
        "method_id": method_id,
        "favored": favored,
        "signals_matched": matched,
        "signals_against": against,
    }


def _method_card_v2(method_id: str) -> dict[str, Any]:
    """V1 prose card + V2 semantic layer — same method id, two projections."""
    item = _METHODS[method_id]
    semantics = _METHOD_SEMANTICS[method_id]
    return {
        "id": method_id,
        "name": item["name"],
        "purpose": item["purpose"],
        "when_to_use": list(item["when_to_use"]),
        "when_not_to_use": list(item["when_not_to_use"]),
        "required_inputs": list(item["required_inputs"]),
        "minimum_information": [dict(r) for r in semantics["minimum_information"]],
        "epistemic_constraints": list(semantics["epistemic_constraints"]),
        "sufficiency": dict(semantics["sufficiency"]),
        "suggested_next": [
            dict(edge) for edge in _COMPOSITION_BY_SOURCE.get(method_id, ())
        ],
    }


def _questions_for(
    method_id: str,
    readiness: Mapping[str, Any],
    recorded_unknowns: frozenset[str] = frozenset(),
) -> list[dict[str, Any]]:
    semantics = _METHOD_SEMANTICS[method_id]
    gap_qs = {q["resolves"]: q for q in semantics.get("gap_questions", ())}
    # A fact the user already declared UNKNOWN is a recorded gap — surface it
    # once as metadata, never re-ask it in a loop.
    out = [
        dict(gap_qs[f])
        for f in readiness.get("unmet_facts", ())
        if f in gap_qs and f not in recorded_unknowns
    ]
    for q in _METHODS[method_id].get("questions", ())[:1]:
        out.append(
            {
                "id": f"deepen_{method_id}",
                "text": q,
                "kind": "deepening",
                "resolves": "optional_deepening",
            }
        )
    return out


def _improve_resolve(context: Mapping[str, Any]) -> dict[str, Any]:
    context = context or {}
    for rule in _IMPROVE_RULES:
        when = rule.get("when", {})
        any_unknown = rule.get("when_any_unknown")
        if when and all(
            _fact_token(context.get(f)) in accepts for f, accepts in when.items()
        ):
            extra = rule.get("any_of")
            if extra and not any(
                _signal_active(g, context, ("yes", "partial", "inferred", "proposed"))
                for group in extra
                for g in group
            ):
                continue
            return {
                "resolved_intent": rule["resolves_intent"],
                "candidate_hint": rule.get("candidate_hint"),
                "note": rule["note"],
            }
        if any_unknown and all(
            _fact_token(context.get(f)) == "unknown" for f in any_unknown
        ):
            return {
                "resolved_intent": rule["resolves_intent"],
                "candidate_hint": rule.get("candidate_hint"),
                "note": rule["note"],
            }
    return {
        "resolved_intent": None,
        "ambiguity": {
            "reason": "Insufficient context to pick a methodological path without guessing.",
            "blocking_gap": "improvement_need",
        },
        "next_question": {
            "id": "clarify_improve_goal",
            "text": (
                "What do you want to improve — do you know the current process, "
                "a defined problem, or the desired outcome?"
            ),
            "kind": "clarifying",
            "resolves": "improvement_need",
        },
    }


def evaluate_sufficiency(
    method_id: str, signals: Mapping[str, Any] | None
) -> dict[str, Any]:
    """READY TO START != SUFFICIENT TO STOP.

    ``signals`` are boolean flags over the closed STOP_REASONS vocabulary
    (lowercase). SUFFICIENT when the purpose was achieved, further progress
    would require speculation, a better method now generates more value, or
    remaining UNKNOWNs are non-blocking and the next question has low
    materiality.
    """
    _resolve_method(method_id)
    signals = signals or {}
    if not signals:
        return {"sufficiency": "UNKNOWN", "stop_reasons": []}
    reasons = [r for r in STOP_REASONS if signals.get(r.lower())]
    if not reasons:
        return {"sufficiency": "NOT_SUFFICIENT", "stop_reasons": []}
    hard = {"PURPOSE_ACHIEVED", "SPECULATION_RISK", "BETTER_METHOD_AVAILABLE"}
    if (
        set(reasons) & hard
        or {"REMAINING_UNKNOWN_NON_BLOCKING", "NEXT_QUESTION_LOW_MATERIALITY"}
        <= set(reasons)
    ):
        return {"sufficiency": "SUFFICIENT", "stop_reasons": reasons}
    return {"sufficiency": "NOT_SUFFICIENT", "stop_reasons": reasons}


def resolve_guide_version(guide_version: str | None) -> str:
    """Fail-closed version resolution — default V1, unknown → ValueError."""
    if guide_version is None or not str(guide_version).strip():
        return WIRE_DEFAULT_GUIDE_VERSION
    key = _norm(guide_version)
    by_norm = {_norm(v): v for v in SUPPORTED_GUIDE_VERSIONS}
    if key in by_norm:
        return by_norm[key]
    raise ValueError(
        f"Unknown guide_version '{guide_version}'. "
        f"Supported: {list(SUPPORTED_GUIDE_VERSIONS)}."
    )


def query_methodology_guide_v2(
    *,
    intent: str | None = None,
    method: str | None = None,
    task: str | None = None,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """V2 methodology intelligence. Read-only guidance — never writes."""
    context = dict(context or {})
    recorded_unknowns = frozenset(context.pop("recorded_unknowns", ()) or ())
    intent_key = _norm(intent)
    task_key = _norm(task)
    if intent_key is not None and intent_key not in INTENT_IDS:
        raise ValueError(
            f"Unknown methodology intent '{intent}'. "
            f"Known intents: {list(INTENT_IDS)}."
        )
    if task_key is not None and intent_key is None:
        # Legacy `task` param maps 1:1 to the same-named V2 intent.
        if task_key not in INTENT_IDS:
            raise ValueError(
                f"Unknown methodology task '{task}'. "
                f"Known tasks: {list(INTENT_IDS[:-2])}."
            )
        intent_key = task_key
    unknown_facts = sorted(set(context) - set(CONTEXT_FACTS))
    base = {
        "guide_version": GUIDE_VERSION_V2,
        "authority": AUTHORITY,
        "read_only": True,
        "writes": False,
        "persists": False,
        "wire_default_version": WIRE_DEFAULT_GUIDE_VERSION,
        "recommended_version": RECOMMENDED_GUIDE_VERSION,
        "supported_versions": list(SUPPORTED_GUIDE_VERSIONS),
        "supported_intents": list(INTENT_IDS),
        "evidence_states": list(EVIDENCE_STATES),
        "invariants": list(INVARIANTS),
    }
    if unknown_facts:
        base["ignored_context_facts"] = unknown_facts

    method_key = _resolve_method(method) if method else None
    if method_key:
        readiness = evaluate_readiness(method_key, context)
        payload = dict(base)
        payload["selection"] = "method"
        payload["method"] = {
            **_METHODS[method_key],
            "minimum_information": [
                dict(r) for r in _METHOD_SEMANTICS[method_key]["minimum_information"]
            ],
            "epistemic_constraints": list(
                _METHOD_SEMANTICS[method_key]["epistemic_constraints"]
            ),
            "sufficiency": dict(_METHOD_SEMANTICS[method_key]["sufficiency"]),
            "suggested_next": [
                dict(e) for e in _COMPOSITION_BY_SOURCE.get(method_key, ())
            ],
            "readiness": readiness["readiness"],
            "missing_information": readiness["unmet_facts"],
        }
        payload["next_questions"] = _questions_for(
            method_key, readiness, recorded_unknowns
        )
        if intent_key:
            payload["intent"] = intent_key
            payload["serves_intent"] = intent_key in _METHOD_SEMANTICS[method_key]["intents"]
        return payload

    if intent_key == "improve":
        resolution = _improve_resolve(context)
        payload = dict(base)
        payload["selection"] = "intent"
        payload["intent"] = "improve"
        payload["meta_routing"] = True
        payload.update(resolution)
        resolved = resolution.get("resolved_intent")
        if resolved:
            sub = _intent_payload(resolved, context, base, recorded_unknowns)
            payload["candidates"] = sub["candidates"]
            payload["next_questions"] = sub["next_questions"]
            hint = resolution.get("candidate_hint")
            if hint:
                for c in payload["candidates"]:
                    if c["method_id"] == hint:
                        c["favored"] = True
                        c.setdefault("signals_matched", []).append("improve_meta_hint")
        else:
            payload["next_questions"] = [resolution["next_question"]]
        return payload

    if intent_key:
        return _intent_payload(intent_key, context, base, recorded_unknowns)

    return {
        **base,
        "selection": "router",
        "rule": "Declare intent (or legacy task). Use the smallest sufficient method; composition is optional.",
        "intents": {
            intent_id: [
                mid for mid, s in _METHOD_SEMANTICS.items() if intent_id in s["intents"]
            ]
            for intent_id in INTENT_IDS
            if intent_id != "improve"
        },
        "meta_intents": {"improve": "Resolves to the best-fit intent from available context."},
        "methods": [_method_card_v2(mid) for mid in list_method_ids()],
        "composition_edges": [dict(e) for e in COMPOSITION_EDGES],
        "readiness_states": list(READINESS_STATES),
        "sufficiency_states": list(SUFFICIENCY_STATES),
        "stop_reasons": list(STOP_REASONS),
        "question_kinds": list(QUESTION_KINDS),
        "context_facts": list(CONTEXT_FACTS),
        "note": "Readiness UNKNOWN means 'cannot evaluate' — not 'not ready'.",
    }


def _intent_payload(
    intent_key: str,
    context: Mapping[str, Any],
    base: Mapping[str, Any],
    recorded_unknowns: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    member_ids = [
        mid for mid, s in _METHOD_SEMANTICS.items() if intent_key in s["intents"]
    ]
    candidates = []
    questions: list[dict[str, Any]] = []
    for mid in member_ids:
        rank = _candidate_rank(mid, context)
        readiness = evaluate_readiness(mid, context)
        candidates.append(
            {
                **rank,
                "readiness": readiness["readiness"],
                "missing_information": readiness["unmet_facts"],
            }
        )
        questions.extend(_questions_for(mid, readiness, recorded_unknowns))
    candidates.sort(key=lambda c: (not c["favored"], member_ids.index(c["method_id"])))
    return {
        **base,
        "selection": "intent",
        "intent": intent_key,
        "candidates": candidates,
        "next_questions": questions,
        "rule": "Candidates are ranked, not assigned. Readiness is per method; composition is optional.",
    }


def render_v2_markdown() -> str:
    """Derived human-readable projection of the canonical V2 definitions.

    ``docs/gpt-actions/teo-method-playbooks-v2.md`` is generated from this
    function — never edited manually (single semantic authority)."""
    bt = chr(96)  # backtick for markdown inline code
    lines = [
        "# TEO Method Playbooks V2",
        "",
        "Derived projection of tm_app/application/methodology/guide_v2.py.",
        "Version: " + bt + GUIDE_VERSION_V2 + bt + " — authority: " + AUTHORITY + ".",
        "READ-only guidance; no writes, persistence or authorization.",
        "",
        "## Intents",
        "",
    ]
    for intent in INTENT_IDS:
        members = [
            mid for mid, s in _METHOD_SEMANTICS.items() if intent in s["intents"]
        ]
        note = " (meta-routing)" if intent == "improve" else ""
        lines.append("- " + bt + intent + bt + note + ": " + (", ".join(members) or "—"))
    lines += ["", "## Methods", ""]
    for mid in list_method_ids():
        item = _METHODS[mid]
        sem = _METHOD_SEMANTICS[mid]
        lines.append("### " + mid + " — " + item["name"])
        lines.append("")
        lines.append("Purpose: " + item["purpose"])
        lines.append("")
        lines.append("Minimum information (readiness):")
        for req in sem["minimum_information"]:
            lines.append(
                "- " + bt + req["fact"] + bt + " accepts: " + ", ".join(req["accepts"])
            )
        if not sem["minimum_information"]:
            lines.append("- none (discovery method)")
        lines.append("")
        lines.append("Epistemic constraints:")
        for c in sem["epistemic_constraints"]:
            lines.append("- " + c)
        lines.append("")
        lines.append("Sufficiency — stop when:")
        for c in sem["sufficiency"]["stop_when"]:
            lines.append("- " + c)
        lines.append("Not sufficient when:")
        for c in sem["sufficiency"]["not_sufficient_when"]:
            lines.append("- " + c)
        lines.append("")
        edges = _COMPOSITION_BY_SOURCE.get(mid, ())
        if edges:
            lines.append("Soft composition (optional):")
            for e in edges:
                lines.append("- -> " + bt + e["target_method"] + bt + ": " + e["purpose"])
            lines.append("")
    lines += [
        "## Composition edges (all optional)",
        "",
    ]
    for e in COMPOSITION_EDGES:
        lines.append(
            "- " + bt + e["source_method"] + bt + " -> " + bt + e["target_method"]
            + bt + " — " + e["condition"]
        )
    lines += [
        "",
        "## Closed vocabularies",
        "",
        "- readiness: " + ", ".join(READINESS_STATES) + " (UNKNOWN != NOT_READY)",
        "- sufficiency: " + ", ".join(SUFFICIENCY_STATES),
        "- stop reasons: " + ", ".join(STOP_REASONS),
        "- question kinds: " + ", ".join(QUESTION_KINDS),
        "- context facts: " + ", ".join(CONTEXT_FACTS),
        "",
    ]
    return "\n".join(lines)
