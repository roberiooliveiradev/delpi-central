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

Fases 0–2 concluídas. Submódulos com RBAC por filial (manifesto v0.2.1), filial escolhida no início, CRUD completo, revisão programada por tempo, auditoria da ferramenta, listagens paginadas server-side e UX de reposição no MFE (jun/2026). Fase 3: import Access e go-live — ver [ROADMAP](../../docs/12-roadmap-e-evolucao/maintenance/ROADMAP.md) e scripts em `scripts/`.

| Testes CI | 56 (`scripts/ci-maintenance-api.sh`) |

## Listagens paginadas

Query params padronizados (`list_query_params.py`):

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `page` | `1` | Página (≥ 1) |
| `page_size` | `20` | Itens por página (1–200) |
| `sort_by` | rota | Campo de ordenação |
| `sort_dir` | `asc` | `asc` ou `desc` |

Resposta em `data`: `{ "items": [...], "total": N }`.

### Filtros adicionais por rota

| Rota | Parâmetros | Formato |
|------|------------|---------|
| `GET .../reposicoes` | `codigo_peca`, `motivo_id`, `data_inicial`, `data_final` | Arrays repetidos na query; datas `YYYY-MM-DD` ou ISO datetime |
| `GET .../preventiva/alertas` | `status`, `ferramenta`, `peca` | `status` repetido para multi-seleção |
| `GET .../revisoes-programadas/realizacoes` | `filial`, `codigo_ferramenta` | Histórico de revisões feitas |
| `GET .../ferramentas/{codigo}/auditoria` | `filial`, paginação | Timeline de mutações da ferramenta |

## Auditoria

Mutações em reposição e revisão programada chamam `log_ferramenta_audit()` — ver [ARCHITECTURE.md](./ARCHITECTURE.md) § Auditoria.

## Filtro de peças (3019)

`GET .../ferramentas/{codigo}/pecas` — somente códigos `3019*` amarrados à ferramenta (peças substituíveis).

`GET .../ferramentas/{codigo}/componentes` — **todos** os componentes amarrados (árvore + estoque); **não** aplica filtro 3019.

Função de reforço: `_filter_pecas_reposicao` em `mini_applicators_routes.py` (teste `test_mini_applicators_routes.py`).

| Script | Uso |
|--------|-----|
| `scripts/import_access_csv.py` | Migração CSV do Access |
| `scripts/bootstrap_dev_sample.py` | Repos de exemplo em dev local |
