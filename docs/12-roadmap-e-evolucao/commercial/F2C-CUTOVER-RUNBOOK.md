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
- [ ] Smoke: open-orders, customers, detail, seller-portfolios

## 1. Redirects (gateway)

Snippet: [gateway/snippets/commercial-f2c-redirects.conf](../../../gateway/snippets/commercial-f2c-redirects.conf) — copiar para `nginx.conf` / `nginx.dev.conf` **somente no flip**.

```bash
./infra/scripts/up-prod-sequential.sh --build gateway
```

## 2. Ocultar do launcher

`showInMenu: false` em [pedidos-venda-abertos.manifest.json](../../../plugins/pedidos-venda-abertos/pedidos-venda-abertos.manifest.json) + re-register.

## 3–4. Comunicação e pós-flip

Entrada canônica = Portal Comercial; deep links antigos redirecionam; aliases RBAC legados permanecem.
