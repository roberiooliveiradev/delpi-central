# Documentação — Manutenção API

Índice técnico da API dedicada (`maintenance-api` / pacote `maint_app`).

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Camadas, ports, gateways, Postgres |
| [integration-contracts.md](./integration-contracts.md) | Consumo api-delpi (TOTVS) |
| [OPERATIONS.md](../../docs/12-roadmap-e-evolucao/maintenance/OPERATIONS.md) | Deploy, RBAC, import Access |
| [../README.md](../README.md) | Quick start |
| [Produto (roadmap/playbook)](../../docs/12-roadmap-e-evolucao/maintenance/README.md) | Visão de produto e fases |

## Convenções

| Item | Valor | Idioma |
|------|-------|--------|
| Plugin id | `maintenance` | Inglês |
| Nome no portal | Manutenção | Português |
| Schema Postgres | `maintenance` | Inglês |
| Pacote Python | `maint_app` | Inglês |
| Prefixo HTTP | `/maintenance` | Inglês |
| Env prefix | `MAINT_*` | Inglês |

## Estado

Fases 0–2 concluídas. Submódulos com RBAC por filial (manifesto v0.2.1), filial escolhida no início, CRUD completo e tabelas paginadas/ordenáveis no MFE (jun/2026). Fase 3: import Access e go-live — ver [ROADMAP](../../docs/12-roadmap-e-evolucao/maintenance/ROADMAP.md) e scripts em `scripts/`.

| Testes CI | 36 (`scripts/ci-maintenance-api.sh`) |

| Script | Uso |
|--------|-----|
| `scripts/import_access_csv.py` | Migração CSV do Access |
| `scripts/bootstrap_dev_sample.py` | Repos de exemplo em dev local |
