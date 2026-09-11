# Desacoplamento de JSONs + inteligência LLM/OpenAPI — Minha DELPI AI

**Status atual:** **REABERTO — Onda J / `VERIFY_FINAL_FAILED`**  
**Plano ativo:** [`planos/11-corrective-cutover-generalization-cleanup.md`](./planos/11-corrective-cutover-generalization-cleanup.md)  
**Candidate anteriormente declarado final:** `782a49721319571f0fe4733d59b8a5cc65ac4c04` — **INVALIDADO como release evidence pela auditoria pós-fechamento**  
**Auditoria vigente:** [`evidence/e11-post-close-audit-2026-09-11.md`](./evidence/e11-post-close-audit-2026-09-11.md)

```text
CUTOVER_RESULT = PARTIAL_PASS
GENERALIZATION_RESULT = INCONCLUSIVE
CLEANUP_RESULT = FAIL
R1_R11_REQUIRED_DIMENSIONS = FAIL
COMPLETE_GATE = FAIL
VERIFY_FINAL = FAIL
FINAL_RESULT = VERIFY_FINAL_FAILED
```

> Os PASS anteriores continuam preservados como evidência histórica do estado em que foram executados. Eles não constituem aceite do estado atual enquanto os bloqueios documentados na auditoria pós-fechamento não forem corrigidos e reexecutados no mesmo candidate final.

## Princípio da iniciativa

```text
catálogo técnico duplicado
→ OpenAPI + Action Catalog

NLU/semântica endpoint-specific
→ semantic understanding + retrieval + structured planner

argument binding
→ semantic delta + OpenAPI schema + validator

multi-turn
→ structured conversation state

policy / business rule / safety
→ determinístico

copy / UX / prompt
→ conteúdo configurável

presentation
→ responseSchema + payload + semantic metadata

contextual prose/recommendations
→ grounded synthesis contextual sem catálogo estático como authority/fallback material permanente
```

## Invariante

```text
NENHUM MAPA LATERAL OU SUBSTITUTO SEMÂNTICO DEVE SER AUTHORITY.
```

`path`, `method` e `operationId` podem existir no Action Catalog como metadata técnica de contrato, execução e observabilidade. Não podem ser usados como heurística hardcoded para decidir domínio, capability, prioridade semântica, continuidade, argument strategy ou apresentação obrigatória no core genérico.

## O que a Onda J já melhorou

- antiga `_DOMAIN_RULES` path-based deixou de ser a authority principal;
- argument binding migrou para schema OpenAPI no caminho principal;
- continuidade path-tail foi reduzida em favor de estado/facets;
- `registrySelectionShadow.cutoverEnabled=true` mantém OpenAPI-first ativo em caminhos relevantes;
- capability metadata passou a derivar de `method + sensitivity`;
- credenciais de smoke deixaram de possuir defaults versionados.

Esses avanços devem ser preservados. A reabertura não é rollback da Onda J.

## Bloqueios vigentes

| ID | Bloqueio | Estado |
|---|---|---|
| A11-01 | R8 marcado PASS com P50/P95 muito acima do alvo Normal `<= 5 s` | **FAIL** |
| A11-02 | corpus `requiredDimensions` não obedece à matriz canônica por classe | **FAIL** |
| A11-03 | manifest offline não é reproduzível pelo runner atual | **FAIL** |
| A11-04 | unknown external prova seleção/binding, não full chain/outcome | **INCONCLUSIVE** |
| A11-05 | live “metamorphic” mede sinônimo, não rename provider/path/operationId | **INCONCLUSIVE** |
| A11-06 | Architecture Enforcement aceita autodeclaração do registry para pular scan | **FAIL** |
| A11-07 | path/operationId ainda participam de semantic affinity em resolver | **FAIL** |
| A11-08 | `operational_route_registry` ainda é catálogo técnico paralelo material | **FAIL** |
| A11-09 | `api_route_domains.json` ainda contém contrato técnico duplicado | **FAIL** |
| A11-10 | single semantic owner não está provado | **PARTIAL/FAIL** |
| A11-11 | `recommendationQueries` permanece `LEGACY_FALLBACK` | **FAIL** |
| A11-12 | IO/generation de filesystem permanece em `domain` | **PARTIAL/FAIL** |

Detalhamento e evidências: [`e11-post-close-audit-2026-09-11.md`](./evidence/e11-post-close-audit-2026-09-11.md).

## Documentos

| Documento | Finalidade |
|---|---|
| [`roadmap.md`](./roadmap.md) | Estado macro + fila corretiva + novo DoD |
| [`planos/11-corrective-cutover-generalization-cleanup.md`](./planos/11-corrective-cutover-generalization-cleanup.md) | Plano ativo da Onda J reaberta |
| [`evidence/e11-post-close-audit-2026-09-11.md`](./evidence/e11-post-close-audit-2026-09-11.md) | Auditoria que invalidou o fechamento anterior |
| [`evidence/e11-s9-final-candidate.md`](./evidence/e11-s9-final-candidate.md) | Candidate histórico invalidado como release final |
| [`evidence/e11-s10-residual-scan-verify-final.md`](./evidence/e11-s10-residual-scan-verify-final.md) | Fechamento histórico invalidado |
| [`evidence/execution-ledger.md`](./evidence/execution-ledger.md) | Ledger de execução e reabertura |
| [`ARCHIVED.md`](./ARCHIVED.md) | Histórico dos fechamentos anteriores |

## Fila corretiva vigente

```text
J-R1  evaluator R8 com threshold canônico          ✅ ATENDIDO
J-R2  requiredDimensions alinhadas automaticamente ✅ ATENDIDO
J-R3  evidence reproduzível                         ✅ ATENDIDO
J-R4  unknown external full chain                   ✅ ATENDIDO
J-R5  metamorphic rename verdadeiro                 ✅ ATENDIDO
J-R6  Architecture Enforcement independente         ✅ ATENDIDO
J-R7  zero path semantic affinity                   ✅ ATENDIDO
J-R8  cleanup registry/content técnico duplicado    ✅ ATENDIDO
J-R9  semantic single owner                         ✅ ATENDIDO
J-R10 recommendations sem LEGACY_FALLBACK material  ← próxima
J-R11 Clean Architecture / IO fora de domain
J-R12 novo candidate R1–R11 + residual + COMPLETE_GATE
```

Não registrar `ARCHIVED`, `VERIFY_FINAL=PASS` ou `FINAL_RESULT=PASS` novamente antes de J-R1…J-R12 cumprirem o gate definido no Plano 11.
