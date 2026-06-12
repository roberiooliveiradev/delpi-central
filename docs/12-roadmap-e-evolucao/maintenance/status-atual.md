# Status atual — Manutenção

**Última atualização:** jun/2026

## O que existe no monorepo

| Peça | Caminho | Status |
|------|---------|--------|
| Docs produto | `docs/12-roadmap-e-evolucao/maintenance/` | ✅ Índice, overview, arquitetura, roadmap, playbook, OPERATIONS |
| Docs API | `maintenance-api/docs/` | ✅ README, arquitetura, contratos |
| MFE | `plugins/maintenance/` | ✅ Home, mini-aplicadores, relatório, configuração, filiais |
| API dedicada | `maintenance-api/` | ✅ CRUD operacional + preventiva + catálogo de submódulos + gateways TOTVS |
| Rotas TOTVS api-delpi | `/engineering/mini-applicators/*` | ✅ ferramentas, peças, golpes, componentes |
| Docker Compose / gateway | `infra/docker-compose*.yml`, `gateway/nginx*.conf` | ✅ Anti-cache em rotas de API |
| CI | `scripts/ci-maintenance-api.sh` | ✅ 56 testes |
| Registro Core API | `plugins/maintenance/scripts/register-manifest.sh` | ✅ Script pronto |
| Import Access | `maintenance-api/scripts/import_access_csv.py` | ✅ CLI CSV + fixtures sample |
| Bootstrap dev | `maintenance-api/scripts/bootstrap_dev_sample.py` | ✅ Seed local para relatório |
| Smoke prod | `scripts/homologacao/check-maintenance-prod.sh` | ✅ Health + JSON da API |

## Entregas recentes (jun/2026)

| Tema | Detalhe |
|------|---------|
| **Filial** | Escolha no Início; nome da filial no badge (catálogo Postgres); uma filial → sem seletor |
| **Submódulos** | Catálogo API (`/options`); permissões por filial no manifesto v0.2.1 |
| **RBAC API** | `FilialAccessScopeService` alinhado ao manifesto (`mini-applicators.view\|manage.filial-XX`); legado `maintenance.view.filial-XX` / `manage.filial-XX` genéricos não concedem escopo |
| **Gateway** | Headers anti-cache em `/apps/*-api/*` — evita `Unexpected token '<'` por HTML cacheado |
| **UI mini-aplicadores** | CRUD reposição, golpes automáticos, filtro histórico por peça, formulário colapsável + botão «Nova reposição», gráfico de golpes no histórico |
| **Tabelas** | `DataTableSection` + `useServerTable` — paginação e ordenação **server-side** em ferramentas, reposições, componentes, alertas, últimas reposições, motivos, status e filiais |
| **Peças (3019)** | `GET .../pecas` filtra códigos `3019*` na API dedicada (TOTVS `B1_GRUPO = 3019` na api-delpi) |
| **Relatório** | Alertas + últimas reposições + detalhe preventivo com gráficos; erros por seção (alertas vs. últimas) |
| **Preventiva API** | `_SUBMODULE_ID = mini-aplicadores` corrigido (typo gerava 403 no relatório) |
| **Componentes / estoque** | Rota TOTVS + painel na ferramenta (estrutura recursiva, locais 01/99) |
| **UI configuração** | CRUD motivos + status preventivo; feedback (`StateBox`) com espaçamento correto |
| **Manifesto v0.2.1** | Rotas internas `showInMenu: false`; tile único no portal |
| **Preventiva por motivo** | Flag `excluir_preventiva` em motivos (migration V005); reposições com esse motivo não entram no cálculo preventivo |
| **Indicadores da ferramenta** | `FerramentaReposicaoIndicadores` ao lado do gráfico de golpes no histórico |
| **Filtros histórico** | Multi-select peça e motivo; intervalo **De/Até** (`data_inicial` / `data_final` na API) |
| **Filtro relatório** | Multi-select de status preventivo (`status` repetido na query) |
| **Peças vs. componentes** | `/pecas` → só `3019*` (reposição); `/componentes` → árvore completa amarrada (estoque) |
| **Datas pt-BR (MFE)** | `BrDateInput` / `BrDatetimeInput` — exibição `dd/mm/aaaa` e `dd/mm/aaaa HH:mm` (24h) |
| **MultiSelectField** | Painel compacto; checkbox à esquerda na mesma linha do rótulo |
| **Revisão programada** | Agenda por ferramenta no detalhe (intervalo, referência manual, marcar feito); alertas no relatório; histórico de realizações com editar/excluir |
| **Auditoria da ferramenta** | `audit_logs` nas mutações de reposição/revisão; timeline paginada no detalhe (`GET .../auditoria`) |
| **StateBox dismissível** | Botão fechar em avisos de sucesso/erro (mini-aplicadores, config, filiais, relatório) |

## Fases do roadmap

| Fase | Status |
|------|--------|
| 0 — Fundação | ✅ Concluída |
| 1 — CRUD operacional | ✅ Concluída |
| 2 — Preventiva + relatório | ✅ Concluída (validar amostra vs WinForms) |
| 3 — Migração + produção | 🚧 Script import + runbook prontos; aguarda export Access e RBAC em prod |
| 4 — Extensões | ⏳ Backlog (links externos, preventiva parametrizável) |

## Próximo passo recomendado

1. Registrar manifesto **v0.2.1** na Core API (`register-manifest.sh`) e atribuir permissões no RBAC.
2. Exportar CSV do Access e rodar `import_access_csv.py`.
3. Validar ranking preventivo contra WinForms (≥5 pares).
4. Smoke test: filial única vs múltiplas; view/manage por submódulo e filial.
