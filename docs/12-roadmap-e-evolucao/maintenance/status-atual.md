# Status atual — Manutenção

**Última atualização:** jun/2026

## O que existe no monorepo

| Peça | Caminho | Status |
|------|---------|--------|
| Docs produto | `docs/12-roadmap-e-evolucao/maintenance/` | ✅ Índice, overview, arquitetura, roadmap, playbook, OPERATIONS |
| Docs API | `maintenance-api/docs/` | ✅ README, arquitetura, contratos |
| MFE | `plugins/maintenance/` | ✅ Home (filial no início), mini-aplicadores, relatório, configuração CRUD |
| API dedicada | `maintenance-api/` | ✅ CRUD operacional + preventiva + catálogo de submódulos + gateways TOTVS |
| Rotas TOTVS api-delpi | `/engineering/mini-applicators/*` | ✅ ferramentas, peças, golpes, componentes |
| Docker Compose / gateway | `infra/docker-compose*.yml` | ✅ |
| CI | `scripts/ci-maintenance-api.sh` | ✅ 16 testes |
| Registro Core API | `plugins/maintenance/scripts/register-manifest.sh` | ✅ Script pronto |
| Import Access | `maintenance-api/scripts/import_access_csv.py` | ✅ CLI CSV + fixtures sample |
| Bootstrap dev | `maintenance-api/scripts/bootstrap_dev_sample.py` | ✅ Seed local para relatório |

## Entregas recentes (jun/2026)

| Tema | Detalhe |
|------|---------|
| **Filial** | Escolha só no Início; uma filial → sem seletor; filtros internos usam sessão + API |
| **Submódulos** | Catálogo API (`/options`); permissões `maintenance.mini-applicators.view\|manage` independentes de filial |
| **Escopo filial** | `maintenance.view.filial-XX` / `manage.filial-XX` filtram dados na API |
| **UI mini-aplicadores** | CRUD reposição (criar/editar/excluir), golpes automáticos, filtro histórico por peça |
| **Componentes / estoque** | Rota TOTVS + painel na ferramenta (estrutura recursiva, locais 01/99) |
| **Relatório** | Últimas reposições por peça + ranking preventivo |
| **UI configuração** | CRUD motivos + edição de status preventivo (manage) |
| **Manifesto v0.3.0** | Rotas internas `showInMenu: false`; tile único no portal |

## Fases do roadmap

| Fase | Status |
|------|--------|
| 0 — Fundação | ✅ Concluída |
| 1 — CRUD operacional | ✅ Concluída |
| 2 — Preventiva + relatório | ✅ Concluída (validar amostra vs WinForms) |
| 3 — Migração + produção | 🚧 Script import + runbook prontos; aguarda export Access e RBAC |
| 4 — Extensões | ⏳ Backlog (links externos, preventiva parametrizável) |

## Próximo passo recomendado

1. Registrar manifesto v0.3.0 (`register-manifest.sh`) e atribuir permissões no RBAC.
2. Exportar CSV do Access e rodar `import_access_csv.py`.
3. Validar ranking preventivo contra WinForms (≥5 pares).
4. Smoke test: filial única vs múltiplas; view/manage por submódulo.
