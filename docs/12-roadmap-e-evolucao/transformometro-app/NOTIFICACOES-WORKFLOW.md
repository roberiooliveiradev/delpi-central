# Notificações de workflow — Transformômetro

Alertas no **sino do portal** quando uma revisão é submetida, aprovada ou rejeitada. O clique abre o processo/revisão no MFE (deep link).

**Relacionado:** [conectar-aplicacao-iframe.md](../../10-guias-operacionais/conectar-aplicacao-iframe.md), [Core API — notificações](../../04-core-api/notificacoes.md), [OPERATIONS.md](./OPERATIONS.md) (variáveis e troubleshooting).

---

## Fluxo

| Ação na API | Destinatários | Tipo visual |
|-------------|---------------|-------------|
| `POST /revisoes/{id}/workflow/submeter` | Aprovadores (`TM_WORKFLOW_APPROVER_*`) | `info` |
| `POST …/workflow/aprovar` | Quem submeteu (último `workflow_submeter` em `audit_logs`) | `success` |
| `POST …/workflow/rejeitar` | Quem submeteu | `warning` |

Falha ao enviar notificação **não** reverte o workflow (apenas log `warning` na API).

---

## Core API

`transformometro-api` chama:

```http
POST {TM_CORE_API_URL}/integrations/notifications
X-Delpi-Service-Token: {CORE_API_INTEGRATIONS_SERVICE_TOKEN}
```

Exemplo de payload (submissão):

```json
{
  "title": "Transformômetro — revisão para aprovar",
  "message": "PROC-0042 — Linha X — revisão v3 aguarda aprovação. Enviada por autor@delpi.com.br.",
  "type": "info",
  "category": "transformometro",
  "sourceApp": "transformometro",
  "emails": ["gestor@delpi.com.br"],
  "action": {
    "type": "portal_route",
    "label": "Abrir revisão",
    "target": "/apps/transformometro"
  },
  "metadata": {
    "source": "transformometro",
    "event": "revisao:submitted",
    "deepPath": "/apps/transformometro/processos/{processoId}/revisoes/{revisaoId}",
    "dedupeKey": "transformometro:revisao:submitted:{revisaoId}"
  }
}
```

A Core API só entrega a usuários com permissão para abrir o app (`transformometro.view` / rotas do manifesto). Categoria `transformometro` está em `notification_constants.py` e no portal (preferências e Admin).

---

## Variáveis de ambiente

Definidas em `infra/.env`, `infra/.env.prod` e repassadas no `docker-compose` do serviço `transformometro-api`.

| Variável | Obrigatória | Default | Descrição |
|----------|-------------|---------|-----------|
| `TM_NOTIFICATIONS_ENABLED` | Para alertas | `false` | Liga o envio após workflow |
| `TM_CORE_API_URL` | Se enabled | `http://core-api:8000` | Base HTTP na **rede Docker** (sem prefixo `/core-api` do gateway) |
| `CORE_API_INTEGRATIONS_SERVICE_TOKEN` | Se enabled | — | Mesmo valor da Core API (`infra/.env`) |
| `TM_PORTAL_ROUTE` | Não | `/apps/transformometro` | `action.target` e prefixo do `deepPath` |
| `TM_WORKFLOW_APPROVER_EMAILS` | Na submissão* | — | CSV de e-mails |
| `TM_WORKFLOW_APPROVER_ROLE_IDS` | Na submissão* | — | CSV de UUIDs de papéis RBAC |

\* Pelo menos um de `TM_WORKFLOW_APPROVER_EMAILS` ou `TM_WORKFLOW_APPROVER_ROLE_IDS` deve estar preenchido para notificar na submissão.

Aliases aceitos no código: `DELPI_CORE_API_URL`, `DELPI_CORE_API_INTERNAL_URL`, `CORE_API_BASE_URL` (fallback de `TM_CORE_API_URL`).

---

## MFE (portal embedded)

O plugin escuta `postMessage` do portal:

- `DELPI_NAVIGATE` → navega para `metadata.deepPath` (hook `useDelpiPortalBridge`)
- `DELPI_EMBEDDED_ROUTE` → filho informa rota ao pai para sincronizar a URL do portal

Rotas internas usadas no deep link:

```text
/apps/transformometro/processos/{processoId}
/apps/transformometro/processos/{processoId}/revisoes/{revisaoId}
```

---

## Ativação (checklist)

1. `TM_NOTIFICATIONS_ENABLED=true` e aprovadores configurados em `infra/.env`
2. `CORE_API_INTEGRATIONS_SERVICE_TOKEN` já presente (compartilhado com outros apps)
3. Rebuild/restart: `transformometro-api`, **Core API** e **Portal** (categoria nova)
4. RBAC: destinatários precisam de acesso ao Transformômetro no portal
5. Teste: submeter revisão → card no sino → **Abrir revisão** abre a tela correta

---

## Código (referência)

| Peça | Caminho |
|------|---------|
| Cliente HTTP | `transformometro-api/tm_app/infrastructure/integrations/core_notifications_client.py` |
| Regras de destino | `transformometro-api/tm_app/application/services/revisao_workflow_notification_service.py` |
| Disparo | `transformometro-api/tm_app/interface/http/routes/crud_routes.py` (após workflow) |
| Bridge MFE | `plugins/transformometro/src/hooks/useDelpiPortalBridge.ts` |
| Testes | `transformometro-api/tests/test_revisao_workflow_notifications.py` |
