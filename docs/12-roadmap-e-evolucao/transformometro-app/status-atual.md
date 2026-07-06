# Status atual — Transformômetro

Atualizado: **jul/2026** (Playbook 20 mapeamento WBS; melhorias com escopo livre V034; UI SelectField + modal de confirmação; duplicação completa de processo)

> **Regra jul/2026 — média por instância.** Cada instância tem baseline/parâmetros próprios. A economia consolidada de um processo é a **média aritmética das instâncias ativas no mês** (`Σ economia_instância / nº_instâncias_ativas`); investimento, horas e ROI seguem a mesma média. Recorte por unidade/setor mostra o **valor real** da instância (média de 1 = ela mesma). Fonte da regra: `transformometro-api/docs/regras-de-calculo.md`.

> **Arquitetura jul/2026 — fonte única + query cache.** A planilha materializada `dashboard_calculos` deixou de ser a fonte: UI, snapshot/chat e Transforma+ leem do **motor live** (`DashboardLiveService`) com `DashboardQueryCache` (TTL + invalidação por geração). O CRUD **não** dispara mais recálculo pesado — apenas invalida o cache em O(1). Faixas de tempo por dia (`YYYY-MM-DD`) passam a valer em todas as leituras. A tabela materializada e o recálculo viram **opt-in** (`TM_DASHBOARD_PERSIST_CACHE`). Flags: `TM_DASHBOARD_QUERY_CACHE` (on), `TM_DASHBOARD_QUERY_CACHE_TTL_SECONDS` (120), `TM_DASHBOARD_PERSIST_CACHE` (off).

> **Regra jul/2026 — instância multi-unidade.** Instâncias com `todas_filiais_ativas` compartilham uma timeline entre filiais. Na visão consolidada, `economia_bruta`, `economia_liquida_mes` e `horas_economizadas_mes` da instância escalam pelo nº de filiais ativas (`escopo_unidades`); recursos compartilhados **não** multiplicam. Cadastro legado duplicado por filial deve ser consolidado via **export JSON → edição manual → import replace** ([json-backup.md](../../../transformometro-api/docs/json-backup.md) § Consolidação cadastral). Detalhe: [regras-de-calculo.md](../../../transformometro-api/docs/regras-de-calculo.md) § Instância multi-unidade.

> **Regra jul/2026 — validade de 1 ano por revisão.** A economia de uma revisão comparável só conta por **12 meses** a partir do início (`data_implantacao`/`data_inicio_vigencia`); a partir do **aniversário** (`início + 12m`, exclusivo) deixa de ser contabilizada (`calc_rules.review_validity_end_date` / `review_effective_end_date`). Uma **nova revisão implantada** (`revisao_ativa`) assume o cálculo com seu próprio ciclo de 12 meses; sem sucessora, o ambiente passa a contribuir 0. O dashboard acompanha as que vencem nos **próximos 90 dias** (`GET /dashboard/vencimentos`, painel “Revisões a vencer”; campos `data_vencimento`/`dias_para_vencer`/`status_vigencia`).

## Fonte de dados e pipeline (runtime)

| Camada | Papel |
|--------|-------|
| **Postgres** (`schema transformometro`) | Fonte de verdade — cadastro, cache `dashboard_calculos`, views V020 |
| **transformometro-api** | CRUD, cálculo, recalc, integração S2S |
| **plugins/transformometro** | UI oficial de cadastro e dashboard |
| **api-delpi** | Contrato público `GET /engineering/transforma-mais/*` → `TransformometroTransformaMaisGateway` |
| **strategic-indicators-api** | KPI Transforma+ via `DelpiEngineeringGateway` → api-delpi |
| **dashboard-engineering** | `TransformaPage` (read-only) → api-delpi |

**Não participam do pipeline:** planilha Google Sheets, `ProcessSummaryCalculator`, `api-delpi/.../google_sheets/transforma_mais/process_repository.py` (código morto).

## Entregue

| Área | Status |
|------|--------|
| API + migrations **V001–V034** | ✅ Auto no boot (`TM_RUN_MIGRATIONS_ON_STARTUP=true`) |
| Processo-mestre + **melhorias** (filial + N setores, escopo livre) | ✅ V013–V015 + **V019** + **V034**; painel MFE **Melhorias** |
| **CRUD filiais** + editar/excluir instância | ✅ MFE `FiliaisPage` + `PUT/DELETE /instancias/{id}` |
| Filiais / setores **UUID** + `codigo_*` | ✅ V011–V012; CRUD + options |
| Revisões por instância + URL canônica | ✅ V014/V018; redirect legado no MFE |
| **Escopo híbrido** `escopo_recurso` | ✅ V016; formulário Recursos + calculador |
| Cache dashboard UUID + denorm | ✅ V017; recalc obrigatório pós-migration |
| **Views leitura rápida** | ✅ V020; snapshot instâncias + evolução mensal |
| **Média por instância** (motor + cache) | ✅ jul/2026; `_calculate_monthly_series` por instância, `calc_rules` divide por `instancias_ativas_mes`, cache/views **V021** (agregação 2 níveis) |
| **Fonte única + query cache** | ✅ jul/2026; `DashboardQueryCache` (TTL+geração), hook invalida O(1), Transforma+/snapshot via motor live, tabela materializada opt-in (`TM_DASHBOARD_PERSIST_CACHE`) |
| **Validade de 1 ano + vencimentos** | ✅ jul/2026; `calc_rules.review_validity_end_date`, cap em `_is_review_valid_for_month`, `GET /dashboard/vencimentos` + painel “Revisões a vencer” (90d) |
| **Transforma+ S2S via cache** | ✅ `engineering_transforma_mais.py` (fallback live) |
| Visões dashboard `view` | ✅ API + toggle MFE + `access_scope` |
| Duplicar **melhoria** (replicar timeline) | ✅ `POST /instancias/{id}/duplicar` |
| **Duplicar processo-mestre** (cópia completa) | ✅ MFE + API — diagrama, WBS, melhorias, revisões, evidências |
| Integração Transforma+ por instância | ✅ `id` = `instancia_id` |
| **RBAC filial** server-side | ✅ S10; manifesto com permissões escopadas |
| CRUD completo + dashboard Fase 4 | ✅ |
| Backup JSON 1.1 | ✅ bundles `filiais`, `processo_instancias`, `processo_instancia_setores` |
| **Consolidação cadastral** (multi-unidade) | ✅ import + runbook manual jul/2026; motor com multiplicador (`escopo_unidades` default 1) |
| Testes API | ✅ `scripts/ci-transformometro-api.sh` (123+) |
| Build MFE | ✅ Docker build `transformometro` |
| Documentação Playbook 18 | ✅ modelagem, arquitetura, regras de cálculo, status |
| **Diagramas de processo (Playbook 19)** | ✅ V026–V028; macro + escopo + overlay; editor BPMN-lite + swimlanes + tela cheia |
| **Mapeamento WBS (Playbook 20)** | ✅ V030–V033; árvore + CSV + escopo/overlay por melhoria/revisão |
| **Colaboração presença (WS)** | ✅ V029 |
| **Campos melhoria** (resumo, fase, prioridade, go-live) | ✅ V034 |
| Documentação Playbook 19 | ✅ playbook, ADR, schemas, [playbook-19-implementation-status.md](../../../transformometro-api/docs/playbook-19-implementation-status.md) |
| Documentação Playbook 20 | ✅ [playbook-20-implementation-status.md](../../../transformometro-api/docs/playbook-20-implementation-status.md) |
| **MFE UX jul/2026** | ✅ SelectField (padrão PAC), modal de confirmação centralizado, transições suaves, linha do tempo |

## Migrations automáticas

Com `TM_RUN_MIGRATIONS_ON_STARTUP=true` (padrão no compose e `infra/.env`), o container **`delpi-transformometro-api`** aplica V001–V034 pendentes no **startup** (`run_migrations_on_startup` no lifespan FastAPI). Falha de migration **impede** a API de subir.

> **V021** redefine `processo_competencia_snapshot` e `dashboard_competencia_evolucao` com a média por instância (agregação em 2 níveis). Só relevante se `TM_DASHBOARD_PERSIST_CACHE=true` (leitura legada da tabela) — nesse caso, rodar **recalc full** após aplicar. Com o padrão (fonte única live), as views/tabela não são usadas.

Conferir:

```bash
docker exec delpi-transformometro-api python -m tm_app.infrastructure.persistence.plugins.migrations_runner status
```

## Pós-deploy Playbook 18 (obrigatório na 1ª vez)

1. **Backup JSON** do cadastro atual (`import_cadastro_json.py export`).
2. Rebuild + recreate `transformometro-api` + `transformometro`.
3. Migrations sobem sozinhas; validar `status` até **V034** (ou última pendente).
4. **Bootstrap filiais** (V011 não faz seed):  
   `python scripts/bootstrap_filiais_from_cadastro.py -i fixtures/cadastro/...json`
5. **Recalc full** do dashboard (obrigatório após V017/V019/V020): Dashboard → Recalcular ou `POST /transformometro/dashboard/recalcular`.
6. Registrar manifesto atualizado (`register-manifest.sh`) — permissões RBAC filial + rota `/filiais`.
7. Smoke: dashboard (3 visões), processo → melhorias → revisão URL canônica, macro → escopo → overlay, mapeamento WBS, Transforma+ summary (<500ms com cache).

Detalhe: [playbook-18-implementation-status.md](../../../transformometro-api/docs/playbook-18-implementation-status.md) · [OPERATIONS.md](./OPERATIONS.md).

## Verificação ambiente dev (jun/2026)

Com `docker compose ... up` no stack local:

- Migrations **V001–V020** aplicadas (`migrations_runner status`)
- Integração S2S `GET .../integrations/engineering/transforma-mais/processes` retorna instâncias do Postgres (IDs UUID)
- api-delpi `GET /engineering/transforma-mais/*` responde 200 via gateway interno

```bash
docker exec delpi-transformometro-api python -m tm_app.infrastructure.persistence.plugins.migrations_runner status
docker exec delpi-api-delpi python -c "
import os, urllib.request, json
t = os.environ['API_DELPI_INTERNAL_SERVICE_TOKEN']
u = 'http://transformometro-api:8000/transformometro/integrations/engineering/transforma-mais/processes'
r = urllib.request.urlopen(urllib.request.Request(u, headers={'X-Delpi-Service-Token': t}))
d = json.loads(r.read())['data']
print('total instancias:', d.get('total'), 'items:', len(d.get('items') or []))
"
```

## Consolidação cadastral em produção (one-shot)

1. `git pull` + rebuild `transformometro-api` (commit com import multi-unidade + calculador).
2. **Export** backup: `python scripts/import_cadastro_json.py export -o backup-pre-consolidacao.json`.
3. Aplicar bundle consolidado (edição manual conforme [json-backup.md](../../../transformometro-api/docs/json-backup.md)).
4. `preview` + `apply --mode replace --yes`.
5. Recalc / smoke dashboard (3 visões, instâncias multi-unidade no MFE).

JSONs de operação **não** entram no git (`fixtures/cadastro/*.json` gitignored).

## Pendente (operacional)

| Item | Responsável |
|------|-------------|
| **Consolidação cadastral** em produção (passos acima) | Ops |
| **`escopo_unidades`** no live/recalc (multiplicador consolidado) | ✅ jul/2026 |
| Deploy produção com runbook acima | Ops |
| Atribuir permissões escopadas na Core API / Portal RBAC (quem precisar) | Ops |
| Planilha somente leitura | Google Workspace |
| Limpeza código morto Sheets na api-delpi (Fase 6) | Dev |

## Variáveis de produção (checklist)

```bash
API_DELPI_INTERNAL_SERVICE_TOKEN=<mesmo valor em api-delpi, SI, transformometro-api>
TRANSFORMOMETRO_API_BASE_URL=http://transformometro-api:8000
TM_RUN_MIGRATIONS_ON_STARTUP=true
PLUGINS_DB_*=<postgres-plugins>
```

## Comandos úteis

```bash
cd ~/projetos/delpi-central
git pull
docker compose -f infra/docker-compose.dev.yml --env-file infra/.env build transformometro-api transformometro
docker compose -f infra/docker-compose.dev.yml --env-file infra/.env up -d --force-recreate transformometro-api transformometro

./scripts/ci-transformometro-api.sh
cd plugins/transformometro && npm run build   # ou build via Docker

export TOKEN="..." BASE_URL="https://www.minhadelpi.com.br"
./plugins/transformometro/scripts/register-manifest.sh
```

## Referências

- [PLAYBOOK-18-instancias-filial-setor-escopo.md](./PLAYBOOK-18-instancias-filial-setor-escopo.md)
- [PLAYBOOK-MODELAGEM.md](./PLAYBOOK-MODELAGEM.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [ROADMAP.md](./ROADMAP.md)
- [OPERATIONS.md](./OPERATIONS.md)
- [regras-de-calculo.md](../../../transformometro-api/docs/regras-de-calculo.md)
- [PLAYBOOK-19-diagramas-processo-revisao-escopo.md](./PLAYBOOK-19-diagramas-processo-revisao-escopo.md)
- [playbook-19-implementation-status.md](../../../transformometro-api/docs/playbook-19-implementation-status.md)
- [adr-diagramas-processo.md](../../../transformometro-api/docs/adr-diagramas-processo.md)
- [PLAYBOOK-20-decomposicao-processo-arvore-mapeamento.md](./PLAYBOOK-20-decomposicao-processo-arvore-mapeamento.md)
- [playbook-20-implementation-status.md](../../../transformometro-api/docs/playbook-20-implementation-status.md)
- [TUTORIAL-USUARIO.md](./TUTORIAL-USUARIO.md)
- [DEPLOYMENT.md](../../../transformometro-api/docs/DEPLOYMENT.md)
