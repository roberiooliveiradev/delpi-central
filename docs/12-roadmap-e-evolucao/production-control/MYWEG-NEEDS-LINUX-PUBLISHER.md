# MyWEG Necessidades — publicador Linux

> **Status:** CLI one-shot versionada · modo pending + timer systemd **versionado** · ativação produtiva **PENDING**  
> **TASK_ID:** `MYWEG-NEEDS-PUBLISHER-MORNING-SCHEDULE`  
> **Owner:** `production-control-api` (job cliente S2S do contrato E1/E2)  
> **Não owner:** ETL `myweg_integrador` / coletor Windows (fora do monorepo; **não** modificar)

## EXISTING_EQUIVALENT / REUSE_DECISION

| Item | Decisão |
|------|--------|
| EXISTING_EQUIVALENT | YES — `jobs/myweg_needs_publisher` (manual E1/E2) |
| SCHEDULER_INVENTORY | Runtime srv-api **PENDING** (SSH sem chave neste agente). No Git: timer versionado reutilizado. |
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

# Dry-run (homologação / gates operacionais) — NÃO editar o script produtivo
docker compose -f docker-compose.yml --env-file .env --profile manual run --rm --no-deps \
  myweg-needs-publisher --dry-run --publish-pending --json

# Publicação real (one-shot) — mesmo contrato do timer
docker compose -f docker-compose.yml --env-file .env --profile manual run --rm --no-deps \
  myweg-needs-publisher --publish --publish-pending --json
# ou: ./scripts/run-myweg-needs-publisher-pending.sh
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
- `infra/systemd/myweg-needs-publisher.timer` — **somente** 06:00, 06:15, 06:30 e 06:45 `America/Sao_Paulo`
- `infra/scripts/run-myweg-needs-publisher-pending.sh` — flock host + compose one-shot (`--publish`)
- `infra/scripts/install-myweg-needs-publisher-timer.sh` — instala units; **não** habilita

### Calendário

```ini
OnCalendar=*-*-* 06:00:00 America/Sao_Paulo
OnCalendar=*-*-* 06:15:00 America/Sao_Paulo
OnCalendar=*-*-* 06:30:00 America/Sao_Paulo
OnCalendar=*-*-* 06:45:00 America/Sao_Paulo
RandomizedDelaySec=0
AccuracySec=1min
Persistent=true
```

- Horários explícitos em `America/Sao_Paulo` — independentes do timezone do host (`Etc/UTC` no srv-api).
- Origem MyWEG envia às 05:00 SP; as quatro tentativas cobrem a janela matinal pós-ETL.
- `Persistent=true` preserva recuperação após reinício: o catch-up pode ocorrer **fora** da janela 06:00–06:45 (exceção operacional, não horário nominal).

Validação local:

```bash
systemd-analyze calendar '*-*-* 06:00:00 America/Sao_Paulo'
systemd-analyze calendar '*-*-* 06:15:00 America/Sao_Paulo'
systemd-analyze calendar '*-*-* 06:30:00 America/Sao_Paulo'
systemd-analyze calendar '*-*-* 06:45:00 America/Sao_Paulo'
systemd-analyze verify infra/systemd/myweg-needs-publisher.service \
  infra/systemd/myweg-needs-publisher.timer
```

### Ativação controlada (srv-api) — NÃO habilitar sem gates

1. `git pull --ff-only` após o push desta task.
2. `sudo ./infra/scripts/install-myweg-needs-publisher-timer.sh` — instala units; **não** habilita o timer.
3. Confirmar última coleta persistida (E2 / estado local) e permissões de `/var/lib/delpi/myweg-publisher-state`.
4. Definir watermark a partir dessa coleta (`--set-activation-watermark` ou `MYWEG_PUBLISHER_ACTIVATION_COLLECTED_AT`).
5. Dry-run via Compose (`--dry-run --publish-pending --json`) — **nunca** alterar temporariamente o script produtivo `run-myweg-needs-publisher-pending.sh`.
6. Avaliar itens `eligible` / `blocked` / `conflict` / `before_watermark` / `already_published`.
7. Somente então: `sudo systemctl enable --now myweg-needs-publisher.timer`.
8. Desativar: `sudo systemctl disable --now myweg-needs-publisher.timer`.

Se watermark, secrets, dry-run, integridade, permissões ou exclusão mútua falharem → **ACTIVATION_PENDING**.

Não declarar automação homologada sem observar uma coleta real publicada (`REAL_NEW_BATCH_SMOKE`).

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
| Código pending + timer matinal SP | esta task |
| Agendamento produtivo (`enable --now`) | **ACTIVATION_PENDING** até watermark + dry-run + smoke |
| SSH inventário runtime | **PENDING** (chave) |
| REAL_NEW_BATCH_SMOKE | **PENDING** (primeira coleta automática prevista 05/11/2026) |
| SB1 auto-persist | **FORA_DO_ESCOPO** (explícito) |
