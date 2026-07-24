# Backup JSON e pacote — Transformômetro

Exportação e importação via `/transformometro/data/export` (JSON), `/transformometro/data/export/package` (pacote `.tmbackup.zip`) e rotas `/import/*`.

## Versão do pacote

| `schema_version` | Mudança |
|------------------|---------|
| `1.0` | Processos, revisões, medições, investimentos, recursos |
| `1.1` | Inclui `setores`, `setor_filiais` e valida FK `processos.setor_id` → `setores` |
| `1.2` | Diagramas (PB19), decomposição WBS (PB20), `contexto` de instância, `revisao_evidencias` |
| `1.3` | `processo_arquivos` (metadados + binários no ZIP) |
| `1.4` | Escopo mestre (`processo_filiais` / `processo_setores` / `todas_filiais_ativas`), matriz e `revisao_referencia_id`, export canônico de instâncias (melhoria/contexto) |

Importação aceita `schema_version` **1.0–1.4** (chaves ausentes em versões antigas são tratadas como listas vazias).

## Pacote `.tmbackup.zip` (recomendado)

```
transformometro-backup-YYYYMMDD-HHMMSS.tmbackup.zip
├── manifest.json
├── cadastro.json
├── evidencias/
│   └── {revisao_id}/
│       └── {nome_armazenado}
└── processo_arquivos/
    └── {processo_id}/
        └── {nome_armazenado}
```

| Rota | Método | Descrição |
|------|--------|-----------|
| `/transformometro/data/export/package` | GET | Download do pacote completo |
| `/transformometro/data/import/package/preview` | POST multipart | Pré-visualização (`file`, `mode`, `import_format`) |
| `/transformometro/data/import/package/apply` | POST multipart | Aplica cadastro + restaura anexos |

Limite padrão: `TM_BACKUP_PACKAGE_MAX_BYTES` (500 MB). Modo `replace` limpa volumes de evidências e arquivos do processo antes de restaurar.

O export JSON (`GET /export`) **não** inclui binários — só metadados em `revisao_evidencias` e `processo_arquivos`.

## Formatos de importação (`import_format`)

| Valor | Uso |
|-------|-----|
| `auto` (padrão) | Detecta legado vs Playbook 18; se não reconhecer, retorna incompatibilidade |
| `legacy` | Backup **1.1** com `processos.filial_id` / `setor_id` |
| `modern` | Backup com `filiais`, `processo_instancias` e `revisoes.instancia_id` |

## Chaves do bundle (cadastro)

1. **`filiais`**, **`setores`**, **`setor_filiais`**
2. **`processos`** — inclui `todas_filiais_ativas` (escopo mestre)
3. **`processo_filiais`**, **`processo_setores`** — vínculos N:N do processo-mestre (códigos de filial/setor)
4. **`processo_instancias`** — melhoria/contexto/fase/prioridade/responsável/datas
5. **`processo_instancia_setores`**
6. **`recursos_compartilhados`**, **`revisoes`** (inclui `revisao_referencia_id`, `matriz_impacto_esforco`), **`medicoes`**, **`investimentos`**, **`recurso_custos`**, **`revisao_recursos_compartilhados`**
7. Diagramas e WBS: `processo_diagramas`, `instancia_diagrama_escopos`, `revisao_diagrama_overlays`, `processo_decomposicao`, `instancia_decomposicao_escopos`, `revisao_decomposicao_overlays`
8. Anexos (meta): **`revisao_evidencias`**, **`processo_arquivos`**

### Fora do backup (intencional)

| Dado | Motivo |
|------|--------|
| `dashboard_calculos` | Cache derivado — recalculado no import |
| Views de snapshot / evolução | Derivadas |
| `collaboration_presence` | Estado realtime efêmero |
| `audit_logs` | Histórico operacional; não faz parte do restore de cadastro |
| Preferências UI (`localStorage`) | UX local do browser |

## Modos de importação

| Modo | Comportamento |
|------|----------------|
| `replace` | Trunca cadastro e volumes de anexos; insere o pacote; recalcula dashboard |
| `merge` | Upsert por PK; vínculos de escopo (`setor_filiais`, `processo_filiais`, `processo_setores`) são sincronizados (replace do conjunto) |

## CLI

```bash
cd transformometro-api
set -a && source ../infra/.env && set +a

python scripts/import_cadastro_json.py export -o fixtures/cadastro/backup.json
python scripts/import_cadastro_json.py preview -i fixtures/cadastro/backup.json --mode replace --format auto
python scripts/import_cadastro_json.py apply -i fixtures/cadastro/backup-legado.json --mode replace --format legacy --yes
```
