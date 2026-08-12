# ADR-002 — Deprecar pedidos-venda-abertos (F2c)

- **Status:** Aceito — execução do flip **somente** após paridade UX completa (rollback ago/2026)
- **Contexto:** Portal Comercial (`plugins/commercial` + `commercial-api`) entrega paridade do Portal do Vendedor

## Decisão

1. Após checklist [HOMOLOGACAO-PARIDADE-PEDIDOS.md](../HOMOLOGACAO-PARIDADE-PEDIDOS.md) / autorização de cutover:
   - Ocultar `pedidos-venda-abertos` do launcher (`showInMenu: false`)
   - Redirects HTTP de deep links antigos → rotas do Portal Comercial
   - Comunicar cutover aos usuários
2. Remoção definitiva do código/manifest PVA = ADR posterior (depreciação ≠ delete).
3. Estado Delpi (carteira/avatar) permanece em `commercial-api` com `COMMERCIAL_PORTFOLIO_SOURCE=commercial`.
4. Reads TOTVS (`list_pedidos_venda_abertos`, ops, billing, NF) permanecem na **api-delpi**.

## Consequências

- Favoritos `/apps/pedidos-venda-abertos/*` precisam de redirect (ver [F2C-CUTOVER-RUNBOOK.md](../F2C-CUTOVER-RUNBOOK.md)).
- Permissões: gates comerciais usam **somente** `commercial.*` (aliases PVA/`api-delpi.access` removidos dos OR-lists — re-grant obrigatório). Ver [PERFIS-E-PERMISSOES.md](../PERFIS-E-PERMISSOES.md).
- Não dual-write entre schemas.

## Não fazer neste ADR

- Apagar o plugin PVA
- Migrar SQL TOTVS para commercial-api
- Runtime `type: module` (F3–F4)
