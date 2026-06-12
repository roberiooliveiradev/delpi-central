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

## Migrations disponíveis

V001–V010 (legado) · **V011–V018** (Playbook 18 S1–S8)

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

## Integração Transforma+ (S9)

- **Listagem S2S:** uma linha por instância operacional; `id` = `instancia_id` (UUID).
- **Campos aditivos em `items[]`:** `processo_id`, `instancia_id`, `codigo_processo` (paridade api-delpi).
- **Filtro `id`:** aceita UUID de instância, `processo_id` ou `codigo_processo`.
- **Backup JSON 1.1:** bundles `filiais` e `processo_instancias` no export/import.

Módulo canônico: `tm_app/application/integrations/engineering_transforma_mais.py`.

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
| GET/POST | `/transformometro/processos/{id}/instancias` | Par operacional `(filial × setor)` |
| GET | `/transformometro/instancias/{id}` | Detalhe com `codigo_filial`, `codigo_setor` |
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
```

## Próximo (pós-Playbook 18 API)

| Item | Foco |
|--------|------|
| **Docs modelo** | Atualizar `PLAYBOOK-MODELAGEM.md`, `ARCHITECTURE.md`, `regras-de-calculo.md` conforme §9 do playbook |

## MFE Playbook §9 (jun/2026)

| Entrega | Status |
|---------|--------|
| Formulário mestre sem `filial_id`/`setor_id` no edit | ✅ `ProcessoFormFields` + `ProcessoUpdateBody` |
| Painel instâncias + replicar timeline | ✅ `ProcessoInstanciasPanel` |
| URL canônica revisão + redirect legado | ✅ `routeParser` + `ProcessoDetailPage` |
| Dashboard toggle visão (`view`) + `access_scope` | ✅ `DashboardPage` + `dashboardViewScope.ts` |
| Tipos/API instância, `Revisao.instancia_id` | ✅ `transformometroApi.ts` |
| Create processo com primeira instância | ✅ `createPayloadFromProcessoForm` |

Módulos: `plugins/transformometro/src/utils/dashboardViewScope.ts`, `ProcessoInstanciasPanel.tsx`, `routeParser.ts`.

## Testes

```bash
./scripts/ci-transformometro-api.sh
```

Suíte inclui `test_dashboard_cache_denorm_service`, `test_shared_resource_scope_service`, `test_dashboard_calculator_escopo_recurso`, `test_filial_access_scope_service`.
