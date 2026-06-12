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

## Migrations disponíveis

V001–V010 (legado) · **V011–V017** (Playbook 18 S1–S6)

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
| POST | `/transformometro/processos` | Corpo ainda aceita `filial_id`/`setor_id` → cria **instância** |

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

## Próximo (S8+)

| Sprint | Foco |
|--------|------|
| **S8** | Duplicar instância (deprecar duplicar processo) |
| **S9–S10** | api-delpi, RBAC |

## Testes

```bash
./scripts/ci-transformometro-api.sh
```

Suíte inclui `test_dashboard_cache_denorm_service`, `test_shared_resource_scope_service`, `test_dashboard_calculator_escopo_recurso`.
