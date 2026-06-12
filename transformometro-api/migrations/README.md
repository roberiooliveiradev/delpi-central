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
| V005 | `V005__revisao_status_aprovacao.sql` | Colunas legado: `status_aprovacao`, `aprovado_em`, `aprovado_por_email`, `motivo_rejeicao` |
| V006 | `V006__drop_workflow_gate.sql` | Normaliza revisões para `aprovada`; default de novas revisões = `aprovada` (sem workflow) |
| V007 | `V007__recurso_custos_vigencia.sql` | Histórico de `valor_mensal` por vigência (`recurso_custos`) + backfill do catálogo |
| V008 | `V008__recurso_base_competencia.sql` | `base_competencia` em recursos compartilhados |
| V009 | `V009__processo_competencia_snapshot_view.sql` | View `processo_competencia_snapshot` (agregação processo × competência) |
| V010 | `V010__create_setores.sql` | Catálogo de setores + `setor_filiais` |
| V011 | `V011__create_filiais.sql` | Catálogo de filiais (`filial_id UUID`, `codigo_filial`) — **sem seed** |

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
