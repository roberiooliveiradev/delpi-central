# Portal Comercial — plano de implementação inicial (status)

> Espelho executável de F0→F2b. Playbook: [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md) § 11.

| Fase | Objetivo | Status |
|------|----------|--------|
| **F0** | Fichas KPI + este plano | `concluído` |
| **F1** | Scaffold `commercial-api` | `concluído` |
| **F2** | Portfolios + avatars + cutover | `concluído` |
| **F2b** | MFE Portal Comercial (paridade) | `concluído` (homologação Comercial pendente) |

Fora do escopo inicial: F2c, F3–F4, F5+.

## Checklist de gates

- [x] F0: [KPI-FICHAS.md](./KPI-FICHAS.md) publicado
- [x] F1: `/apps/commercial-api/health` + compose/gateway
- [x] F2: migrations M1 + backfill + dual-read `COMMERCIAL_PORTFOLIO_SOURCE` + audit transfer
- [ ] F2b: [HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md) 100% pelo Comercial

## Cutover carteira (ops)

1. Rodar migrations: `COMMERCIAL_RUN_MIGRATIONS_ON_STARTUP=true`
2. Backfill: `python scripts/backfill_from_pedidos_venda_abertos.py` (no container)
3. Conferir contagens sellers/customers/avatars
4. `COMMERCIAL_PORTFOLIO_SOURCE=commercial`
5. Rotas CRUD em api-delpi `/sellers*` marcadas deprecated (código permanece até F2c)

## Artefatos

| Pacote | Path |
|--------|------|
| API | `commercial-api/` |
| MFE | `plugins/commercial/` |
| Homologação | [HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md) |

## Ordem de PRs (referência)

1. Docs F0  
2. Scaffold API  
3. Migrations + backfill  
4. Rotas portfolio/avatar  
5. Cutover flag  
6. Plugin scaffold  
7. Telas paridade  
8. Homologação  
