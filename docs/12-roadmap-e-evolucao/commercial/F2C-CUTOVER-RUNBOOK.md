# F2c — runbook de cutover (Portal do Vendedor → Portal Comercial)

**Pré-requisito:** [HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md) + [ADR-002](./adr/ADR-002-deprecar-pedidos-venda-abertos.md).

**Status (ago/2026):** flip de código aplicado (nginx + manifest). Dev validado. Prod: rebuild gateway + re-register com `TOKEN`.

---

## 0. Pré-check técnico

- [x] `COMMERCIAL_PORTFOLIO_SOURCE=commercial`
- [x] Backfill + [reconcile_portfolio_counts.sh](../../../commercial-api/scripts/reconcile_portfolio_counts.sh) OK (dev)
- [x] Portal Comercial no launcher (`TOKEN=… ./plugins/commercial/scripts/register-manifest.sh`)
- [x] Smoke: open-orders, customers, detail, seller-portfolios paths / remoteEntry / health

## 1. Redirects (gateway)

Snippet fonte: [gateway/snippets/commercial-f2c-redirects.conf](../../../gateway/snippets/commercial-f2c-redirects.conf)

**Aplicado inline** (compose não monta `snippets/`) em:

- [gateway/nginx.conf](../../../gateway/nginx.conf)
- [gateway/nginx.dev.conf](../../../gateway/nginx.dev.conf)

Rebuild/reload gateway:

```bash
# Dev
./infra/scripts/up-dev-sequential.sh --build gateway

# Prod
./infra/scripts/up-prod-sequential.sh --build gateway
```

| De | Para |
|----|------|
| `/apps/pedidos-venda-abertos` | `/apps/commercial/open-orders` |
| `/apps/pedidos-venda-abertos/` | `/apps/commercial/open-orders` |
| `/apps/pedidos-venda-abertos/clientes` | `/apps/commercial/customers` |
| `/apps/pedidos-venda-abertos/clientes/:c/:l` | `/apps/commercial/customers/:c/:l` |
| `/apps/pedidos-venda-abertos/configuracao` | `/apps/commercial/seller-portfolios` |

**Assets** `/apps/pedidos-venda-abertos/assets/*` permanecem (imagem antiga) até remoção do serviço.

Smoke redirects (esperado 302):

```bash
curl -sI http://localhost/apps/pedidos-venda-abertos | grep -i Location
curl -sI http://localhost/apps/pedidos-venda-abertos/clientes/001234/01 | grep -i Location
```

## 2. Ocultar do launcher

Em [pedidos-venda-abertos.manifest.json](../../../plugins/pedidos-venda-abertos/pedidos-venda-abertos.manifest.json):

- Todas as rotas: `"showInMenu": false`
- `name` / `description` / label raiz prefixados com «(legado)»

Re-registrar (obrigatório em **cada** ambiente após pull):

```bash
# Dev
TOKEN=… BASE_URL=http://localhost \
  ./plugins/pedidos-venda-abertos/scripts/register-manifest.sh

# Prod
TOKEN=… BASE_URL=https://minhadelpi.com.br \
  ./plugins/pedidos-venda-abertos/scripts/register-manifest.sh
```

## 3. Comunicação

- Entrada canônica = **Portal Comercial** (`/apps/commercial`)
- Deep links antigos redirecionam automaticamente (302)
- Aliases RBAC `pedidos-venda-abertos.*` permanecem até migração completa para `commercial.*`

## 4. Pós-flip

- [x] Favoritos e bookmarks (redirects 302 validados em dev)
- [x] RBAC: aliases legados documentados; preferir `commercial.*`
- [ ] Monitorar 404 / Mixed Content em **prod** após deploy
- Remoção de código PVA: ADR futuro

## Mapa de rotas (referência)

| Capacidade | Comercial |
|------------|-----------|
| Pedidos | `/apps/commercial/open-orders` |
| Carteira | `/apps/commercial/customers` |
| Detalhe | `/apps/commercial/customers/:codigo/:loja` |
| Admin | `/apps/commercial/seller-portfolios` |
