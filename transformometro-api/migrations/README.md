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
| V012 | `V012__setores_uuid.sql` | Setores com PK UUID + `codigo_setor`; `setor_filiais` com FKs UUID |
| V013 | `V013__create_processo_instancias.sql` | Instâncias operacionais `(processo, filial, setor)` |
| V014 | `V014__revisoes_instancia_id.sql` | `revisoes.instancia_id` + backfill a partir de processos legados |
| V015 | `V015__processo_mestre.sql` | Remove `filial_id`/`setor_id` de `processos` (par em `processo_instancias`) |
| V016 | `V016__recurso_escopo_recurso.sql` | `escopo_recurso` em recursos (`empresa` \| `filial` \| `setor`) |
| V017 | `V017__dashboard_calculos_uuid.sql` | Cache `dashboard_calculos` PK UUID + FKs instância/filial/setor; view snapshot recriada |
| V018 | `V018__revisoes_unique_por_instancia.sql` | Unique `(instancia_id, versao_revisao)`; chave por instância |
| V019 | `V019__processo_instancia_setores.sql` | Amarração N:N instância × setores; instância = processo × filial (ou todas ativas) |
| V020 | `V020__dashboard_integration_views.sql` | Views `dashboard_competencia_evolucao` e `instancia_operacional_snapshot` (leitura rápida dashboard + api-delpi) |
| V024 | `V024__revisao_evidencias.sql` | Evidências por revisão (metadado Postgres + binário em volume) |
| V025 | `V025__audit_logs_user_name.sql` | `user_name` em `audit_logs` para linha do tempo |
| V026 | `V026__processo_diagramas.sql` | Diagrama macro `flowchart_v1` por processo-mestre |
| V027 | `V027__instancia_diagrama_escopo.sql` | Escopo de nós do macro por instância |
| V028 | `V028__revisao_diagrama_overlays.sql` | Overlay as-is/to-be por revisão |
| V029 | `V029__collaboration_presence.sql` | Presença colaborativa e travas soft por seção (`collaboration_presence`) |
| V030 | `V030__processo_decomposicao.sql` | Árvore WBS (`processo_decomposicao`) no processo-mestre |
| V031 | `V031__instancia_decomposicao_escopo.sql` | Escopo de nós WBS por melhoria (`instancia_decomposicao_escopo`) |
| V032 | `V032__revisao_decomposicao_overlays.sql` | Overlay WBS as-is/to-be por revisão |
| V033 | `V033__instancia_contexto.sql` | Contexto operacional da melhoria (metadados de escopo) |
| V034 | `V034__melhoria_campos_e_escopo_livre.sql` | Campos rollout em `processo_instancias`; remove unique `(processo, filial)` |
| V035 | `V035__revisao_referencia_comparacao.sql` | `revisoes.revisao_referencia_id` — referência de comparação entre revisões |
| V038 | `V038__revisao_matriz_impacto_esforco.sql` | `revisoes.matriz_impacto_esforco` JSONB — overrides Playbook 21 |
| V039 | `V039__beneficio_calculo_categoria.sql` | `revisoes.beneficio_calculo_categoria` + colunas de capacidade em `dashboard_calculos` (Playbook 22; só DDL) |

## Notas V019–V020

- **V019** remove `setor_id` de `processo_instancias`; setores passam por `processo_instancia_setores`. Consolida duplicatas `(processo, filial)` usando `(MIN(instancia_id::text))::uuid` — Postgres não suporta `MIN(uuid)` nativo.
- **V020** depende de V019 (`todas_filiais_ativas`). Views leem `dashboard_calculos`; executar recalc após aplicar.
- Se a API não sobe no boot: `docker logs delpi-transformometro-api --tail 50` e conferir migration pendente com `migrations_runner status`.

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
