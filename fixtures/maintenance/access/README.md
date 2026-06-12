# Export Access — MiniAplicadoresBD

Exporte as tabelas do Access em **CSV UTF-8** (delimitador vírgula, cabeçalho na primeira linha).

| Arquivo Access | CSV esperado | Colunas mínimas |
|----------------|--------------|-----------------|
| TabMotivo | `TabMotivo.csv` | `Descricao` |
| TabStatusPeca | `TabStatusPeca.csv` | `Descricao`, `Operador`, `Percentual` |
| TabReposicoes | `TabReposicoes.csv` | `Filial`, `CodigoFerramenta`, `CodigoPeca`, `DataReposicao`, `Golpes`, `Motivo` |

Arquivos `*.sample.csv` nesta pasta são exemplos mínimos para validar o CLI (`--dry-run`).

## Importação

```bash
cd maintenance-api
set -a && source ../infra/.env && set +a
python scripts/import_access_csv.py \
  --motivos ../fixtures/maintenance/access/TabMotivo.csv \
  --status ../fixtures/maintenance/access/TabStatusPeca.csv \
  --reposicoes ../fixtures/maintenance/access/TabReposicoes.csv \
  --filial 01 \
  --dry-run
```

Remova `--dry-run` para gravar no Postgres.
