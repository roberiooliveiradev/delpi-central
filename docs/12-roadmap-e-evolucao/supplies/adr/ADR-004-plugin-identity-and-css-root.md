# ADR-004 — Identidade do plugin e classe CSS root

| Campo | Valor |
|-------|--------|
| Status | Aceito |
| Data | 2026-09-08 |

---

## Contexto

Hipótese inicial do pedido: `plugin id: supplies`, `basePath: /apps/supplies`, API `supplies-api`.

Varredura:

| Superfície | Achado | Classificação |
|------------|--------|----------------|
| Pacote `plugins/supplies` | Inexistente | CONFIRMADO_NO_CODIGO |
| Pacote `supplies-api` | Inexistente | CONFIRMADO_NO_CODIGO |
| Compose `supplies` / `supplies-api` | Inexistente | CONFIRMADO_NO_CODIGO |
| Gateway `/apps/supplies` | Inexistente | CONFIRMADO_NO_CODIGO |
| SI / chat `departmentId: supplies` | Existe (domínio, não app) | CONFIRMADO_NO_CODIGO |
| Fixture Portal `id: "supplies"`, `basePath: "/apps/supplies"`, `supplies.view` | Só teste `portal/src/ui/admin/rbac/rbacAccessTree.test.ts` | CONFIRMADO_NO_CODIGO — **não** é app |
| Classe CSS `.dashboard-supplies` | Root do MFE **legado** `plugins/dashboard-supplies` | CONFIRMADO_NO_CODIGO |

A regra de plugins exige root `dashboard-{nome}`. Usar `.dashboard-supplies` no Portal **durante a coexistência** vazaria CSS entre dois MFEs no mesmo documento do portal.

## Decisão

| Campo | Valor |
|-------|--------|
| Plugin id | `supplies` |
| Nome UI | Portal Suprimentos |
| basePath | `/apps/supplies` |
| API | `supplies-api` / `/apps/supplies-api` |
| CSS root | **`.dashboard-supplies-portal.dashboard-page`** |
| Prefixo BEM local | `sp-` |
| Tokens | `--sp-*` mapeados para `--delpi-ui-*` |
| `portalScopeClassName` | `dashboard-supplies-portal` |

Permission de entrada do produto: `supplies.access` (não `supplies.view` da fixture). A fixture de teste do Portal deverá ser ajustada na fase E3 para não colidir semanticamente — **não** nesta etapa.

## Alternativas rejeitadas

| Alternativa | Motivo |
|-------------|--------|
| id `dashboard-supplies` | Já é o cockpit legado |
| id `supplies-portal` | Desnecessário; Comercial usou `commercial` |
| CSS `.dashboard-supplies` no Portal | Colisão na coexistência |
| Reusar prefixo `cm-` | Família visual sim; tokens/prefixo do Comercial não |

## Consequência

Documentos, Compose futuro, manifest e `index.css` do MFE usam **somente** `.dashboard-supplies-portal` como root. O legado permanece `.dashboard-supplies` até cutover.
