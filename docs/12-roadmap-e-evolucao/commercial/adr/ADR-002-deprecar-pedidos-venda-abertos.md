# ADR-002 — Deprecar pedidos-venda-abertos (F2c)

- **Status:** Aceito · **executado** (set/2026) — MFEs `pedidos-venda-abertos` e `propostas-comerciais` removidos; redirects ativos
- **Contexto:** Portal Comercial (`plugins/commercial` + `commercial-api`) com paridade do Portal do Vendedor
- **Runbook:** [F2C-CUTOVER-RUNBOOK.md](../F2C-CUTOVER-RUNBOOK.md)

## Decisão

1. Após checklist [HOMOLOGACAO-PARIDADE-PEDIDOS.md](../HOMOLOGACAO-PARIDADE-PEDIDOS.md) / autorização de cutover:
   - Ocultar / remover apps legados do launcher
   - Redirects HTTP de deep links antigos → rotas do Portal Comercial
   - Comunicar cutover aos usuários
2. Remoção do código/manifest dos MFEs = parte do F2c (este ADR + runbook). Docs históricos permanecem em `docs/12-roadmap-e-evolucao/{pedidos-venda-abertos,propostas-comerciais}/`.
3. Estado Delpi (carteira/avatar) permanece em `commercial-api` com `COMMERCIAL_PORTFOLIO_SOURCE=commercial`.
4. Reads TOTVS (`list_pedidos_venda_abertos`, ops, billing, NF, ADY) permanecem na **api-delpi** como SQL/parametrização — consumidos via BFF commercial-api.
5. **Escopo de carteira do Portal:** somente **commercial-api** (`ResolveCommercialCustomerScopeService`). Ver [SCOPE-OWNERSHIP.md](../SCOPE-OWNERSHIP.md).
6. Regra de membership na api-delpi orientada ao plugin PVA **não** evolui mais — plugin removido.

## Consequências

- Favoritos `/apps/pedidos-venda-abertos/*` e `/apps/propostas-comerciais/*` redirecionam ([F2C-CUTOVER-RUNBOOK.md](../F2C-CUTOVER-RUNBOOK.md)).
- Permissões: gates comerciais usam **somente** `commercial.*` (aliases PVA podem permanecer até limpeza de perfis). Ver [PERFIS-E-PERMISSOES.md](../PERFIS-E-PERMISSOES.md).
- Ops residual: unregister apps no Core + smoke 302 em prod (mesmo runbook).
- Não dual-write entre schemas.

## Não fazer neste ADR

- Migrar SQL TOTVS para commercial-api
- Apagar volume de avatares nem rotas api-delpi TOTVS
- Runtime `type: module` (F3–F4)
- Remover `dashboard-commercial` (decisão separada / Gestão nativa)
