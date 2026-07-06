# Backup JSON e pacote — Transformômetro

Exportação e importação via `/transformometro/data/export` (JSON), `/transformometro/data/export/package` (pacote `.tmbackup.zip`) e rotas `/import/*`.

## Versão do pacote

| `schema_version` | Mudança |
|------------------|---------|
| `1.0` | Processos, revisões, medições, investimentos, recursos |
| `1.1` | Inclui `setores`, `setor_filiais` e valida FK `processos.setor_id` → `setores` |
| `1.2` | Diagramas (PB19), decomposição WBS (PB20), `contexto` de instância, `revisao_evidencias` |

Importação aceita `schema_version` **1.1** ou **1.2** (chaves ausentes em 1.1 são tratadas como listas vazias).

## Pacote `.tmbackup.zip` (recomendado)

```
transformometro-backup-YYYYMMDD-HHMMSS.tmbackup.zip
├── manifest.json       # formato, schema, SHA-256 por arquivo
├── cadastro.json       # bundle JSON (schema 1.2)
└── evidencias/
    └── {revisao_id}/
        └── {nome_armazenado}
```

| Rota | Método | Descrição |
|------|--------|-----------|
| `/transformometro/data/export/package` | GET | Download do pacote completo |
| `/transformometro/data/import/package/preview` | POST multipart | Pré-visualização (`file`, `mode`, `import_format`) |
| `/transformometro/data/import/package/apply` | POST multipart | Aplica cadastro + restaura evidências |

Limite padrão: `TM_BACKUP_PACKAGE_MAX_BYTES` (500 MB). Modo `replace` apaga evidências no volume antes de restaurar o pacote.

O export JSON (`GET /export`) **não** inclui binários de evidência — só metadados em `revisao_evidencias` quando exportado via pacote ou após upgrade 1.2.

## Formatos de importação (`import_format`)

| Valor | Uso |
|-------|-----|
| `auto` (padrão) | Detecta legado vs Playbook 18 pelo conteúdo do JSON; se não reconhecer, retorna **incompatibilidade** (não tenta importar como moderno por padrão) |
| `legacy` | Backup **1.1** com `processos.filial_id` / `setor_id`, sem `processo_instancias` ou `revisoes.instancia_id` |
| `modern` | Backup **Playbook 18** com `filiais`, `processo_instancias` e `revisoes.instancia_id` |

### Legado → Playbook 18

Na importação `legacy` (ou `auto` quando detectado), a API:

1. Cria **filiais sintéticas** a partir dos códigos referenciados (`processos`, `setor_filiais`).
2. Gera **instâncias de processo** (processo × filial × setor).
3. Preenche **`revisoes.instancia_id`** com a instância do processo.
4. Normaliza setores com UUID determinístico quando necessário.

O export atual inclui `"import_format": "modern"` no JSON.

## Chaves do bundle

Ordem lógica de dependência:

1. **`filiais`** — cadastro de filiais (Playbook 18; gerado na importação legada)
2. **`setores`** — cadastro de setores (`setor_id`, `nome_setor`, `status_setor`, …)
3. **`setor_filiais`** — vínculos N:N (`setor_id`, `filial_id`); substituídos integralmente na importação
4. **`processos`** — FK `setor_id` obrigatória e referenciada em `setores`
5. **`processo_instancias`** — instância operacional (processo × filial × setor **ou** multi-unidade)
6. **`processo_instancia_setores`** — vínculos N:N instância ↔ setor (`instancia_id`, `setor_id`)
7. **`recursos_compartilhados`**, **`revisoes`** (com `instancia_id`), **`medicoes`**, **`investimentos`**, **`recurso_custos`**, **`revisao_recursos_compartilhados`**
8. **`processo_diagramas`** — macro `flowchart_v1` por `processo_id` (Playbook 19, V026)
9. **`instancia_diagrama_escopos`** — escopo de nós por `instancia_id` (V027)
10. **`revisao_diagrama_overlays`** — overlay as-is/to-be por `revisao_id` (V028)
11. **`processo_decomposicao`**, **`instancia_decomposicao_escopos`**, **`revisao_decomposicao_overlays`** — mapeamento WBS (PB20, V030–V032)
12. **`revisao_evidencias`** — metadados de evidências por revisão (V024); binários só no pacote `.tmbackup.zip`

Diagramas e decomposição dependem de `processos` → `processo_instancias` → `revisoes` na importação (FK validada no preview).

### Instância multi-unidade (`todas_filiais_ativas`)

| Campo | Regra |
|-------|--------|
| `todas_filiais_ativas` | `true` quando a mesma timeline vale para **todas** as filiais ativas |
| `filial_id` | **Nullable** quando `todas_filiais_ativas = true` (validação de import aceita ausência de FK) |
| `processo_instancia_setores` | Obrigatório amarrar setores à instância; pares `(instancia_id, setor_id)` únicos |

Substitui o anti-padrão legado de **um processo duplicado por filial** com o mesmo nome.

## Modos de importação

| Modo | Comportamento |
|------|----------------|
| `replace` | Trunca cadastro (incl. setores) e insere tudo do JSON; recalcula `dashboard_calculos` |
| `merge` | Upsert por PK nas entidades; `setor_filiais` é sincronizado (delete + insert do JSON) |

Corpo das rotas `POST /data/import/preview` e `POST /data/import/apply`:

```json
{
  "mode": "merge",
  "import_format": "auto",
  "data": { "...": "bundle exportado" }
}
```

## Export enriquecido

O export inclui pais referenciados por FK mesmo quando `deletado = true` (ex.: processo só citado em revisão arquivada), para o JSON ser autocontido.

## CLI (Postgres direto)

Recomendado para baseline Playbook 18 e restore entre ambientes:

```bash
cd transformometro-api
set -a && source ../infra/.env && set +a

python scripts/import_cadastro_json.py export -o fixtures/cadastro/backup.json
python scripts/import_cadastro_json.py preview -i fixtures/cadastro/backup.json --mode replace --format auto
python scripts/import_cadastro_json.py apply -i fixtures/cadastro/backup-legado.json --mode replace --format legacy --yes
```

Implementação: `tm_app/cli/cadastro_json_cli.py` · wrapper `scripts/import_cadastro_json.py`.

Arquivos JSON operacionais (export/correção) ficam **fora do git** — use `fixtures/cadastro/` (gitignored) ou `scripts/out/` local.

## Consolidação cadastral manual (jul/2026)

Migração one-shot de bases que ainda tinham **processos duplicados por filial** (modelo pré–Playbook 18) para **processo-mestre + instâncias**. Não há script versionado no repositório: o fluxo é **export → edição do JSON → import replace**.

### Quando usar

- Mesmo processo cadastrado duas vezes (SC + ES) com revisões equivalentes.
- Objetivo: reduzir cadastro, renumerar `codigo_processo` (PROC-0001…) e usar instância multi-unidade onde os parâmetros são idênticos.

### Regras de transformação

| Situação | Resultado no JSON |
|----------|-------------------|
| Duplicatas **idênticas** (mesmo nome, mesmas medições/investimentos) | **1** processo + **1** instância com `todas_filiais_ativas: true`, `filial_id: null` |
| Duplicatas **divergentes** (baseline/volumes diferentes entre filiais) | **1** processo + **2** instâncias (uma por filial, `todas_filiais_ativas: false`) |
| Processo só em uma filial | **1** processo + **1** instância na filial |
| Processo vazio / sem revisões úteis | Descartar do bundle |
| Rateio de recursos entre duplicatas | Manter **só o peso do canônico** escolhido |

Renumerar `codigo_processo` sequencialmente (PROC-0001, PROC-0002, …) **sem buracos**, na ordem desejada de exibição.

### Checklist antes do `apply --mode replace`

1. **Backup** com `export` no ambiente de origem (produção exige backup explícito antes do replace).
2. `schema_version: "1.1"` e chaves Playbook 18 presentes (`filiais`, `processo_instancias`, `processo_instancia_setores`).
3. Em cada instância importável: `status_instancia: "ativo"`, `deletado: false`.
4. `created_at` / `updated_at` preenchidos nas instâncias (o export enriquecido pode omitir — copiar da revisão mais antiga ou do processo).
5. Remover campos **só de export** que não existem na tabela (`setores` embutidos, `codigo_setor` derivado, etc.) — manter só colunas persistidas.
6. Revisões apontam para `instancia_id` correto após merge de duplicatas.
7. `preview --mode replace` **sem erros** (FK, duplicata em `processo_instancia_setores`, `filial_id` ausente indevido).

### Comandos (produção)

```bash
cd transformometro-api
set -a && source ../infra/.env && set +a

python scripts/import_cadastro_json.py export -o backup-pre-consolidacao.json
# editar manualmente → cadastro-consolidado.json

python scripts/import_cadastro_json.py preview -i cadastro-consolidado.json --mode replace
python scripts/import_cadastro_json.py apply -i cadastro-consolidado.json --mode replace --yes
```

O `apply` em modo `replace` trunca o cadastro, insere o bundle e dispara recálculo do cache (`dashboard_calculos`) quando `TM_DASHBOARD_PERSIST_CACHE` estiver ativo.

### Validação pós-import

```bash
docker exec delpi-transformometro-api python -m tm_app.infrastructure.persistence.plugins.migrations_runner status
docker exec -i delpi-transformometro-api sh -lc 'python - <<PY
from tm_app.application.services.dashboard_recalc_service import DashboardRecalcService
print(DashboardRecalcService().recalculate())
PY'
```

Smoke: dashboard consolidado, filtro por filial, processo → painel de instâncias (multi-unidade vs por filial).

Regra de economia multi-unidade no motor: [regras-de-calculo.md](regras-de-calculo.md) § Instância multi-unidade.

## Código

- Serviço JSON: `tm_app/application/services/json_backup_service.py`
- Pacote ZIP: `tm_app/application/services/backup_package_service.py`
- Repositório: `tm_app/infrastructure/persistence/json_backup_repository.py`
- Testes: `tests/test_json_backup_service.py`, `tests/test_backup_package_service.py`
