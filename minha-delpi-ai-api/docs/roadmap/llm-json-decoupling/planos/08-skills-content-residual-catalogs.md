# Plano 08 — Skills/help/content -> remover catálogos técnicos residuais

**Prioridade:** P2  
**Status execução:** Onda G · Plano 08 **ATENDIDO** (E8.S1–S6) · próxima plano 09 / Onda H  
**Evidência:** [`../evidence/e8-s1-skills-help-residual-inventory.md`](../evidence/e8-s1-skills-help-residual-inventory.md) · [`../evidence/e8-s2-skill-catalog-cleanup.md`](../evidence/e8-s2-skill-catalog-cleanup.md) · [`../evidence/e8-s3-help-capabilities-cleanup.md`](../evidence/e8-s3-help-capabilities-cleanup.md) · [`../evidence/e8-s4-ear-mixed-bundle-copy-split.md`](../evidence/e8-s4-ear-mixed-bundle-copy-split.md) · [`../evidence/e8-s5-content-audit-gate.md`](../evidence/e8-s5-content-audit-gate.md) · [`../evidence/e8-s6-document-cleanup.md`](../evidence/e8-s6-document-cleanup.md) · [`../evidence/execution-ledger.md`](../evidence/execution-ledger.md)  
**Objetivo perceptível:** conteúdo editorial continua rico e configurável, mas deixa de anunciar ou depender de endpoints hardcoded quando a disponibilidade real pode ser consultada no runtime.

## CURRENT

Fontes prioritárias:

- `app/content/pt-BR/skills/catalog.json`;
- `capabilities.json` e `features_catalog.json` quando houver paths/params/actions específicos;
- `external_action_responses.json` quando misturar copy com route-specific execution policy;
- demais bundles com `executionPathHint`, `routeHints`, path examples, operation names ou duplicação técnica.

Exemplo de dívida:

```text
skill editorial
-> executionPathHint = GET/POST /rota-especifica
```

A skill sabe o que faz, mas não deveria ser fonte de qual endpoint está habilitado.

## TARGET

```text
skill/help editorial
-> descreve capacidade, policy e exemplos humanos

runtime capability resolver
-> consulta skills enabled + allowed actions + features reais

resposta de ajuda
-> combina conteúdo editorial + disponibilidade real
```

## Requisitos

| ID | Requisito |
|---|---|
| R08-01 | Encontrar hints técnicos duplicados fora do Action Catalog/OpenAPI. |
| R08-02 | Preservar labels, descriptions, examples, policy files e aliases editoriais úteis. |
| R08-03 | Help deve derivar disponibilidade da sessão, não do texto estático. |
| R08-04 | Não remover exemplos técnicos quando forem documentação explícita e não autoridade de runtime. |
| R08-05 | Separar copy de execution/network policy em bundles mistos. |

## Etapas

### E8.S1 — Auditoria de conteúdo

**Status:** **ATENDIDO** (2026-09-10) — evidência [`../evidence/e8-s1-skills-help-residual-inventory.md`](../evidence/e8-s1-skills-help-residual-inventory.md)

**Feito:** freeze de contagens (3 hints path-like; 12 features com requiredActions path; routeHints=0); classificação PATH_COUPLED/UX_COPY/DEAD; sem mutação de conteúdo.

**Fazer (histórico):** search por `GET /`, `POST /`, …, `executionPathHint`, `routeHints` dentro de `app/content`.

### E8.S2 — Skill catalog cleanup

**Status:** **ATENDIDO** (2026-09-10) — evidência [`../evidence/e8-s2-skill-catalog-cleanup.md`](../evidence/e8-s2-skill-catalog-cleanup.md)

**Feito:** hints path-like → capability keys (`sql_execution`, `product_analyser`, `quality_action_plans`, `document_vision`); policy/derived preservados; enablement continua por actions.

**Não fazer:** esconder do usuário limitações reais da skill — **respeitado**.

### E8.S3 — Help/capabilities cleanup

**Status:** **ATENDIDO** (2026-09-10) — evidência [`../evidence/e8-s3-help-capabilities-cleanup.md`](../evidence/e8-s3-help-capabilities-cleanup.md)

**Feito:** `_matches_actions` actionId-first + path fallback; piloto `get_product_stock` em `stock_lookup`; E4 catalog answer intocado.

### E8.S4 — Mixed bundles cleanup

**Status:** **ATENDIDO** (2026-09-10) — evidência [`../evidence/e8-s4-ear-mixed-bundle-copy-split.md`](../evidence/e8-s4-ear-mixed-bundle-copy-split.md)

**Feito:** `actionSelectionCopy` (routeClarification, refinementFallbackMessages, emptyRivalSuggestions); matchers/policy PATH ficam em `actionSelection`; `httpExecution` intocado.

### E8.S5 — Audit gate

**Status:** **ATENDIDO** (2026-09-10) — evidência [`../evidence/e8-s5-content-audit-gate.md`](../evidence/e8-s5-content-audit-gate.md)

**Feito:** `scripts/audit_assistant_technical_duplication.py` + testes positive/negative/sibling.

### E8.S6 — Cleanup documental

**Status:** **ATENDIDO** (2026-09-10) — evidência [`../evidence/e8-s6-document-cleanup.md`](../evidence/e8-s6-document-cleanup.md)

**Feito:** README de content + status do programa alinhados à ownership pós-S2–S5.

## Invariantes

- Ajuda e onboarding continuam rápidos e previsvisíveis.
- Skill policy não depende do LLM para existir.
- Endpoint em exemplo documental não vira automaticamente dívida; o problema é servir como fonte runtime duplicada.
- Availability sempre respeita agente/binding/RBAC/policy.

## Aceite

```text
SKILL_RUNTIME_ENDPOINT_HINT_DEPENDENCY = ZERO
HELP_REFLECTS_ALLOWED_CAPABILITIES = PASS
CONTENT_AUDIT = PASS
UX_COPY_PRESERVED = PASS
POLICY_OWNERSHIP = PASS
```
