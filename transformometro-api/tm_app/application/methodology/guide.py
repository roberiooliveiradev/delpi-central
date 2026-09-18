"""Compact TÉO methodology playbooks for MCP READ.

Editorial source: ``docs/gpt-actions/teo-method-playbooks.md``.
This module is the runtime projection. It does not authorize, persist, or
turn a hypothesis into a domain fact.

Methods without a sufficient section in that playbook are not invented here.
"""

from __future__ import annotations

import unicodedata
from typing import Any

GUIDE_VERSION = "teo-method-playbooks-v1"
AUTHORITY = "GUIDANCE_NOT_SOURCE_OF_TRUTH"

EVIDENCE_STATES = (
    "OBSERVED/INFORMED",
    "CALCULATED",
    "INFERRED",
    "PROPOSED",
    "UNKNOWN",
)

INVARIANTS = (
    "INFERRED != FACT",
    "PROPOSED != SAVED",
    "DRAFT != ACTIVE",
    "TO-BE != PRODUCTION STATE",
    "AS-IS != TO-BE",
    "current process != proposal",
    "suggested cause != proven cause",
    "suggested automation != implemented automation",
    "estimated gain != measured gain",
    "proposed improvement != active improvement",
    "chosen method != source of truth",
    "ChatGPT confirmation != authorization",
)

CONVERSATIONAL_FLOW = (
    "UNDERSTAND",
    "DEFINE SCOPE",
    "CHOOSE MINIMUM METHOD",
    "ASK EVIDENCE-ORIENTED QUESTIONS",
    "MAP AS-IS",
    "IDENTIFY GAPS",
    "FORM HYPOTHESES",
    "VALIDATE HYPOTHESES",
    "PROPOSE TO-BE",
    "DEFINE METRICS",
    "PREPARE REGISTRATION",
    "CONFIRM",
    "WRITE",
    "VERIFY",
)

DIAGRAM_RULE = {
    "source": "get_catalog.diagram_catalog",
    "flowchart_v1": "Transformômetro source of truth for process diagrams",
    "mermaid": "derived only",
    "rule": "Do not hardcode node or edge types in the methodology guide.",
}

SHARED_EVIDENCE_RULES = (
    "Do not promote a hypothesis to a fact.",
    "Label every material claim OBSERVED/INFORMED, CALCULATED, INFERRED, PROPOSED or UNKNOWN.",
    "Reuse information already in the conversation or in authorized records.",
    "Ask at most one principal question per turn unless the user asks for a batch.",
    "If the user says they do not know, record UNKNOWN; do not pressure the same gap.",
    "This guide is READ-only. It does not register, activate or authorize writes.",
)

_TM = {
    "process": "Corporate process / macroprocess record. Do not create a method entity.",
    "instance": "Unit/department application of the process. Not a method entity.",
    "baseline_revision": "Calculable AS-IS revision + measurement when the user confirms persistence.",
    "scenario_revision": "TO-BE proposal as a scenario revision. Not production state until activated by governed ACT.",
    "decomposition_tree": "Hierarchical WBS. Not SIPOC/Ishikawa/SWOT storage.",
    "revision_decomposition_overlay": "AS-IS vs TO-BE structural delta on a revision.",
    "process_diagram": "Flow. Types only from get_catalog.diagram_catalog (flowchart_v1).",
    "revision_diagram_overlay": "Visual delta. Same catalog rule.",
    "measurement": "Indicators / analyze. API numbers are CALCULATED.",
    "investment_or_shared_resource": "Costs. Do not invent budgets.",
    "evidence": "Evidence metadata only. Binary upload stays UI-only.",
}

_TASKS: dict[str, tuple[str, ...]] = {
    "discover": ("macroprocess", "key_process"),
    "map": ("end_to_end", "sipoc", "as_is"),
    "diagnose": ("ishikawa", "five_whys", "lean"),
    "redesign": ("tdr", "to_be"),
    "measure": ("kpi",),
    "prioritize": ("ctp",),
    "interview": ("sipoc",),
}

_ALIASES = {
    "macroprocessos": "macroprocess",
    "macroprocesso": "macroprocess",
    "macroprocesses": "macroprocess",
    "processos_chave": "key_process",
    "processo_chave": "key_process",
    "key_processes": "key_process",
    "processo_ponta_a_ponta": "end_to_end",
    "ponta_a_ponta": "end_to_end",
    "e2e": "end_to_end",
    "endtoend": "end_to_end",
    "5_porques": "five_whys",
    "cinco_porques": "five_whys",
    "fivewhys": "five_whys",
    "5whys": "five_whys",
    "ishikawa_5_whys": "ishikawa",
    "as-is": "as_is",
    "asis": "as_is",
    "estado_atual": "as_is",
    "to-be": "to_be",
    "tobe": "to_be",
    "estado_futuro": "to_be",
    "tear_down": "tdr",
    "teardown": "tdr",
    "swot_adaptativo": "swot",
}


def _norm(value: str | None) -> str | None:
    if value is None:
        return None
    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.strip().lower().replace("-", "_").replace(" ", "_")
    return text or None


def _playbook(
    *,
    method_id: str,
    name: str,
    purpose: str,
    when_to_use: tuple[str, ...],
    when_not_to_use: tuple[str, ...],
    required_inputs: tuple[str, ...],
    questions: tuple[str, ...],
    steps: tuple[str, ...],
    outputs: tuple[str, ...],
    common_mistakes: tuple[str, ...],
    mapping_focus: tuple[str, ...],
    source_section: str,
) -> dict[str, Any]:
    return {
        "id": method_id,
        "name": name,
        "purpose": purpose,
        "when_to_use": list(when_to_use),
        "when_not_to_use": list(when_not_to_use),
        "required_inputs": list(required_inputs),
        "questions": list(questions),
        "steps": list(steps),
        "outputs": list(outputs),
        "evidence_rules": list(SHARED_EVIDENCE_RULES),
        "common_mistakes": list(common_mistakes),
        "transformometro_mapping": {key: _TM[key] for key in mapping_focus},
        "source_section": source_section,
        "persists": False,
        "authorizes": False,
    }


_METHODS: dict[str, dict[str, Any]] = {
    item["id"]: item
    for item in (
        _playbook(
            method_id="macroprocess",
            name="Macroprocess discovery",
            purpose="Identify the organization's macroprocesses as a coherent value chain.",
            when_to_use=(
                "The value chain is not structured.",
                "The user speaks about broad functions, not one process.",
                "The user asks what the major processes are.",
            ),
            when_not_to_use=(
                "A specific process and its flow are already known.",
                "The need is causal diagnosis or a TO-BE redesign.",
            ),
            required_inputs=("Sector or business context, or an explicit UNKNOWN.",),
            questions=(
                "What does the organization deliver, and to whom?",
                "Which major stages turn demand into that delivery?",
                "Which support activities (quality, people, improvement) sit beside the primary chain?",
            ),
            steps=(
                "Use primary vs support only as a lens, not as company facts.",
                "Check MECE: little overlap, major responsibilities covered.",
                "Mark each candidate OBSERVED/INFORMED or INFERRED.",
                "Do not persist inferred macroprocesses without user review and a governed write.",
            ),
            outputs=("Category", "Macroprocess", "Description", "Evidence basis", "Open questions"),
            common_mistakes=(
                "Treating Porter categories as observed company structure.",
                "Drilling into subprocesses before the chain is stable.",
            ),
            mapping_focus=("process", "decomposition_tree"),
            source_section="teo-method-playbooks.md §4",
        ),
        _playbook(
            method_id="key_process",
            name="Key-process discovery",
            purpose="Decompose one known macroprocess into processes that produce distinct outcomes.",
            when_to_use=(
                "A macroprocess is known.",
                "The user needs the main processes inside it.",
            ),
            when_not_to_use=(
                "The macroprocess itself is still unknown.",
                "The user already needs a start-to-finish flow of one process.",
            ),
            required_inputs=("Named macroprocess, or UNKNOWN if it is not established.",),
            questions=(
                "Which distinct outcomes does this macroprocess produce?",
                "Which of these candidates should be added, removed or renamed?",
            ),
            steps=(
                "Explain macroprocess vs key process vs subprocess when levels are mixed.",
                "Keep candidates PROPOSED until the user validates them.",
                "Do not silently drift into activity detail.",
            ),
            outputs=("Macroprocess", "Key process", "Description", "Evidence basis", "Validation status"),
            common_mistakes=(
                "Saving unvalidated candidates as the corporate tree.",
                "Collapsing key process and subprocess.",
            ),
            mapping_focus=("process", "decomposition_tree", "instance"),
            source_section="teo-method-playbooks.md §5",
        ),
        _playbook(
            method_id="end_to_end",
            name="End-to-end mapping",
            purpose="Turn a known key process into a bounded start-to-finish flow.",
            when_to_use=(
                "A key process is known.",
                "The user needs the cross-functional path from trigger to outcome.",
            ),
            when_not_to_use=(
                "Suppliers, inputs and customers are the gap — use SIPOC first.",
                "The problem is a cause investigation, not the flow boundary.",
            ),
            required_inputs=("Trigger or starting event", "Expected final outcome"),
            questions=(
                "What event starts this process?",
                "What outcome or customer value ends it?",
                "Where does the work cross functions?",
            ),
            steps=(
                "Keep trigger, ordered stages, handoffs and final outcome explicit.",
                "Leave KPI management and continuous improvement outside the operational flow unless they are part of the transaction.",
                "Mark missing stages UNKNOWN instead of inventing them.",
            ),
            outputs=("Trigger", "Stage", "Owner if known", "Input", "Output", "Final outcome"),
            common_mistakes=(
                "Drawing governance activities inside the transactional flow by default.",
                "Persisting a narrative as flowchart_v1 without the catalog shape.",
            ),
            mapping_focus=("process", "process_diagram", "decomposition_tree", "instance"),
            source_section="teo-method-playbooks.md §6",
        ),
        _playbook(
            method_id="sipoc",
            name="SIPOC",
            purpose="Capture and validate the AS-IS boundary without silently proposing improvements.",
            when_to_use=(
                "The process exists but suppliers, inputs, outputs, customers or rules are incomplete.",
                "A structured AS-IS interview is needed.",
                "The process is still poorly known.",
            ),
            when_not_to_use=(
                "The user already wants a redesigned future state.",
                "The only gap is a measured indicator.",
            ),
            required_inputs=("Process name or a short description of the work.",),
            questions=(
                "Who supplies the input that starts each phase?",
                "What leaves the phase, and who receives it?",
                "Which current rule or indicator is actually in use today?",
            ),
            steps=(
                "Summarize what is known, missing and contradictory before filling SIPOC.",
                "For each phase: supplier, input, activities, output, customer, current rules, existing indicators, observed critical points.",
                "Check handoffs between phases.",
                "Keep quick wins out of the AS-IS. Recommendations are PROPOSED and separate.",
            ),
            outputs=("Phase SIPOC", "Missing information", "Contradictions", "PROPOSED quick wins only after AS-IS"),
            common_mistakes=(
                "Inventing suppliers, inputs or rules.",
                "Putting improvement actions inside the current-state SIPOC.",
            ),
            mapping_focus=("process", "decomposition_tree", "process_diagram", "baseline_revision"),
            source_section="teo-method-playbooks.md §7",
        ),
        _playbook(
            method_id="lean",
            name="Lean analysis",
            purpose="Inspect a known-enough current flow for waste, flow breaks, waiting and rework.",
            when_to_use=(
                "The current flow is known enough to discuss value, waiting, rework or demand.",
                "The symptom is delay, rework, handoffs or overload.",
            ),
            when_not_to_use=(
                "The process boundary is still unknown — map first.",
                "The need is a strategic context, not flow waste.",
            ),
            required_inputs=("A described current flow or authorized process records.",),
            questions=(
                "Where does the work wait, return or get redone?",
                "What would the customer consider value in this flow?",
            ),
            steps=(
                "Apply value, value stream, flow, pull and continuous improvement as lenses.",
                "Use waste types only when relevant: waiting, handoffs, rework, defects, overprocessing, excess inventory, motion, underused capability.",
                "Label pattern recognition INFERRED, not observed.",
            ),
            outputs=("Lens", "Observed evidence", "Hypothesis", "Impact", "Missing evidence", "PROPOSED opportunity"),
            common_mistakes=(
                "Declaring waste without an evidence state.",
                "Treating a Lean label as a measured gain.",
            ),
            mapping_focus=("process_diagram", "baseline_revision", "measurement"),
            source_section="teo-method-playbooks.md §8",
        ),
        _playbook(
            method_id="ishikawa",
            name="Ishikawa",
            purpose="Structure causal hypotheses for a clearly defined effect.",
            when_to_use=(
                "There is a defined problem or effect.",
                "Several possible cause families need to be separated before deepening one chain.",
            ),
            when_not_to_use=(
                "The effect itself is not stated.",
                "The user only needs a process boundary (SIPOC) or a strategic SWOT.",
            ),
            required_inputs=("Effect or problem statement.",),
            questions=(
                "What exactly is the effect, and how would we recognize it?",
                "Which cause categories fit this problem — not a generic 6M list?",
            ),
            steps=(
                "Validate the problem statement first.",
                "Build MECE categories adapted to the problem. Do not force 6M.",
                "Let the user revise categories before deepening them.",
                "Causes suggested by TÉO stay INFERRED until evidence validates them.",
            ),
            outputs=("Effect", "Category", "Initial cause", "Evidence state", "Evidence needed"),
            common_mistakes=(
                "Forcing manufacturing 6M categories.",
                "Calling an inferred cause a proven root cause.",
            ),
            mapping_focus=("process", "evidence", "baseline_revision"),
            source_section="teo-method-playbooks.md §9",
        ),
        _playbook(
            method_id="five_whys",
            name="5 Whys",
            purpose="Build one causal hypothesis chain for a defined effect. It does not prove root cause by itself.",
            when_to_use=(
                "The effect is defined.",
                "One candidate cause should be deepened, often after Ishikawa.",
            ),
            when_not_to_use=(
                "Cause families are still mixed — use Ishikawa first.",
                "There is no evidence plan to test the chain.",
            ),
            required_inputs=("Effect", "One starting cause or category."),
            questions=(
                "Why does this happen?",
                "What evidence would confirm or reject this link?",
            ),
            steps=(
                "Walk a short why-chain. Stop when the next why is UNKNOWN or circular.",
                "Keep the candidate root cause INFERRED.",
                "Do not write 'causa raiz comprovada' without evidence.",
                "Ask what observation would change the chain.",
            ),
            outputs=("Why chain", "Candidate root cause", "Evidence state", "Confidence", "Evidence needed"),
            common_mistakes=(
                "Stopping at five questions by ritual when the chain is already UNKNOWN.",
                "Treating the last why as a measured fact.",
            ),
            mapping_focus=("evidence", "process"),
            source_section="teo-method-playbooks.md §9",
        ),
        _playbook(
            method_id="ctp",
            name="CTP prioritization",
            purpose="Prioritize candidate causes or critical-to-process factors already on the table.",
            when_to_use=(
                "Candidate causes or critical factors already exist.",
                "The user must choose what deserves attention first.",
            ),
            when_not_to_use=(
                "Causes have not been listed yet.",
                "The user needs a flow map, not a priority.",
            ),
            required_inputs=("A list of candidate factors, even if some are INFERRED.",),
            questions=(
                "How severe and how frequent is each factor, and how strong is the evidence?",
                "How hard, costly, slow or reversible would a response be?",
            ),
            steps=(
                "Separate problem criticality (impact, frequency, evidence) from solution implementability (effort, cost, lead time, dependencies, reversibility).",
                "Do not use one ambiguous cost score that mixes damage and effort.",
                "If TÉO suggests a score, mark it PROPOSED and ask for correction before it becomes a decision basis.",
            ),
            outputs=("Factor", "Criticality notes", "Implementability notes", "Evidence state", "PROPOSED priority"),
            common_mistakes=(
                "Fabricating numeric scores as facts.",
                "Mixing business damage and implementation effort in one axis.",
            ),
            mapping_focus=("measurement", "investment_or_shared_resource"),
            source_section="teo-method-playbooks.md §10",
        ),
        _playbook(
            method_id="tdr",
            name="Tear-down and redesign",
            purpose="Challenge the current design and propose a better TO-BE after AS-IS is understood.",
            when_to_use=(
                "AS-IS is sufficiently understood.",
                "The user wants a redesigned future process.",
            ),
            when_not_to_use=(
                "Current state is still mostly UNKNOWN.",
                "The user only asked to document what happens today.",
            ),
            required_inputs=("Understood AS-IS steps, handoffs or rules.",),
            questions=(
                "Which step exists only because of a habit, a system limit or a real constraint?",
                "What would the future flow do differently, and what risk does that create?",
            ),
            steps=(
                "Understand AS-IS, then tear down each relevant step, handoff and rule.",
                "Eliminate, simplify, combine, parallelize, standardize.",
                "Automate only deterministic work that is justified. Automation opportunity is not authorization.",
                "Design TO-BE, compare, list risks and a measurement candidate.",
                "Do not use personality scoring or opaque employment ranking as redesign mechanisms.",
            ),
            outputs=("Current step", "Necessity challenge", "Redesign mechanism", "PROPOSED TO-BE", "Risk", "Measurement candidate"),
            common_mistakes=(
                "Designing TO-BE before AS-IS is known.",
                "Treating an automation idea as an implemented change.",
            ),
            mapping_focus=(
                "scenario_revision",
                "revision_diagram_overlay",
                "revision_decomposition_overlay",
                "process_diagram",
            ),
            source_section="teo-method-playbooks.md §11",
        ),
        _playbook(
            method_id="kpi",
            name="KPI design",
            purpose="Define measurable indicators tied to a process objective, CTP or expected outcome.",
            when_to_use=(
                "The process, objective or critical factor is known.",
                "Measurement still needs to be defined or checked.",
            ),
            when_not_to_use=(
                "The process outcome is still undefined.",
                "The user wants a strategic SWOT, not an indicator.",
            ),
            required_inputs=("Objective or critical factor the indicator should reflect.",),
            questions=(
                "What decision should this indicator change?",
                "What is the formula, unit, direction, source and frequency — or UNKNOWN?",
            ),
            steps=(
                "Collect name, definition, unit, formula, direction, baseline, target, frequency, source, owner, grain and data-quality notes.",
                "Company target is OBSERVED/INFORMED. TÉO target is PROPOSED. API result is CALCULATED.",
                "Never invent a material formula or a company target as policy.",
            ),
            outputs=("Indicator definition", "Formula status", "Baseline/target with evidence state", "Source of truth"),
            common_mistakes=(
                "Inventing a formula and presenting it as official.",
                "Calling an estimated gain a measured result.",
            ),
            mapping_focus=("measurement", "baseline_revision", "scenario_revision"),
            source_section="teo-method-playbooks.md §12",
        ),
        _playbook(
            method_id="swot",
            name="Adaptive SWOT",
            purpose="Produce a decision-oriented strategic reading, not a generic four-box list.",
            when_to_use=(
                "The question is strategic context, not a detailed flow diagnosis.",
                "Internal and external factors both matter to a decision.",
            ),
            when_not_to_use=(
                "The user needs suppliers, stages or a root-cause chain.",
                "A process flowchart is the actual deliverable.",
            ),
            required_inputs=("Decision, scope and horizon — or UNKNOWN.",),
            questions=(
                "What decision should this SWOT inform?",
                "Which strength or threat is evidenced, and which is only a perception?",
            ),
            steps=(
                "Strengths and weaknesses are internal/current. Opportunities and threats are external.",
                "A future action is not automatically an opportunity.",
                "Separate proven fact, example, recurring perception, hypothesis and missing information.",
                "Do not invent owners, deadlines, targets or budgets. Use 'A definir' when absent.",
            ),
            outputs=("SWOT matrix", "Prioritized factors", "Strategies with factor references", "Assumptions and gaps"),
            common_mistakes=(
                "Using SWOT as a substitute for process diagnosis.",
                "Listing wishes as opportunities.",
            ),
            mapping_focus=("process",),
            source_section="teo-method-playbooks.md §13",
        ),
        _playbook(
            method_id="as_is",
            name="AS-IS",
            purpose="Describe the current process as observed or informed, separated from any proposal.",
            when_to_use=(
                "The user needs the current state before diagnosis or redesign.",
                "Conversation is mixing today's work with desired changes.",
            ),
            when_not_to_use=(
                "The user explicitly asked only for a future proposal and AS-IS is already established.",
            ),
            required_inputs=("What happens today, from the user or from authorized records.",),
            questions=(
                "What happens today, before any improvement?",
                "Which part of this description was observed, and which is still missing?",
            ),
            steps=(
                "Keep a section AS-IS / OBSERVED distinct from PROBLEMS / HYPOTHESES and TO-BE / PROPOSED.",
                "A quick win is never an AS-IS fact.",
                "Prefer SIPOC or end-to-end when the boundary itself is the gap.",
                "Calculable current state, after confirmation, maps to a baseline revision — not before.",
            ),
            outputs=("Current steps", "Evidence state per claim", "Open unknowns"),
            common_mistakes=(
                "Writing recommendations inside the current-state description.",
                "Treating a draft diagram as the active production flow.",
            ),
            mapping_focus=("baseline_revision", "process_diagram", "decomposition_tree", "measurement"),
            source_section="teo-method-playbooks.md §2.3 and §7",
        ),
        _playbook(
            method_id="to_be",
            name="TO-BE",
            purpose="Propose a future process without claiming it is saved or active.",
            when_to_use=(
                "AS-IS is understood enough to propose a change.",
                "The user asked to design the future state.",
            ),
            when_not_to_use=(
                "Current state is still mostly unknown.",
                "The user asked to register or activate a change — that is PREPARE/ACT, not this guide.",
            ),
            required_inputs=("Established or explicitly partial AS-IS.",),
            questions=(
                "What should change relative to the current state, and what must stay?",
                "Has this future state been confirmed for registration, or is it still a proposal?",
            ),
            steps=(
                "Read current context before designing. Do not invent the current state.",
                "Label the design PROPOSED.",
                "State that TO-BE is not production state and is not saved until a governed write verifies it.",
                "Use TDR when the redesign itself must challenge each step.",
            ),
            outputs=("PROPOSED future flow", "Delta vs AS-IS", "Risks", "Not-saved status"),
            common_mistakes=(
                "Saying the TO-BE is active or persisted because it was discussed.",
                "Skipping AS-IS.",
            ),
            mapping_focus=(
                "scenario_revision",
                "revision_diagram_overlay",
                "revision_decomposition_overlay",
            ),
            source_section="teo-method-playbooks.md §2.3 and §11",
        ),
    )
}


def list_method_ids() -> tuple[str, ...]:
    return tuple(_METHODS)


def query_methodology_guide(
    *,
    method: str | None = None,
    task: str | None = None,
) -> dict[str, Any]:
    """Return the router, one playbook, or the methods recommended for a task.

    Unknown method/task raises ValueError (governed validation, not a write).
    """
    method_key = _resolve_method(method)
    task_key = _resolve_task(task)
    base = {
        "guide_version": GUIDE_VERSION,
        "authority": AUTHORITY,
        "read_only": True,
        "writes": False,
        "evidence_states": list(EVIDENCE_STATES),
        "invariants": list(INVARIANTS),
        "diagram_rule": dict(DIAGRAM_RULE),
    }
    if method_key:
        payload = dict(base)
        payload["selection"] = "method"
        payload["method"] = _METHODS[method_key]
        if task_key:
            payload["task"] = task_key
            payload["recommended_for_task"] = method_key in _TASKS[task_key]
        return payload
    if task_key:
        ids = _TASKS[task_key]
        return {
            **base,
            "selection": "task",
            "task": task_key,
            "recommended_method_ids": list(ids),
            "methods": [_index_card(_METHODS[method_id]) for method_id in ids],
            "note": "Call again with method=<id> for the full playbook. Use the smallest sufficient method.",
        }
    return {
        **base,
        "selection": "router",
        "conversational_flow": list(CONVERSATIONAL_FLOW),
        "rule": "Use the smallest sufficient method. Do not apply every method by default.",
        "task_router": {task: list(ids) for task, ids in _TASKS.items()},
        "methods": [_index_card(item) for item in _METHODS.values()],
        "note": "Call again with method=<id> for questions, steps and outputs.",
    }


def _index_card(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "name": item["name"],
        "purpose": item["purpose"],
        "when_to_use": list(item["when_to_use"]),
    }


def _resolve_method(method: str | None) -> str | None:
    key = _norm(method)
    if key is None:
        return None
    key = _ALIASES.get(key, key)
    if key not in _METHODS:
        known = ", ".join(list_method_ids())
        raise ValueError(f"Unknown methodology method '{method}'. Known methods: {known}.")
    return key


def _resolve_task(task: str | None) -> str | None:
    key = _norm(task)
    if key is None:
        return None
    if key not in _TASKS:
        known = ", ".join(_TASKS)
        raise ValueError(f"Unknown methodology task '{task}'. Known tasks: {known}.")
    return key
