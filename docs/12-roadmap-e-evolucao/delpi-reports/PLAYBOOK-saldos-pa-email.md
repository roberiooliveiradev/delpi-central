# Playbook — Saldos PA (e-mail agendado)

> **Provider key:** `stock_balances_pa`  
> **Nome na UI Reports:** Saldos PA (armazém 01)  
> **Agenda:** `weekdays` (seg–sex), horário escolhido pelo usuário  
> **Timezone:** `America/Sao_Paulo`

## Objetivo

Enviar por e-mail (Microsoft Graph) o Excel de saldos de PA do armazém 01, com o mesmo contrato do export do Portal PCP. O usuário **agenda no Portal PCP**; o **Delpi Reports** cria a definição/agenda, dispara o cron e monitora runs/deliveries.

## Ownership

| Responsabilidade | Dono |
|------------------|------|
| UI de agendamento (ícone calendário na toolbar → modal) | Portal PCP (`plugins/production-control`) |
| BFF agenda (`GET/PUT .../email-schedule`) | `production-control-api` (`PC_REPORTS_VIEW` + filial) |
| Provider, Graph, cron, runs | Delpi Reports (`api-delpi` schema `reports`) |
| Monitoramento admin | MFE `plugins/reports` |

## Recorte de produtos

- Inclusão: prefixos por filial (`01` → `9…`; `02` → `8…` e `9…`), armazém `01`, saldo positivo
- Exclusão canônica: códigos que começam com `9035` (lista PCP + e-mail Reports)

## Fluxo

```text
PCP MFE → production-control-api → PUT/GET /reports/personal-subscriptions/stock_balances_pa (S2S)
cron → POST /reports/schedules/process-pending
     → Provider collect + render_email (XLSX anexo)
     → Graph sendMail
```

## Params do provider

| Param | Valores | Uso |
|-------|---------|-----|
| `branch` | `01` \| `02` | Filial TOTVS; prefixos PA 01→`9…`, 02→`8…`+`9…` |

## Excel anexo

- Colunas: Produto, Quantidade (× 1000)
- Nome: `ESTOQUE MATRIZ - DD-MM-AAAA` (01) / `SALDO FILIAL - DD-MM-AAAA` (02)
- Bordas em todas as células (openpyxl)

## Subject / corpo

- Subject: `Saldos em estoque — {ESTOQUE MATRIZ|SALDO FILIAL} | {DD-MM-AAAA}`
- Corpo: brand layout + texto curto (armazém 01, filial, data, total) + anexo

## Modelo de agenda pessoal

Uma definição por `(providerKey, created_by_user_id, params.branch)`; destinatário = o próprio usuário; `scheduleKind: weekdays`.

## Checklist homologação

- [ ] Salvar horário no PCP cria definição visível no Delpi Reports
- [ ] Preview/run manual envia Excel com bordas e qtde × 1000
- [ ] Cron em dia útil no horário gera delivery `sent`
- [ ] Sábado/domingo não disparam
- [ ] MFE PCP sem chamada direta a `/apps/api-delpi`

## Ops

```bash
# Dev
./infra/scripts/up-dev-sequential.sh --fase api --build api-delpi production-control-api
./infra/scripts/up-dev-sequential.sh --fase mfe --build production-control reports

# Cron (já existente)
# api-delpi/scripts/process-pending-report-schedules.sh
```

Em produção: migrations Reports só com `up` — nunca `reset --plugin reports`.
