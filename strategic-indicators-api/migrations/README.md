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
| V028 | period_scores_versions | Até 3 versões por escopo/competência (`version_number`, `is_clean`) |
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
| V021 | per_unit_branch_goals | `supports_branch_goals` em `per_unit`; duplica metas consolidadas de Produção para filiais 01 e 02 |
| V022 | supplies_average_of_units | `aggregation_mode = average_of_units` para Suprimentos |
| V023 | supplies_branch_goals_2026 | Metas 2026 Suprimentos: duplica consolidado → Filial 01/02 (indicadores ativos) |
| V024 | department_aggregation_alignment | Comercial/Engenharia `consolidated`; Produção/Suprimentos `average_of_units` |
| V025 | zero_monthly_curve_goal_value | Zera `goal_value` em metas `monthly_curve` (meta só na curva mensal) |
| V026 | commercial_per_unit_restructure | Comercial `average_of_units`; `commercial-rol` único; inativa rol-matrix/branch |

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

Se o startup falhar com **checksum divergente** em migration já aplicada (ex.: V028 tornada idempotente após o `up`):

```bash
docker stop delpi-strategic-indicators-api   # se estiver em restart loop
docker run --rm --network infra_delpi-network \
  -v "$(pwd)/strategic-indicators-api:/app" \
  --env-file infra/.env \
  -e PLUGINS_DB_HOST=postgres-plugins \
  infra-strategic-indicators-api python3 scripts/run_migrations.py repair-checksums
docker start delpi-strategic-indicators-api
```

## Startup automático

`SI_RUN_MIGRATIONS_ON_STARTUP=true` aplica migrations pendentes antes do warm-up (recomendado em dev).

## Reset (cuidado)

```bash
python strategic-indicators-api/scripts/run_migrations.py reset
```

Remove o schema `strategic_indicators` inteiro.
