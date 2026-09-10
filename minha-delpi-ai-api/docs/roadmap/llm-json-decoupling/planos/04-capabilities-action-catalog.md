# Plano 04 — Capabilities e mini catálogos -> Action Catalog dinâmico

**Prioridade:** P1  
**Status execução:** Onda E · plano 04 **ATENDIDO** (S1–S5; S6 pathRules já DONE) · próxima = plano 05 E5.S1  
**Evidência:** [`../evidence/e4-s1-capability-inventory.md`](../evidence/e4-s1-capability-inventory.md) · [`../evidence/e4-s2-capability-discovery-baseline.md`](../evidence/e4-s2-capability-discovery-baseline.md) · [`../evidence/e4-s3-ux-capability-contract.md`](../evidence/e4-s3-ux-capability-contract.md) · [`../evidence/e4-s4-dynamic-capability-view.md`](../evidence/e4-s4-dynamic-capability-view.md) · [`../evidence/e4-s5-remove-action-mini-catalog.md`](../evidence/e4-s5-remove-action-mini-catalog.md) · [`../evidence/execution-ledger.md`](../evidence/execution-ledger.md)  
**Objetivo perceptível:** o chat deve explicar e descobrir o que consegue fazer a partir das actions realmente autorizadas na sessão, sem manter um segundo catálogo manual de endpoints/capabilities.

**HEAD revalidado:** pós-`78a25befe` (D1 path→display / capabilities UX)

## EXECUTION_DRIFT (2026-09-10)

| Item | Estado no código | Impacto neste plano |
|------|------------------|---------------------|
| `capabilities.pathRules` | **REMOVIDO** | R04-02 e E4.S6 = **ATENDIDO** |
| Classificação UX de actions | `capability_ux_classification.json` + `CapabilityUxClassifierService` no import → `delpi_metadata.uxCapability` | Materialização parcial; não reintroduzir pathRules |
| Agrupamento «o que você pode fazer?» | `ChatCapabilitiesCatalogAnswerService.resolve_ux_capability` | Lê metadata/classificador, não token-in-path |
| Composer chips (legado `includePathRulesFromCapabilities`) | Lê `keywordRules` do bundle UX | Nome de flag legado; fonte já não é pathRules |

**Não refazer** cutover de pathRules. Trabalho restante = mini-catálogo `capability_registry.action.*` e help dinâmico.

## CURRENT (restante)

Fontes prioritárias ainda abertas:

- `capability_registry.json`, especialmente `action.*`, `routeHints` (morto no Python), `whenToUse`, `whenNot`, `descriptionForModel`;
- consumers de discovery (`ChatCapabilityDiscoveryService` / task planner / turn preparation);
- copy/help em `capabilities.json` que ainda cita exemplos de path como documentação (UX, não authority de routing).

Já resolvido (não é CURRENT de dívida):

- `capabilities.pathRules` / `pathRuleDefault` path-based;
- ponteiro `capabilityUxClassificationBundle`.

Problema residual:

```text
OpenAPI/Action Catalog
+
capability_registry.action.*
=
ainda duas fontes para “o que o agente consegue via tools”
```

## TARGET

```text
OpenAPI import
-> Action Catalog normalizado (+ uxCapability materializado)
-> provider/action binding
-> allowed actions da sessão
-> capability view/help/retrieval
```

Capabilities não-OpenAPI (RAG, web, skills, transforms) continuam em catálogo próprio.

## Requisitos

| ID | Requisito | Estado |
|---|---|---|
| R04-01 | Separar action capabilities de RAG/web/skill/transform | **ATENDIDO** (E4.S5) |
| R04-02 | Eliminar `pathRules` como fonte de classificação por endpoint | **ATENDIDO** |
| R04-03 | Gerar classificação/label útil a partir da metadata real do Action Catalog | **ATENDIDO** (`uxCapability` contrato E4.S3) |
| R04-04 | Respeitar `allowed_action_ids` e bindings na Ajuda e no composer | **ATENDIDO** |
| R04-05 | Nova API externa sem alteração manual de capability registry | **ATENDIDO** (actions via catalog) |

## Etapas

### E4.S1 — Inventário de consumers (revalidar pós-D1) — **ATENDIDO**

**Fazer:** localizar reads de `capability_registry.action.*`, `routeHints`, `descriptionForModel`, `whenToUse`, `whenNot`; confirmar **zero** consumers de `capabilities.pathRules`.

**Feito:** [`../evidence/e4-s1-capability-inventory.md`](../evidence/e4-s1-capability-inventory.md).

**Pronto quando:** matriz atualizada; pathRules = DELETE confirmado. ✅

### E4.S2 — Baseline de capability discovery — **ATENDIDO**

**Fazer:** registrar “o que você pode fazer?”, help por tema, agent vs common chat, provider externo (já há smoke live pós-D1 — reusar como baseline).

**Feito:** harness discovery + allowed_ids help; [`../evidence/e4-s2-capability-discovery-baseline.md`](../evidence/e4-s2-capability-discovery-baseline.md).

**Teste:** R1/R4/R7/R9/R10/R11. ✅ (freeze unitário das famílias)

### E4.S3 — Semantic metadata materialization — **ATENDIDO**

**Fazer:** consolidar `uxCapability` como contrato canônico; avaliar lacunas summary/tags/entity/shape; **não** criar `x-delpi.capabilityGroup` manual por operation.

**Feito:** contrato + testes path-exclusion/rename; evidência [`../evidence/e4-s3-ux-capability-contract.md`](../evidence/e4-s3-ux-capability-contract.md).

**Teste:** reindex/import; unknown; metamorphic rename; fallback «Outras consultas». ✅

### E4.S4 — Dynamic capability view — **ATENDIDO**

**Feito:** help já Action Catalog + allowed; evidência [`../evidence/e4-s4-dynamic-capability-view.md`](../evidence/e4-s4-dynamic-capability-view.md).

### E4.S5 — Remove action mini catalog — **ATENDIDO**

**Feito:** removidos `action.*`/`routeHints`; discovery sintetiza do Action Catalog; evidência [`../evidence/e4-s5-remove-action-mini-catalog.md`](../evidence/e4-s5-remove-action-mini-catalog.md).

**Teste:** search/audit residual + baselines atualizados. ✅

### E4.S6 — `capabilities.pathRules` cutover

**Status:** **SKIP / ATENDIDO** (D1). Evidência: `residual_path_display_e5_hcap04_decision.json`, `residual_path_display_e10_verify_final.json`, live capabilities.

## Invariantes

- Help nunca anuncia action não autorizada.
- Label amigável não influencia autorização.
- Falha de classificação semântica não torna a action inutilizável; existe fallback pelo OpenAPI/`Outras consultas`.
- RAG/web/skills não são forçados para dentro do Action Catalog se não forem OpenAPI actions.
- Não reintroduzir `pathRules` nem `capabilityGroup` por endpoint.

## Aceite

```text
DYNAMIC_ALLOWED_CAPABILITIES = PASS   # restante E4.S4–S5
UNKNOWN_PROVIDER_HELP = PASS
PATHRULES_NOT_REQUIRED = PASS         # ATENDIDO
NO_DUPLICATE_ACTION_REGISTRY = PASS   # após E4.S5
AUTHORIZED_ONLY = PASS
```
