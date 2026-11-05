# MyWEG Necessidades — publicador Linux

> **Status:** CLI one-shot versionada · modo pending + timer systemd **versionado** · ativação produtiva **controlada**  
> **TASK_ID:** `MYWEG-NEEDS-LINUX-PUBLISHER-AUTOMATION`  
> **Owner:** `production-control-api` (job cliente S2S do contrato E1/E2)  
> **Não owner:** ETL `myweg_integrador` / coletor Windows (fora do monorepo; **não** modificar)

## EXISTING_EQUIVALENT / REUSE_DECISION

| Item | Decisão |
|------|--------|
| EXISTING_EQUIVALENT | YES — `jobs/myweg_needs_publisher` (manual E1/E2) |
| SCHEDULER_INVENTORY | Runtime srv-api **PENDING** (SSH sem chave neste agente). No Git: **nenhum** timer/cron MyWEG versionado antes desta task. |
| REUSE_DECISION | EXTEND — `--publish-pending` + watermark + run lock + units systemd |
| NÃO | daemon Python permanente, alterar ETL 05h00, `dry_run=false` SB1 automático, Docker socket no job, secret no unit file |

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
# Manual (preservado)
python -m production_control_app.jobs.myweg_needs_publisher \
  --dry-run|--publish \
  --collection-id <id> | --latest \
  [--json]

# Pendências (novo) — ordem collected_at ASC, limite por execução
python -m production_control_app.jobs.myweg_needs_publisher \
  --dry-run|--publish \
  --publish-pending \
  [--max-batches 5] \
  [--include-historical] \
  [--json]

# Marco de ativação (evita backfill em massa)
python -m production_control_app.jobs.myweg_needs_publisher \
  --set-activation-watermark '2026-11-04T14:28:27-03:00' --json
```

Compose (profile `manual` — **não** sobe no `up` padrão). Rodar a partir de `infra/`:

```bash
cd ~/projetos/delpi-central/infra
docker compose -f docker-compose.yml --env-file .env --profile manual run --rm --no-deps \
  myweg-needs-publisher --dry-run --publish-pending --json

docker compose -f docker-compose.yml --env-file .env --profile manual run --rm --no-deps \
  myweg-needs-publisher --publish --publish-pending --json
```

Env relevantes:

| Variável | Papel |
|---|---|
| `MYWEG_PUBLISHER_ACTIVATION_COLLECTED_AT` | Marco ISO — só publica `collected_at >= marco` (salvo `--include-historical`) |
| `MYWEG_PUBLISHER_MAX_BATCHES_PER_RUN` | Limite sequencial (default 5) |
| `API_DELPI_INTERNAL_SERVICE_TOKEN` | S2S (compose `.env`) |

## Agendamento (systemd)

Arquivos versionados:

- `infra/systemd/myweg-needs-publisher.service`
- `infra/systemd/myweg-needs-publisher.timer` — a cada ~30 min, 05:30–14:00 (não presume fim fixo do ETL às 05h)
- `infra/scripts/run-myweg-needs-publisher-pending.sh` — flock host + compose one-shot
- `infra/scripts/install-myweg-needs-publisher-timer.sh` — instala units; **não** habilita

### Ativação controlada

1. Commit/push/deploy imagem `production-control-api` (publisher reusa a imagem).
2. Definir watermark (último lote já persistido ou marco desejado).
3. Dry-run pending real.
4. `sudo ./infra/scripts/install-myweg-needs-publisher-timer.sh`
5. `sudo systemctl enable --now myweg-needs-publisher.timer`
6. Desativar: `sudo systemctl disable --now myweg-needs-publisher.timer`

Se watermark, secrets, dry-run ou exclusão mútua falharem → **ACTIVATION_PENDING**.

## Concorrência e autoridade

- Run lock no estado (`publisher_run.lock`) + flock no host script.
- Estado local = tentativas operacionais.
- Ingestão E2 + idempotency/hash = autoridade de lotes aceitos.
- Mesmo `collection_id` com hash diferente → `conflict` (não sobrescreve).
- SB1: coletas novas ficam `pending`; **não** há automação de `dry_run=false`.

## Observabilidade

Saída JSON: `pending`, `published`, `rejected`, `blocked`, `skipped`, itens com `status` (`eligible`/`blocked`/`conflict`/`already_published`/`before_watermark`/`published`/`idempotent`/`failed`/`busy`/…).

## Homologação

| Item | Estado |
|------|--------|
| Código pending + timer | esta task |
| Agendamento produtivo | **ACTIVATION_PENDING** até watermark + enable no srv-api |
| SSH inventário runtime | **PENDING** (chave) |
| REAL_NEW_BATCH_SMOKE | **PENDING** |
| SB1 auto-persist | **FORA_DO_ESCOPO** (explícito) |
