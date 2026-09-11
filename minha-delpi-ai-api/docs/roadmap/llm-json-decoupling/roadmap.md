# Roadmap — desacoplamento de JSONs e generalização LLM/OpenAPI

**Status:** **REABERTO — Onda J**  
**Plano ativo:** [`planos/11-corrective-cutover-generalization-cleanup.md`](./planos/11-corrective-cutover-generalization-cleanup.md)  
**Candidate `782a49721319571f0fe4733d59b8a5cc65ac4c04`:** histórico; **release evidence invalidada**  
**Auditoria vigente:** [`evidence/e11-post-close-audit-2026-09-11.md`](./evidence/e11-post-close-audit-2026-09-11.md)  
**VERIFY_FINAL:** FAIL · **FINAL_RESULT:** `VERIFY_FINAL_FAILED`

## 1. Resultado esperado

```text
mensagem + contexto estruturado
→ semantic understanding com owner canônico
→ goals/subtasks/entities/references
→ allowed Action Catalog
→ semantic retrieval
→ structured planner restricted to candidates
→ OpenAPI schema binder + validator
→ RBAC/policy/confirmation
→ generic execution
→ responseSchema + semantic metadata
→ schema-driven presentation
→ grounded synthesis + contextual recommendations
```

### Invariantes

- API nova não exige regra no core por provider/path/operationId;
- `x-delpi.*` é enrichment opcional, nunca pré-requisito universal;
- path/method/operationId permanecem dados técnicos, não semantic authority;
- argument binding vem do schema OpenAPI;
- multi-turn usa estado estruturado;
- recommendation contextual não depende de catálogo estático como fallback material;
- domain/application respeitam Clean Architecture;
- evals aplicam os thresholds e requiredDimensions canônicos sem autodeclaração/bypass;
- evidência de release é reproduzível e pertence ao mesmo candidate final.

## 2. Histórico × estado vigente

Ondas A–I continuam históricas. A Onda J corrigiu parte dos drifts, mas seu fechamento anterior foi invalidado por auditoria pós-fechamento.

| Área | Estado atual |
|---|---|
| `_DOMAIN_RULES` path-based antiga | **CORRIGIDO** |
| schema-first argument binding | **PASS/PARTIAL** |
| structured continuity | **PASS/PARTIAL** |
| capability method+sensitivity | **PASS** |
| smoke credentials sem defaults | **PASS** |
| technical parallel registry | **FAIL** |
| path-based semantic affinity | **FAIL** |
| semantic single owner | **PARTIAL/FAIL** |
| contextual recommendations | **FAIL** |
| Clean Architecture residual | **PARTIAL/FAIL** |
| unknown external full chain | **INCONCLUSIVE** |
| true metamorphic rename | **INCONCLUSIVE** |
| R8 latency | **FAIL** |
| R1–R11 release evidence | **FAIL / INVALIDADA** |
| Architecture Enforcement | **FAIL** |
| COMPLETE_GATE | **FAIL** |

## 3. Drifts pós-fechamento que reabriram a Onda J

| ID | Drift | Prioridade |
|---|---|---|
| A11-01 | evaluator R8 não aplica alvo Normal `<= 5 s` | P0 |
| A11-02 | corpus `requiredDimensions` diverge da matriz canônica | P0 |
| A11-03 | manifest offline não é reproduzível pelo runner | P0 |
| A11-04 | unknown API não prova execução/presentation/outcome full chain | P0 |
| A11-05 | live metamorphic é sinônimo, não rename técnico | P0 |
| A11-06 | semantic scanner aceita self-attestation do registry | P0 |
| A11-07 | resolver ainda usa path/operationId em semantic affinity | P0 |
| A11-08 | registry técnico paralelo permanece material | P0 |
| A11-09 | assistant content ainda duplica contrato técnico | P0 |
| A11-10 | semantic ownership permanece distribuído | P1 |
| A11-11 | recommendations mantêm `LEGACY_FALLBACK` | P0 |
| A11-12 | filesystem/generation permanece em domain | P1 |

## 4. Fila de execução reaberta

A Onda J continua sendo o plano ativo. Não criar outro plano paralelo para o mesmo objetivo.

```text
J-R1  corrigir R8
  → threshold por responseMode
  → Normal <= 5 s
  → P50/P95 comparados ao contrato

J-R2  corrigir requiredDimensions
  → derivar/validar matriz a partir de chat-ai-flow-families.md
  → impedir corpus incompleto para classes críticas

J-R3  evidence reproducibility
  → runners são única fonte dos manifests
  → nenhum manifest pode contradizer seu próprio runner

J-R4  unknown external full chain
  → provider OpenAPI realmente executável em ambiente controlado
  → executor HTTP + response + presentation + R9

J-R5  metamorphic rename verdadeiro
  → provider/path/operationId todos renomeados
  → summary/description/tags/schema equivalentes
  → mesmo resultado sem core edit

J-R6  Architecture Enforcement independente
  → remover bypass por cleanupMeta/autodeclaração
  → scanner prova comportamento/estrutura real

J-R7  zero path semantic affinity
  → remover filtros semânticos por path/operationId do resolver
  → semantic metadata/retrieval/schema como authority

J-R8  cleanup registry/content técnico
  → retirar operationIds/method/priorities/route maps que duplicam OpenAPI
  → remover pathPrefixToDepartmentId e parameterStrategies residuais sem owner legítimo

J-R9  semantic single owner
  → classificar TOKEN_RULES/routers/mappers
  → KEEP somente vocabulário transversal comprovado
  → remover árvores que ensinam intenção operacional/route family em paralelo

J-R10 contextual recommendations
  → candidate contextual/LLM grounded no caminho normal
  → remover recommendationQueries como LEGACY_FALLBACK material

J-R11 Clean Architecture
  → filesystem/generator fora de domain
  → infrastructure/tooling por ports

J-R12 candidate final novo
  → R1–R11 canônicos
  → unknown full chain
  → metamorphic verdadeiro
  → latency válida
  → residual scan
  → COMPLETE_GATE
  → VERIFY_FINAL
```

## 5. Definition of Done vigente

```text
R8_THRESHOLD_CANONICAL = PASS
REQUIRED_DIMENSIONS_MATRIX = PASS
EVIDENCE_REPRODUCIBLE = PASS
UNKNOWN_EXTERNAL_FULL_CHAIN = PASS
METAMORPHIC_PROVIDER_PATH_OPERATION_ID_RENAME = PASS
ARGUMENT_SCHEMA_AUTHORITY = PASS
MULTI_TURN_STRUCTURED_STATE = PASS
ARCHITECTURE_GATE_INDEPENDENT = PASS
NO_PATH_SEMANTIC_AFFINITY = PASS
TECHNICAL_PARALLEL_REGISTRY = 0 ou JUSTIFIED_NON_SEMANTIC com prova independente
ASSISTANT_CONTENT_TECHNICAL_DUPLICATION = 0
SEMANTIC_AUTHORITY_SINGLE_OWNER = PASS
CONTEXTUAL_RECOMMENDATIONS = PASS
LEGACY_RECOMMENDATION_FALLBACK = 0
CAPABILITY_SECURITY_METADATA = PASS
CLEAN_ARCHITECTURE = PASS
SECURITY_HYGIENE = PASS
SEND_STREAM_SIMULATE_UI = PASS
PERSIST_RELOAD_F5 = PASS
R1_R11_REQUIRED_DIMENSIONS = PASS
RESIDUAL_SCAN = PASS
DOCS_MATCH_FINAL_HEAD = PASS
COMPLETE_GATE = PASS
VERIFY_FINAL = PASS
FINAL_RESULT = PASS
```

Se qualquer linha material estiver `FAIL`, `PARTIAL`, `INCONCLUSIVE`, `LEGACY_FALLBACK` ou sustentada por evidence stale/não reproduzível:

```text
FINAL_RESULT = VERIFY_FINAL_FAILED
```

## 6. Evidências

- Auditoria vigente: [`e11-post-close-audit-2026-09-11.md`](./evidence/e11-post-close-audit-2026-09-11.md)
- Candidate histórico invalidado: [`e11-s9-final-candidate.md`](./evidence/e11-s9-final-candidate.md)
- Fechamento histórico invalidado: [`e11-s10-residual-scan-verify-final.md`](./evidence/e11-s10-residual-scan-verify-final.md)
- Ledger: [`execution-ledger.md`](./evidence/execution-ledger.md)

Não re-arquivar o programa antes de um novo candidate cumprir integralmente a seção 5.
