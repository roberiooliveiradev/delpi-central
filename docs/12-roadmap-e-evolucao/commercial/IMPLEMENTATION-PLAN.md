# Portal Comercial — plano de implementação (status)

> Playbook: [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md) § 11.

| Fase | Objetivo | Status |
|------|----------|--------|
| **F0** | Fichas KPI | `concluído` |
| **F1** | Scaffold `commercial-api` | `concluído` |
| **F2** | Portfolios + avatars | `concluído` |
| **F2b** | MFE paridade (scaffold) | `concluído` |
| **F2b harden** | UX real + clients + scope | `parcial` — open-orders ainda **subset** do PVA |
| **Cutover dados** | backfill + `COMMERCIAL_PORTFOLIO_SOURCE=commercial` | `pronto` (ops) |
| **F2c** | Depreciar PVA | **rollback** (ago/2026) — reativar só após paridade UX |

## Gap de paridade (bloqueia F2c)

O Portal Comercial **não** substitui ainda a UX operacional do PVA em pedidos:

- KPIs (pode faturar, parcial, atraso)
- Filtros (cliente, status estoque, datas)
- Tabela ~16 colunas + previsão OP FIFO + badges
- Excel, column picker, fonte, sort/paginação

Enquanto isso, **Portal do Vendedor permanece no launcher** e sem redirects.

## Cutover de dados (ops)

```bash
docker exec -it delpi-commercial-api \
  python scripts/backfill_from_pedidos_venda_abertos.py
./commercial-api/scripts/reconcile_portfolio_counts.sh
```

## F2c

Artefatos em [F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md) / snippet nginx — **não aplicar** até fechar o gap acima.

## Checklist gates

- [x] F0 KPI-FICHAS
- [x] F1 health + compose
- [x] F2 migrations + dual-read + transfer audit
- [ ] F2b harden — paridade UX open-orders com PVA
- [ ] Homologação Comercial real ([HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md))
- [ ] F2c flip menu + redirects
