# Portal Comercial — plano de implementação (status)

> Playbook: [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md) § 11.

| Fase | Objetivo | Status |
|------|----------|--------|
| **F0** | Fichas KPI | `concluído` |
| **F1** | Scaffold `commercial-api` | `concluído` |
| **F2** | Portfolios + avatars | `concluído` |
| **F2b** | MFE paridade (scaffold) | `concluído` |
| **F2b harden** | UX real + clients + scope | `concluído` (ago/2026 — port PVA completo) |
| **Cutover dados** | backfill + `COMMERCIAL_PORTFOLIO_SOURCE=commercial` | `pronto` (ops) |
| **F2c** | Depreciar PVA | **pendente** — após homologação Comercial/QA |

## Paridade UX (F2b harden)

Portal Comercial absorveu a UX do PVA:

- Pedidos: KPIs, filtros, tabela ~16 cols, Excel, previsão OP, column picker, fonte, sort/paginação
- Carteira: agregação por pedidos, KPIs, gráfico 12m, tendência, detalhe com abas
- Admin: `SellerPortfoliosPage` via **commercial-api** (carteiras/avatars/enrichment)

Reads TOTVS continuam na api-delpi; estado Delpi na commercial-api.

## Cutover de dados (ops)

```bash
docker exec -it delpi-commercial-api \
  python scripts/backfill_from_pedidos_venda_abertos.py
./commercial-api/scripts/reconcile_portfolio_counts.sh
```

## F2c

Só após [HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md) 100% ✅ — ver [F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md).

## Checklist gates

- [x] F0 KPI-FICHAS
- [x] F1 health + compose
- [x] F2 migrations + dual-read + transfer audit
- [x] F2b harden — paridade UX open-orders/carteira com PVA
- [ ] Homologação Comercial ([HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md))
- [ ] F2c flip menu + redirects
