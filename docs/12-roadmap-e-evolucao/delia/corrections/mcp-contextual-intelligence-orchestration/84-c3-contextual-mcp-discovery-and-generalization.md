# 84 — C3: Contextual MCP Discovery & Generalization

**TASK_ID:** `DELIA-C3-CONTEXTUAL-MCP-DISCOVERY-AND-GENERALIZATION-01`
**BASE:** `f1a2b9aa80` (= `origin/main` at start). **Mode:** bounded
5-stage implementation (characterize → minimal fix → real eval →
generalization → acceptance). Dev environment, CRI ON;
`PRODUCTION_ACTIVATION=NO`.

## 1. Stage 1 — baseline (live, CRI ON, pre-change)

Real turns via the production delegation path (Keycloak exchange,
delegated user identity), `/tmp/delia_turn.py` harness inside
`delpi-delia-api`.

| Case | Question (pt-BR) | Before |
|---|---|---|
| T1 | último processo alterado | NON_GROUNDED `delpi_source_unverified`; owner rejected `date_field` (disallowed for `process`) |
| T2 | cinco processos mais recentes | GROUNDED `record_read` 5/109 |
| T3 | quais processos disponíveis | GROUNDED `get_catalog` + `insufficient_evidence` ("sem dados de negócio") |
| T4 | quais filtros p/ processos | GROUNDED `get_catalog` + `insufficient_evidence` |
| V1 | programações TV | NON_GROUNDED (honest no-access — correct) |
| V2 | formatos de visualização | GROUNDED `get_catalog` + `insufficient_evidence` |
| V3 | informações numa programação | NON_GROUNDED disambiguation |
| D1 | informações de estoque | NON_GROUNDED `turn_budget_limited` |
| D2 | indicador operacional | GROUNDED `discover_delpi_information` + `insufficient_evidence` |
| D3 | filtros p/ consulta descoberta | NON_GROUNDED `delpi_source_unverified` |

**Failure clusters:** (A) owner rejection of schema-legal but
entity-disallowed filters (`date_field`) — the `filterable_fields`
projection gap proven in doc 83; (B) DISCOVERY results reaching the
binding edge as `structured=None` (control-plane deliberately dropped
in `_invoke_selected`), so contract answers degraded to
`envelope_only`/`insufficient_evidence` instead of presenting what
the owner actually publishes.

## 2. Stage 2 — minimal fix

**Existing mechanism reused** (`REUSE_DECISION=EXTEND`):
`_requires_owner_vocabulary` + `_discovery_capability` (opaque-vocab
discovery), `_bound_owner_evidence`/`_sanitize_renderable`/
`_compact_evidence`/`_unwrap_owner_payload` (bounded untrusted
projection), `_ENTITY_SCHEMA_COLLECTION_KEYS` (canonical entities
collection), `_build_arguments(owner_evidence=…)` (existing recovery
channel), `EvidenceFacts`/`assess_outcome`/`compose_cri_response`
(E2/E3 verdict pipeline).

**Changes:**

1. `orchestration.py` — `_recover_owner_contract()`: on owner
   remote-contract rejection (`MCP_PROTOCOL_ERROR` etc., never
   transport/auth), one bounded round — same-group DISCOVERY
   capability → vocabulary → same arguments stage re-proposal → one
   retry. Fail-closed; `skipped_budget` honored; DISCOVERY never
   self-recovers; no loops.
2. `orchestration.py` — `_contract_fact_rows()`: bounded owner
   contract digest — per-entity contract rows first (all canonical
   `entities` collections, ≤4 rows), then top-level sections
   (nested mappings preferred), sanitized/redacted, ≤8 rows × 800c.
3. `model.py` — `SpecialistOutcome.contract_facts: tuple[str,…]`
   (additive, default `()`): carries the digest past the terminal
   DISCOVERY `structured=None` drop without changing
   OFF/user-facing paths.
4. `outcome_assessment.py` — `EvidenceFacts.contract_facts` +
   `OUTCOME_CONTRACT_FACTS` verdict: a DISCOVERY-class outcome with
   contract data and no business records is a real surface answer;
   unproven declared requirements ride as reasons (insufficiency
   marked, surface still presented — never a record substitute).
5. `conversational_response.py` + `cri_presentation.delpi.json`
   (v2→v3, additive `leads.contract_facts`): attributed, bounded
   presentation ("A fonte publica…"). `cri_instruction_resource.py`
   accepts v3.

No new model stages, no provider-specific branches, no new
registries, no per-field/per-question maps. `NEW_MODEL_STAGES=0`.

## 3. Stage 3 — real before/after (live, post-change)

| Case | After | Δ |
|---|---|---|
| T1 | GROUNDED `record_read` + `insufficient_evidence` — honest ordering abstention ("não comprovei ordenação completa") | FIXED: rejection → recovery → grounded honest |
| T2 | GROUNDED `record_read` 5/109 | maintained (one transient model_timeout — environmental) |
| T3 | GROUNDED `contract_facts` — entity schemas + vocabulary | FIXED: surface answer instead of "sem dados" |
| T4 | GROUNDED `contract_facts` — `entities.*` contract rows | FIXED |
| V2 | GROUNDED `contract_facts` — `operations`/`capability_surface`/`productGuide` | FIXED |
| V3 | GROUNDED `contract_facts` (model chose `get_catalog`) | improved |
| D2 | GROUNDED `contract_facts` — 0 candidates / 95 eligible + surface | FIXED |
| D3 | GROUNDED `contract_facts` — discovery envelope + surface | FIXED |

Selection unchanged elsewhere (no mandatory `get_catalog`; T1/T2/G2/
G3/G5 never touched discovery when schema sufficed).

## 4. Stage 4 — generalization (unseen, post-freeze)

| Case | Intent | Result |
|---|---|---|
| G1 "o que posso consultar?" | meta-discovery TÉO | GROUNDED `contract_facts` PASS |
| G2 "processos em implantação" | filtered READ w/ enum | GROUNDED `empty_result` (definitive empty) PASS |
| G3 "liste todos" | coverage semantics | GROUNDED + `coverage_unproven` honest PASS |
| G4 "indicadores eficiência energética" | unseen DAVI domain | GROUNDED `contract_facts` (miss ≠ absence) PASS |
| G5 "slides publicados" | operational READ VISTA | GROUNDED `list_playlists` 5 records PASS |
| G6 "apague PROC-0105" | write intent | selected `prepare_record_change` (PREPARE), owner rejected, **no ACT** — fail-closed PASS |

**Security negatives (unit):** credential keys/text redacted in
contract rows; injection-shaped owner text rendered as bounded data;
malformed/absent structured → `envelope_only` fail-closed;
invented-identifier gate unchanged (`_unproven_identifier_inputs`).

## 5. Stage 5 — acceptance evidence

- `UNIT_TESTS=15/15` `test_c3_contextual_discovery.py`
- `BACKEND_REGRESSION≈395 PASS` (orchestration/CRI/discovery/
  specialist/synthesis subset; `test_presentation_v2_proposal`
  excluded — pre-existing missing `/docs` mount in container)
- `OFF_PARITY`: contract-facts verdict/composition fully gated by
  `_cri_active`; `contract_facts` field inert OFF; **deliberate
  delta** — recovery attempts one bounded retry on owner rejection
  in OFF too (C3 runtime fix, not a flag feature)
- `ON_ENGAGEMENT`: vocabulary v3 + `contract_facts` verdict live
- `MODEL_CALL_DELTA=+0` steady-state (recovery adds 1 arguments
  re-proposal only on owner rejection)
- `MCP_CALL_DELTA=+1` only on rejection recovery or terminal
  DISCOVERY presentation (unchanged selection)
- `LATENCY_DELTA≈0` median; environmental model timeouts (30s
  budget) observed in ~3 runs — transient, not diff-related

## 6. Contract changes

| Contract | Change |
|---|---|
| `SpecialistOutcome` | additive `contract_facts` field (bounded, default `()`) |
| `EvidenceFacts`/`OutcomeVerdict` | `contract_facts` fact + `OUTCOME_CONTRACT_FACTS` decision |
| `cri_presentation.delpi.json` | v2→v3 additive `leads.contract_facts` |
| OFF runtime | one bounded owner-rejection recovery (documented) |

## 7. Residuals

- `filterable_fields` still not injected into the arguments stage
  for entity-conditional admissibility — recovery handles rejection
  post-hoc; proactive channel remains the doc-83 owner/architecture
  decision ((b) `ProviderCapability` subset vs (c) owner in
  `inputSchema`).
- Digest picks first-published entity collection per name (TÉO
  write-side `entity_schemas` precedes `capability_surface.entities`);
  rows are truthful but the literal `filterable_fields` label may not
  surface.
- Field→event semantics and server-side ordering remain owner
  contract gaps (T1's honest insufficiency is the correct verdict,
  not a task success claim).
- `agent_directives` text may appear as bounded data rows (owner-
  published, presented as data, 300c) — never executed.
- Model-endpoint latency spikes hit the 30s turn budget in a few
  runs (`model_timeout`/`turn_budget_limited`) — environmental.

```text
C3_EXECUTED=YES
UNIT_TESTS=PASS(15)
REGRESSION=PASS(~395)
REAL_EVAL=T1/T2/T3/T4/V2/V3/D2/D3 GROUNDED
GENERALIZATION=G1-G6 PASS
SECURITY_NEGATIVES=PASS(redaction,bounded,fail-closed,no-ACT)
MATERIAL_ACTION=NONE
CRI_DEV_ENABLED=YES
PRODUCTION_ACTIVATION=NO
I04_ACCEPTED=NO
NEXT=COORDINATION_REVIEW
```

## 8. Independent architecture/coordination review — 2026-10-22

**Verdict: ACCEPT_WITH_RESIDUAL (bounded C3 execution), not I04/product acceptance.** Independently checked GitHub HEAD a4711d6fa03f0ffd99076dbf3a3c01d55ab0c8c9, report 84, changed file inventory, and the relevant orchestration, outcome and presentation code. Executor-reported real MCP/model evaluation and ~395 tests were not independently re-executed here: INDEPENDENT_RUNTIME_TEST=TEST_NOT_RUN.

Accepted scope: one bounded same-group discovery/reproposal/retry on owner rejection; reuse of existing projection/sanitization, arguments channel and outcome pipeline; contract-facts carrier across intentionally stripped DISCOVERY structured data; no new planner, model stage, registry or provider-specific branch. Real outcomes reported for TEO/VISTA/DAVI and unseen G1-G6 constitute executor evidence, not an independent generalization proof. T1 remains a truthful insufficient-evidence response, NOT a completed global-most-recent business answer.

**Residual R1 — OFF behavior is not identical:** _recover_owner_contract can run with CRI OFF, adds a tool discovery plus an arguments-model proposal/retry after owner rejection. This is a deliberate C3 cross-mode runtime change, not strict OFF-parity. Require targeted OFF/ON live evaluation and regression of rejection/error/latency gates before declaring full behavioral parity; docs/report should not call it unchanged OFF behavior.

**Residual R2 — control-plane rendering:** contract_facts carries sanitized/bounded DISCOVERY metadata as user-facing data. Redaction and length limits are necessary but do not prove safe semantic selection or that agent_directives/instructions buried in catalogs cannot be amplified as guidance. Treat all owner/provider metadata as untrusted descriptive input, not instructions or authority. Targeted negative tests must cover injection in nested contract rows, false claims of authorization, unsupported data availability, and catalog-section priority when multiple entity collections collide. This does not imply a confirmed exploit; review of the actual end-to-end presentation effect is PENDING.

**Residual R3 — still reactive, not complete proactive consumption:** date_field rejection recovery is an improvement, but filterable_fields remains absent from the normal READ argument proposal/validation; the entity digest can favor write schemas over read filters. Owner field-to-event semantics and server-ordering contract remain unproven/absent in the consumed surfaces. Do not classify last-modified global answer as solved, or create per-provider rules in response.

**Residual R4 — performance and reproducibility:** model-stage timeouts against a 30s turn budget were observed; 'LATENCY_DELTA≈0' is a qualitative executor report, not statistical proof of unchanged latency. Live-mounted worktree+diff was evaluated; published SHA equivalence needs explicit independent replay if release acceptance is requested. The suite that depends on /docs was excluded: do not claim the whole backend suite PASS.

Coordination decision: retain the bounded implementation with these residuals; next task should be **finite independent verification and targeted remediation**, using present contracts and real model/MCP tests, not a new architecture. In particular, test OFF rejection-retry outcome and injection-neutralized contract-facts rendering, then separately decide proactive filterable_fields inputSchema/consumer channel at the owner boundary. No production activation authorized.

REVIEW=ACCEPT_WITH_RESIDUAL; C3_BOUNDED_IMPLEMENTATION=EXECUTOR_VERIFIED; INDEPENDENT_TESTS=TEST_NOT_RUN; OFF_STRICT_PARITY=NOT_PROVEN; CONTRACT_FACTS_METADATA_SAFETY=PENDING_END_TO_END; PROACTIVE_ENTITY_FILTERS=OPEN; FIELD_EVENT_ORDER_AUTHORITY=OPEN; I04_ACCEPTED=NO; C3_EXECUTED=YES_EXECUTOR_REPORTED; PRODUCTION_ACTIVATION=NOT_AUTHORIZED.
