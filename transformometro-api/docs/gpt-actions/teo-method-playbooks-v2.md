# TEO Method Playbooks V2

Derived projection of tm_app/application/methodology/guide_v2.py.
Version: `teo-method-playbooks-v2` — authority: GUIDANCE_NOT_SOURCE_OF_TRUTH.
READ-only guidance; no writes, persistence or authorization.

## Intents

- `discover`: macroprocess, key_process, project_charter
- `map`: sipoc, end_to_end, as_is, vsm
- `diagnose`: lean, ishikawa, five_whys, dmaic, pareto, five_s, msa, fmea, hypothesis_test, doe_intro
- `redesign`: tdr, to_be, pdca
- `measure`: kpi, pareto, defect_metrics, descriptive_statistics, msa, process_capability, control_chart, control_plan
- `prioritize`: ctp
- `interview`: sipoc, voc_ctq
- `strategic_analysis`: swot
- `improve` (meta-routing): —

## Lean Six Sigma

Belts are competence references, not methods. TÉO does not certify and does not claim ISO 13053-1 or ISO 18404 conformity. Statistical results are UNKNOWN unless an authorized measurement calculated them. V1 method ids and their prose stay unchanged.

Frameworks: dmaic, pdca
Competence references: yellow_belt, green_belt, black_belt
Added tools: voc_ctq, project_charter, vsm, pareto, five_s, defect_metrics, descriptive_statistics, msa, process_capability, control_chart, fmea, hypothesis_test, doe_intro, control_plan
Reused V1 tools: sipoc, lean, ishikawa, five_whys, as_is, to_be, kpi, end_to_end

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

### yellow_belt — Yellow Belt competence reference

Purpose: Name the awareness scope for participating in a Lean Six Sigma effort without leading the statistics.

Minimum information (readiness):
- none (discovery method)

Epistemic constraints:
- TÉO is not a certifying body. Belt names describe competence scope, not a granted IASSC, ASQ or ISO 18404 credential.
- A belt is not selected as the method for a process problem.

Sufficiency — stop when:
- The competence boundary is clear and a real tool is chosen next.
Not sufficient when:
- The user still thinks the belt itself will analyze the process.

### green_belt — Green Belt competence reference

Purpose: Name the project-leadership scope: DMAIC on one process, with measurement discipline and basic statistical judgment.

Minimum information (readiness):
- none (discovery method)

Epistemic constraints:
- TÉO is not a certifying body. Belt names describe competence scope, not a granted IASSC, ASQ or ISO 18404 credential.
- No statistical engine runs inside this guide. A number is CALCULATED only when an authorized measurement API returned it; otherwise the result stays UNKNOWN. Do not invent Cp, p-values, sigma levels or savings.

Sufficiency — stop when:
- The project scope and the missing data are explicit.
Not sufficient when:
- Statistical results were implied without data.

### black_belt — Black Belt scope reference

Purpose: Mark the coaching and advanced-statistics scope that this delivery does not implement.

Minimum information (readiness):
- none (discovery method)

Epistemic constraints:
- TÉO is not a certifying body. Belt names describe competence scope, not a granted IASSC, ASQ or ISO 18404 credential.
- No Black Belt program is implemented.

Sufficiency — stop when:
- The user was redirected to a smaller method.
Not sufficient when:
- A training curriculum was started.

### dmaic — DMAIC

Purpose: Guide a structured improvement of an existing process through Define, Measure, Analyze, Improve and Control.

Minimum information (readiness):
- `problem_defined` accepts: yes
- `structured_improvement` accepts: yes

Epistemic constraints:
- A phase output is not a proven cause and not a saved record.
- Causal hypotheses stay INFERRED until evidence validates them.
- Do not open DMAIC when the user asked only to organize steps.

Sufficiency — stop when:
- The next phase has a clear output or an explicit data gap.
Not sufficient when:
- Every phase was recited with no process-specific gap.

Soft composition (optional):
- -> `sipoc`: Frame the process before measuring it.

### pdca — PDCA

Purpose: Run a short Plan-Do-Check-Act cycle when a full DMAIC project is heavier than the decision.

Minimum information (readiness):
- `future_state_proposed` accepts: yes, proposed

Epistemic constraints:
- A checked trial is not a proven root cause.

Sufficiency — stop when:
- Plan, trial, check and act are distinguished, or the check is UNKNOWN.
Not sufficient when:
- Success was declared without a check.

### voc_ctq — VOC and CTQ

Purpose: Turn customer language into a few measurable critical-to-quality requirements.

Minimum information (readiness):
- `process_identified` accepts: yes

Epistemic constraints:
- A CTQ is a requirement, not a cause and not a baseline.

Sufficiency — stop when:
- Each CTQ is measurable or explicitly UNKNOWN.
Not sufficient when:
- Requirements remain slogans.

### project_charter — Project charter

Purpose: Bound a DMAIC-style effort: problem, goal, scope, customers and the first indicators.

Minimum information (readiness):
- `problem_defined` accepts: yes
- `structured_improvement` accepts: yes

Epistemic constraints:
- The charter stays PROPOSED. It does not authorize the project.

Sufficiency — stop when:
- Problem, goal, scope and starting indicator are stated or marked UNKNOWN.
Not sufficient when:
- The problem statement already hides the solution.

### vsm — Value stream map

Purpose: See material and information flow, waits and rework across a value stream, then a future-state sketch.

Minimum information (readiness):
- `flow_known` accepts: yes, partial

Epistemic constraints:
- A value-stream sketch does not replace native BPMN.
- Future state stays PROPOSED.

Sufficiency — stop when:
- Current waits are visible or explicitly UNKNOWN.
Not sufficient when:
- The future state was drawn before the current waits.

Soft composition (optional):
- -> `lean`: Name the wastes visible on the current stream.

### pareto — Pareto

Purpose: Separate the few categories that concentrate defects, delays or stockouts from the long tail.

Minimum information (readiness):
- `problem_defined` accepts: yes

Epistemic constraints:
- A frequent category is not a proven cause.
- No statistical engine runs inside this guide. A number is CALCULATED only when an authorized measurement API returned it; otherwise the result stays UNKNOWN. Do not invent Cp, p-values, sigma levels or savings.

Sufficiency — stop when:
- Categories are ranked from authorized counts, or frequencies stay UNKNOWN.
Not sufficient when:
- Categories were ranked from opinion.

Soft composition (optional):
- -> `ishikawa`: Open cause families for the categories that concentrate the count.

### five_s — 5S

Purpose: Make a workplace orderly enough that the agreed standard is visible.

Minimum information (readiness):
- `waste_symptoms` accepts: yes

Epistemic constraints:
- A 5S story is not an audit score.

Sufficiency — stop when:
- The visible standard is proposed and what was observed is separated.
Not sufficient when:
- Cleanup was treated as proof the delay is gone.

### defect_metrics — Defect and time metrics

Purpose: Define DPU, DPMO, cycle time and rework as indicators, without fabricating the figures.

Minimum information (readiness):
- `objective_known` accepts: yes

Epistemic constraints:
- No statistical engine runs inside this guide. A number is CALCULATED only when an authorized measurement API returned it; otherwise the result stays UNKNOWN. Do not invent Cp, p-values, sigma levels or savings.
- DPMO without a real opportunity definition is UNKNOWN.

Sufficiency — stop when:
- The metric is defined and the value is CALCULATED or UNKNOWN.
Not sufficient when:
- A sigma level was stated without data.

### descriptive_statistics — Descriptive statistics

Purpose: Say what a distribution summary would mean, and refuse a summary the data do not support.

Minimum information (readiness):
- `measurement_available` accepts: yes
- `measurement_system_trusted` accepts: yes, partial

Epistemic constraints:
- No statistical engine runs inside this guide. A number is CALCULATED only when an authorized measurement API returned it; otherwise the result stays UNKNOWN. Do not invent Cp, p-values, sigma levels or savings.
- A mean is not a cause.

Sufficiency — stop when:
- The summary is CALCULATED from an authorized series or left UNKNOWN.
Not sufficient when:
- Chat anecdotes were averaged.

### msa — Measurement system analysis

Purpose: Decide whether the gage or the process is the variation before any capability claim.

Minimum information (readiness):
- `quality_variation` accepts: yes

Epistemic constraints:
- No statistical engine runs inside this guide. A number is CALCULATED only when an authorized measurement API returned it; otherwise the result stays UNKNOWN. Do not invent Cp, p-values, sigma levels or savings.
- Do not discuss capability until measurement trust is yes or the gap is explicit.

Sufficiency — stop when:
- Measurement trust is established or the missing check is explicit.
Not sufficient when:
- Capability was recommended while trust is unknown.

Soft composition (optional):
- -> `process_capability`: Discuss capability only after measurement trust is established.

### process_capability — Process capability

Purpose: Explain Cp/Cpk and Pp/Ppk and the difference between a stable process and a capable one, without computing them here.

Minimum information (readiness):
- `measurement_system_trusted` accepts: yes
- `quality_variation` accepts: yes
- `measurement_available` accepts: yes

Epistemic constraints:
- No statistical engine runs inside this guide. A number is CALCULATED only when an authorized measurement API returned it; otherwise the result stays UNKNOWN. Do not invent Cp, p-values, sigma levels or savings.
- Stability and capability are different. No Cp/Cpk/Pp/Ppk is computed here.

Sufficiency — stop when:
- The series and the spec are available for an authorized calculation, or the gap is explicit.
Not sufficient when:
- An index was quoted without a series.

### control_chart — Control chart guidance

Purpose: Explain how a control chart would show stability and a reaction rule, without plotting invented points.

Minimum information (readiness):
- `measurement_system_trusted` accepts: yes
- `measurement_available` accepts: yes

Epistemic constraints:
- No statistical engine runs inside this guide. A number is CALCULATED only when an authorized measurement API returned it; otherwise the result stays UNKNOWN. Do not invent Cp, p-values, sigma levels or savings.
- Specification limits are not control limits.

Sufficiency — stop when:
- The series exists for an authorized chart, or the chart is explicitly not drawn.
Not sufficient when:
- Stability was declared from memory.

### fmea — FMEA

Purpose: List how a step can fail, the effect, and the current detection, as hypotheses with severity judgment kept explicit.

Minimum information (readiness):
- `process_identified` accepts: yes
- `problem_defined` accepts: yes

Epistemic constraints:
- No severity score is invented. A mode is not a proven cause.

Sufficiency — stop when:
- Modes, effects and current detection are listed with evidence states.
Not sufficient when:
- An RPN table was filled to look complete.

### hypothesis_test — Hypothesis and before/after comparison

Purpose: Say what a comparison would need, and refuse a significant-result claim without a real test.

Minimum information (readiness):
- `measurement_available` accepts: yes
- `measurement_system_trusted` accepts: yes

Epistemic constraints:
- No statistical engine runs inside this guide. A number is CALCULATED only when an authorized measurement API returned it; otherwise the result stays UNKNOWN. Do not invent Cp, p-values, sigma levels or savings.
- Correlation is not causation. No p-value is produced.

Sufficiency — stop when:
- The comparison question and the missing series are explicit.
Not sufficient when:
- Significance was claimed from anecdotes.

### doe_intro — Introductory design of experiments

Purpose: Recognize when many factors are tangled and a one-factor story will mislead, without designing or analyzing an experiment here.

Minimum information (readiness):
- `candidates_known` accepts: yes
- `quality_variation` accepts: yes

Epistemic constraints:
- No statistical engine runs inside this guide. A number is CALCULATED only when an authorized measurement API returned it; otherwise the result stays UNKNOWN. Do not invent Cp, p-values, sigma levels or savings.
- No experimental matrix is generated.

Sufficiency — stop when:
- It is clear whether a designed trial is warranted.
Not sufficient when:
- A fake design was published.

### control_plan — Control plan

Purpose: Specify how a result stays in place: indicator, owner, frequency, trigger and reaction.

Minimum information (readiness):
- `improvement_regressed` accepts: yes

Epistemic constraints:
- Proposed, implemented and measured are different states.
- Stability is not declared here.

Sufficiency — stop when:
- Owner, indicator, trigger and reaction are stated or marked UNKNOWN.
Not sufficient when:
- The plan assumes a result that was never measured.

Soft composition (optional):
- -> `kpi`: Attach the reaction plan to an indicator the platform can actually read.

## Composition edges (all optional)

- `ishikawa` -> `five_whys` — A single candidate cause is chosen from the Ishikawa set.
- `sipoc` -> `end_to_end` — Trigger and outcome become identifiable.
- `sipoc` -> `as_is` — The work itself needs a narrative description, not only a frame.
- `end_to_end` -> `as_is` — The mapped flow needs OBSERVED vs missing detail.
- `as_is` -> `lean` — The current flow is known enough to discuss value and waste.
- `as_is` -> `tdr` — Redesign is desired and AS-IS is sufficiently known.
- `tdr` -> `to_be` — The redesign produced a draft future flow.
- `to_be` -> `kpi` — The TO-BE defines an outcome worth measuring.
- `pareto` -> `ishikawa` — Authorized counts exist and one category is selected. The category is still not a proven cause.
- `msa` -> `process_capability` — measurement_system_trusted is yes and a specification exists.
- `dmaic` -> `sipoc` — The process boundary is still thin.
- `vsm` -> `lean` — The current stream shows waits or rework.
- `control_plan` -> `kpi` — An indicator is named.

## Closed vocabularies

- readiness: READY, PARTIAL, NOT_READY, UNKNOWN (UNKNOWN != NOT_READY)
- sufficiency: SUFFICIENT, NOT_SUFFICIENT, UNKNOWN
- stop reasons: PURPOSE_ACHIEVED, REMAINING_UNKNOWN_NON_BLOCKING, NEXT_QUESTION_LOW_MATERIALITY, SPECULATION_RISK, BETTER_METHOD_AVAILABLE
- question kinds: clarifying, readiness, evidence, deepening
- context facts: organization_context, macroprocess_known, process_identified, boundary_known, as_is_known, flow_known, problem_defined, candidate_cause, candidates_known, multiple_cause_families, causes_open, waste_symptoms, operational_cause_focus, objective_known, future_state_proposed, future_defined, redesign_desired, measurement_available, strategic_question, scope_defined, horizon_defined, quality_variation, measurement_system_trusted, defect_concentration, improvement_regressed, administrative_delay, mapping_only, structured_improvement
