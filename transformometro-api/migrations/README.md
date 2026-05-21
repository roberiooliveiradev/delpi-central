# Migrations — Transformômetro

Padrão de nome: `V###__descricao.sql`  
Schema: **`transformometro`** no Postgres **postgres-plugins** (`PLUGINS_DB_*`).

## Versões

| Versão | Arquivo | Conteúdo |
|--------|---------|----------|
| V001 | `V001__create_transformometro_schema.sql` | Schema + `schema_migrations` |
| V002 | `V002__create_transformometro_tables.sql` | Processos, revisões, medições, investimentos, recursos, vínculos, `audit_logs` |
| V003 | `V003__create_dashboard_calculos.sql` | Tabela derivada `dashboard_calculos` |
| V004 | `V004__processo_familia_agrupador.sql` | `familia_processo`, `agrupador_ferramenta` em `processos` |
| V005 | `V005__revisao_status_aprovacao.sql` | Workflow: `status_aprovacao`, `aprovado_em`, `aprovado_por_email`, `motivo_rejeicao` |

Revisões existentes na V005 recebem `status_aprovacao = 'aprovada'`; novas entram como `rascunho`.

## Comandos

Na raiz do monorepo (com `PLUGINS_DB_*` exportadas):

```bash
python -m tm_app.infrastructure.persistence.plugins.migrations_runner status
python -m tm_app.infrastructure.persistence.plugins.migrations_runner up
```

No container:

```bash
docker exec delpi-transformometro-api python -m tm_app.infrastructure.persistence.plugins.migrations_runner status
docker exec delpi-transformometro-api python -m tm_app.infrastructure.persistence.plugins.migrations_runner up
```

Startup automático: `TM_RUN_MIGRATIONS_ON_STARTUP=true` (padrão no `infra/docker-compose.yml` para `transformometro-api`).
