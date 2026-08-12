# F2c — runbook de cutover (Portal do Vendedor → Portal Comercial)

**Pré-requisito:** [HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md) 100% ✅ + [ADR-002](./adr/ADR-002-deprecar-pedidos-venda-abertos.md).

**Status (ago/2026):** paridade UX portada para `plugins/commercial`. PVA permanece no menu até assinatura Comercial/QA. Snippet de redirects **não** está ativo no nginx.

---

## Gap de UX (fechado em engenharia)

- [x] KPIs (pode faturar, parcial, atraso)
- [x] Filtros (cliente, status estoque, datas)
- [x] Tabela ~16 colunas + previsão OP FIFO + badges
- [x] Excel + column picker + fonte + sort/paginação
- [x] Carteira agregada + detalhe com abas
- [x] Admin carteiras via commercial-api

## 0. Pré-check técnico

- [ ] Homologação Comercial/QA assinada
- [ ] `COMMERCIAL_PORTFOLIO_SOURCE=commercial` + backfill/reconcile
- [ ] Migration `V005__seller_portfolio_members` aplicada (`up` só — nunca `reset`)
- [ ] Smoke: open-orders, customers, detail, seller-portfolios
- [ ] Smoke multi-membro: usuário em 2 carteiras; `/me.portfolios[]`; filtro «Todas»; member secundário vê clientes

### Multi-membro (obrigatório)

Membership N:N vive **somente** em `commercial.seller_portfolio_members`. O schema legado `pedidos_venda_abertos.sellers.user_id UNIQUE` **não** comporta o mesmo usuário em várias carteiras nem vários membros por carteira.

Antes de promover multi-membro em produção:

1. `COMMERCIAL_PORTFOLIO_SOURCE=commercial` em api-delpi e commercial-api
2. Writes de carteira **só** via commercial-api (sem dual-write N:N para PVA)
3. Confirmar V005 + backfill de owners
4. PVA no launcher: se ainda ativo, escopo 1:1 pode divergir — preferir commercial-only no flip

## 1. Redirects (gateway)

Snippet: [gateway/snippets/commercial-f2c-redirects.conf](../../../gateway/snippets/commercial-f2c-redirects.conf) — copiar para `nginx.conf` / `nginx.dev.conf` **somente no flip**.

```bash
./infra/scripts/up-prod-sequential.sh --build gateway
```

## 2. Ocultar do launcher

`showInMenu: false` em [pedidos-venda-abertos.manifest.json](../../../plugins/pedidos-venda-abertos/pedidos-venda-abertos.manifest.json) + re-register.

## 3–4. Comunicação e pós-flip

Entrada canônica = Portal Comercial; deep links antigos redirecionam; aliases RBAC legados permanecem.
