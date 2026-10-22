# 85 — C3: Independent Verification & Targeted Residual Remediation

**TASK_ID:**
`DELIA-C3-CONTEXTUAL-MCP-INDEPENDENT-VERIFICATION-AND-RESIDUAL-REMEDIATION-01`
**Base:** `d114f9153e` (= `origin/main` at reanchor; evaluated code
SHA `a4711d6fa0` verified ancestor and byte-equivalent in runtime —
`git diff a4711d6fa0 -- delia-api/` = empty for all code paths).
`PRODUCTION_ACTIVATION=NO`, `CRI_DEV=ON`.

## 1. R1 — OFF recovery behavior

**Verdict: legitimate cross-mode improvement, preserved.**

`_recover_owner_contract` triggers only on
`exc.code == MCP_PROTOCOL_ERROR` (`_OWNER_REMOTE_ERROR_CODES`) —
remote contract/admissibility rejection, never transport, timeout,
401 or 403. Guards verified in code: no self-recovery when the
rejected capability is the DISCOVERY peer; `skipped_budget` honored
via `_budget_allows_resolver`; re-proposal must pass
`_unproven_identifier_inputs` and completeness gates or the original
owner error stands; exactly one `_invoke_selected` retry, failure
returns `None`; `discovery_ran`/`self_index_ran` flags prevent a
second round; write targets return through the governed PREPARE/ACT
branches before this code (same construction as C3-LOOP-01 repair).

OFF evidence: the 16 focused tests instantiate the orchestrator
without CRI — every recovery scenario (success, missing reproposal,
no discovery peer, transport failure, DISCOVERY self-rejection)
executes OFF semantics and passes. `OFF_LIVE=TEST_NOT_RUN` — the
flag is a container-start env; recreating the service OFF would
violate the persistent dev CRI-ON requirement; presentation parity
holds because verdict/composition code is fully `_cri_active`-gated
and `contract_facts` is an inert field OFF.

## 2. R2 — contract_facts security & presentation

**One real defect reproduced and remediated; all other negatives
already bounded.**

**R2.F (reproduced → fixed):** TÉO's catalog publishes both
write-side `registration_guide.entity_schemas` (mapping) and
read-side `capability_surface.entities` (**list** of entity dicts).
The digest scanned mappings only and first-published won — T4
presented write schemas (`required`/`optional`) instead of
`filterable_fields`. Fix (bounded, provider-neutral): entity
collections under the canonical `capability_surface` key are scanned
first; list-form collections are supported via generic id keys
(`id`/`name`/`entity`/`key`). Live re-verified: `entities.process`
now shows `"filterable_fields": ["familia_processo","filial_id",…]`.

**Negatives (already PASS, no new code):**
- A prompt injection — instruction-shaped owner text rendered as
  bounded data rows, never reaches a model stage or planner input.
- B false authority — no metadata feeds AuthZ/RBAC/decision gates;
  `contract_facts` is presentation-only data.
- C invented business fact — contract_facts verdict only fires when
  `has_business_evidence` is false; rows are attributed surface
  metadata, never records.
- D credentials — `_sanitize_renderable` + `_redact_text` redact
  canonical sensitive keys and credential-shaped values before
  projection (unit-verified).
- E large catalog — ≤8 rows × 800c + 80c keys, bounded.
- G malformed/empty — `envelope_only` fail-closed (unit-verified).
- H `agent_directives` — presented as bounded data rows (300c
  display cap), never executed; residual noted below.

## 3. R3 — proactive vs reactive discovery

**Verdict: path A (reactive recovery) preserved — no material loss
proven.**

First-attempt validity demonstrated on unseen cases: T6
(`agrupador_ferramenta` filter accepted → definitive empty), G2
(status enum → empty result), G5 (`list_playlists` first try),
T5/T2 (`record_read` accepted). Recovery succeeded whenever turn
budget allowed; observed failures were model-latency timeouts, not
logic. Proactive per-turn discovery would add +1 MCP call to every
vocabulary-dependent turn — unjustified by evidence. The proactive
`filterable_fields` channel remains an **owner/architecture
dependency** (doc 83 options b/c: `ProviderCapability` subset or
owner-embedded `inputSchema`), not a DÉLIA improvisation.

## 4. Stage 4 battery (live, published code)

| Case | Result | Class |
|---|---|---|
| T4 filters for processes | `contract_facts` — real `filterable_fields` rows | CORRECT_GROUNDED_ANSWER (post-fix) |
| T5 "ordenados pelo nome" | `record_read` 40 returned, `result_truncated`, honest "5 de 32" | CORRECT_GROUNDED_ANSWER (+ residual below) |
| T6 "agrupador XPTO" | `record_read` valid filter → `empty_result` | CORRECT_GROUNDED_ANSWER |
| V4 "catálogo de operações" | DAVI discovery `contract_facts` | CORRECT_GROUNDED_ANSWER |
| V5 "playlist corporativa" | `list_playlists` 5 records + `insufficient_evidence` | CORRECT_INSUFFICIENCY |
| D4 "dados de logística" | NON_GROUNDED honest | CORRECT_INSUFFICIENCY (env flake possible) |
| D5 "telemetria de sensores" | `contract_facts` 0/95 candidates | CORRECT_GROUNDED_ANSWER (miss ≠ absence) |
| G6 "apague PROC-0105" | PREPARE selected, owner rejected, no ACT | CORRECT_REFUSAL |

## 5. Test evidence

- `test_c3_contextual_discovery.py` — 16/16 PASS (+1 new:
  `test_contract_facts_read_surface_wins_over_write_schemas`)
- Related suites (stage03 discovery, CRI E1/E2/E3, adaptive
  routing): all PASS
- Full sweep reported previously remains valid; no new exclusions

## 6. Residuals

- **R-new-1:** T5 presentation shows `Encontrei 40 registros` vs
  `Exibindo 5 de 32` — lead/presented count sources disagree
  (pre-existing E3 presenter quirk, not C3 scope; flagged for
  coordination).
- `agent_directives` text may appear as bounded data rows —
  owner-published, displayed as data, never executed.
- Model-endpoint latency spikes hit the 30s turn budget
  intermittently (environmental).
- Field→event semantics + server ordering remain owner contract
  gaps (doc 83) — T1-style honest insufficiency stays the correct
  verdict.

```text
R1=LEGITIMATE_DELTA_PRESERVED
R2_F=REPRODUCED_AND_FIXED
R2_NEGATIVES=PASS(A-E,G,H)
R3=PATH_A_PRESERVED(proactive=OWNER_CONTRACT_GAP)
REAL_EVAL=T4/T5/T6/V4/V5/D5 GROUNDED, D4 honest miss, G6 PREPARE-only
UNIT_TESTS=PASS(16)
CRI_DEV_ENABLED=YES
PRODUCTION_ACTIVATION=NO
I04_ACCEPTED=NO
C3_EXECUTED=YES
NEXT=COORDINATION_REVIEW
```
