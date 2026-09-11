# Plano 11 — Correção arquitetural: cutover + generalização + cleanup sem residual

**Prioridade:** P0  
**Status execução:** **REABERTO — Onda J / `VERIFY_FINAL_FAILED`** · J-R1–J-R4 **ATENDIDO** · próxima = **J-R5**  
**BASE_GIT_SHA original (E11.S0):** `8bc84fc6d1cea3edc8cd0c08dceee90f9303e777`  
**Candidate anteriormente declarado final:** `782a49721319571f0fe4733d59b8a5cc65ac4c04` — **histórico invalidado como release evidence**  
**Auditoria pós-fechamento:** [`../evidence/e11-post-close-audit-2026-09-11.md`](../evidence/e11-post-close-audit-2026-09-11.md)  
**Objetivo perceptível:** concluir de fato o desacoplamento OpenAPI-first, removendo authorities paralelas e substitutos semânticos do legado, provando generalização para API nunca vista e fechando somente com evidência reproduzível, thresholds canônicos e zero pendência material escondida como PASS.

> O primeiro fechamento da Onda J é preservado como histórico em E11.S9/E11.S10. A auditoria posterior demonstrou que `COMPLETE_GATE` e `VERIFY_FINAL` não podiam ter passado. Este documento volta a ser o plano ativo para o mesmo objetivo; não criar plano paralelo.

---

## 0. Regras obrigatórias de execução

Antes de qualquer diff de runtime, ler na ordem:

1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`
2. `.cursor/rules/development-standards-index.mdc`
3. `.cursor/rules/evidence-driven-execution.mdc`
4. `.cursor/rules/plan-construction.mdc`
5. `.cursor/rules/plan-execution.mdc`
6. `.cursor/rules/test-and-commit.mdc`
7. `.cursor/rules/openapi-first-universal-tool-routing.mdc`
8. `.cursor/rules/operational-api-routing.mdc`
9. `.cursor/rules/assistant-content-json.mdc`
10. `.cursor/rules/ai-intelligence-evaluation.mdc`
11. `.cursor/rules/clean-architecture-chat-api.mdc`
12. `.cursor/rules/ai-external-tools-security.mdc`
13. `.cursor/rules/llm-stack-centralized.mdc`
14. `minha-delpi-ai-api/docs/testing/chat-ai-flow-families.md`

### Sequência inviolável

```text
CUTOVER
→ PROVA DE WIRING REAL
→ GENERALIZAÇÃO
→ POSITIVE + SIBLING + NEGATIVE
→ METAMORPHIC / UNKNOWN API quando material
→ CLEANUP
→ BUSCA RESIDUAL SEMÂNTICA
→ VERIFY
→ COMPLETE_GATE
```

### Sem “concluído com pendência”

Enquanto existir item material do escopo em qualquer estado abaixo, o plano permanece aberto:

```text
PARTIAL
ATENDIDO_PARCIAL
LEGACY_FALLBACK
SHADOW_ONLY
INCONCLUSIVE
PENDING
DEFERRED sem justificativa real de fora de escopo
TODO
FIXME
HACK
TEMPORARY
feature flag sem exit criteria
compatibility branch sem exit criteria
evidence stale ou não reproduzível
gate enfraquecido para acomodar candidate
```

---

# 1. Estado histórico da Onda J

A execução E11.S0–S10 gerou melhorias válidas e um primeiro fechamento. A auditoria pós-fechamento reclassifica esse estado assim:

| Etapa | Estado pós-auditoria | Observação |
|---|---|---|
| E11.S0 | PASS histórico | rebaseline/freeze preservados |
| E11.S1 | **REABERTO — FAIL** | gate possui bypass por autodeclaração |
| E11.S2 | PASS com verify final pendente | `_DOMAIN_RULES` antiga removida como authority |
| E11.S3 | PASS/PARTIAL | schema-first ativo; content técnico residual |
| E11.S4 | PASS/PARTIAL | structured continuity melhorou; metamorphic final pendente |
| E11.S5 | **REABERTO — FAIL** | registry/path semantic affinity material |
| E11.S6 | **REABERTO — PARTIAL/FAIL** | single semantic owner não provado |
| E11.S7 capability | PASS | method+sensitivity correto |
| E11.S7 recommendations | **REABERTO — FAIL** | `recommendationQueries` = `LEGACY_FALLBACK` |
| E11.S8 credentials | PASS | env-only |
| E11.S8 Clean Architecture | **REABERTO — PARTIAL/FAIL** | filesystem/generator em domain |
| E11.S9 | **INVALIDADO** | R8/dimensões/evidence/unknown/metamorphic |
| E11.S10 | **INVALIDADO** | COMPLETE_GATE não podia passar |

O histórico detalhado permanece nas evidências E11.S0–S10 e no ledger.

---

# 2. Drifts pós-fechamento confirmados

## A11-01 — R8 aprovado sem threshold canônico

Modo Normal possui alvo total `<= 5 s`. O candidate histórico registrou aproximadamente P50 `41,5 s` e P95 `50,7 s`; o runner marcou PASS apenas porque P95/tokens/provider estavam presentes.

**Estado:** `FAIL`  
**Tipo:** `EVALUATION_GATE_WEAKENING`.

## A11-02 — `requiredDimensions` do corpus incompletas

Classes de args, security, compound e unknown provider não carregam todas as dimensões mínimas definidas em `chat-ai-flow-families.md`.

**Estado:** `FAIL`  
**Tipo:** `REQUIRED_DIMENSION_COVERAGE_DRIFT`.

## A11-03 — evidence não reproduzível

O runner offline atual grava `globalReleasePass=false` enquanto live dims estão deferred; o manifest versionado possui `globalReleasePass=true` e mantém `reasonGlobalReleasePassFalse`.

**Estado:** `FAIL`  
**Tipo:** `NON_REPRODUCIBLE_EVIDENCE`.

## A11-04 — unknown external API sem full chain

Import/retrieval/selection/binding foram provados, porém o provider live usa `example.invalid` e o harness aceita falha HTTP após binding.

**Estado:** `INCONCLUSIVE` para executor/response/presentation/R9.

## A11-05 — metamorphic live não renomeia provider/path/operationId

O smoke live compara sinônimos de estoque. Isso prova robustez linguística, não invariância a rename técnico.

**Estado:** `INCONCLUSIVE`.

## A11-06 — Architecture Enforcement com self-attestation bypass

`SEMANTIC_TECHNICAL_OPERATION_ID_CATALOG` pode retornar sem analisar o registry se o próprio JSON declarar `cleanupMeta.operationIdsRuntimeAuthority=false`.

**Estado:** `FAIL`.

## A11-07 — path/operationId ainda participam de semantic affinity

`OperationalRouteActionResolverService` ainda usa path/operationId, suffix/markers e regras como `/products/`, `search`, `supplier` e facets contidas no path para filtrar candidates.

**Estado:** `FAIL`.

## A11-08 — registry técnico paralelo permanece

`operational_route_registry.json` mantém `operationIds`, method, priority, terms/predicates/domínios e possui consumers runtime.

**Estado:** `FAIL`.

## A11-09 — assistant content técnico duplicado

`api_route_domains.json` ainda possui `method`, `parameterStrategies` e `pathPrefixToDepartmentId`, entre outros nós que devem ser eliminados ou justificados como regra não técnica por owner canônico.

**Estado:** `FAIL`.

## A11-10 — semantic single owner não provado

Permanecem `ChatTurnUnderstandingService`, `ChatIntentRouter`, `ChatTurnAnalysis`, `ChatTaskPlannerService` heurístico e mappers `_TOKEN_RULES` KPI/product/production em paralelo.

**Estado:** `PARTIAL/FAIL`.

## A11-11 — recommendations com `LEGACY_FALLBACK`

O producer e o content mantêm `recommendationQueries` estático; LLM contextual segue opt-in.

**Estado:** `FAIL`.

## A11-12 — Clean Architecture residual

`OperationalRouteRegistryGeneratorService` permanece em domain fazendo filesystem/generation.

**Estado:** `PARTIAL/FAIL`.

---

# 3. Ledger de requisitos revisado

| ID | Requisito | Estado vigente |
|---|---|---|
| RQ11-01 | Eliminar path→domain maps/substitutos do core genérico | PASS com verify final pendente |
| RQ11-02 | Eliminar endpoint→parameterStrategy e usar OpenAPI schema | PASS/PARTIAL |
| RQ11-03 | Eliminar continuidade derivada de path/operationId | PASS/PARTIAL |
| RQ11-04 | Remover registry/operationIds como authority de routing | **FAIL** |
| RQ11-05 | Consolidar ownership semântico | **PARTIAL/FAIL** |
| RQ11-06 | Recommendations contextuais sem legado material | **FAIL** |
| RQ11-07 | Capability metadata contract-derived | PASS |
| RQ11-08 | Clean Architecture boundaries/DI/filesystem | **PARTIAL/FAIL** |
| RQ11-09 | Remover credenciais hardcoded/defaults | PASS |
| RQ11-10 | Architecture Enforcement independente e conceitual | **FAIL** |
| RQ11-11 | Unknown external full chain + true metamorphic rename | **INCONCLUSIVE** |
| RQ11-12 | Candidate final R1–R11 com matriz/thresholds corretos | **FAIL** |
| RQ11-13 | Encerrar fallbacks/shadows/TODOs materiais | **FAIL** |
| RQ11-14 | Docs refletirem estado real | PASS após reabertura documental |

---

# 4. Arquitetura TARGET

```text
USER MESSAGE + STRUCTURED CONVERSATION STATE
        |
        v
CANONICAL SEMANTIC TURN UNDERSTANDING
        |
        v
goals + entities + references + presentation intent
        |
        v
ALLOWED ACTION CATALOG
        |
        v
semantic retrieval per goal
        |
        v
STRUCTURED PLANNER restricted to candidates
        |
        v
argument delta
        |
        v
OPENAPI SCHEMA BINDER + VALIDATOR
        |
        v
RBAC + sensitivity + confirmation
        |
        v
GENERIC EXECUTOR
        |
        v
responseSchema + payload + semantic metadata
        |
        v
SCHEMA-DRIVEN PRESENTATION
        |
        v
GROUNDED SYNTHESIS + CONTEXTUAL RECOMMENDATIONS
```

### Invariantes

- API nova não exige editar core por endpoint/provider/path/operationId;
- `x-delpi.*` é opcional;
- path/method/operationId são metadata técnica, não decisão semântica;
- LLM não escolhe action fora de candidates autorizadas;
- RBAC/safety/validation são determinísticos;
- MFE não redecide semântica;
- F5/reload reutiliza estado persistido;
- eval/gates não podem ser aprovados por self-attestation do artefato auditado;
- runner e manifest devem produzir o mesmo veredito.

---

# 5. Fila corretiva reaberta

## J-R1 — corrigir R8

**Objetivo:** tornar latency gate aderente ao contrato canônico.  
**Status:** **ATENDIDO** · `R8_THRESHOLD_CANONICAL=PASS` · evidência [`../evidence/e11-j-r1-r8-threshold-canonical.md`](../evidence/e11-j-r1-r8-threshold-canonical.md)

Fazer:

- resolver threshold por responseMode;
- Normal `<= 5 s`, Rápida `<= 3 s`, Pensador `<= 15 s` enquanto esses forem os valores canônicos;
- comparar P50/P95 conforme a regra definida para release;
- falhar quando threshold obrigatório for excedido;
- não aumentar threshold apenas para acomodar o candidate.

**Gate:** `R8_THRESHOLD_CANONICAL = PASS` (**cumprido** — `ChatR8LatencyThresholdService` + runner `run_e9_s11_efficiency_live.py`).

**Próxima:** J-R2.

## J-R2 — corrigir requiredDimensions

**Objetivo:** impedir corpus que cubra menos dimensões que a matriz canônica.  
**Status:** **ATENDIDO** · `REQUIRED_DIMENSIONS_MATRIX=PASS` · evidência [`../evidence/e11-j-r2-required-dimensions-matrix.md`](../evidence/e11-j-r2-required-dimensions-matrix.md)

Fazer:

- materializar uma validação automática entre cada classe/caso e `chat-ai-flow-families.md`;
- security precisa incluir R10;
- args precisam incluir R3;
- compound/action OpenAPI precisam incluir todas as dimensões mínimas aplicáveis;
- corpus inválido bloqueia runner antes dos testes.

**Gate:** `REQUIRED_DIMENSIONS_MATRIX = PASS` (**cumprido** — `ChatRequiredDimensionsMatrixService` + `r1_r11_corpus_v2` + `assert_corpus_required_dimensions.py`).

**Próxima:** J-R3.

## J-R3 — evidence reproduzível

**Objetivo:** runner ser a única fonte de manifest/veredito.  
**Status:** **ATENDIDO** · `EVIDENCE_REPRODUCIBLE=PASS` · evidência [`../evidence/e11-j-r3-evidence-reproducible.md`](../evidence/e11-j-r3-evidence-reproducible.md)

Fazer:

- regenerar manifests por script;
- proibir edição manual de campos de resultado;
- hash do runner/config/corpus no manifest;
- teste que reexecuta/verifica consistência estrutural;
- qualquer divergência = FAIL.

**Gate:** `EVIDENCE_REPRODUCIBLE = PASS` (**cumprido** — `ChatEvidenceReproducibilityService` + align script + provenance no runner offline).

**Próxima:** J-R4.

## J-R4 — unknown external full chain

**Objetivo:** provar plugabilidade real além de seleção/binding.  
**Status:** **ATENDIDO** · `UNKNOWN_EXTERNAL_FULL_CHAIN=PASS` · evidência [`../evidence/e11-j-r4-unknown-external-full-chain.md`](../evidence/e11-j-r4-unknown-external-full-chain.md)

Fazer:

- provider OpenAPI nunca visto em ambiente controlado/local;
- endpoint executável;
- import/index/binding sem core edit;
- retrieval/planner/args/validator/policy/executor;
- response real;
- presentation schema-driven;
- oracle R9 do outcome.

**Gate:** `UNKNOWN_EXTERNAL_FULL_CHAIN = PASS` (**cumprido** — HTTP local + `HttpExternalActionGateway` + presentation/outcome).

**Próxima:** J-R5.

## J-R5 — metamorphic rename verdadeiro

Criar V1 e V2 semanticamente equivalentes:

```text
providerKey V1 != V2
path V1 != V2
operationId V1 != V2
summary/description/tags/schema equivalentes
```

Provar comportamento equivalente sem nova regra no core/registry/content.

**Gate:** `METAMORPHIC_PROVIDER_PATH_OPERATION_ID_RENAME = PASS`.

## J-R6 — Architecture Enforcement independente

Fazer:

- remover bypass baseado em `cleanupMeta.operationIdsRuntimeAuthority=false`;
- classificação KEEP/observer não pode silenciar o scanner sem prova externa;
- positive/sibling/negative para registry/path affinity/content duplication;
- gate deve detectar comportamento equivalente com outro nome/arquivo.

**Gate:** `ARCHITECTURE_GATE_INDEPENDENT = PASS`.

## J-R7 — zero path semantic affinity

Fazer cutover dos consumers reais antes do DELETE:

- remover path/operationId markers/suffixes como filtro semântico;
- remover regras `/products/`, `search`, `supplier` etc. usadas para decidir afinidade de route;
- semantic metadata do Action Catalog + retrieval + schema substituem a decisão;
- uso de path continua permitido somente para execução/contrato/observabilidade.

Provas: known, sibling, negative, unknown, metamorphic.

**Gate:** `NO_PATH_SEMANTIC_AFFINITY = PASS`.

## J-R8 — cleanup registry/content técnico

Classificar cada campo de `operational_route_registry.json` e `api_route_domains.json`:

```text
CONTRACT_DUPLICATION_REMOVE
SEMANTIC_AUTHORITY_REMOVE
UX_POLICY_KEEP
BUSINESS_POLICY_KEEP
OBSERVABILITY_KEEP
DEAD_CODE_REMOVE
```

Remover especialmente, quando duplicarem OpenAPI/Action Catalog ou ensinarem routing:

- operationIds manuais;
- HTTP method duplicado;
- route priorities por endpoint;
- pathPrefixToDepartmentId;
- parameterStrategies que reconstruam contrato técnico;
- generators/mirrors que congelam OpenAPI em segundo catálogo sem consumer legítimo.

**Gate:** `ASSISTANT_CONTENT_TECHNICAL_DUPLICATION=0` e `TECHNICAL_PARALLEL_REGISTRY=0` ou exceção comprovadamente não semântica.

## J-R9 — semantic single owner

Inventariar e decidir ownership real de:

- `ChatTurnUnderstandingService`;
- `ChatTurnAnalysisService`;
- `ChatIntentRouterService`;
- `ChatTaskPlannerService`;
- KPI/Product/Production mappers;
- `_TOKEN_RULES` e bundles associados.

KEEP apenas heurística realmente transversal, de alta precisão, com negative cases, que não ensine endpoint/domain route/catalogToken operacional como segunda authority.

**Gate:** `SEMANTIC_AUTHORITY_SINGLE_OWNER = PASS`.

## J-R10 — contextual recommendations

Fazer:

- user goals + facts + limitations + result refs + allowed actions + already executed como grounding;
- reutilizar síntese LLM do turno quando apropriado;
- fallback LLM-off deve ser genérico/contextual e não profile estático de domínio;
- remover `recommendationQueries` como `LEGACY_FALLBACK` material;
- smoke mede contextualidade, utilidade e grounding, não igualdade com catálogo legado.

**Gate:** `CONTEXTUAL_RECOMMENDATIONS=PASS` e `LEGACY_RECOMMENDATION_FALLBACK=0`.

## J-R11 — Clean Architecture

Fazer:

- mover filesystem/generation/persistence de domain para infrastructure/tooling;
- usar ports pequenos onde cruzar boundary;
- composition root injeta adapters;
- domain não conhece Path/file write de infraestrutura.

**Gate:** `CLEAN_ARCHITECTURE = PASS`.

## J-R12 — novo candidate final

Somente após J-R1…J-R11:

1. registrar novo `FINAL_CANDIDATE_GIT_SHA`;
2. executar unit/contract;
3. positive/sibling/negative;
4. true unknown full chain;
5. true metamorphic rename;
6. compound/multi-turn/required args/security;
7. recommendations contextual;
8. send/stream/simulate/UI;
9. persist/reload/F5;
10. R8 P50/P95 contra thresholds reais;
11. R11 tokens/tool/model-call/cost;
12. residual semantic scan independente;
13. verificar runner↔manifest reproduzível;
14. preencher matriz final requisito→evidência no mesmo candidate.

---

# 6. Definition of Done vigente

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

Se qualquer linha material estiver `PARTIAL`, `WARN` obrigatório, `INCONCLUSIVE`, `LEGACY_FALLBACK`, `FAIL`, stale ou não reproduzível:

```text
FINAL_RESULT = VERIFY_FINAL_FAILED
```

---

# 7. Matriz de fechamento vigente

| Requisito | Estado agora | Próxima prova necessária |
|---|---|---|
| RQ11-01 | PASS pendente reverify | residual + metamorphic final |
| RQ11-02 | PASS/PARTIAL | cleanup content + R3 canônico |
| RQ11-03 | PASS/PARTIAL | F5 + true metamorphic final |
| RQ11-04 | FAIL | J-R6/J-R7/J-R8 |
| RQ11-05 | PARTIAL/FAIL | J-R9 |
| RQ11-06 | FAIL | J-R10 |
| RQ11-07 | PASS | revalidate no final candidate |
| RQ11-08 | PARTIAL/FAIL | J-R11 |
| RQ11-09 | PASS | security hygiene no final candidate |
| RQ11-10 | FAIL | J-R6 |
| RQ11-11 | INCONCLUSIVE | J-R4/J-R5 |
| RQ11-12 | FAIL | J-R1/J-R2/J-R3/J-R12 |
| RQ11-13 | FAIL | cleanup/fallback zero material |
| RQ11-14 | PASS documental | manter docs alinhados a cada etapa |

---

# 8. Saída obrigatória do Cursor por subetapa

```text
STEP:
HEAD_BEFORE:
HEAD_AFTER:
REQUIREMENTS_COVERED:
FILES_CHANGED:
CANONICAL_OWNER:
IMPLEMENTATION_RESULT:
TESTS:
POSITIVE:
SIBLING:
NEGATIVE:
GENERALIZATION:
UNKNOWN_EXTERNAL:
METAMORPHIC:
RESIDUAL_SEARCH:
EVIDENCE_REPRODUCIBILITY:
DRIFTS_FOUND:
POSTCONDITIONS_PROVED:
COMPLETE_GATE:
NEXT_STEP_UNLOCKED:
COMMIT_REALIZADO: sim|nao
PUSH_REALIZADO: sim|nao
```

Não escrever “feito”, “100%”, “concluído” ou “PASS” sem preencher os campos materiais.

---

# 9. Revisão adversarial final

Antes de `FINAL_RESULT=PASS`, responder com evidência independente:

1. Algum mapa JSON foi apenas movido para Python/TS?
2. Existe path→domain semantic authority?
3. Existe endpoint→parameter strategy?
4. Follow-up depende de path/operationId?
5. Registry/operationIds ainda ensina routing de actions conhecidas?
6. Algum resolver usa path/operationId para semantic affinity?
7. Nova API exige editar core/registry/content?
8. Unknown provider executou HTTP real controlado e produziu outcome R9?
9. Provider/path/operationId foram realmente renomeados no metamorphic?
10. Existe mais de um semantic owner concorrente?
11. Há TOKEN_RULES que ensinam catálogo/route/domain em paralelo?
12. Recommendations dependem de lista estática por profile?
13. `LEGACY_FALLBACK` chegou a zero no requisito material?
14. Capability metadata reflete write/admin/destructive?
15. Algum domain service faz filesystem/infrastructure IO indevido?
16. Smoke possui credential default?
17. O R8 compara P50/P95 com o threshold do modo?
18. O corpus exige todas as dimensões mínimas da classe?
19. O manifest pode ser regenerado idêntico pelo runner?
20. Algum gate confia em autodeclaração do próprio artefato auditado?
21. Toda evidence pertence ao novo `FINAL_CANDIDATE_GIT_SHA`?
22. README/roadmap/ledger/changelog descrevem exatamente o estado real?
23. O runtime final ficou mais simples e geral, ou só redistribuiu conhecimento?

Qualquer resposta material sem prova mantém o plano aberto.
