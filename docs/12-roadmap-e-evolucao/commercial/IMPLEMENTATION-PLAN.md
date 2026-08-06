# Portal Comercial — plano de implementação (status)

> Playbook: [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md) § 11.

| Fase | Objetivo | Status |
|------|----------|--------|
| **F0** | Fichas KPI | `concluído` |
| **F1** | Scaffold `commercial-api` | `concluído` |
| **F2** | Portfolios + avatars | `concluído` |
| **F2b** | MFE paridade (scaffold) | `concluído` |
| **F2b harden** | UX real + clients + scope | `concluído` (ago/2026 — port PVA completo) |
| **Wave G** | Shell/IA, Home, Meu dia, worklist, timeline Conta 360 | `concluído` (ago/2026 — sem F2c) |
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

## Wave G (CRM leve — sem F2c)

Entregue na mesma trilha do Portal Comercial (F5 parcial):

- Docs: [DESIGN-IA-COMERCIAL.md](./DESIGN-IA-COMERCIAL.md), [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md), [HOMOLOGACAO-WAVE-G.md](./HOMOLOGACAO-WAVE-G.md)
- `plugin-ui`: `AlertQueue`, `ScopeChipBar`, `WorklistItem`
- MFE: `/my-day`, Home com fila de alertas, timeline na Conta 360
- API: migration `V003` (`tasks`/`activities`), `/me/worklist`, `/tasks`, `/activities`

**Não inclui F2c** (ocultar PVA).

## F2c

Só após [HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md) 100% ✅ — ver [F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md).

## Checklist gates

- [x] F0 KPI-FICHAS
- [x] F1 health + compose
- [x] F2 migrations + dual-read + transfer audit
- [x] F2b harden — paridade UX open-orders/carteira com PVA
- [x] Wave G — worklist / Meu dia / RBAC por capacidade
- [ ] Homologação Comercial ([HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md))
- [ ] F2c flip menu + redirects
