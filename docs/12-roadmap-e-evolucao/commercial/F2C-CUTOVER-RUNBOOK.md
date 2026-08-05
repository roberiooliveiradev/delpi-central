# F2c — runbook de cutover (Portal do Vendedor → Portal Comercial)

**Pré-requisito:** [HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md) 100% ✅ + [ADR-002](./adr/ADR-002-deprecar-pedidos-venda-abertos.md).

**Não execute o flip de menu antes da assinatura Comercial.**

---

## 0. Pré-check técnico

- [ ] `COMMERCIAL_PORTFOLIO_SOURCE=commercial`
- [ ] Backfill + [reconcile_portfolio_counts.sh](../../../commercial-api/scripts/reconcile_portfolio_counts.sh) OK
- [ ] Portal Comercial no launcher (`TOKEN=… ./plugins/commercial/scripts/register-manifest.sh`)
- [ ] Smoke: open-orders, customers, detail, seller-portfolios, avatar, transfer

## 1. Redirects (gateway)

Snippet pronto: [gateway/snippets/commercial-f2c-redirects.conf](../../../gateway/snippets/commercial-f2c-redirects.conf)

Incluir no `nginx.conf` / `nginx.dev.conf` **no momento do flip** (antes do location genérico de assets):

```nginx
include /etc/nginx/snippets/commercial-f2c-redirects.conf;
```

Ou copiar o conteúdo do snippet. Rebuild/reload gateway:

```bash
./infra/scripts/up-prod-sequential.sh --build gateway
# ou: docker exec delpi-gateway nginx -s reload  (se volume montado)
```

| De | Para |
|----|------|
| `/apps/pedidos-venda-abertos` | `/apps/commercial/open-orders` |
| `/apps/pedidos-venda-abertos/` | `/apps/commercial/open-orders` |
| `/apps/pedidos-venda-abertos/clientes` | `/apps/commercial/customers` |
| `/apps/pedidos-venda-abertos/clientes/:c/:l` | `/apps/commercial/customers/:c/:l` |
| `/apps/pedidos-venda-abertos/configuracao` | `/apps/commercial/seller-portfolios` |

**Assets** `/apps/pedidos-venda-abertos/assets/*` podem permanecer (imagem antiga) até remoção do serviço.

## 2. Ocultar do launcher

Em [pedidos-venda-abertos.manifest.json](../../../plugins/pedidos-venda-abertos/pedidos-venda-abertos.manifest.json):

- Todas as rotas: `"showInMenu": false`
- Opcional: prefixar `name` / `description` com «(legado)»

Re-registrar:

```bash
TOKEN=… BASE_URL=https://minhadelpi.com.br \
  ./plugins/pedidos-venda-abertos/scripts/register-manifest.sh
```

## 3. Comunicação

- Aviso no portal / e-mail: entrada canônica = **Portal Comercial**
- Deep links antigos redirecionam automaticamente

## 4. Pós-flip

- [ ] Favoritos e bookmarks testados
- [ ] RBAC: preferir `commercial.accounts.view` / `commercial.seller-portfolios.manage`
- [ ] Monitorar 404 / Mixed Content
- Remoção de código PVA: ADR futuro

## Mapa de rotas (referência)

| Capacidade | Comercial |
|------------|-----------|
| Pedidos | `/apps/commercial/open-orders` |
| Carteira | `/apps/commercial/customers` |
| Detalhe | `/apps/commercial/customers/:codigo/:loja` |
| Admin | `/apps/commercial/seller-portfolios` |
