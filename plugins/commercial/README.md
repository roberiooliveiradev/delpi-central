# Portal Comercial

Microfrontend federado do domínio comercial — paridade F2b com o Portal do Vendedor (`pedidos-venda-abertos`).

## Rotas UI

| Rota | Descrição |
|------|-----------|
| `/apps/commercial` | Início — atalhos para pedidos, carteira e admin |
| `/apps/commercial/open-orders` | Pedidos de venda em aberto (TOTVS) |
| `/apps/commercial/customers` | Minha carteira de clientes |
| `/apps/commercial/customers/:codigo/:loja` | Detalhe do cliente |
| `/apps/commercial/seller-portfolios` | Administração de carteiras |

## APIs

| Base | Uso |
|------|-----|
| `/apps/commercial-api` | Carteiras, avatars, enrichment (`X-Delpi-Caller-App: commercial`) |
| `/apps/api-delpi/pedidos-venda-abertos/` | Pedidos em aberto (read TOTVS) — **barra final** (evita Mixed Content atrás de HTTPS) |

Clients usam paths **relativos** ao gateway. A `commercial-api` roda com `redirect_slashes=False` (list/create de `seller-portfolios` **sem** barra final).

## RBAC

| Permissão | Escopo |
|-----------|--------|
| `commercial.accounts.view` | Acesso geral (alias cutover: `pedidos-venda-abertos.access`) |
| `commercial.seller-portfolios.manage` | Admin carteiras (alias: `pedidos-venda-abertos.admin`) |

Registrar no Core:

```bash
TOKEN=<jwt> BASE_URL=http://localhost ./plugins/commercial/scripts/register-manifest.sh
```

## Cutover de carteira

Default Compose: `COMMERCIAL_PORTFOLIO_SOURCE=commercial` (após backfill).

```bash
docker exec -it delpi-commercial-api python scripts/backfill_from_pedidos_venda_abertos.py
./commercial-api/scripts/reconcile_portfolio_counts.sh
```

Não há dual-write com o schema legado. **F2c em rollback** até paridade UX open-orders com o PVA — [F2C-CUTOVER-RUNBOOK.md](../../docs/12-roadmap-e-evolucao/commercial/F2C-CUTOVER-RUNBOOK.md).

## Dev

```bash
cd plugins/commercial
npm install
npm run dev
npm run build
```

Smoke federado: `curl -I http://localhost/apps/commercial/assets/remoteEntry.js`

## Estrutura

```
src/
  api/           — httpClient + clients commercial-api / api-delpi
  app/           — rotas, shell, navegação, portfolio scope
  features/      — home, open-orders, customers, seller-portfolios
  shared/        — formatadores
```
