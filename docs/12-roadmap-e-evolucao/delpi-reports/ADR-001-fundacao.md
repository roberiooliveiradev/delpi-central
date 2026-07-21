# ADR-001 — Fundação Delpi Reports

**Status:** Aceito (2026-07-21)  
**Contexto:** Plugin de envio de relatórios por e-mail (`reports`), backend na api-delpi.

## Decisões

### 1. Persistência em schema `reports`

- Migrations em `api-delpi/migrations/plugins/reports/`
- Tabelas: definitions, recipients, schedules, runs, deliveries
- Detalhe: [SCHEMA.md](./SCHEMA.md) · `V001__create_reports_core.sql`

### 2. Providers desacoplados

- Contrato: `ReportProviderPort` (`key`, `describe_params`, `collect`, `render_email`)
- Registry: `ReportProviderRegistry` (composition root na Fase 1+)
- Motor genérico **não** referencia paths de estoque; usa `provider_key`

### 3. Entrega por Microsoft Graph

- Método novo: `MicrosoftGraphMailClient.send_mail_to(to_addresses, attachments?)`
- Legado: `send_mail()` continua usando `GRAPH_MAIL_RECIPIENT` (canal-denúncia)
- Remetente Reports: `GRAPH_REPORTS_MAIL_SENDER` (default compose: `minhadelpi@delpi.com.br`), fallback `GRAPH_MAIL_SENDER`

### 4. RBAC (manifesto-alvo MFE Fase 1)

| Código | Uso |
|--------|-----|
| `reports.view` | Ver definições, histórico, preview |
| `reports.manage` | CRUD, destinatários, agendas, disparar |
| `reports.view.filial-sc` / `filial-es` | Escopo TOTVS branch `01` / `02` |
| `reports.manage.filial-sc` / `filial-es` | Gestão com escopo de filial |

Constantes: `api_delpi_permissions.py` (`REPORTS_*`, `REPORTS_BRANCH_VIEW_PERMS`).

## Consequências

- Fase 1: scaffold MFE + CRUD HTTP sobre o schema
- Fase 2: primeiro provider `safety_stock_shortage_30d`
- Fase 3: composer Graph com `GRAPH_REPORTS_MAIL_SENDER` + motor de run
- Ops: conceder `Mail.Send` na mailbox `minhadelpi@delpi.com.br`

## Referências

- [ROADMAP.md](./ROADMAP.md)
- [README.md](./README.md)
- Cliente: `api-delpi/app/infrastructure/providers/microsoft_graph/microsoft_graph_mail_client.py`
