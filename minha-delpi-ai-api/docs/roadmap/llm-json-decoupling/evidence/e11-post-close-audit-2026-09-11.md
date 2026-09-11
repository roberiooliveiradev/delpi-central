# Auditoria pós-fechamento — Onda J

**Data:** 2026-09-11  
**AUDIT_BASE_HEAD:** `30e2d8938e6baf8916fcc62af584d4e826dc2e68`  
**Candidate anteriormente declarado final:** `782a49721319571f0fe4733d59b8a5cc65ac4c04`  
**Resultado da auditoria:** `VERIFY_FINAL_FAILED`  
**Efeito:** Onda J / Plano 11 reabertos; o candidate `782a4972…` permanece histórico e não é release evidence vigente.

## 1. Resumo executivo

A Onda J corrigiu drifts reais e preserváveis, especialmente:

- remoção da antiga authority `_DOMAIN_RULES` path-based;
- schema OpenAPI como caminho principal de argument binding;
- redução da continuidade por path-tail em favor de estado/facets;
- cutover OpenAPI-first ativo em caminhos importantes;
- capability metadata derivada de `method + sensitivity`;
- remoção de defaults versionados de credenciais de smoke.

A auditoria pós-fechamento encontrou, porém, inconsistências materiais entre código, regras canônicas e evidências de release. Por isso, o estado correto não é `PASS`.

```text
CUTOVER_RESULT = PARTIAL_PASS
GENERALIZATION_RESULT = INCONCLUSIVE
CLEANUP_RESULT = FAIL
R1_R11_REQUIRED_DIMENSIONS = FAIL
COMPLETE_GATE = FAIL
VERIFY_FINAL = FAIL
FINAL_RESULT = VERIFY_FINAL_FAILED
```

## 2. Bloqueios confirmados

### A11-01 — R8 aprovado sem aplicar o threshold canônico

`docs/testing/chat-ai-flow-families.md` define para modo Normal alvo total `<= 5 s` e exige P50/P95.

O candidate registrou aproximadamente:

```text
P50 = 41.522 s
P95 = 50.708 s
responseMode = normal
```

Mesmo assim `run_e9_s11_efficiency_live.py` marca `PASS` quando existem trials suficientes, provider não é Ollama, P95 existe e tokens existem. O runner não compara o valor de P50/P95 com o limite de 5 s.

**Classificação:** `EVALUATION_GATE_WEAKENING`  
**Impacto:** R8 = FAIL; `globalReleasePass=true` inválido.

### A11-02 — corpus R1–R11 não respeita a matriz mínima de dimensões

O corpus congelado associa classes críticas a dimensões incompletas ou incorretas. Exemplos:

- required args / enum-type → apenas R5;
- unauthorized / write confirmation / injection → apenas R11;
- compound → apenas R1/R7;
- unknown external OpenAPI → apenas R9/R11.

A matriz canônica exige conjuntos mais amplos por classe, incluindo R2/R3/R4/R8/R9/R10/R11 conforme o risco.

**Classificação:** `REQUIRED_DIMENSION_COVERAGE_DRIFT`  
**Impacto:** `R1_R11_REQUIRED_DIMENSIONS=PASS` não é sustentável.

### A11-03 — manifest offline não é reproduzível pelo runner atual

O runner `run_e11_s9_final_candidate_offline.py` grava `globalReleasePass=false` porque as dimensões live ficam deferred. O manifest versionado registra `globalReleasePass=true` e simultaneamente mantém `reasonGlobalReleasePassFalse` explicando que offline sozinho não fecha release.

**Classificação:** `NON_REPRODUCIBLE_EVIDENCE`  
**Impacto:** evidence chain de E11.S9 inválida até regeneração automática no mesmo candidate.

### A11-04 — unknown external API prova routing/binding, não a cadeia completa

O smoke cria provider nunca visto, importa/binda a action e usa `baseUrl=https://example.invalid`. O próprio harness aceita falha HTTP após seleção/binding.

Isso prova:

```text
OpenAPI import
→ Action Catalog
→ retrieval
→ selection
→ argument binding
```

Não prova:

```text
executor HTTP real
→ resposta
→ presentation
→ outcome R9
```

**Classificação:** `UNKNOWN_PROVIDER_FULL_CHAIN_INCONCLUSIVE`.

### A11-05 — gate live chamado metamorphic mede sinônimo, não rename técnico

O smoke final compara frases equivalentes de estoque e verifica a mesma família `/stock`. Isso mede paraphrase/synonym robustness.

O requisito metamórfico do programa é renomear provider/path/operationId preservando summary/description/tags/schema e provar comportamento equivalente.

**Classificação:** `METAMORPHIC_EVIDENCE_SCOPE_MISMATCH`.

### A11-06 — Architecture Enforcement possui bypass por autodeclaração

A regra `SEMANTIC_TECHNICAL_OPERATION_ID_CATALOG` deixa de inspecionar o registry quando `cleanupMeta.operationIdsRuntimeAuthority=false`.

O próprio artefato auditado não pode ser fonte suficiente para desligar a inspeção da propriedade que está sendo auditada.

**Classificação:** `ARCHITECTURE_GATE_SELF_ATTESTATION_BYPASS`.

### A11-07 — ainda existe afinidade semântica baseada em path/operationId

`OperationalRouteActionResolverService` ainda usa `path`, `operationId`, `pathSuffix`, markers e verificações como `/products/`, `search`, `supplier`, facets contidas no path etc. para filtrar/aceitar candidates em rotas do registry.

**Classificação:** `PATH_BASED_SEMANTIC_AFFINITY_RESIDUAL`  
**Impacto:** `NO_PATH_SEMANTIC_ROUTING` = FAIL.

### A11-08 — registry técnico paralelo permanece material

`operational_route_registry.json` continua contendo rotas manuais com `operationIds`, `method`, `priority`, `termsFrom`, `customPredicate`, domínio e presentation reason. Há consumers runtime de seleção operacional por registry.

**Classificação:** `TECHNICAL_PARALLEL_REGISTRY_RESIDUAL`.

### A11-09 — content ainda contém contrato técnico duplicado

`api_route_domains.json` ainda mantém `method`, `parameterStrategies` e `pathPrefixToDepartmentId`, entre outros dados que pertencem ao OpenAPI/Action Catalog ou à camada de argument binding.

**Classificação:** `ASSISTANT_CONTENT_TECHNICAL_DUPLICATION`.

### A11-10 — ownership semântico ainda está dividido

Permanecem em paralelo:

- `ChatTurnUnderstandingService` heurístico;
- family mappers KPI/product/production;
- `_TOKEN_RULES` extensos;
- `ChatIntentRouter`;
- `ChatTurnAnalysis` LLM;
- `ChatTaskPlannerService` heurístico;
- Action Catalog/retrieval/planner OpenAPI-first.

Vocabulário transversal pode permanecer, mas tabelas que transformam linguagem em `catalogToken`, `kind`, route family ou intenção operacional precisam ser reavaliadas contra o owner semântico alvo.

**Classificação:** `SEMANTIC_AUTHORITY_SINGLE_OWNER_NOT_PROVEN`.

### A11-11 — recommendations continuam com `LEGACY_FALLBACK`

O producer declara explicitamente `recommendationQueries = LEGACY_FALLBACK`; o content mantém listas estáticas por profile e o wiring LLM contextual continua opt-in.

O próprio Plano 11 define que `LEGACY_FALLBACK` material mantém o plano aberto quando faz parte do objetivo original.

**Classificação:** `CONTEXTUAL_RECOMMENDATION_CUTOVER_INCOMPLETE`.

### A11-12 — Clean Architecture ainda possui IO de filesystem em domain

`OperationalRouteRegistryGeneratorService` permanece em `app/domain/services` e executa leitura/escrita de arquivos, geração e persistência de artefatos.

**Classificação:** `CLEAN_ARCHITECTURE_BOUNDARY_RESIDUAL`.

## 3. Estado corrigido por subetapa

| Etapa | Estado pós-auditoria |
|---|---|
| E11.S0 | PASS histórico / baseline válido |
| E11.S1 | **REABERTO — FAIL**: gate possui bypass de autodeclaração |
| E11.S2 | PASS com revalidação final pendente |
| E11.S3 | PASS/PARTIAL: schema authority melhorou; content residual ainda requer cleanup |
| E11.S4 | PASS/PARTIAL: structured continuity melhorou; revalidação metamórfica final pendente |
| E11.S5 | **REABERTO — FAIL**: registry/path affinity material permanece |
| E11.S6 | **REABERTO — PARTIAL/FAIL**: single semantic owner não provado |
| E11.S7 capability | PASS |
| E11.S7 recommendations | **REABERTO — FAIL**: `LEGACY_FALLBACK` |
| E11.S8 security credentials | PASS |
| E11.S8 Clean Architecture | **REABERTO — PARTIAL/FAIL** |
| E11.S9 | **INVALIDADO**: R8 + dimensões + evidence reproducibility + unknown/metamorphic |
| E11.S10 | **INVALIDADO**: COMPLETE_GATE não podia passar |

## 4. Fila corretiva obrigatória

A Onda J continua sendo o plano ativo. Não criar plano paralelo para o mesmo objetivo.

```text
J-R1  corrigir evaluator R8 e aplicar thresholds canônicos por responseMode
J-R2  alinhar corpus/requiredDimensions à matriz canônica automaticamente
J-R3  tornar manifests/evidências reproduzíveis e gerados somente pelos runners
J-R4  provar unknown provider em full chain com executor HTTP controlado + outcome/presentation
J-R5  executar metamorphic rename verdadeiro de provider/path/operationId
J-R6  remover self-attestation bypass do Architecture Enforcement
J-R7  eliminar path/operationId semantic affinity residual
J-R8  reduzir/remover operational_route_registry e content técnico duplicado
J-R9  consolidar semantic ownership e classificar/remover TOKEN_RULES não transversais
J-R10 concluir cutover contextual de recommendations e remover LEGACY_FALLBACK material
J-R11 mover IO/generation de domain para infrastructure/tooling
J-R12 gerar novo candidate final e executar R1–R11 + residual scan + COMPLETE_GATE
```

## 5. Gate para novo fechamento

Um novo `FINAL_RESULT=PASS` só pode ser registrado depois que **todos** os itens abaixo forem verdadeiros no mesmo candidate final:

```text
R8_THRESHOLD_CANONICAL = PASS
REQUIRED_DIMENSIONS_MATRIX = PASS
EVIDENCE_REPRODUCIBLE = PASS
UNKNOWN_EXTERNAL_FULL_CHAIN = PASS
METAMORPHIC_PROVIDER_PATH_OPERATION_ID_RENAME = PASS
ARCHITECTURE_GATE_INDEPENDENT = PASS
NO_PATH_SEMANTIC_AFFINITY = PASS
TECHNICAL_PARALLEL_REGISTRY = 0 ou JUSTIFIED_NON_SEMANTIC com prova independente
ASSISTANT_CONTENT_TECHNICAL_DUPLICATION = 0
SEMANTIC_AUTHORITY_SINGLE_OWNER = PASS
CONTEXTUAL_RECOMMENDATIONS = PASS
LEGACY_RECOMMENDATION_FALLBACK = 0
CLEAN_ARCHITECTURE = PASS
R1_R11_REQUIRED_DIMENSIONS = PASS
RESIDUAL_SCAN = PASS
COMPLETE_GATE = PASS
VERIFY_FINAL = PASS
FINAL_RESULT = PASS
```

Qualquer `PARTIAL`, `LEGACY_FALLBACK`, `INCONCLUSIVE`, evidence stale ou gate enfraquecido mantém:

```text
FINAL_RESULT = VERIFY_FINAL_FAILED
```
