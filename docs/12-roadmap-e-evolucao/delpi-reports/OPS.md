# Delpi Reports — operações

> Roadmap: [ROADMAP.md](./ROADMAP.md) · API: `api-delpi/docs/api/delpi-reports.md`

## Variáveis de ambiente (api-delpi)

| Variável | Uso |
|----------|-----|
| `GRAPH_REPORTS_TENANT_ID` | Tenant Azure AD da app Reports |
| `GRAPH_REPORTS_CLIENT_ID` | App registration Reports |
| `GRAPH_REPORTS_CLIENT_SECRET` | Segredo Reports |
| `GRAPH_REPORTS_MAIL_SENDER` | Remetente (`minhadelpi@delpi.com.br`) |
| `GRAPH_HTTP_TIMEOUT_SECONDS` | Timeout HTTP Graph (default 15) |
| `REPORTS_MAIL_BATCH_SIZE` | Destinatários por `sendMail` (default 40) |
| `REPORTS_RUN_ARTIFACTS_DIR` | Pasta de HTML das runs (default `/app/data/reports-runs`) |

**Não** reutilizar `GRAPH_MAIL_*` do canal-denúncia.

Volume Compose (prod e dev):

```text
${DELPI_DATA_HOST_DIR}/reports-runs → /app/data/reports-runs
```

## Azure AD

1. App registration com `Mail.Send` (application permission) + admin consent.
2. Application Access Policy na mailbox `minhadelpi@delpi.com.br` restringindo a app Reports.
3. Validar: `Test-ApplicationAccessPolicy` → Concedido.

## Disparo automático (poller + cron)

### Poller interno (canônico)

A `api-delpi` sobe um poller daemon (`REPORTS_SCHEDULE_POLL_SECONDS`, default **900** = 15 min) que chama o mesmo use case de `POST /reports/schedules/process-pending` **sem HTTP**.  
Assim o envio não depende de cron no WSL/host. `0` desliga o poller.

Log estruturado: `reports_schedule_poller_tick` / `reports_schedule_poller_failed`.

### Cron no host (opcional / redundante)

Script: `api-delpi/scripts/process-pending-report-schedules.sh`  
Lê `API_DELPI_INTERNAL_SERVICE_TOKEN` de `infra/.env`.  
Ordem de destino: `API_DELPI_BASE_URL` → `docker exec delpi-api-delpi` (porta 8000 interna) → gateway host `:9080` → `:80`.

```cron
*/15 * * * * /home/michael/projetos/delpi-central/api-delpi/scripts/process-pending-report-schedules.sh >>/tmp/delpi-reports-cron.log 2>&1
```

Log: `/tmp/delpi-reports-cron.log`. Conferir: `crontab -l` · `tail -f /tmp/delpi-reports-cron.log`.

**Sintoma clássico de cron quebrado:** `Próximo disparo` no passado (ex.: 23/10 com hoje 26/10) + log com `Failed to connect to 127.0.0.1 port 80` enquanto o gateway local publica **9080**. Manual continua funcionando porque o MFE usa o gateway certo; o plugin **não** registra falha do cron (a API nunca foi chamada).

O worker faz **claim atômico** (`FOR UPDATE SKIP LOCKED`) e avança `next_run_at` **antes** do envio — dois workers paralelos não duplicam o mesmo slot.

## Hook por evento

```http
POST /apps/api-delpi/reports/definitions/{id}/run?trigger=event
```

Permissão `reports.manage*` (ou service token se a rota for estendida). `trigger` aceito: `manual` (default), `schedule`, `event`.

## Troubleshooting

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| NDR / Unknown To | E-mail mascarado (`t***@`) gravado | Re-selecionar destinatário com `reveal_email=true`; API rejeita `***` |
| Sem e-mail / 403 Graph | Access Policy ou secret | Conferir policy + `GRAPH_REPORTS_*` no container |
| Run duplicada no mesmo horário | Worker antigo sem claim | Atualizar api-delpi (Fase 4) + migration V002 |
| Artefato sumiu após recreate | Sem volume | Montar `reports-runs` no Compose |
| Timeout Graph intermitente | Rede / throttling | Retry 1s/2s/4s (até 3) já no client |
| Próximo disparo no passado / sem e-mail automático / sem falha no plugin | Cron host inacessível (porta 80 vs 9080) ou poller desligado | Ver `/tmp/delpi-reports-cron.log`; garantir poller (`REPORTS_SCHEDULE_POLL_SECONDS>0`) e rebuild `api-delpi`; script com fallback Docker/`9080` |
| Catch-up após falha do worker | `process-pending` envia 1 e-mail por agenda vencida | Se já houve envio manual no dia, preferir só avançar `next_run_at` (salvar agenda na UI) ou aceitar 1 disparo de recuperação |
