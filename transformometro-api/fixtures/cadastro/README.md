# Cadastro Transformômetro — snapshot JSON

Pasta para o **export do ambiente atual** antes da refatoração (Playbook 18) e para reaplicar cadastro após migrations de **schema** (sem seed de conteúdo nas migrations).

## Baseline Playbook 18 (jun/2026)

Arquivo local (gitignored): `transformometro-cadastro-20260612.json` — export validado schema 1.1 (58 processos, 118 revisões).

## Exportar (ambiente de origem)

Com Postgres acessível e variáveis `PLUGINS_DB_*`:

```bash
cd transformometro-api
set -a && source ../infra/.env && set +a

python scripts/import_cadastro_json.py export \
  -o fixtures/cadastro/transformometro-cadastro-$(date +%Y%m%d).json
```

Alternativa via API (JWT no portal):

```bash
curl -sS -H "Authorization: Bearer $TOKEN" \
  "http://localhost/apps/transformometro-api/transformometro/data/export" \
  -o fixtures/cadastro/transformometro-cadastro.json
```

## Importar (ambiente destino)

1. Aplicar migrations de **estrutura** apenas (`migrations_runner up`) — sem INSERT de dados.
2. Pré-visualizar:

```bash
python scripts/import_cadastro_json.py preview \
  -i fixtures/cadastro/transformometro-cadastro-YYYYMMDD.json \
  --mode replace
```

3. Aplicar (substitui todo o cadastro + recalcula `dashboard_calculos`):

```bash
python scripts/import_cadastro_json.py apply \
  -i fixtures/cadastro/transformometro-cadastro-YYYYMMDD.json \
  --mode replace \
  --yes
```

Modo `merge`: upsert por PK; útil para sincronizar deltas sem truncate.

## Consolidação multi-unidade (jul/2026)

Para bases com processos duplicados por filial, ver runbook completo em [docs/json-backup.md](../../docs/json-backup.md) (seção **Consolidação cadastral manual**). Resumo: export → merge manual no JSON (instância `todas_filiais_ativas` ou 2 instâncias se divergente) → `apply --mode replace`.

## Git

Arquivos `*.json` nesta pasta estão no `.gitignore` (dados operacionais). Versionar só este README e o script em `scripts/import_cadastro_json.py`.

## Schema

`schema_version: "1.1"` — ver [docs/json-backup.md](../../docs/json-backup.md).
