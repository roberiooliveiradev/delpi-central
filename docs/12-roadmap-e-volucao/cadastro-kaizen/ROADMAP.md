# Roadmap — Cadastro de Kaizens

> **Arquivo:** `docs/12-roadmap-e-evolucao/cadastro-kaizen/ROADMAP.md`  
> **Status:** Fases 0–3 concluídas em dev; Fases 4–10 planejadas  
> **Produto:** Minha DELPI  
> **Escopo:** plugin `cadastro-kaizen` + rotas `api-delpi/quality/kaizens/records` + schema `quality` (postgres-plugins)  
> **Atualizado:** 2026-06-15

---

## Objetivo

Substituir o cadastro operacional de kaizens na planilha Google Sheets por um fluxo na plataforma com:

- Persistência em **PostgreSQL** (`quality.kaizens`)
- CRUD via **api-delpi** com permissões RBAC dedicadas
- **MFE** federado para listagem, formulário e importação da planilha legada
- Convivência temporária com o **dashboard de qualidade**, que ainda lê KPIs da planilha (`GET /quality/kaizens/summary`)

Documentação operacional: [plugins/cadastro-kaizen/README.md](../../../plugins/cadastro-kaizen/README.md) · [DOCUMENTACAO.md](../../../plugins/cadastro-kaizen/docs/DOCUMENTACAO.md)

---

## Status atual (dev)

| Área | Situação | Observação |
|------|----------|------------|
| Migrations `quality` V026/V027 | ✅ Aplicadas | `quality.submodules` + `quality.kaizens` |
| CRUD Postgres `/kaizens/records` | ✅ | List, create, get, update, delete lógico |
| Cálculo de economia | ✅ | `KaizenSavingsCalculator` (tempo/material/financeiro/misto/qualitativo) |
| Importação planilha → Postgres | ✅ | `POST .../import-from-sheet` + botão na UI |
| MFE listagem + formulário | ✅ | Filtros, paginação client-side, rotas `/novo` e `/editar/{uuid}` |
| Docker dev | ✅ | `delpi-cadastro-kaizen`, gateway `/apps/cadastro-kaizen` |
| Dados piloto | ✅ | 21 kaizens importados via API em ambiente local |
| Registro Core API / RBAC prod | ⏳ Pendente | Manifesto existe; falta registrar e atribuir perfis |
| Homologação automatizada | ⏳ Pendente | Sem `check-cadastro-kaizen.sh` nem CI dedicado |
| Dashboard lê Postgres | ❌ Futuro | `summary` ainda usa Google Sheets |
| Agente / chat (rotas operacionais) | ❌ Futuro | Knowledge base sem rotas `records` |

---

## Princípios

1. **Thin client:** regras de economia e validação na api-delpi; MFE só orquestra formulário e tabela.
2. **Uma fonte por fluxo:** cadastro operacional = Postgres; leitura analítica legada = Sheets até cutover explícito.
3. **API primeiro:** importação e migrações via HTTP (`import-from-sheet`), não scripts offline em produção.
4. **Idempotência:** importação ignora duplicatas (filial + título + data de implantação).
5. **Permissões no backend:** `cadastro-kaizen.view` / `cadastro-kaizen.manage` (+ aliases `api-delpi.quality.access`).
6. **Envelope canônico:** `meta.operationId` + `meta.shape` em todas as rotas de cadastro.

---

## Visão de fases

```text
Fase 0  — Schema Postgres (quality)                    ✅
Fase 1  — API CRUD + domínio (calculator, repository)  ✅
Fase 2  — MFE cadastro-kaizen (UI + Docker)            ✅
Fase 3  — Importação planilha via API + documentação   ✅
Fase 4  — Produção: manifesto, RBAC, compose prod      ⏳ PRÓXIMA
Fase 5  — Homologação CI/smoke + testes E2E           ⏳
Fase 6  — Unificar leitura analítica (summary → PG)    📋
Fase 7  — Integração dashboard-quality + SI            📋
Fase 8  — Agente Minha DELPI (actions + knowledge)     📋
Fase 9  — Cutover planilha (desativação Sheets)        📋
Fase 10 — Evoluções UX e governança                    📋
```

---

## Fase 0 — Schema PostgreSQL ✅

**Entregáveis**

- [x] `V026__create_quality_submodules.sql` — submódulo `kaizen`
- [x] `V027__create_kaizens.sql` — tabela `quality.kaizens` (soft delete, checks status/tipo economia)
- [x] Boot automático: `RUN_PLUGINS_MIGRATIONS_ON_STARTUP` no compose

**Critério de pronto:** `docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin quality` mostra V026/V027 aplicadas.

---

## Fase 1 — API CRUD e domínio ✅

**Entregáveis**

- [x] `PostgresKaizenRepository` — list, get, create, update, delete lógico
- [x] `KaizenSavingsCalculator` + `enrich_savings_fields`
- [x] `kaizen_records_router` — rotas sob `/quality/kaizens/records`
- [x] Permissões `cadastro-kaizen.view` / `cadastro-kaizen.manage` em `api_delpi_permissions.py`
- [x] `route_contract_registry` — operationIds e shapes
- [x] Testes: `test_kaizen_savings_calculator`, `test_kaizen_repository`, smoke meta

**Critério de pronto:** CRUD via curl com JWT retorna envelope `success: true` e meta semântico.

---

## Fase 2 — MFE `cadastro-kaizen` ✅

**Entregáveis**

- [x] Vite + Module Federation (`base: /apps/cadastro-kaizen/`)
- [x] `cadastro-kaizen.manifest.json` (permissões + rota menu)
- [x] Páginas: listagem, novo, editar
- [x] `httpClient` com `X-Delpi-Caller-App: cadastro-kaizen`
- [x] API base `/apps/api-delpi/quality/kaizens/records`
- [x] Dockerfile + serviço `cadastro-kaizen` em `docker-compose.dev.yml` / `docker-compose.yml`
- [x] Design system `kz-*` alinhado aos dashboards

**Critério de pronto:** `remoteEntry.js` 200 via gateway; listagem carrega registros com token válido.

---

## Fase 3 — Importação planilha + docs ✅

**Entregáveis**

- [x] `ImportKaizensFromSheetUseCase` + `kaizen_sheet_import_mapper`
- [x] `POST /quality/kaizens/records/import-from-sheet` (`dry_run` opcional)
- [x] `list_active_kaizen_details` no repositório Sheets
- [x] Correção `GET /quality/kaizens/{kaizen_id:path}` (IDs com `/`)
- [x] Botão «Importar planilha» na listagem do MFE
- [x] README + DOCUMENTACAO.md do plugin
- [x] Seção em `06-modulos-departamentais.md` e índice `docs/08-plugins`

**Critério de pronto:** importação idempotente; 21 linhas ativas da planilha refletidas no Postgres em dev.

---

## Fase 4 — Produção operacional ⏳ **PRÓXIMA**

**Objetivo:** plugin visível e utilizável por usuários de qualidade em ambiente real.

**Entregáveis**

- [ ] Registrar manifesto na Core API (`plugins/cadastro-kaizen/scripts/register-manifest.sh`)
- [ ] Atribuir `cadastro-kaizen.view` e `cadastro-kaizen.manage` aos perfis/grupos de qualidade (Keycloak / admin permissões)
- [ ] Validar `gateway.depends_on` inclui `cadastro-kaizen` em `docker-compose.yml` (prod)
- [ ] Confirmar migrations `quality` em postgres-plugins de **produção/staging**
- [ ] Executar importação inicial via API em staging (`import-from-sheet`) com validação pela área de negócio
- [ ] Comunicar convivência: **dashboard-quality ainda lê Sheets** — alterações só no cadastro não atualizam KPIs do painel

**Comandos**

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
./plugins/cadastro-kaizen/scripts/register-manifest.sh

docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin quality

curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "X-Delpi-Caller-App: cadastro-kaizen" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}' \
  "http://localhost/apps/api-delpi/quality/kaizens/records/import-from-sheet" | jq .
```

**Critério de pronto:** usuário com permissão vê «Cadastro de Kaizens» no menu; consegue criar/editar/excluir; importação dry-run OK em staging.

**Riscos**

| Risco | Mitigação |
|-------|-----------|
| Usuário edita no cadastro e não vê mudança no dashboard | Comunicação + Fase 6 |
| Permissão ausente → 403 | Checklist RBAC antes do go-live |
| Planilha e Postgres divergem | Importação idempotente + data de corte documentada |

---

## Fase 5 — Homologação e CI 📋

**Objetivo:** regressão automatizada no padrão dos outros plugins.

**Entregáveis**

- [ ] `scripts/ci/build-cadastro-kaizen.sh` — `npm run ci` no plugin
- [ ] `scripts/homologacao/check-cadastro-kaizen.sh` — smoke: `remoteEntry.js` + `GET /records` com `TOKEN`
- [ ] `scripts/homologacao/check-cadastro-kaizen-api.sh` — E2E: create → get → update → delete → import dry_run
- [ ] Entrada no `docs/08-plugins/README.md` (CI + homologação)
- [ ] (Opcional) job no pipeline CI do repositório

**Critério de pronto:** scripts passam em dev com `TOKEN` exportado; falham de forma clara sem token ou sem container.

---

## Fase 6 — Revisões temporais + summary Postgres 📋

**Objetivo:** versionar alterações de kaizen (status, economia, datas) e fazer `GET /quality/kaizens/summary` calcular o passado de forma confiável a partir do Postgres.

**Especificação:** [ESPECIFICACAO-REVISOES.md](./ESPECIFICACAO-REVISOES.md)

> **Pré-requisito de design:** não migrar `summary` para Postgres **sem** revisões — sobrescrever a cabeça invalida ganhos e contagens históricas.

### Fase 6a — Schema e revisão automática

- [ ] Migration `V028__create_kaizen_revisions.sql`
- [ ] `KaizenRevisionRepository` + `KaizenRevisionService` (POST/PUT criam revisão; fecham `effective_until`)
- [ ] Backfill: revisão `1` para kaizens já importados
- [ ] `GET /records/{id}/revisions`, `GET /records/{id}/at?date=`
- [ ] Testes unitários de vigência e diff de campos gatilho

### Fase 6b — Cálculo temporal

- [ ] `KaizenTemporalSavingsCalculator` (ganhos por segmento de vigência no intervalo)
- [ ] Fixtures `kaizen_revision_regression_cases.py` (implantado jan → descontinuado mar; correção economia em jun)
- [ ] Paridade documentada com `_days_active_in_range` da planilha

### Fase 6c — Summary → Postgres

- [ ] `PostgresKaizenQueryRepository` implementando `KaizenQueryRepositoryPort` **usando revisões**
- [ ] Feature flag `KAIZEN_SUMMARY_SOURCE=postgres|sheets|dual`
- [ ] Testes comparando amostra Sheets vs Postgres (tolerância documentada)
- [ ] Atualizar `strategic-indicators-api/docs/QUALITY_INDICATORS.md`

### Fase 6d — UI histórico

- [ ] Campo «Vigente a partir de» no formulário quando status/economia mudam
- [ ] Timeline `KaizenRevisionTimeline` na edição

**Critério de pronto:** dashboard-quality exibe totais coerentes para meses passados após mudança de status/economia; `summary` com `postgres` não depende da planilha.

**Dependências:** Fase 4 (dados em prod); validação de negócio dos 21+ registros.

---

## Fase 7 — Integração dashboard-quality 📋

**Objetivo:** experiência coesa entre painel e cadastro.

**Entregáveis**

- [ ] Link «Cadastrar / editar» no dashboard apontando para `/apps/cadastro-kaizen` (quando usuário tem `cadastro-kaizen.manage`)
- [ ] (Opcional) Deep link por título/filial na listagem do cadastro
- [ ] Alinhar labels de status e tipos de economia entre dashboard e cadastro
- [ ] Remover ou marcar como legado aviso «dados da planilha» na UI do dashboard após Fase 6

**Critério de pronto:** fluxo documentado: usuário vê KPI no dashboard → abre cadastro → altera registro → KPI reflete após Fase 6.

---

## Fase 8 — Agente Minha DELPI 📋

**Objetivo:** chat e agentes consultam/operam kaizens cadastrados.

**Entregáveis**

- [ ] Registrar rotas `records` em `minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md`
- [ ] OpenAPI / `openapi_agent_metadata` para operações de cadastro (se exposto a agentes)
- [ ] Actions permitidas no agente de qualidade: `list_kaizen_records`, `get_kaizen_record` (leitura); escrita sob `cadastro-kaizen.manage`
- [ ] Casos em `chat_intelligence_regression_cases.py` para perguntas tipo «quantos kaizens implantados na filial 01?»
- [ ] Sincronizar catálogo gerado `_generated/api-delpi-openapi-catalog.md`

**Critério de pronto:** pergunta no chat retorna dados do Postgres, não da planilha.

**Dependência:** Fase 6 recomendada para uma única fonte de verdade.

---

## Fase 9 — Cutover planilha (desativação Sheets) 📋

**Objetivo:** planilha deixa de ser fonte operacional e analítica.

**Entregáveis**

- [ ] Data de corte acordada com qualidade
- [ ] Importação final + conferência de contagem (planilha ativa = registros PG não deletados)
- [ ] Congelar edição na planilha (processo humano) ou coluna `migrated=true`
- [ ] Remover dependência de `QUALITY_KAIZEN_SHEET_GID` em runtime (ou manter só backup/export)
- [ ] Comunicado + treinamento usuários
- [ ] (Opcional) campo `legacy_sheet_id` em `quality.kaizens` para rastreabilidade

**Critério de pronto:** nenhuma rota de produção lê Sheets para kaizen; planilha arquivada.

---

## Fase 10 — Evoluções UX e governança 📋

**Backlog priorizável**

| Item | Descrição |
|------|-----------|
| Export CSV/Excel | Listagem exportável para auditoria |
| Histórico de alterações | Coberto pela Fase 6 (revisões) — evoluir com `change_reason` e export |
| Anexos | Fotos/evidências do kaizen (padrão auditoria-5s NC) |
| Validação filial 02 | Dados reais filial SC na planilha |
| Paginação server-side | Substituir paginação client quando `total` > 200 |
| Bulk edit / status em lote | Operações em massa via API |
| Sincronização reversa | ❌ Não recomendado — Postgres é fonte após Fase 9 |
| OpenAPI público | Tags e exemplos no Swagger para todas as rotas `records` |

---

## Checklist go-live (resumo)

```text
[ ] Migrations quality aplicadas (prod)
[ ] Manifesto registrado Core API
[ ] RBAC view + manage atribuídos
[ ] remoteEntry.js e /records 200 em prod
[ ] Importação inicial validada pela qualidade
[ ] Comunicado: dashboard ainda usa Sheets até Fase 6
[ ] Runbook de suporte (README + este ROADMAP)
```

---

## Comandos úteis (dev)

```bash
# Stack mínima cadastro
cd infra
docker compose -f docker-compose.dev.yml --env-file .env up -d --build \
  postgres-plugins api-delpi cadastro-kaizen gateway

# Testes api-delpi (kaizen)
cd api-delpi
PYTHONPATH="../shared:.:." pytest \
  tests/unit/test_kaizen_savings_calculator.py \
  tests/unit/test_import_kaizens_from_sheet_use_case.py \
  tests/test_route_meta_smoke.py -k "kaizen" -q

# Build MFE
cd plugins/cadastro-kaizen && npm run ci
```

---

## Documentos relacionados

| Documento | Conteúdo |
|-----------|----------|
| [status-atual.md](./status-atual.md) | Snapshot rápido do que está pronto |
| [PLAYBOOK-EVOLUCAO-KAIZEN.md](./PLAYBOOK-EVOLUCAO-KAIZEN.md) | Evolução (modo visual/edição, evidências, revisões versionadas, campos ricos) — Fases 6+ |
| [plugins/cadastro-kaizen/README.md](../../../plugins/cadastro-kaizen/README.md) | Guia operacional |
| [plugins/cadastro-kaizen/docs/DOCUMENTACAO.md](../../../plugins/cadastro-kaizen/docs/DOCUMENTACAO.md) | Contratos HTTP e arquitetura |
| [api-delpi/docs/api/06-modulos-departamentais.md](../../../api-delpi/docs/api/06-modulos-departamentais.md) | Rotas qualidade |
| [plugins/dashboard-quality/docs/ROADMAP.md](../../../plugins/dashboard-quality/docs/ROADMAP.md) | Dashboard (leitura Sheets) |
| [strategic-indicators-api/docs/QUALITY_INDICATORS.md](../../../strategic-indicators-api/docs/QUALITY_INDICATORS.md) | Indicadores SI derivados de kaizen |

---

## Decisões registradas

| Data | Decisão |
|------|---------|
| 2026-06 | Cadastro operacional em Postgres; planilha permanece para dashboard até cutover |
| 2026-06 | Rotas de leitura Sheets em `/quality/kaizens/summary`; CRUD em `/quality/kaizens/records` |
| 2026-06 | Importação via API (`import-from-sheet`), não script offline em produção |
| 2026-06 | IDs legados da planilha com `/` suportados via `{kaizen_id:path}` |

---

## Próxima ação recomendada

**Fase 4 — Produção operacional:**

1. Registrar manifesto na Core API de staging/produção.
2. Atribuir permissões aos perfis de qualidade.
3. Rodar importação `dry_run` e depois importação real em staging.
4. Validar com usuário piloto (listar, editar um kaizen, criar novo).

Em paralelo, planejar **Fase 5** (scripts `check-cadastro-kaizen*.sh`) antes do merge amplo em produção.
