# Comitê de Ética e Conduta — API

API dedicada do plugin **Comitê de Ética e Conduta**: atas de reunião com versionamento e assinatura manuscrita (PNG), cadastro de membros do comitê e notificações in-app via Core API.

## Endpoints (prefixo gateway)

Base: `/apps/comite-etica-conduta-api`

| Grupo | Paths |
|-------|--------|
| Saúde | `GET /health` |
| Acesso | `GET /access` |
| Membros | `GET/POST /members`, `PATCH/DELETE /members/{id}`, `POST /members/{id}/end` |
| Atas | `GET/POST /minutes`, `GET/PATCH /minutes/{id}`, send/sign/finalize/cancel/export… |
| Assinatura pessoal | `GET/PUT /signatures/me`, imagem PNG |

Comitê **único corporativo** (`unit_code = 00`). Sem filtro SC/ES.

## Permissões

- `comite-etica-conduta.view`
- `comite-etica-conduta.manage`
- `comite-etica-conduta.sign`

## Persistência

- Schema Postgres: `comite_etica` (volume `postgres-plugins`)
- Migrations em `migrations/` (runner no boot se `CEC_RUN_MIGRATIONS_ON_STARTUP=true`)
- Volumes: assinaturas PNG e PDFs sob `${DELPI_DATA_HOST_DIR}/comite-etica-conduta/`

## Notificações

`CecPortalNotificationService` → Core `POST /integrations/notifications` com `userIds` + `action.type=portal_route`:

- Envio para assinatura → deep link `/apps/comite-etica-conduta/atas/{id}/sign`
- Ata assinada / recusada → `/apps/comite-etica-conduta/atas/{id}`

## E-mail Outlook (Microsoft Graph)

No `send-for-signature`, além da notificação in-app, `CecSignPendingMailService` envia e-mail a cada signatário:

1. Resolve SMTP via Core `POST /integrations/directory/users/lookup` (token S2S)
2. Envia via Microsoft Graph (`sendMail`), mesmas credenciais do **Delpi Reports** (`GRAPH_REPORTS_*`), com override opcional `CEC_GRAPH_*`
3. Link absoluto: `{PUBLIC_BASE_URL}/apps/comite-etica-conduta/atas/{id}/sign`

Falhas de e-mail **não** interrompem o envio da ata (só log). Desligar: `CEC_MAIL_ENABLED=false`.

## Dev

```bash
./infra/scripts/up-dev-sequential.sh --build comite-etica-conduta-api
```
