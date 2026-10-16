# 29 — Stage 03 · Discovery / Guidance — Inventory & Implementation Brief (PLANNED)

**TASK:** `DELIA-C3-CONVERSATIONAL-INTELLIGENCE-STAGE02-CLOSURE-STAGE03-IMPLEMENTATION-01` / **TASK B**  
**MODE:** Authorization Gate + inventory + proposed brief — **NO RUNTIME**.  
**STATUS:** `PLANNED` · `STAGE_03_IMPLEMENTATION_AUTHORIZED=NO` · `STAGE_03_AUTHORIZATION_REQUIRED`

---

## 1. Authorization Gate (obrigatório)

Consultado após persistência do aceite Stage02 (doc [28](./28-stage-02-independent-architecture-acceptance-closure.md) / §6.201):

| Check | Result |
|---|---|
| Stage02 aceite persistido | YES (`YES_WITH_RESIDUAL`) |
| Plano mestre / doc02 Etapa 03 | PLANNED — discovery/guidance provider-neutral |
| Doc03 evals row Etapa 03 | `PLANNED` / `NOT_STARTED` / `PENDING` |
| Ledger authorization explícita Stage03 | **AUSENTE** — todas entradas recentes `STAGE_03_AUTHORIZED=NO` |
| Product Master / Coordination runtime authorize | **NÃO ENCONTRADA** neste HEAD |
| Phase C3/C4/C5 | `C3_EXECUTED=NO`; Stage03 ≠ C3 phase completion |

```text
STAGE_02_ACCEPTANCE_PERSISTED=YES (doc28 / §6.201)
STAGE_03_REQUIREMENTS_IDENTIFIED=PARTIAL (doc02 §Etapa03 + matriz 20/25 candidates)
STAGE_03_ACCEPTANCE_CRITERIA_IDENTIFIED=PARTIAL (doc03 CI cases + D3-* candidates)
STAGE_03_OWNER_CONFIRMED=YES (DÉLIA Intelligence/Orchestration; owners Domain/MCP)
STAGE_03_CONTRACTS_CONFIRMED=PARTIAL (reuse live tools/list §6.126; no new Stage03 wire approved)
STAGE_03_IMPLEMENTATION_AUTHORIZED=NO
```

**STOP runtime.** Este documento não autoriza código.

---

## 2. Escopo canônico (orientação, não aprovação)

Do [02 — plano bounded](./02-bounded-delivery-plan.md):

- Consumir authenticated live `tools/list` como superfície primária (§6.126).
- Buscar DISCOVERY/get_catalog/guidance **somente** quando pertinente e autorizado.
- **Não** criar `get_product_guide` obrigatório, catálogo local MCP, ou tratar erro owner como instrução confiável.
- Gate: zero hardcode TÉO/DAVI/VISTA; zero discovery universal de strings; nenhum ACT por guia.

Comportamento alvo (produto): orientar “como cadastrar…” sem PREPARE/ACT pelo verbo; declarar limitação se guidance ausente (já parcialmente observado em CI-LIVE-01).

---

## 3. Inventory — EXISTING_EQUIVALENT

| Responsibility | Owner | Canonical source | Consumers | Contract | Current impl | Tests | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|---|---|---|---|---|---|
| Interactive turns | delia-api Application | `HandleInteractiveTurn` | MFE | MESSAGE/APPLY/REJECT | PROVEN Stage02 | interaction suite | YES | REUSE |
| Intent/goal | orchestration | turn_goal / native_assessment | planner | model propose + gates | PROVEN | stage02r2 | YES | REUSE/EXTEND |
| Capability projection | specialist interop | live tools/list + class | orchestrator | DISCOVERY\|READ\|ANALYSIS\|PREPARE\|ACT | PROVEN | interop tests | YES | REUSE |
| Provider-neutral orchestration | capability_provision | semantic select | turns | no owner branches | PROVEN | provider-neutral | YES | REUSE |
| Clarification | intelligence loop | clarification gates | turns | no internal leak | PROVEN | IL tests | YES | REUSE |
| Grounded rendering | presentation / outcome | deterministic | MFE | epistemic classes | PROVEN | presentation | YES | REUSE |
| Product guide / guidance topic | owner MCP (DAVI etc.) | owner tools | orchestrator | topic catalog | PARTIAL (unknown topic → limitation) | live CI-01 | TO_INVENTORY | EXTEND if authorized |
| Evidence/provenance | attempt provenance | provider_id/capability | UI | SourceRef | PROVEN | live CI-04 | YES | REUSE |
| PendingWrite / ACT path | orchestration | doc18 | MFE | Stage02 ACCEPT | PROVEN | concurrent | YES | **REUSE — do not alter** |
| Chat AI catalog/RAG | minha-delpi-ai-api | OUT_OF_SCOPE | — | — | — | — | N/A | **DO_NOT_REUSE** |

```text
EXISTING_EQUIVALENT=YES (core path)
REUSE_DECISION=REUSE|EXTEND (guidance seam only if authorized)
EXISTING_OWNER=delia-api orchestration + remote specialists
EXISTING_CONTRACT=live tools/list + SpecialistOperationClass; Stage02 command contract
NEW_RUNTIME=NO (until authorized)
NEW_ENGINE=NO
NEW_REGISTRY=NO
```

---

## 4. Proposed implementation brief (PLANNED — not authorized)

**Se e somente se** Coordination autorizar Stage03 no ledger:

1. EXTEND seleção/clarification para priorizar DISCOVERY/guidance quando `PROMPT_CLASS=guidance` (sem novo planner).
2. Consumir guidance/catalog owner-bound já projetado; fail-closed se topic/capability ausente.
3. Preservar D3-10: verbo de escrita em pergunta orientativa ≠ PREPARE.
4. Eval harness: D3-01..15 reconciliados com matriz 20/25; holdouts obrigatórios.
5. Zero alteração MESSAGE→ACT / PendingWrite / multi-worker.

**Abstraction Gate:** qualquer NEW formatter/registry → rejeitar sem Architecture decision.

---

## 5. Candidate RQ/AC (não implementados)

| RQ_ID | Requirement | Criticality | Status |
|---|---|---|---|
| RQ-S03-01 | Guidance grounded when owner topic exists | HIGH | NOT_IMPLEMENTED |
| RQ-S03-02 | Honest limitation when guidance missing | HIGH | PARTIAL (live behavior) |
| RQ-S03-03 | Provider-neutral discovery (no owner if) | HIGH | PARTIAL (infra exists) |
| RQ-S03-04 | Writing-verb question ≠ PREPARE/ACT | CRITICAL | PARTIAL (B1/B2 + CI-01) |
| RQ-S03-05 | AuthZ fail-closed on protected capability | HIGH | PARTIAL (platform) |
| RQ-S03-06 | Tool rename / metamorphic invariance | HIGH | NOT_IMPLEMENTED (Stage03 eval) |

AC: D3-01..15 = `PENDING` / `TEST_NOT_RUN` até autorização.

```text
TOTAL_RQ=6 (candidate)
APPLICABLE_RQ=6
IMPLEMENTED_RQ=0
PARTIAL_RQ=3
NOT_IMPLEMENTED_RQ=3
BLOCKED_RQ=0 (blocked by authorization, not by defect)
TASK_VERIFIED_COVERAGE_PCT=0 (no Stage03 implementation claim)
```

---

## 6. Exit

```text
TASK_B_STATUS=AUTHORIZATION_GATE_FAILED_RUNTIME_BLOCKED
STAGE_03_AUTHORIZATION_SOURCE=NONE_IN_LEDGER_OR_MASTER_PLAN_DECISION
STAGE_03_IMPLEMENTATION_AUTHORIZED=NO
IMPLEMENTATION_VERDICT=NOT_STARTED
STAGE_03_STARTED=NO
NEXT=RETURN_TO_ARCHITECTURE_COORDINATION_FOR_STAGE_03_AUTHORIZATION
```

`STAGE 02 ACCEPTANCE ≠ AUTOMATIC STAGE 03 AUTHORIZATION`
