# ADR-008 — Access / Manage do Portal Suprimentos

| Campo | Valor |
|-------|-------|
| Status | Parcialmente vigente — catálogo access/manage permanece; unidade e view-all do Portal foram superseded por [ADR-009](./ADR-009-product-access-and-operational-data-scope.md) |
| Contexto | Catálogo funcional fragmentado de ADR-007 não é o target de uso do produto |
| Relacionados | ADR-006, ADR-007, PERFIS-E-PERMISSOES.md |

## Decisão

A Core API permanece a única authority de apps, manifests, routes, permissions, roles, groups, grants, overrides e effective permissions.

Uso normal do Portal Suprimentos é `supplies.access`. Administração do produto é `supplies.manage`. `manage` não implica `access`. Quem administra e usa o produto recebe os dois grants.

Unidade como `supplies.unit.*` e `supplies.purchase-requests.view-all` **não** fazem parte do contrato vigente. Esses eixos foram superseded por ADR-009: unidade é filtro de dados `01`/`02`, e a SC do Portal é acompanhamento global comprovado por S2S da supplies-api.

Códigos fragmentados foram removidos do catálogo ativo depois da migração dos grants no Core local. Não há alias. ADR-007 permanece o registro histórico.

Estratégia: EXPAND → MIGRATE → VERIFY → CONTRACT. Remoção dos códigos antigos só com zero consumer e zero grant residual. E9 usa `supplies.access` AND unit scope AND regra de negócio. Não cria permission de entregas.

ADR-007 permanece o registro histórico da minimização de 2026-09-08. Esta decisão o supersede no catálogo funcional.
