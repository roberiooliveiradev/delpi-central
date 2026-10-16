# 30 — Stage 03 · Bounded Implementation Authorization

**DECISION_ID:** `DELIA-C3-STAGE-03-BOUNDED-IMPLEMENTATION-AUTHORIZATION-01`  
**TASK:** `DELIA-C3-CONVERSATIONAL-INTELLIGENCE-STAGE-03-IMPLEMENTATION-01`  
**MODE:** documentary authorization — **must precede** any functional Stage03 diff  
**AUTHORITY:** Architecture / Coordination + Product Master (bounded authorize in task brief)

---

## 1. Decisão

```text
STAGE_02_ACCEPTED=YES_WITH_RESIDUAL

STAGE_03_AUTHORIZATION_DECISION=APPROVED_BOUNDED
STAGE_03_AUTHORIZED=YES
STAGE_03_STARTED=NO
STAGE_03_ACCEPTED=NO

AUTHORIZED_SCOPE=PROVIDER_NEUTRAL_DISCOVERY_AND_GUIDANCE
AUTHORIZED_OPERATION_CLASSES=DISCOVERY|READ|NON_MUTATING_ANALYSIS
MATERIAL_ACT_AUTHORIZED=NO

C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
PRODUCTION_READINESS=NOT_PROVEN
```

`STAGE_03_AUTHORIZED=YES` autoriza **somente** implementar o slice após reancoragem e este registro. Não é implementação nem aceite.

## 2. Escopo autorizado

- Extender seams existentes de Discovery/Guidance provider-neutral.
- Consumir authenticated live `tools/list`.
- Invocar DISCOVERY/get_catalog/guidance **somente** quando pertinente e autorizado.
- Orientação grounded + limitações honestas.
- Preservar Stage02: `MESSAGE != ACT`, `PREPARE != ACT`, PendingWrite, typed APPLY/REJECT.

## 3. Exclusões

- Novo planner / engine / registry / catálogo MCP local.
- Hardcode DAVI/TÉO/VISTA.
- `get_product_guide` obrigatório universal.
- Dependência Minha DELPI Chat.
- ACT/PREPARE material empresarial; mutações Domain.
- Avanço C3_EXECUTED / C4 / C5 / production readiness.
- Alteração PendingWrite sem finding material.
- Markdown CP-333 / presentation.v2.

## 4. Owners

| Concern | Owner |
|---|---|
| Implementation | delia-api Application (capability_provision / interaction) |
| Capability existence/class | Remote specialist (tools/list) |
| AuthZ | Core + Domain |
| Acceptance | Architecture / Coordination (independent review) |

## 5. Contratos existentes

- Doc18 / §6.184 execution scope (preserved).
- §6.126 specialist-owned live tools/list.
- SpecialistOperationClass DISCOVERY|READ|ANALYSIS|PREPARE|ACT.
- Doc29 inventory: EXISTING_EQUIVALENT=YES core; REUSE|EXTEND guidance seam.

## 6. CP/RQ/AC aplicáveis (candidatos reconciliados)

| RQ | Objetivo | Status at authorize |
|---|---|---|
| RQ-S03-01 | Guidance grounded when available | NOT_IMPLEMENTED |
| RQ-S03-02 | Honest limitation when absent | PARTIAL |
| RQ-S03-03 | Provider-neutral discovery | PARTIAL (infra) |
| RQ-S03-04 | Writing-verb question ≠ PREPARE/ACT | PARTIAL (Stage02) |
| RQ-S03-05 | AuthZ fail-closed | PARTIAL (platform) |
| RQ-S03-06 | Tool rename invariance | NOT_IMPLEMENTED |

CPs globais **não** promovidos por esta autorização.

## 7. Segurança

`DISCOVERY != APPROVAL` · `MCP RESULT != FACT` · `GUIDANCE != EXECUTION` · `MATERIAL_ACT_AUTHORIZED=NO`

## 8. Reuse Gate

```text
EXISTING_EQUIVALENT=YES (core path)
REUSE_DECISION=EXTEND (_requires_owner_vocabulary / discovery plan gate)
NEW_PLANNER=NO NEW_REGISTRY=NO NEW_ENGINE=NO
```

## 9. Critérios de aceite (implementação → review)

- D3-01..15 verdes no escopo aplicável (ou residual explícito).
- Stage02 regression verde.
- Provider-neutrality / no owner-name branches.
- Evidence report + independent review; `STAGE_03_ACCEPTED=NO` até Coordination.

## 10. STOP

Authority conflict · ownership change · ACT required · Chat dependency · Abstraction Gate fail → `ARCHITECTURE_DECISION_REQUIRED` / `EXECUTION_DRIFT`.

## 11. NEXT

```text
NEXT=INVENTORY_BASELINE_RED_THEN_MINIMAL_EXTEND
```

After implementation evidence: `INDEPENDENT_STAGE_03_ARCHITECTURE_REVIEW`.

**Post-implementation pointer (does not rewrite the authorize-time decision above):** evidence in [31](./31-stage-03-discovery-guidance-implementation-report.md) / ledger §6.205; `STAGE_03_ACCEPTED` remains `NO` until independent review.
