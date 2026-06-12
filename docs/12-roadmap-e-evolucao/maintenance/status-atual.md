# Status atual — Manutenção

**Última atualização:** jun/2026

## O que existe no monorepo

| Peça | Caminho | Status |
|------|---------|--------|
| Docs produto | `docs/12-roadmap-e-evolucao/maintenance/` | ✅ Índice, overview, arquitetura, roadmap, playbook, OPERATIONS |
| Docs API | `maintenance-api/docs/` | ✅ README, arquitetura, contratos |
| MFE | `plugins/maintenance/` | ✅ Home, mini-aplicadores, relatório preventivo, configuração |
| API dedicada | `maintenance-api/` | ✅ CRUD operacional + preventiva + gateways TOTVS |
| Rotas TOTVS api-delpi | `/engineering/mini-applicators/*` | ✅ ferramentas, peças, golpes |
| Docker Compose / gateway | `infra/docker-compose*.yml` | ✅ |
| CI | `scripts/ci-maintenance-api.sh` | ✅ 9 testes |
| Registro Core API | `plugins/maintenance/scripts/register-manifest.sh` | ✅ Script pronto |
| Import Access | `maintenance-api/scripts/import_access_csv.py` | ✅ CLI CSV |

## Fases do roadmap

| Fase | Status |
|------|--------|
| 0 — Fundação | ✅ Concluída |
| 1 — CRUD operacional | ✅ Concluída |
| 2 — Preventiva + relatório | ✅ Concluída (validar amostra vs WinForms) |
| 3 — Migração + produção | 🚧 Script import + runbook prontos; aguarda export Access e RBAC |
| 4 — Extensões | ⏳ Backlog |

## Próximo passo recomendado

1. Registrar manifesto (`register-manifest.sh`) e atribuir `maintenance.*` no RBAC.
2. Exportar CSV do Access e rodar `import_access_csv.py`.
3. Validar ranking preventivo contra WinForms (≥5 pares).
4. Rebuild containers locais e smoke test com usuário `rober`.
