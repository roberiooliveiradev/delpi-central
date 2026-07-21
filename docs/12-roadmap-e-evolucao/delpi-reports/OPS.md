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

## Cron (host)

Script: `api-delpi/scripts/process-pending-report-schedules.sh`  
Lê `API_DELPI_INTERNAL_SERVICE_TOKEN` de `infra/.env` (não precisa exportar no crontab).  
No host usa o gateway `http://127.0.0.1/apps/api-delpi` (ignora `http://api-delpi:…` do Compose).

```cron
*/15 * * * * /home/michael/projetos/delpi-central/api-delpi/scripts/process-pending-report-schedules.sh >>/tmp/delpi-reports-cron.log 2>&1
```

Log: `/tmp/delpi-reports-cron.log`. Conferir: `crontab -l` · `tail -f /tmp/delpi-reports-cron.log`.

O worker faz **claim atômico** (`FOR UPDATE SKIP LOCKED`) e avança `next_run_at` **antes** do envio — dois crons paralelos não duplicam o mesmo slot.

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
