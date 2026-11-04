# MyWEG Necessidades — publicador Linux (manual)

> **Status:** CLI one-shot versionada · execução **manual** · cron/timer **desativado**  
> **TASK_ID:** `MYWEG-NEEDS-LINUX-PUBLISHER-MANUAL`  
> **Owner:** `production-control-api` (job cliente S2S do contrato E1/E2)  
> **Não owner:** ETL `myweg_integrador` (fora do monorepo; **não** modificar)

## EXISTING_EQUIVALENT / REUSE_DECISION

| Item | Decisão |
|------|--------|
| EXISTING_EQUIVALENT | Nenhum publicador MyWEG no monorepo. Padrões próximos: smokes S2S + `API_DELPI_INTERNAL_SERVICE_TOKEN` + compose one-shot. |
| REUSE | Contrato E1 (`normalize_source_records`, `validate_ingest_batch`, hashes) + POST E2 `/integrations/myweg/need-batches` |
| CRIAR | `production_control_app/jobs/myweg_needs_publisher` + serviço Compose `profiles: [manual]` |
| NÃO | cron, systemd timer, alteração do ETL 05h00, Docker socket, secret manager paralelo |

## Artefatos de origem (srv-api)

```text
/home/michael/.local/share/MyWEG-Automacao/normalizados/<collection_id>/
  necessidades_tratadas.csv
  necessidades_tratadas.xlsx
  para_conferencia_pcp.csv
  resumo.json   # último arquivo; NÃO atômico — exige estabilidade por hash duplo
```

Lock `.lock` / `etl.lock` → rejeita publicação (sinal auxiliar; não altera o ETL).

## CLI

```bash
python -m production_control_app.jobs.myweg_needs_publisher \
  --dry-run|--publish \
  --collection-id <id> | --latest \
  [--json]
```

Compose (agendamento desativado — só `--profile manual`):

```bash
cd ~/projetos/delpi-central/infra
docker compose --profile manual run --rm myweg-needs-publisher --dry-run --latest --json
docker compose --profile manual run --rm myweg-needs-publisher \
  --publish --collection-id 20261104_172829_20261104_142827_EXPORT_20261104_142826 --json
```

Token S2S vem do `.env` do compose (`API_DELPI_INTERNAL_SERVICE_TOKEN`), montagem RO dos normalizados, estado em volume separado. Sem Docker socket.

## Homologação inicial

Coleta já persistida (idempotente esperado `HTTP 200 created=false`):

`20261104_172829_20261104_142827_EXPORT_20261104_142826`

Sem backfill em massa. Sem ativar agenda.

## Correção /latest (E2 follow-up)

`get_latest_batch` / `list_batches` ordenam por `collected_at DESC, imported_at DESC, collection_id ASC` — import tardio de coleta antiga **não** vira latest.
