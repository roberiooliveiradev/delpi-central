# Backup JSON — Transformômetro

Exportação e importação cadastral via `/transformometro/data/export` e `/transformometro/data/import/*`.

## Versão do pacote

| `schema_version` | Mudança |
|------------------|---------|
| `1.0` | Processos, revisões, medições, investimentos, recursos |
| `1.1` | Inclui `setores`, `setor_filiais` e valida FK `processos.setor_id` → `setores` |

Pacotes `1.0` devem ser reexportados após upgrade da API; importação exige `schema_version: "1.1"`.

## Chaves do bundle

Ordem lógica de dependência:

1. **`setores`** — cadastro de setores (`setor_id`, `nome_setor`, `status_setor`, …)
2. **`setor_filiais`** — vínculos N:N (`setor_id`, `filial_id`); substituídos integralmente na importação
3. **`processos`** — FK `setor_id` obrigatória e referenciada em `setores`
4. **`recursos_compartilhados`**, **`revisoes`**, **`medicoes`**, **`investimentos`**, **`recurso_custos`**, **`revisao_recursos_compartilhados`**

## Modos de importação

| Modo | Comportamento |
|------|----------------|
| `replace` | Trunca cadastro (incl. setores) e insere tudo do JSON; recalcula `dashboard_calculos` |
| `merge` | Upsert por PK nas entidades; `setor_filiais` é sincronizado (delete + insert do JSON) |

## Export enriquecido

O export inclui pais referenciados por FK mesmo quando `deletado = true` (ex.: processo só citado em revisão arquivada), para o JSON ser autocontido.

## CLI (Postgres direto)

Recomendado para baseline Playbook 18 e restore entre ambientes:

```bash
cd transformometro-api
set -a && source ../infra/.env && set +a

python scripts/import_cadastro_json.py export -o fixtures/cadastro/backup.json
python scripts/import_cadastro_json.py preview -i fixtures/cadastro/backup.json --mode replace
python scripts/import_cadastro_json.py apply -i fixtures/cadastro/backup.json --mode replace --yes
```

Implementação: `tm_app/cli/cadastro_json_cli.py` · wrapper `scripts/import_cadastro_json.py`.

## Código

- Serviço: `tm_app/application/services/json_backup_service.py`
- Repositório: `tm_app/infrastructure/persistence/json_backup_repository.py`
- Testes: `tests/test_json_backup_service.py`
