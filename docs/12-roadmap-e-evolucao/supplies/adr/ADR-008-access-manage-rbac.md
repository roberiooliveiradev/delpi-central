# ADR-008 — Access / Manage do Portal Suprimentos

| Campo | Valor |
|-------|-------|
| Status | Contrato ativo (Core local 0.3.0 após registro final) |
| Contexto | Catálogo funcional fragmentado de ADR-007 não é o target de uso do produto |
| Relacionados | ADR-006, ADR-007, PERFIS-E-PERMISSOES.md |

## Decisão

A Core API permanece a única authority de apps, manifests, routes, permissions, roles, groups, grants, overrides e effective permissions.

Uso normal do Portal Suprimentos é `supplies.access`. Administração do produto é `supplies.manage`. `manage` não implica `access`, todas as unidades, `view-all` nem superadmin. Quem administra e usa o produto recebe os dois grants.

Eixos preservados (ADR-006 e ADR-007, não reescritos):

- `supplies.unit.filial-{TOTVS}` — sem unidade, dado unit-scoped é negado. `manage` não concede all units.
- `supplies.purchase-requests.view-all` — bypass de centro de custo somente dentro das unidades autorizadas.

`supplies.purchase-requests.export` permanece no catálogo até o inventário runtime do Core provar ausência de segregação material. Target arquitetural, se essa prova existir: exportação normal coberta por `supplies.access`.

Códigos fragmentados foram removidos do catálogo ativo depois da migração dos grants no Core local. Não há alias. ADR-007 permanece o registro histórico.

Estratégia: EXPAND → MIGRATE → VERIFY → CONTRACT. Remoção dos códigos antigos só com zero consumer e zero grant residual. E9 usa `supplies.access` AND unit scope AND regra de negócio. Não cria permission de entregas.

ADR-007 permanece o registro histórico da minimização de 2026-09-08. Esta decisão o supersede no catálogo funcional.
