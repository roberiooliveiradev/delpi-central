# Portal Comercial — plano de implementação (status)

> Playbook: [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md) § 11.

| Fase | Objetivo | Status |
|------|----------|--------|
| **F0** | Fichas KPI | `concluído` |
| **F1** | Scaffold `commercial-api` | `concluído` |
| **F2** | Portfolios + avatars | `concluído` |
| **F2b** | MFE paridade (scaffold) | `concluído` |
| **F2b harden** | UX real + clients + scope | `concluído` (homologação Comercial pendente) |
| **Cutover dados** | backfill + `COMMERCIAL_PORTFOLIO_SOURCE=commercial` | `pronto` (ops: rodar backfill/reconcile) |
| **F2c** | Depreciar PVA | `artefatos prontos` — flip de menu após ✅ homologação |

## Cutover de dados (ops)

Não há dual-write. Após a flag, CRUD canônico = só `commercial-api`. Rotas api-delpi `/sellers*` permanecem até F2c (deprecated).

```bash
# 1) Migrations (startup da commercial-api ou runner)
# 2) Backfill (preserva UUIDs + copia avatars)
docker exec -it delpi-commercial-api \
  python scripts/backfill_from_pedidos_venda_abertos.py

# 3) Reconciliar contagens
./commercial-api/scripts/reconcile_portfolio_counts.sh

# 4) Garantir env COMMERCIAL_PORTFOLIO_SOURCE=commercial e recriar API
./infra/scripts/up-dev-sequential.sh --build commercial-api
# prod: ./infra/scripts/up-prod-sequential.sh --build commercial-api
```

## F2c

Ver [F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md) e [adr/ADR-002-deprecar-pedidos-venda-abertos.md](./adr/ADR-002-deprecar-pedidos-venda-abertos.md).

## Checklist gates

- [x] F0 KPI-FICHAS
- [x] F1 health + compose
- [x] F2 migrations + dual-read + transfer audit
- [x] F2b harden (filtros, ops, billing/NF, admin, avatar write)
- [ ] Homologação Comercial ([HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md))
- [ ] F2c flip menu + redirects em produção
