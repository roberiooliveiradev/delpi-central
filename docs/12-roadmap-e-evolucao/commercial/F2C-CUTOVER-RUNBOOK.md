# F2c — runbook de cutover (Portal do Vendedor → Portal Comercial)

**Pré-requisito:** paridade UX **completa** do Portal Comercial com o PVA (não só checklist mínima) + [HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md) + [ADR-002](./adr/ADR-002-deprecar-pedidos-venda-abertos.md).

**Status (ago/2026):** cutover **revertido**. Redirects removidos do nginx; PVA de volta ao menu. Motivo: commercial open-orders sem KPIs / filtros ricos / tabela 16 cols / Excel / previsão OP / column picker.

---

## Gap que bloqueia o flip

Portar (ou reutilizar) do PVA para `plugins/commercial` open-orders:

1. KPIs: linhas, valor, pode faturar, parcial, atraso  
2. Filtros: cliente, status estoque tipado, datas entrega  
3. Colunas: loja, pedido cliente, entregue, saldo, alocado, previsão OP, status estoque  
4. Modal FIFO de OPs  
5. Excel + column picker + fonte + sort/paginação  

Referência: `plugins/pedidos-venda-abertos/src/pages/PedidosVendaAbertosPage.tsx`, `PedidosTable.tsx`, `FilterBar.tsx`.

---

## 0. Pré-check técnico

- [ ] Paridade UX open-orders fechada
- [ ] `COMMERCIAL_PORTFOLIO_SOURCE=commercial` + backfill/reconcile
- [ ] Portal Comercial no launcher
- [ ] Smoke: open-orders (paridade), customers, detail, seller-portfolios

## 1. Redirects (gateway)

Snippet (ainda **não** inline no nginx): [gateway/snippets/commercial-f2c-redirects.conf](../../../gateway/snippets/commercial-f2c-redirects.conf)

Só copiar para `nginx.conf` / `nginx.dev.conf` no momento do flip real.

```bash
./infra/scripts/up-prod-sequential.sh --build gateway
```

## 2. Ocultar do launcher

Em [pedidos-venda-abertos.manifest.json](../../../plugins/pedidos-venda-abertos/pedidos-venda-abertos.manifest.json): `"showInMenu": false` + re-register.

## 3–4. Comunicação e pós-flip

Ver histórico deste runbook; só após § gap fechado.
