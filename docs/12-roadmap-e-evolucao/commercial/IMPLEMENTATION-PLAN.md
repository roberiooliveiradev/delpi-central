# Portal Comercial — plano de implementação (status)

> Playbook: [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md) § 11.

| Fase | Objetivo | Status |
|------|----------|--------|
| **F0** | Fichas KPI | `concluído` |
| **F1** | Scaffold `commercial-api` | `concluído` |
| **F2** | Portfolios + avatars | `concluído` |
| **F2b** | MFE paridade (scaffold) | `concluído` |
| **F2b harden** | UX real + clients + scope | `concluído` |
| **Cutover dados** | backfill + `COMMERCIAL_PORTFOLIO_SOURCE=commercial` | `concluído` |
| **F2c** | Depreciar PVA | `concluído` (redirects + menu oculto; re-register em cada ambiente) |

## Cutover de dados (ops)

Não há dual-write. CRUD canônico = só `commercial-api`. Rotas api-delpi `/sellers*` permanecem deprecated até ADR de remoção.

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

Flip aplicado (ago/2026):

- Redirects inline em `gateway/nginx.conf` + `nginx.dev.conf`
- Manifest PVA: `showInMenu: false` + prefixo «(legado)»
- Dev: gateway rebuild + `register-manifest` PVA OK
- Prod: `./infra/scripts/up-prod-sequential.sh --build gateway` + `TOKEN=… ./plugins/pedidos-venda-abertos/scripts/register-manifest.sh`

## Checklist gates

- [x] F0 KPI-FICHAS
- [x] F1 health + compose
- [x] F2 migrations + dual-read + transfer audit
- [x] F2b harden (filtros, ops, billing/NF, admin, avatar write)
- [x] Homologação / autorização de cutover ([HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md))
- [x] F2c flip menu + redirects (código + dev; prod: rebuild gateway + re-register)
