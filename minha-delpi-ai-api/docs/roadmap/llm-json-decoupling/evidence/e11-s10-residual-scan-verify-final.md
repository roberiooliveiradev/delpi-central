# E11.S10 — Residual scan + VERIFY_FINAL — histórico invalidado

**Estado original:** `COMPLETE_GATE + VERIFY_FINAL=PASS`  
**Candidate runtime avaliado:** `782a49721319571f0fe4733d59b8a5cc65ac4c04`  
**Estado vigente:** **INVALIDADO — `VERIFY_FINAL=FAIL` / `FINAL_RESULT=VERIFY_FINAL_FAILED`**  
**Auditoria:** [`e11-post-close-audit-2026-09-11.md`](./e11-post-close-audit-2026-09-11.md)

> Este documento preserva o fechamento anterior para rastreabilidade. A auditoria posterior demonstrou que alguns itens classificados como KEEP/não bloqueantes eram incompatíveis com o próprio COMPLETE_GATE do Plano 11 e que parte das evidências de E11.S9 não sustentava release PASS.

## 1. Correções válidas preservadas

A auditoria não invalida todas as mudanças da Onda J. Permanecem como avanços reais:

- `_DOMAIN_RULES` path-based antiga deixou de ser authority principal;
- schema-first argument binding foi incorporado ao caminho principal;
- continuidade path-tail foi reduzida em favor de estado/facets;
- OpenAPI-first possui cutover ativo em caminhos relevantes;
- capability metadata deriva de `method + sensitivity`;
- defaults versionados de credenciais de smoke foram removidos.

## 2. Por que o residual scan anterior não pode fechar o programa

O fechamento anterior manteve como pós-programa:

- `operationIds` observer arrays;
- `recommendationQueries` como `LEGACY_FALLBACK`;
- `_TOKEN_RULES` de vocabulary/facet/kind;
- filesystem/generator em domain como backlog CA.

A auditoria de código mostrou que parte desses itens não é puramente observacional ou fora de escopo:

### Registry técnico

`operational_route_registry.json` continua contendo rotas manuais com `operationIds`, `method`, `priority`, `termsFrom`, predicates e domínios, com consumers runtime em seleção operacional.

### Path semantic affinity

`OperationalRouteActionResolverService` ainda usa path/operationId e fragments como `/products/`, `search`, `supplier`, facets contidas no path e markers/suffixes para filtrar candidates em determinadas rotas.

### Assistant content técnico

`api_route_domains.json` ainda mantém informações como `method`, `parameterStrategies` e `pathPrefixToDepartmentId`, que precisam ser removidas ou justificadas por owner não técnico e prova independente de que não duplicam OpenAPI/Action Catalog.

### Recommendations

O producer ainda declara `recommendationQueries = LEGACY_FALLBACK`. O próprio Plano 11 define que `LEGACY_FALLBACK` material mantém o plano aberto quando o requisito original exige o cutover contextual.

### Clean Architecture

`OperationalRouteRegistryGeneratorService` permanece em `domain` fazendo IO/generation de filesystem. Isso conflita com o requisito explícito de Clean Architecture do plano.

## 3. Architecture Enforcement anterior não é prova suficiente

O scanner `SEMANTIC_TECHNICAL_OPERATION_ID_CATALOG` pode retornar sem inspecionar o registry quando o próprio JSON declara `cleanupMeta.operationIdsRuntimeAuthority=false`.

Portanto:

```text
SEMANTIC_* full-tree = 0
```

não pode ser usado isoladamente como prova de ausência de authority técnica enquanto o gate aceitar autodeclaração do próprio artefato auditado.

Classificação:

```text
ARCHITECTURE_GATE_INDEPENDENT = FAIL
```

## 4. E11.S9 também foi invalidado

A auditoria encontrou:

```text
R8 = FAIL
REQUIRED_DIMENSIONS_MATRIX = FAIL
EVIDENCE_REPRODUCIBLE = FAIL
UNKNOWN_EXTERNAL_FULL_CHAIN = INCONCLUSIVE
METAMORPHIC_PROVIDER_PATH_OPERATION_ID_RENAME = INCONCLUSIVE
```

Detalhes em [`e11-s9-final-candidate.md`](./e11-s9-final-candidate.md) e na auditoria pós-fechamento.

## 5. Veredito corrigido

```text
CUTOVER_RESULT = PARTIAL_PASS
GENERALIZATION_RESULT = INCONCLUSIVE
CLEANUP_RESULT = FAIL
UNKNOWN_EXTERNAL_API = INCONCLUSIVE_FULL_CHAIN
METAMORPHIC_RENAME = INCONCLUSIVE
ARGUMENT_SCHEMA_AUTHORITY = PASS/PARTIAL
MULTI_TURN_STRUCTURED_STATE = PASS/PARTIAL
SEMANTIC_AUTHORITY_SINGLE_OWNER = PARTIAL/FAIL
CONTEXTUAL_RECOMMENDATIONS = FAIL
CAPABILITY_SECURITY_METADATA = PASS
CLEAN_ARCHITECTURE = PARTIAL/FAIL
SECURITY_HYGIENE = PASS
SEND_STREAM_SIMULATE_UI = PASS_HISTORICAL
PERSIST_RELOAD_F5 = PASS_HISTORICAL
R1_R11_REQUIRED_DIMENSIONS = FAIL
ARCHITECTURE_GATE_INDEPENDENT = FAIL
RESIDUAL_SCAN = FAIL
DOCS_MATCH_FINAL_HEAD = PASS após esta correção documental
COMPLETE_GATE = FAIL
VERIFY_FINAL = FAIL
FINAL_RESULT = VERIFY_FINAL_FAILED
```

## 6. Reabertura obrigatória

A Onda J / Plano 11 volta a ficar ativa. Próximas correções:

```text
J-R1  R8 threshold canônico
J-R2  requiredDimensions canônicas
J-R3  evidence reproduzível
J-R4  unknown external full chain
J-R5  metamorphic rename verdadeiro
J-R6  Architecture Enforcement independente
J-R7  zero path semantic affinity
J-R8  cleanup registry/content técnico
J-R9  semantic single owner
J-R10 recommendations sem LEGACY_FALLBACK material
J-R11 Clean Architecture
J-R12 novo candidate final + residual scan + COMPLETE_GATE
```

## 7. Regra para novo fechamento

Não marcar novamente `COMPLETE_GATE`, `VERIFY_FINAL` ou `FINAL_RESULT` como PASS enquanto existir qualquer requisito material em `FAIL`, `PARTIAL`, `INCONCLUSIVE`, `LEGACY_FALLBACK`, evidence stale/não reproduzível ou gate enfraquecido.

O próximo fechamento deve referenciar um **novo `FINAL_CANDIDATE_GIT_SHA`** e evidências frescas produzidas pelos runners corrigidos.
