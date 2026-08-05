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
| `/apps/api-delpi/pedidos-venda-abertos` | Pedidos em aberto (read TOTVS) |

## RBAC

| Permissão | Escopo |
|-----------|--------|
| `commercial.accounts.view` | Acesso geral (alias cutover: `pedidos-venda-abertos.access`) |
| `commercial.seller-portfolios.manage` | Admin carteiras (alias: `pedidos-venda-abertos.admin`) |

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
  app/           — rotas, shell, navegação
  features/      — páginas por jornada
  shared/        — formatadores
```
