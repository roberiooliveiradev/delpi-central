# Backup JSON — Transformômetro

Exportação e importação cadastral via `/transformometro/data/export` e `/transformometro/data/import/*`.

## Versão do pacote

| `schema_version` | Mudança |
|------------------|---------|
| `1.0` | Processos, revisões, medições, investimentos, recursos |
| `1.1` | Inclui `setores`, `setor_filiais` e valida FK `processos.setor_id` → `setores` |

Pacotes `1.0` devem ser reexportados após upgrade da API; importação exige `schema_version: "1.1"`.

## Formatos de importação (`import_format`)

| Valor | Uso |
|-------|-----|
| `auto` (padrão) | Detecta legado vs Playbook 18 pelo conteúdo do JSON |
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
5. **`processo_instancias`** — instância operacional (processo × filial × setor)
6. **`recursos_compartilhados`**, **`revisoes`** (com `instancia_id`), **`medicoes`**, **`investimentos`**, **`recurso_custos`**, **`revisao_recursos_compartilhados`**

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

## Código

- Serviço: `tm_app/application/services/json_backup_service.py`
- Repositório: `tm_app/infrastructure/persistence/json_backup_repository.py`
- Testes: `tests/test_json_backup_service.py`
