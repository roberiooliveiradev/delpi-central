# Migrations — Strategic Indicators

Scripts SQL versionados para o schema **`strategic_indicators`** no banco **postgres-plugins** (`PLUGINS_DB_*`).

Padrão: `V###__descricao.sql`

**Fonte oficial:** apenas `strategic-indicators-api/migrations/`.  
O diretório `api-delpi/migrations/plugins/strategic-indicators/` é legado — não adicionar versões novas lá.

## Versões

| Versão | Arquivo | Conteúdo |
|--------|---------|----------|
| V001 | schema + extensions | Schema `strategic_indicators`, extensões |
| V002 | module_settings | Configurações do módulo |
| V003 | settings_audit | Auditoria de settings |
| V004 | departments | Departamentos |
| V005 | department_indicators | Indicadores por departamento |
| V006 | indicator_goals | Metas versionadas |
| V007 | change_requests | Solicitações de alteração |
| V008 | change_request_comments | Comentários |
| V009 | seed admin | Estrutura padrão + metas (ano corrente no seed) |
| V010 | period_scores | Scores por competência/escopo (indicadores materializados) |
| V011 | refresh_state | Estado do job periódico de refresh (5 min) |
| V012 | calculation_snapshots | Insumos do cálculo (catálogo, metas, medições) por competência/escopo |
| V013 | indicator_goals unique | Uma meta ativa por indicador/ano (índice parcial) |
| V014 | catalog_inputs_hash | Fingerprint do catálogo em materializados |
| V015 | commercial restructure | Catálogo Comercial: pesos/metas, OTD pedidos, % ROL novos negócios |
| V016 | goal_scope_branch | Metas por consolidado / filial 01 / 02 (todos indicadores `consolidated`) |
| V017 | scope all consolidated | Reaplica `supports_branch_goals` para todo `scope_type = consolidated` |
| V018 | quality_branch_goals_2026 | Metas Qualidade 01/02; inativa metas consolidadas legadas |
| V019 | hr_branch_goals_and_catalog | Catálogo RH (6 indicadores), metas 2026 por filial, PDI contagem |
| V020 | hr_quality_average_of_units | `aggregation_mode = average_of_units` para RH e Qualidade |

## Comandos

Na raiz do monorepo:

```bash
export PYTHONPATH="$(pwd)/strategic-indicators-api:$(pwd)/shared"
python strategic-indicators-api/scripts/run_migrations.py status
python strategic-indicators-api/scripts/run_migrations.py up
```

No container:

```bash
docker exec delpi-strategic-indicators-api python3 scripts/run_migrations.py up
```

## Startup automático

`SI_RUN_MIGRATIONS_ON_STARTUP=true` aplica migrations pendentes antes do warm-up (recomendado em dev).

## Reset (cuidado)

```bash
python strategic-indicators-api/scripts/run_migrations.py reset
```

Remove o schema `strategic_indicators` inteiro.
