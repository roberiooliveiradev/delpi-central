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
| Fixture Portal `id: "supplies"`, `basePath: "/apps/supplies"`, `supplies.view` | Só teste `portal/src/ui/admin/rbac/rbacAccessTree.test.ts` | CONFIRMADO_NO_CODIGO — não é app |
| Classe CSS `.dashboard-supplies` | Root do MFE legado `plugins/dashboard-supplies` | CONFIRMADO_NO_CODIGO |

A regra de plugins exige root isolado. Usar `.dashboard-supplies` durante coexistência vazaria CSS entre dois MFEs no mesmo documento do portal.

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
| Permission de entrada | **`supplies.portal.access`** |

A fixture `supplies.view` não é contrato do produto e deverá ser ajustada na fase de implementação.

O catálogo de permission segue [ADR-007](./ADR-007-permission-minimization.md): permissions novas representam capacidades materiais, não CRUD técnico.

## Alternativas rejeitadas

| Alternativa | Motivo |
|-------------|--------|
| id `dashboard-supplies` | Já é o cockpit legado |
| id `supplies-portal` | Desnecessário; domínio técnico `supplies` já está livre |
| CSS `.dashboard-supplies` | Colisão com legado |
| Reusar prefixo `cm-` | Família visual sim; tokens/prefixo do Comercial não |
| `supplies.access` | Contrato de dois segmentos; para novo plugin preferir `module.resource.action` |

## Consequência

Documentos, futuro manifest, Compose e `index.css` usam `supplies`, `/apps/supplies`, `supplies-api`, `.dashboard-supplies-portal` e `supplies.portal.access`. O legado permanece inalterado até cutover.
