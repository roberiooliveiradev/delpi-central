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

Compose (agendamento desativado — só `--profile manual`). **Obrigatório** rodar a partir de `infra/` (ou passar `-f`):

```bash
cd /home/operador/projetos/delpi-central/infra
# Após rebuild do production-control-api, o publisher reutiliza a mesma imagem.
docker compose -f docker-compose.yml --env-file .env --profile manual run --rm --no-deps \
  myweg-needs-publisher --dry-run \
  --collection-id 20261104_172829_20261104_142827_EXPORT_20261104_142826 --json

docker compose -f docker-compose.yml --env-file .env --profile manual run --rm --no-deps \
  myweg-needs-publisher --publish \
  --collection-id 20261104_172829_20261104_142827_EXPORT_20261104_142826 --json
```

Se `no configuration file provided: not found` aparecer, o cwd não era `infra/`.  
Se o erro de normalização **não** trouxer `chaves_recebidas=`, a imagem do publisher está stale — rode `docker compose ... build production-control-api` de novo.

Token S2S vem do `.env` do compose (`API_DELPI_INTERNAL_SERVICE_TOKEN`), montagem RO dos normalizados, estado em volume separado. Sem Docker socket.

## Homologação inicial

Coleta já persistida (idempotente esperado `HTTP 200 created=false`):

`20261104_172829_20261104_142827_EXPORT_20261104_142826`

Sem backfill em massa. Sem ativar agenda.

### Evidência de entrega (TASK `MYWEG-NEEDS-LINUX-PUBLISHER-MANUAL`)

| Item | Estado |
|------|--------|
| Feature + fixes | `9d0abef0db` … `30eea7225f` em `main` |
| Testes locais | publisher + E1/E2 + CSV `;`/aliases |
| Agendamento | **DESATIVADO** (`profiles: [manual]`; sem cron/timer) |
| Deploy srv-api | **PROVEN** — rebuild `production-control-api` |
| Smoke dry-run | **PROVEN** — 532 · 745746 UN · 2 refs vazias · `http.sent=false` |
| Smoke reenvio | **PROVEN** — HTTP 200 · `created=false` · id `bcf31e45-c812-4316-95e2-9bb9f6e46707` · sha `f2c20b35…` |

## Correção /latest (E2 follow-up)

`get_latest_batch` / `list_batches` ordenam por `collected_at DESC, imported_at DESC, collection_id ASC` — import tardio de coleta antiga **não** vira latest.
