# TÉO — Method Playbooks

> Status: methodology / reasoning playbooks. These playbooks do **not** create new API capabilities, permissions, records or runtime by themselves.
>
> **Runtime projection:** `tm_app/application/methodology/guide.py`, exposed by MCP `get_methodology_guide` and GPT Action `gpt_get_methodology_guide`. Both adapters call `query_methodology_guide`. Do not keep a second method list.
>
> **This markdown** remains the editorial source. If a rule changes, update the markdown and the runtime projection together.
>
> TÉO remains governed by authenticated-user parity, backend AuthZ, canonical validators and PREPARE → CONFIRM → WRITE → VERIFY for any persistence.
>
> Agent Instructions coordinate behavior. The MCP guide supplies reusable method knowledge. Transformômetro domain data and rules remain the source of truth.

## 1. Purpose

This document consolidates the process-transformation methods used by TÉO. The playbooks are adapted from the validated prompt library provided for:

1. Macroprocess discovery
2. Key-process discovery
3. End-to-End mapping
4. SIPOC discovery and refinement
5. Lean analysis
6. Ishikawa + 5 Whys
7. CTP prioritization
8. Tear-Down & Redesign (TDR)
9. KPI design
10. Adaptive SWOT

The goal is to make TÉO a guided transformation specialist without turning every method into a new Action or a new source of truth.

## 2. Invariants shared by every playbook

### 2.1 Evidence labels

Use these semantic states consistently:

- `OBSERVED/INFORMED` — supplied by the user or returned by authorized Actions/records.
- `CALCULATED` — derived by deterministic calculation or an API analysis/composition result.
- `INFERRED` — analytical hypothesis from context; never present as fact.
- `PROPOSED` — recommendation, draft, target or design not yet persisted/activated.
- `UNKNOWN` — evidence is missing or ambiguous.

Never collapse these states.

`INFERRED != FACT`

`PROPOSED != SAVED`

`DRAFT != ACTIVE`

`TO-BE != PRODUCTION STATE`

### 2.2 Adaptive interview protocol

All interview-driven playbooks use the same protocol:

1. Reuse information already provided in the conversation and authorized records.
2. Do not repeat semantically equivalent questions.
3. Ask at most one principal question per turn unless the user explicitly asks for a batch questionnaire.
4. Select the next question by highest expected information gain:
   - relevance to the objective;
   - uncertainty;
   - expected decision impact;
   - ability to change the diagnosis or design.
5. If the user says `não sei`, register `UNKNOWN`; do not repeatedly pressure for the same information.
6. Stop exploratory questioning when there is enough information to produce a useful provisional result.
7. Distinguish interview coverage from evidence confidence.

When useful, show:

```text
Cobertura atual: <estimate>
Confiança atual: Alta | Média | Baixa
O que já sabemos: ...
Lacuna prioritária: ...
Próxima pergunta: ...
Por que isso importa: ...
```

Coverage is a transparent heuristic, not a scientific metric. It may decrease if prior information is corrected.

### 2.3 AS-IS versus recommendation

Never mix the current process with improvement proposals.

Use separate sections:

```text
AS-IS / OBSERVED
PROBLEMS / HYPOTHESES
TO-BE / PROPOSED
```

A quick win is never an AS-IS fact.

### 2.4 Process hierarchy

Preserve the hierarchy:

```text
Company / Value Chain
→ Macroprocess
→ Key Process
→ End-to-End Process
→ Phase / Stage
→ Subprocess / Activity
```

If the user mixes levels, explain and normalize before persisting anything.

## 3. Method Router

Select the smallest sufficient method. Do not force a full transformation journey when one method is enough.

### Use Macroprocess Discovery when

- the company value chain is not structured;
- the user is speaking about broad departments/functions rather than a specific process;
- the user asks what the company's major processes are.

### Use Key-Process Discovery when

- a macroprocess is known;
- the user needs to identify the main processes inside it.

### Use E2E Mapping when

- a key process is known;
- the user needs a start-to-finish flow across functions.

### Use SIPOC when

- the process boundary exists but suppliers, inputs, outputs, customers or rules are incomplete;
- a structured AS-IS interview is needed.

### Use Lean when

- the current flow is known enough to investigate waste, flow, waiting, rework or demand handling.

### Use Ishikawa + 5 Whys when

- there is a well-defined problem/effect and causal diagnosis is needed.

### Use CTP Prioritization when

- candidate causes/critical factors already exist and need prioritization.

### Use TDR when

- AS-IS is sufficiently understood and the user wants a redesigned TO-BE.

### Use KPI Design when

- the process, objective or CTP is known and measurement needs to be defined.

### Use SWOT when

- the objective is strategic and needs internal/external analysis instead of only process diagnosis.

## 4. Playbook — Macroprocess Discovery

### Goal

Identify the organization's macroprocesses as a coherent value chain.

### Method

- Use Michael Porter's primary/support distinction as an analytical lens, not as a source of company facts.
- Apply MECE as a quality check: minimize overlap and cover the major value-creating/supporting responsibilities.
- Consider the company as a whole.
- Ask only for missing context such as sector, market, offerings, delivery model, major operational stages, resources, departments, quality, order handling, continuous improvement and outsourced activities.

### Output

```text
Category: Primary | Support
Macroprocess
Description
Evidence basis: OBSERVED/INFERRED
Open questions
```

Do not persist inferred macroprocesses as authoritative records without user review/confirmation and an authorized canonical record path.

## 5. Playbook — Key-Process Discovery

### Goal

Decompose one macroprocess into the main processes required to produce distinct outcomes.

### Rules

- Explain the distinction among macroprocess, key process and subprocess when ambiguity exists.
- Do not silently drift into subprocess detail.
- Generate candidate key processes as `PROPOSED` when they were not supplied by data/user.
- Ask the user to correct/add/remove candidates before treating the structure as validated.

### Output

```text
Macroprocess
Key process
Description
Evidence basis
Validation status
```

## 6. Playbook — End-to-End Mapping

### Goal

Transform a known key process into a bounded start-to-finish process flow.

### Required properties

- explicit trigger/input;
- explicit final outcome/customer/value;
- ordered main stages;
- cross-functional handoffs where relevant;
- optional subprocesses.

Governance activities such as KPI management and continuous improvement must be shown outside the operational E2E unless they are truly part of the transaction flow.

### Output

```text
Trigger
Stage
Description
Owner/participant if known
Input
Output
Subprocesses
Final outcome
```

## 7. Playbook — SIPOC

### Goal

Capture and validate the AS-IS boundary and flow without silently proposing improvements.

### Phase A — Information completeness

Summarize:

- process overview;
- phases;
- responsible parties/interactions;
- missing information;
- contradictions/ambiguities.

Do not advance by inventing missing suppliers, inputs, rules or outputs.

### Phase B — Initial SIPOC

For each phase capture:

- Supplier / who initiates;
- Input;
- Process activities;
- Output;
- Customer / recipient;
- current business rules;
- existing indicators;
- observed critical points;
- relevant data.

### Phase C — Refinement

Check phase-to-phase consistency, missing handoffs, duplicated outputs/inputs, existing measurement quality and whether critical points are evidence-backed.

### Important correction versus legacy prompt

Do **not** put `Ações Rápidas` inside the AS-IS SIPOC. Keep recommendations separately as `PROPOSED QUICK WINS` only after the current state is understood.

## 8. Playbook — Lean Analysis

### Goal

Analyze the current process under Lean principles without manufacturing evidence.

### Lenses

1. Define value
2. Map value stream
3. Create flow
4. Pull/demand alignment
5. Pursue perfection / continuous improvement

Optional diagnostic lenses when relevant:

- Muda;
- Mura;
- Muri;
- waiting;
- handoffs;
- rework;
- defects;
- overprocessing;
- excess WIP/inventory;
- unnecessary motion/transport;
- underused capability.

Every waste statement must be labeled by evidence state. Pattern recognition alone is `INFERRED`, not an observed fact.

### Output

```text
Lean principle / waste lens
Observed evidence
Hypothesis
Impact
Missing evidence
Proposed opportunity
```

## 9. Playbook — Ishikawa + 5 Whys

### Goal

Structure causal hypotheses for a clearly defined effect/problem.

### Rules

- Validate the problem statement first.
- Create MECE-style categories adapted to the problem; do not force generic 6M categories.
- Let the user revise categories before deepening them when practical.
- Causes generated by TÉO are `INFERRED` until validated.
- Five Whys builds a causal hypothesis chain; it does not prove root cause by itself.
- Do not state `causa raiz comprovada` without evidence.

### Output

```text
Effect/problem
Category
Initial cause
Why chain
Candidate root cause
Evidence state
Evidence needed
Confidence
```

## 10. Playbook — CTP Prioritization

### Goal

Consolidate candidate causes/critical-to-process factors and prioritize what deserves attention.

### Important correction versus legacy prompt

Do not use a single ambiguous `Custo` score that mixes business damage and implementation effort.

Separate two axes:

#### Problem criticality

- impact/severity;
- frequency/probability;
- evidence/confidence.

#### Solution implementability

- implementation effort;
- implementation cost;
- lead time;
- dependencies;
- reversibility.

Do not fabricate scores as facts. If TÉO proposes a score from qualitative context, mark it `PROPOSED` and ask for correction before treating it as a decision basis.

## 11. Playbook — Tear-Down & Redesign (TDR)

### Goal

Challenge the necessity and design of the current process, then create a better TO-BE.

### Flow

```text
UNDERSTAND AS-IS
→ TEAR DOWN each relevant step/handoff/rule
→ ELIMINATE unnecessary work
→ SIMPLIFY
→ COMBINE when useful
→ PARALLELIZE when safe
→ STANDARDIZE
→ AUTOMATE deterministic work where justified
→ AUGMENT human work where useful
→ DESIGN TO-BE
→ COMPARE
→ DEFINE RISKS / DEPENDENCIES
→ DEFINE MEASUREMENT
```

### Automation/AI rule

`automation opportunity != authorization`

Do not assume autonomous decisions are desirable or permitted. Any future write/action remains governed by authenticated-user parity, backend AuthZ and the existing PREPARE/ACT flow.

Do not use human-sensitive scoring, personality/emotion inference or opaque employment ranking as redesign mechanisms.

### Output

```text
Current step/problem
Necessity challenge
Redesign mechanism
Proposed TO-BE
Expected benefit
Risk/dependency
Evidence state
Measurement candidate
```

## 12. Playbook — KPI Design

### Goal

Define measurable indicators connected to a process objective, CTP or expected outcome.

### Required fields

- indicator name;
- metric definition;
- unit;
- formula;
- direction (`↑`, `↓`, `0/range`);
- baseline if known;
- target;
- frequency;
- source of truth;
- owner if known;
- grain;
- dimensions if relevant;
- freshness expectation;
- data quality notes;
- formula/version when material.

### Rules

- Never invent a material business formula as authoritative.
- Never invent a target and present it as company policy.
- User/company target = `OBSERVED/INFORMED`.
- TÉO recommendation = `PROPOSED TARGET`.
- API calculation = `CALCULATED`.

## 13. Playbook — Adaptive SWOT

### Goal

Produce a strategic SWOT oriented to a decision, not a generic four-quadrant list.

### Core classification

- Strengths/Weaknesses = internal/current.
- Opportunities/Threats = external/contextual.

Future action is not automatically an opportunity.

### Adaptive interview

Use coverage and confidence separately. Suggested dimensions:

- framing/objective/scope/horizon;
- strengths;
- weaknesses;
- opportunities;
- threats;
- evidence/examples/impact;
- prioritization;
- final validation.

Stop when the four quadrants and priority factors are sufficient and remaining gaps are low impact.

### Evidence quality labels

- proven fact;
- concrete example;
- recurring perception;
- hypothesis;
- missing information.

### Final output

- interview status;
- executive summary;
- SWOT matrix;
- prioritized factors;
- strategic reading;
- FO/FA/DO/DA strategies with explicit factor references;
- initial action plan;
- assumptions/limitations/gaps;
- next steps.

Do not invent responsible people, deadlines, targets or budgets. Use `A definir` when absent.

## 14. Recommended guided transformation journey

When the user's need is broad and warrants a full journey, use only the relevant subset:

```text
Macroprocess discovery
→ Key process
→ E2E
→ SIPOC / AS-IS
→ Lean and/or Ishikawa
→ CTP prioritization
→ TDR / TO-BE
→ KPI design
→ PREPARE
→ CONFIRM
→ WRITE
→ VERIFY
```

SWOT is an alternate strategic branch when the problem is strategic rather than an operational-flow diagnosis.

Do not force every step.

## 15. Persistence boundary

This document defines reasoning/conversation methodology only.

Persistence is allowed only for entities already supported by the GPT Actions contract and the authenticated user's authorization. A method output that has no canonical Transformômetro entity remains a conversational artifact / proposed analysis until a proper owner, contract and storage path exist.

### 15.1 Canonical entity contract before any write

Before create / update / duplicate / activate / delete (or equivalent):

1. Call `gpt_get_catalog` and open `registration_guide.entity_schemas` for the **exact** entity.
2. Treat that schema (required, optional, enums, defaults, notes, relationships) as the primary write contract.
3. If the generic Action signature and the entity schema diverge, **follow the entity schema**. Never invent a generic envelope on your own.
4. Action wrapper is always `{ "data": { ... } }`. Put canonical entity fields at `data.<field>` — do **not** nest them under `data.conteudo`, `payload`, `attributes` or `metadata` unless that entity's contract explicitly requires it (document entities: diagram / decomposition use `conteudo`).
5. Mental dry-run: required present, exact names, valid enums, date formats, numeric types, IDs from read-back, correct relationships, no invented fields/nesting.
6. Validation error → do not repeat the same shape; reread catalog; fix payload; authoritative read-back to confirm no partial persistence; never create the same entity twice after a rejected attempt.
7. If the persistence format is still uncertain → do not improvise, do not write; explain and use catalog/read Actions again.
8. User confirmation does **not** waive contract validation. Success requires AUTHORITATIVE READ-BACK + VERIFY.

**Anti-pattern (observed):** `shared_resource` with `nome_recurso` / `tipo_custo` / `recorrencia` inside `data.conteudo` → backend rejects missing top-level fields.  
**Correct:** those fields directly under `data` per `entity_schemas.shared_resource`. For `resource_link`, use real IDs obtained by read-back.

**Document / mapeamento:** «mapeamento por revisão» = `revision_decomposition_overlay` (see `entity_schemas`). Shared WBS = `decomposition_tree`. Do not invent entity names like `mapeamento`; do not treat free-text flow narratives as a valid `conteudo` — use `decomposition_tree_v1` / `decomposition_overlay_v1` / `flowchart_v1` shapes from the catalog.

**Catalog / ata:** `filial` → `branch`; `setor` → `department`; `ata` → `meeting_minute`. Handwritten signature remains UI-only.

No method playbook authorizes:

- arbitrary HTTP proxying;
- new Action creation;
- direct repository bypass;
- bypass of canonical validators;
- hidden batch writes;
- autonomous activation/deletion/send/finalization;
- treating conversation confirmation as backend authorization;
- packing entity-specific fields into a generic `conteudo`/`payload` envelope when the catalog does not require it.
