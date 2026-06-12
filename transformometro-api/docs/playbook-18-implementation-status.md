# Playbook 18 — status de implementação (API)

Referência: [`docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-18-instancias-filial-setor-escopo.md`](../../docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-18-instancias-filial-setor-escopo.md)

Última atualização: jun/2026

## Sprints concluídos

| Sprint | Migrations | Entrega |
|--------|------------|---------|
| **S1 — Filiais UUID** | V011 | Tabela `filiais`, CRUD `/filiais`, options do banco, `bootstrap_filiais_from_cadastro.py` |
| **S2 — Setores UUID** | V012 | PK UUID + `codigo_setor`, `setor_filiais` com FKs UUID, import/export JSON 1.1 preservado |
| **S3 — Instâncias** | V013–V014 | `processo_instancias`, `revisoes.instancia_id`, backfill legado, rotas de instância |
| **S4 — Processo mestre** | V015 | Remove `filial_id`/`setor_id` de `processos`; create API grava instância |
| **S5 — Escopo híbrido** | V016 | `escopo_recurso` + `SharedResourceScopeService` no calculador |
| **S6 — Cache dashboard** | V017 | `dashboard_calculos` PK UUID, FKs instância/filial/setor, denorm `codigo_*`, view snapshot |
| **S7 — Visões dashboard** | — | `DashboardViewScopeService`, query `view=consolidated\|filial\|department` |
| **S8 — Duplicar instância** | V018 | `POST /instancias/{id}/duplicar`; depreca `POST /processos/{id}/duplicar` |
| **S9 — Integração api-delpi** | — | Listagem por instância (`id` = `instancia_id`); backup `filiais` + `processo_instancias` |
| **S10 — RBAC filial** | — | `FilialAccessScopeService`, permissões escopadas, filtro server-side |
| **S11 — Instância × N setores** | V019 | Junction `processo_instancia_setores`; instância = processo × filial ou `todas_filiais_ativas`; CRUD filiais/instâncias no MFE |
| **S12 — Leitura rápida (cache/views)** | V020 | Views SQL + rotas snapshot; Transforma+ S2S lê `dashboard_calculos` quando populado |

## Migrations disponíveis

V001–V010 (legado) · **V011–V020** (Playbook 18 S1–S12)

Ver [migrations/README.md](../migrations/README.md).

## Cache dashboard (`dashboard_calculos`)

| Campo | Tipo | Notas |
|-------|------|-------|
| `dashboard_calculo_id` | UUID PK | Gerado no insert; upsert por `(revisao_id, competencia)` |
| `instancia_id` | UUID FK | Via revisão → instância operacional |
| `filial_id` / `setor_id` | UUID FK | Denormalizados da instância |
| `codigo_filial` / `codigo_setor` | VARCHAR | Filtros MFE (`01`, `engenharia`) e export |

Módulo canônico: `tm_app/domain/services/dashboard_cache_denorm_service.py` · consumido por `DashboardCalculatorService` e `DashboardCalculoRepository`.

**Pós-V017:** executar recalc full (`POST /dashboard/recalc` ou job interno) — a migration trunca o cache.

View `processo_competencia_snapshot` usa `codigo_*` como `filial_id`/`setor_id` expostos (compat MFE).

### Views de integração (V020)

| View | Uso |
|------|-----|
| `dashboard_competencia_evolucao` | Evolução mensal agregada (base de `query_evolucao`) |
| `instancia_operacional_snapshot` | Uma linha por instância com economia diária, payback e implantação (última competência materializada) |

Rotas snapshot:

- `GET /transformometro/dashboard/snapshot/instancias` — leitura via view acima
- Metadados em `GET /transformometro/dashboard/snapshot/meta` (`evolucao_view`, `instancia_view`)

**Pós-V020:** exige V019 aplicada (`todas_filiais_ativas` em `processo_instancias`). Recalcular cache após migrations.

## Visões analíticas (`view`)

| Valor | Comportamento |
|-------|----------------|
| `consolidated` (default) | Sem filtro de filial/setor |
| `filial` | Exige `filial_id` (código ou UUID) |
| `department` | Exige `filial_id` + `setor_id` |

Módulo canônico: `tm_app/application/services/dashboard_view_scope_service.py` · usado por live, snapshot, export e rotas `/dashboard/*`.

Inferência legada: só `filial_id` → filial; `filial_id` + `setor_id` → departamento; nenhum → consolidado.

## Duplicar instância (S8)

- **Canônico:** `InstanciaDuplicateService` + `POST /instancias/{id}/duplicar` com `{ filial_id, setor_id }` destino.
- Copia revisões, medições, investimentos e vínculos para nova instância do **mesmo processo-mestre**.
- **V018:** unique `(instancia_id, versao_revisao)`; `chave_unica_processo_revisao` = `{instancia_id}|{versao}`.
- **Legado:** `POST /processos/{id}/duplicar` mantido com header `Deprecation` e campo `deprecated` na resposta.

## Integração Transforma+ (S9 + S12)

- **Listagem S2S:** uma linha por instância operacional; `id` = `instancia_id` (UUID).
- **Campos aditivos em `items[]`:** `processo_id`, `instancia_id`, `codigo_processo` (paridade api-delpi).
- **Filtro `id`:** aceita UUID de instância, `processo_id` ou `codigo_processo`.
- **Backup JSON 1.1:** bundles `filiais`, `processo_instancias` e `processo_instancia_setores` no export/import.
- **Leitura rápida (S12):** com `dashboard_calculos` populado, `EngineeringTransformaMaisService` lê cache/views em vez de `load_raw()` + cálculo live (~1s+). Fallback live se cache vazio.

Módulo canônico: `tm_app/application/integrations/engineering_transforma_mais.py` · repositório `DashboardCalculoRepository.query_instancias_operacionais` / `query_resumo` / `query_evolucao`.

## Instância × N setores (S11 — V019)

| Conceito | Regra |
|----------|-------|
| Instância | `(processo_id, filial_id)` **ou** `todas_filiais_ativas = true` (filial nullable) |
| Setores | N:N em `processo_instancia_setores` |
| Revisões | Timeline na **instância** (compartilhada entre setores amarrados) |
| Consolidação legado | Duplicatas `(processo, filial)` mescladas; `MIN(instancia_id::text)::uuid` escolhe canônica |

Rotas CRUD adicionais:

| Método | Rota | Notas |
|--------|------|-------|
| PUT/DELETE | `/transformometro/instancias/{id}` | Atualiza setores, filial, rótulo, status |
| GET/POST/PUT/DELETE | `/transformometro/filiais` | CRUD filial (MFE `FiliaisPage`) |

Módulo canônico: `ProcessoInstanciaRepository` · junction sync em `_sync_setores`.

## RBAC por filial (S10)

Permissões escopadas (manifesto `transformometro.manifest.json`):

| Permissão | Efeito |
|-----------|--------|
| `transformometro.view.filial-01` / `filial-02` | Leitura server-side filtrada à filial |
| `transformometro.view.consolidated` | Visão consolidada do dashboard (com escopo filial ativo) |
| `transformometro.manage.filial-01` / `filial-02` | CRUD de instâncias/processos na filial |

**Compatibilidade:** usuários só com permissões globais legadas (`transformometro.view`, `transformometro.processes.manage`, …) permanecem **sem restrição de filial** até receberem permissões escopadas no Keycloak.

Módulo canônico: `tm_app/application/services/filial_access_scope_service.py` · helpers HTTP em `tm_app/interface/http/filial_access_http.py`.

Rotas S2S (`/integrations/engineering/transforma-mais/*`) e service token **não** aplicam RBAC filial.

`GET /options` expõe `access_scope` (`mode`, `allowed_filiais`, `can_view_consolidated`).

## Escopo de recurso (`escopo_recurso`)

| Valor | Pool de rateio |
|-------|----------------|
| `empresa` | Todos os vínculos elegíveis (padrão legado) |
| `filial` | Vínculos da mesma filial da instância da revisão |
| `setor` | Vínculos do mesmo par filial × setor |

Módulo canônico: `tm_app/domain/services/shared_resource_scope_service.py` · consumido por `DashboardCalculatorService._get_eligible_links_for_resource`.

Campo exposto em `GET /options` (`escopo_recurso`) e CRUD `/recursos-compartilhados`.

## Rotas novas (S1–S4)

| Método | Rota | Notas |
|--------|------|-------|
| GET/POST | `/transformometro/filiais` | CRUD filial |
| GET/PUT/DELETE | `/transformometro/filiais/{id}` | Aceita UUID ou `codigo_filial` |
| GET/POST | `/transformometro/processos/{id}/instancias` | Instância operacional (filial + N setores) |
| GET | `/transformometro/instancias/{id}` | Detalhe com `codigo_filial`, setores[] |
| PUT/DELETE | `/transformometro/instancias/{id}` | Editar setores/filial ou soft-delete (S11) |
| POST | `/transformometro/instancias/{id}/duplicar` | Copia timeline para outro par filial × setor (S8) |
| POST | `/transformometro/processos` | Corpo ainda aceita `filial_id`/`setor_id` → cria **instância** |
| POST | `/transformometro/processos/{id}/duplicar` | **Deprecado** — header `Deprecation: true` |

## Compatibilidade MFE / JSON 1.1

- **`GET /options`:** `filiais[].id` e `setores[].id` permanecem **códigos de negócio**; campos UUID adicionais: `filial_id`, `setor_id`.
- **Import cadastro:** `processos.filial_id`/`setor_id` no JSON criam instância no `apply`.
- **Recursos sem `escopo_recurso` no JSON:** default `empresa` (sem mudança numérica).
- **Queries cache/export:** filtro `filial_id=01` usa `codigo_filial`; UUID resolve FK `filial_id`.

## Procedimento pós-migration

```bash
cd transformometro-api
set -a && source ../infra/.env && set +a
python -m tm_app.infrastructure.persistence.plugins.migrations_runner up
python scripts/bootstrap_filiais_from_cadastro.py -i fixtures/cadastro/transformometro-cadastro-YYYYMMDD.json
# Após V017: recalcular cache dashboard (full)
# Após V019–V020: recalcular cache (views dependem de dashboard_calculos)
```

## Legado fora do runtime (jun/2026)

| Artefato | Situação |
|----------|----------|
| Planilha Google Sheets | Não alimenta API/SI/MFE — desligar escrita (ops) |
| `api-delpi/.../google_sheets/transforma_mais/process_repository.py` | Código morto — composer usa `TransformometroTransformaMaisGateway` |
| `TRANSFORMA_MAIS_SHEET_*` / `TRANSFORMA_MAIS_DATA_SOURCE` | Config órfã na api-delpi |
| `ProcessSummaryCalculator` (SI) | Removido — ver `strategic-indicators-api/docs/LEGACY_CLEANUP.md` |
| Rotas `/engineering/transforma-mais/*` | Contrato HTTP **ativo**; backend = Postgres via S2S |

Consumidores ativos: `plugins/transformometro` (cadastro), `dashboard-engineering/TransformaPage` (read-only), SI (KPI), chat (rotas api-delpi).

## Próximo (pós-Playbook 18)

| Item | Foco |
|--------|------|
| **Deploy produção** | Runbook em [status-atual.md](../../docs/12-roadmap-e-evolucao/transformometro-app/status-atual.md) |
| **RBAC Keycloak** | Atribuir permissões escopadas onde necessário |
| **Limpeza Fase 6** | Remover código Sheets morto e env vars órfãs na api-delpi — [ROADMAP.md](../../docs/12-roadmap-e-evolucao/transformometro-app/ROADMAP.md) |

## Documentação (índice)

| Documento | Conteúdo |
|-----------|----------|
| [PLAYBOOK-18](../../docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-18-instancias-filial-setor-escopo.md) | Plano e checklist §9 |
| [PLAYBOOK-MODELAGEM](../../docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-MODELAGEM.md) | Entidades, instâncias, escopo, pipeline |
| [ARCHITECTURE](../../docs/12-roadmap-e-evolucao/transformometro-app/ARCHITECTURE.md) | Diagramas, rotas, RBAC, MFE |
| [regras-de-calculo.md](regras-de-calculo.md) | Fórmulas + `escopo_recurso` + visões |
| [OPERATIONS](../../docs/12-roadmap-e-evolucao/transformometro-app/OPERATIONS.md) | Runbook deploy e troubleshooting |
| [migrations/README.md](../migrations/README.md) | V001–V020 |

## MFE Playbook §9 (jun/2026)

| Entrega | Status |
|---------|--------|
| Formulário mestre sem `filial_id`/`setor_id` no edit | ✅ `ProcessoFormFields` + `ProcessoUpdateBody` |
| Painel instâncias + replicar timeline | ✅ `ProcessoInstanciasPanel` (multi-setor, editar/excluir) |
| Página Filiais (CRUD) | ✅ `FiliaisPage` + rota `/filiais` |
| URL canônica revisão + redirect legado | ✅ `routeParser` + `ProcessoDetailPage` |
| Dashboard toggle visão (`view`) + `access_scope` | ✅ `DashboardPage` + `dashboardViewScope.ts` |
| Tipos/API instância, `Revisao.instancia_id` | ✅ `transformometroApi.ts` |
| Create processo com primeira instância | ✅ `createPayloadFromProcessoForm` |
| Setores: `codigo_setor` na UI (UUID só na API) | ✅ `setorCatalogForm` |
| Recursos: campo `escopo_recurso` no formulário | ✅ `recursoCatalogForm` + `RecursoCatalogFormFields` |
| Doc `regras-de-calculo.md` § escopo recurso | ✅ alinhado a `SharedResourceScopeService` |

Módulos: `plugins/transformometro/src/utils/dashboardViewScope.ts`, `ProcessoInstanciasPanel.tsx`, `routeParser.ts`.

## Testes

```bash
./scripts/ci-transformometro-api.sh
```

Suíte inclui `test_dashboard_cache_denorm_service`, `test_shared_resource_scope_service`, `test_dashboard_calculator_escopo_recurso`, `test_filial_access_scope_service`.
