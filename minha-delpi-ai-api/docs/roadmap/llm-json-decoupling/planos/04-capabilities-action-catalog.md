# Plano 04 — Capabilities e mini catálogos -> Action Catalog dinâmico

**Prioridade:** P1  
**Objetivo perceptível:** o chat deve explicar e descobrir o que consegue fazer a partir das actions realmente autorizadas na sessão, sem manter um segundo catálogo manual de endpoints/capabilities.

## CURRENT

Fontes prioritárias:

- `capabilities.json`, especialmente `pathRules` e conteúdo dependente de API conhecida;
- `capability_registry.json`, especialmente `action.*`, `routeHints`, `whenToUse`, `whenNot` e descrição duplicada de actions;
- consumers de self-help, agent capabilities, routing hints e composer.

Problema:

```text
OpenAPI/Action Catalog
+
capabilities/pathRules
+
capability_registry.action.*
=
mais de uma fonte de verdade para a mesma capacidade
```

## TARGET

```text
OpenAPI import
-> Action Catalog normalizado
-> provider/action binding
-> allowed actions da sessão
-> semantic classification/materialization opcional
-> capability view/help/retrieval
```

Capabilities não-OpenAPI, como RAG, web, skills e transforms, continuam em catálogo próprio.

## Requisitos

| ID | Requisito |
|---|---|
| R04-01 | Separar action capabilities de RAG/web/skill/transform capabilities. |
| R04-02 | Eliminar `pathRules` como fonte de classificação por endpoint. |
| R04-03 | Gerar classificação/label útil a partir da metadata real do Action Catalog. |
| R04-04 | Respeitar `allowed_action_ids` e bindings na Ajuda e no composer. |
| R04-05 | Nova API externa deve aparecer sem alteração manual de capability registry. |

## Etapas

### E4.S1 — Inventário de consumers

**Fazer:** localizar todos os reads de `pathRules`, `capability_registry.action.*`, `routeHints`, `descriptionForModel`, `whenToUse`, `whenNot` e aliases de action.

**Pronto quando:** cada read está classificado como retrieval, help, composer, UI, test ou legado.

### E4.S2 — Baseline de capability discovery

**Fazer:** registrar respostas de “o que você pode fazer?”, “quais actions?”, help por tema, agent active vs common chat e provider externo.

**Teste:** R1/R4/R7/R9/R10/R11.

### E4.S3 — Semantic metadata materialization

**Fazer:** avaliar se summary/description/tags/schema já bastam; quando não bastarem, classificar semanticamente no import/index e materializar resultado cacheável com provenance/version/hash.

**Não fazer:** nova taxonomia manual por endpoint obrigatória.

**Teste:** reindex após alteração de schema; unknown provider; cache invalidation.

### E4.S4 — Dynamic capability view

**Fazer:** construir capability list a partir das actions permitidas + capabilities não-OpenAPI; manter copy de seção/help separada da fonte técnica.

**Teste:** mesma action permitida/não permitida entre dois agentes; provider disabled; action disabled.

### E4.S5 — Remove action mini catalog

**Fazer:** retirar `action.*` manual do `capability_registry` quando o Action Catalog cobrir integralmente o uso; preservar RAG/web/skill/transform.

**Teste:** search/audit para routeHints técnicos residuais.

### E4.S6 — `capabilities.pathRules` cutover

**Fazer:** substituir grouping/classification por metadata materializada ou fallback genérico; remover path grouping legado somente após parity.

**Teste:** rename de path/operationId sem alterar semântica e capability grouping esperado.

## Invariantes

- Help nunca anuncia action não autorizada.
- Label amigável não influencia autorização.
- Falha de classificação semântica não torna a action inutilizável; existe fallback pelo OpenAPI.
- RAG/web/skills não são forçados para dentro do Action Catalog se não forem OpenAPI actions.

## Aceite

```text
DYNAMIC_ALLOWED_CAPABILITIES = PASS
UNKNOWN_PROVIDER_HELP = PASS
PATHRULES_NOT_REQUIRED = PASS
NO_DUPLICATE_ACTION_REGISTRY = PASS
AUTHORIZED_ONLY = PASS
```
