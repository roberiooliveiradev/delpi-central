# MyWEG Necessidades — publicador Linux

> **Status:** CLI one-shot · pending + timer · **resolução SB1 automática (E4)** · ativação produtiva controlada  
> **TASK_ID:** `MYWEG-NEEDS-AUTOMATIC-SB1-RESOLUTION`  
> **Owner:** `production-control-api` (job cliente S2S dos contratos E1/E2/E4)  
> **Não owner:** ETL `myweg_integrador` / coletor Windows (fora do monorepo; **não** modificar)

## EXISTING_EQUIVALENT / REUSE_DECISION

| Item | Decisão |
|------|--------|
| EXISTING_EQUIVALENT | YES — `jobs/myweg_needs_publisher` + `POST .../sb1-resolve` + `MyWegSb1ResolveService` |
| REUSE_DECISION | EXTEND — após ingestão (ou recuperação de `already_published`) chama E4 S2S |
| NÃO | segundo scheduler SB1, novo motor de matching, `dry_run=false` SB1 fora do serviço E4, alterar ETL 05h00 |

## Sequência automática

```text
timer 06:00/15/30/45 America/Sao_Paulo
  → discover pending (watermark + max_batches)
  → POST /integrations/myweg/need-batches          # E2 ingest
  → POST /integrations/myweg/need-batches/sb1-resolve
       dry_run=false, skip_if_complete=true        # E4
  → already_published no watermark sem SB1 completa
       → mesmo sb1-resolve (recuperação; PG é autoridade)
```

Flag de rollback: `MYWEG_PUBLISHER_AUTO_SB1_RESOLVE=false`.

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

# Pendências + SB1 automática (quando AUTO_SB1_RESOLVE=true)
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

# Dry-run — NÃO editar o script produtivo
docker compose -f docker-compose.yml --env-file .env --profile manual run --rm --no-deps \
  myweg-needs-publisher --dry-run --publish-pending --json

# Publicação real (one-shot) — mesmo contrato do timer
./scripts/run-myweg-needs-publisher-pending.sh
```

Env relevantes:

| Variável | Papel |
|---|---|
| `MYWEG_PUBLISHER_ACTIVATION_COLLECTED_AT` | Marco ISO — só publica `collected_at >= marco` |
| `MYWEG_PUBLISHER_MAX_BATCHES_PER_RUN` | Limite de ingestões por execução (default 5) |
| `MYWEG_PUBLISHER_MAX_SB1_BATCHES_PER_RUN` | Limite de recuperações SB1 em `already_published` (default 5) |
| `MYWEG_PUBLISHER_AUTO_SB1_RESOLVE` | `true` (default) executa E4; `false` = só ingestão |
| `MYWEG_PUBLISHER_TIMEOUT_SECONDS` | Timeout HTTP (default 180 — cobre lookup SB1) |
| `API_DELPI_INTERNAL_SERVICE_TOKEN` | S2S (compose `.env`) |

## Agendamento (systemd)

- `infra/systemd/myweg-needs-publisher.timer` — **somente** 06:00, 06:15, 06:30 e 06:45 `America/Sao_Paulo`
- `Persistent=true` — catch-up após reboot pode sair da janela matinal (exceção)
- Install **não** habilita: `sudo ./infra/scripts/install-myweg-needs-publisher-timer.sh`

## Resolução SB1 (E4)

- Serviço canônico: `MyWegSb1ResolveService` + projeção V026
- Preferência PCP 9/8 via `disambiguation_policy=prefer_production_over_sample` (só no caminho MyWEG)
- Persistência só com `evaluate_field_semantics` comprovada
- `skip_if_complete=true`: se PG já tem run completed + vínculos sem `unavailable`, não reconsulta Protheus
- Falha SB1 **não** apaga ingestão; próximo timer recupera
- Ambiguous / not_found / divergent / blocked **não** viram confirmed

Ver detalhes e regra 8/9 em `MYWEG-NEEDS-PROTHEUS-E4.md`.

## Observabilidade

JSON do pending inclui por item:

- `status` da ingestão (`published` / `idempotent` / `already_published` / …)
- `sb1.status` (`resolved` / `already_resolved` / `incomplete` / `failed` / `auth_failed` / `semantics_blocked`)
- `sb1.counts` (confirmed / ambiguous / …)
- totais: `sb1_resolved`, `sb1_skipped`, `sb1_failed`

Estado local (`publisher_state.json`) guarda tentativas operacionais; **autoridade da resolução = PostgreSQL V026**.

## Diagnóstico rápido (srv-api)

```bash
journalctl -u myweg-needs-publisher.service -n 120 --no-pager
cd ~/projetos/delpi-central/infra
docker compose -f docker-compose.yml --env-file .env --profile manual run --rm --no-deps \
  myweg-needs-publisher --dry-run --publish-pending --json
```

## Homologação

| Item | Estado |
|------|--------|
| Código pending + SB1 automática | esta task |
| Preferência 9/8 (19106407 → 90264221) | testes unitários |
| Timer produtivo | habilitado (gates matutinos) |
| AC-01/AC-02 smoke **nova** coleta real pós-deploy | **PENDING** |
| SB1 auto fora do E4 | **FORA_DO_ESCOPO** |
