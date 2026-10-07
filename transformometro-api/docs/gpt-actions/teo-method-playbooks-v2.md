# TEO Method Playbooks V2

Derived projection of tm_app/application/methodology/guide_v2.py.
Version: `teo-method-playbooks-v2` — authority: GUIDANCE_NOT_SOURCE_OF_TRUTH.
READ-only guidance; no writes, persistence or authorization.

## Intents

- `discover`: macroprocess, key_process
- `map`: sipoc, end_to_end, as_is
- `diagnose`: lean, ishikawa, five_whys
- `redesign`: tdr, to_be
- `measure`: kpi
- `prioritize`: ctp
- `interview`: sipoc
- `strategic_analysis`: swot
- `improve` (meta-routing): —

## Methods

### macroprocess — Macroprocess discovery

Purpose: Identify the organization's macroprocesses as a coherent value chain.

Minimum information (readiness):
- none (discovery method)

Epistemic constraints:
- Candidate macroprocesses stay INFERRED until user-validated.
- Value-chain categories are a lens, not company facts.

Sufficiency — stop when:
- Value chain is coherent and MECE enough to proceed.
- Further drilling would need domain facts not yet available.
Not sufficient when:
- Major overlaps or uncovered scopes remain.

### key_process — Key-process discovery

Purpose: Decompose one known macroprocess into processes that produce distinct outcomes.

Minimum information (readiness):
- `macroprocess_known` accepts: yes

Epistemic constraints:
- Key-process candidates stay PROPOSED until validated.

Sufficiency — stop when:
- Key processes produce distinct outcomes and are validated.
Not sufficient when:
- The macroprocess itself is not established.

### end_to_end — End-to-end mapping

Purpose: Turn a known key process into a bounded start-to-finish flow.

Minimum information (readiness):
- `process_identified` accepts: yes
- `boundary_known` accepts: yes

Epistemic constraints:
- Missing stages stay UNKNOWN — not invented.

Sufficiency — stop when:
- Trigger-to-outcome flow with handoffs is stable.
Not sufficient when:
- Trigger or final outcome still unknown.

Soft composition (optional):
- -> `as_is`: Attach evidence states to the mapped flow.

### sipoc — SIPOC

Purpose: Capture and validate the AS-IS boundary without silently proposing improvements.

Minimum information (readiness):
- `process_identified` accepts: yes

Epistemic constraints:
- AS-IS entries must not embed improvement proposals.
- Unknown suppliers/inputs stay UNKNOWN — never invented.

Sufficiency — stop when:
- Boundary, phases and handoffs are consistent enough for the next method.
- Remaining gaps are recorded UNKNOWN without blocking.
Not sufficient when:
- The process itself is not identified.

Soft composition (optional):
- -> `end_to_end`: Turn a clarified boundary into a start-to-finish flow.
- -> `as_is`: Describe the current state once the boundary is framed.

### lean — Lean analysis

Purpose: Inspect a known-enough current flow for waste, flow breaks, waiting and rework.

Minimum information (readiness):
- `flow_known` accepts: yes, partial

Epistemic constraints:
- Pattern recognition stays INFERRED — a Lean label is not a measured gain.

Sufficiency — stop when:
- Waste hypotheses are labelled with evidence state and next lens adds no value.
Not sufficient when:
- The current flow is not known enough.

### ishikawa — Ishikawa

Purpose: Structure causal hypotheses for a clearly defined effect.

Minimum information (readiness):
- `problem_defined` accepts: yes

Epistemic constraints:
- TÉO-suggested causes stay INFERRED until evidence validates them.
- suggested cause != proven cause.

Sufficiency — stop when:
- Cause families are MECE enough and a candidate line is selected.
Not sufficient when:
- The effect is not yet defined.

Soft composition (optional):
- -> `five_whys`: Deepen one selected causal line after families are separated.

### five_whys — 5 Whys

Purpose: Build one causal hypothesis chain for a defined effect. It does not prove root cause by itself.

Minimum information (readiness):
- `problem_defined` accepts: yes
- `candidate_cause` accepts: yes, inferred, proposed

Epistemic constraints:
- INFERRED candidate satisfies 'candidate causal line' but is never promoted to validated cause by this method.
- 5th why != proven root cause — stop when the next why is UNKNOWN.

Sufficiency — stop when:
- The chain reaches a testable candidate or UNKNOWN without ritual 'five'.
- Continuing would require speculation.
Not sufficient when:
- No candidate causal line exists yet.

### ctp — CTP prioritization

Purpose: Prioritize candidate causes or critical-to-process factors already on the table.

Minimum information (readiness):
- `candidates_known` accepts: yes

Epistemic constraints:
- Suggested scores stay PROPOSED until corrected by the user.

Sufficiency — stop when:
- Priorities separate criticality from implementability.
Not sufficient when:
- No candidate factors are on the table.

### tdr — Tear-down and redesign

Purpose: Challenge the current design and propose a better TO-BE after AS-IS is understood.

Minimum information (readiness):
- `as_is_known` accepts: yes, partial

Epistemic constraints:
- Redesign proposals stay PROPOSED; automation opportunity != authorization.

Sufficiency — stop when:
- Each relevant step was challenged and a PROPOSED TO-BE exists.
Not sufficient when:
- AS-IS is still mostly unknown.

Soft composition (optional):
- -> `to_be`: Explicit the future state produced by the redesign.

### kpi — KPI design

Purpose: Define measurable indicators tied to a process objective, CTP or expected outcome.

Minimum information (readiness):
- `objective_known` accepts: yes

Epistemic constraints:
- TÉO-proposed targets stay PROPOSED; API results stay CALCULATED.

Sufficiency — stop when:
- Indicator has definition, source and evidence states.
Not sufficient when:
- There is nothing conceptually measurable yet.

### swot — Adaptive SWOT

Purpose: Produce a decision-oriented strategic reading, not a generic four-box list.

Minimum information (readiness):
- `strategic_question` accepts: yes, inferred, proposed
- `scope_defined` accepts: yes
- `horizon_defined` accepts: yes

Epistemic constraints:
- Perceptions stay labelled; wishes are not opportunities.
- SWOT does not substitute a causal or flow diagnosis.

Sufficiency — stop when:
- The strategic matrix informs the declared decision.
Not sufficient when:
- No decision, scope or horizon is set.

### as_is — AS-IS

Purpose: Describe the current process as observed or informed, separated from any proposal.

Minimum information (readiness):
- `process_identified` accepts: yes

Epistemic constraints:
- AS-IS stays OBSERVED/INFORMED and separate from PROPOSED.
- A draft AS-IS is DRAFT — never ACTIVE state.

Sufficiency — stop when:
- Current state is described well enough for the declared goal.
Not sufficient when:
- Observed and proposed statements are still mixed.

Soft composition (optional):
- -> `lean`: Inspect a described flow for waste and flow breaks.
- -> `tdr`: Challenge the described design toward a TO-BE.

### to_be — TO-BE

Purpose: Propose a future process without claiming it is saved or active.

Minimum information (readiness):
- `as_is_known` accepts: yes, partial

Epistemic constraints:
- PROPOSED TO-BE never becomes ACTIVE without a governed write.
- TDR is not a mandatory prerequisite of TO-BE.

Sufficiency — stop when:
- The PROPOSED future flow and its delta vs AS-IS are stated.
Not sufficient when:
- The future definition is still absent and AS-IS is weak.

Soft composition (optional):
- -> `kpi`: Define measurement for the proposed future state.

## Composition edges (all optional)

- `ishikawa` -> `five_whys` — A single candidate cause is chosen from the Ishikawa set.
- `sipoc` -> `end_to_end` — Trigger and outcome become identifiable.
- `sipoc` -> `as_is` — The work itself needs a narrative description, not only a frame.
- `end_to_end` -> `as_is` — The mapped flow needs OBSERVED vs missing detail.
- `as_is` -> `lean` — The current flow is known enough to discuss value and waste.
- `as_is` -> `tdr` — Redesign is desired and AS-IS is sufficiently known.
- `tdr` -> `to_be` — The redesign produced a draft future flow.
- `to_be` -> `kpi` — The TO-BE defines an outcome worth measuring.

## Closed vocabularies

- readiness: READY, PARTIAL, NOT_READY, UNKNOWN (UNKNOWN != NOT_READY)
- sufficiency: SUFFICIENT, NOT_SUFFICIENT, UNKNOWN
- stop reasons: PURPOSE_ACHIEVED, REMAINING_UNKNOWN_NON_BLOCKING, NEXT_QUESTION_LOW_MATERIALITY, SPECULATION_RISK, BETTER_METHOD_AVAILABLE
- question kinds: clarifying, readiness, evidence, deepening
- context facts: organization_context, macroprocess_known, process_identified, boundary_known, as_is_known, flow_known, problem_defined, candidate_cause, candidates_known, multiple_cause_families, causes_open, waste_symptoms, operational_cause_focus, objective_known, future_state_proposed, future_defined, redesign_desired, measurement_available, strategic_question, scope_defined, horizon_defined
