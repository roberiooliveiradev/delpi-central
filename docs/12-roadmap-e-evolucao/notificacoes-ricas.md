# Roadmap — Notificações ricas (Minha DELPI)

> **Status:** Fases 1–7 concluídas · maio/2026  
> **Escopo:** Core API + Portal

---

## 1. O que já está implementado

| Área | Entrega |
|------|---------|
| **Modelo** | `type`, `category`, `presentation` (`text` \| `html` \| `template`), `action`, `htmlContent`, `metadata`, `expiresAt`, `icon` |
| **Segurança** | HTML sanitizado com `bleach` na Core API; validação de `portal_route` e `external_url` |
| **Templates sistema** | `welcome_v1`, `birthday_v1`, `company_event_v1` (somente leitura no Admin) |
| **Templates customizados** | CRUD `GET/POST/DELETE /admin/notifications/templates` + migration `c9d0e1f2a3b4` |
| **Variáveis** | `{userName}`, `{userFullName}`, `{userEmail}` preenchidas por destinatário no dispatch |
| **Admin Portal** | Painéis numerados, pills de formato, múltiplos destinatários, preview por destinatário, `expiresAt` |
| **Usuário** | Sino, home, `/notifications` (abas **Histórico** + **Preferências**), ações no card |
| **RBAC Admin** | `PUT /admin/rbac/users/:id` com `birthDate` para automação de aniversário |
| **API envio** | `POST /admin/notifications`, `POST /integrations/notifications` |
| **API leitura** | `GET /me/notifications` (não lidas), `GET /me/notifications/history` (paginado + filtros) |
| **API usuário** | `PATCH /me/notifications/<id>/important`, `DELETE /me/notifications/<id>` (soft delete) |
| **Preferências** | `GET/PATCH /me/notifications/preferences` (`mutedCategories`) |

---

## 2. Modelo conceitual

| Dimensão | Campo | Exemplos | Uso |
|----------|--------|----------|-----|
| **Severidade visual** | `type` | `info`, `success`, `warning`, `error` | Cor, destaque na UI |
| **Categoria** | `category` | `welcome`, `birthday`, `company_event`, `system`, `announcement`, `custom` | Ícone, template, filtros |
| **Apresentação** | `presentation` | `text`, `html`, `template` | Texto, HTML sanitizado ou card React |
| **Ação (CTA)** | `action` | `portal_route`, `external_url` | Botão no card |

### Ação (`action`)

```json
{
  "type": "portal_route",
  "label": "Abrir Minha DELPI Chat",
  "target": "/apps/minha-delpi-ai"
}
```

| `action.type` | `target` | Comportamento no Portal |
|---------------|----------|-------------------------|
| `none` | — | Só marca como lida |
| `portal_route` | `/admin`, `/apps/crm` | `navigate(target)` |
| `external_url` | `https://...` | Nova aba (`noopener`) |

---

## 3. Conteúdo HTML personalizado

- Campo `htmlContent` (persistido como `html_content`).
- **Sanitização obrigatória no backend** (`bleach`) antes de gravar.
- Tags permitidas: `p`, `br`, `strong`, `em`, `ul`, `ol`, `li`, `a`, `h3`, `h4`, `span`.
- `message` continua como **fallback** (preview, clientes simples).

---

## 4. Templates

### Sistema (somente leitura)

| Template | `category` | Variáveis |
|----------|------------|-----------|
| Boas-vindas | `welcome` | `userName` (auto) |
| Aniversário | `birthday` | `userName` (auto), `years` |
| Evento empresa | `company_event` | `eventName`, `eventDate`, `location` |

### Customizados

Criados no Admin → armazenados em `notification_custom_templates` → renderizados com as mesmas regras de variáveis.

---

## 5. API

### `GET /me/notifications`

Lista **não lidas** e não expiradas (array, compatível com o sino).

### `GET /me/notifications/history`

Histórico paginado.

| Query | Valores | Default |
|-------|---------|---------|
| `status` | `all`, `unread`, `read` | `all` |
| `category` | categorias do modelo | — |
| `important` | `true` | — |
| `limit` | 1–100 | `20` |
| `offset` | ≥ 0 | `0` |

```json
{
  "items": [{ "id": "uuid", "title": "…", "message": "…", "read": false, "createdAt": "…" }],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

### Envio `POST /admin/notifications` e `/integrations/notifications`

Campos opcionais: `category`, `presentation`, `htmlContent`, `templateId`, `templateVars`, `icon`, `action`, `metadata`, `expiresAt`, `scheduledAt`, `broadcast`, `userIds`, `emails`, `roleIds`, `groupIds`.

Resposta de envio imediato: `201` com `createdCount`. Agendado: `202` com `status: "pending"` e `scheduledAt`.

### Auditoria e agendamento (Admin)

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/admin/notifications/dispatches` | Lista campanhas (`limit`, `offset`) |
| GET | `/admin/notifications/dispatches/:id` | Detalhe com `payload` (edição) |
| PUT | `/admin/notifications/dispatches/:id` | Atualiza envio **agendado** `pending` (body igual ao POST + `scheduledAt`) |
| POST | `/admin/notifications/dispatches/process-pending` | Processa envios com `scheduledAt` vencido |
| POST | `/integrations/notifications/process-pending` | Mesmo processamento (service token, para cron) |

Tabela `notification_dispatches`: payload completo, status, contadores, erro.

---

## 6. UI Portal

Detalhes: [Portal — Notificações](../06-portal-frontend/notificacoes.md).

| Superfície | Comportamento |
|------------|----------------|
| **Sidebar (sino)** | Não lidas; marcar lida, importante e excluir; “Ver todas” → `/notifications` |
| **Home** | Resumo + até 4 cards com as mesmas ações |
| **`/notifications` — Histórico** | Status (todas/não lidas/lidas), categoria, importantes, paginação, `NotificationCard` |
| **`/notifications` — Preferências** | `NotificationPreferencesPanel` — silenciar categorias (exceto `system`) |
| **Admin → Notificações** | Envio, `roleIds`/`groupIds`, agendamento, histórico com **Editar** em pendentes, preview HTML, templates |
| **Admin → Usuário** | Data de nascimento no modal RBAC |

---

## 7. Fases (roadmap)

| Fase | Status | Entrega |
|------|--------|---------|
| **1** | ✅ | Migration rica, HTML, action, category, UI base |
| **2** | ✅ | Templates React + customizados + variáveis |
| **2b** | ✅ | Layout admin em painéis, editor HTML com toolbar de variáveis |
| **3** | ✅ | `expiresAt`, histórico paginado, **agendamento** (`scheduledAt`) e **auditoria de envios** (`notification_dispatches`) |
| **4** | ✅ | Preferências do usuário (opt-out por categoria, exceto `system`) |
| **5** | ✅ | Centro `/notifications` com filtros (status, categoria, importantes), excluir e marcar importante |
| **6** | ✅ | Automação (welcome no 1º login, aniversário via cron), destinatários por `roleIds`/`groupIds` |
| **7** | ✅ | Rate limit em integrações; pré-visualização HTML no Admin |

---

## 8. Envios agendados — processamento automático

Campanhas com `scheduledAt` ficam `pending` até `scheduled_at <= now`. A **Core API** inclui um scheduler em background (thread daemon) que chama o mesmo fluxo de `process-pending` a cada intervalo configurável — **não é necessário clicar em “Processar agendados”** no Admin.

| Variável | Default | Descrição |
|----------|---------|-----------|
| `NOTIFICATIONS_DISPATCH_SCHEDULER_ENABLED` | `true` | Liga/desliga o scheduler interno |
| `NOTIFICATIONS_DISPATCH_POLL_SECONDS` | `60` | Intervalo entre verificações (mín. 15s) |
| `NOTIFICATIONS_DISPATCH_BATCH_LIMIT` | `20` | Máx. dispatches por ciclo (máx. 50) |

O botão **Processar agendados** e o cron externo continuam úteis para forçar processamento imediato ou redundância em ambientes com várias réplicas da API (onde cada instância roda o scheduler — use cron + service token e desabilite o interno com `NOTIFICATIONS_DISPATCH_SCHEDULER_ENABLED=false` se preferir um único worker).

Script opcional: `scripts/process-pending-notifications.sh`.

```bash
export DELPI_API_BASE_URL="https://<host>"
export CORE_API_INTEGRATIONS_SERVICE_TOKEN="..."
./scripts/process-pending-notifications.sh

# Aniversários (1x/dia, requer `users.birth_date` preenchido no Admin):
./scripts/run-birthday-notifications.sh

# Ambos (pending + aniversários):
./scripts/run-notification-maintenance.sh

# Ou curl direto:
curl -s -X POST "https://<host>/core-api/integrations/notifications/process-pending" \
  -H "X-Delpi-Service-Token: $CORE_API_INTEGRATIONS_SERVICE_TOKEN"

# Ou superadmin na rota admin (menos indicado para cron)
curl -s -X POST "https://<host>/core-api/admin/notifications/dispatches/process-pending" \
  -H "Authorization: Bearer <token>"
```

---

## 9. Segurança

1. HTML sempre sanitizado na Core API.
2. `portal_route` só paths relativos (`/...`), sem `//` externo.
3. `external_url` só `https:`.
4. Integrações externas: rate limit (`NOTIFICATIONS_INTEGRATION_RATE_LIMIT` / `NOTIFICATIONS_INTEGRATION_RATE_WINDOW_SECONDS`, default 60/min por IP e rota).

---

## 10. Evoluções opcionais (pós-fase 7)

| Item | Descrição |
|------|-----------|
| Retenção | Job para arquivar/remover notificações lidas antigas |
| Rate limit | Redis para múltiplas réplicas da Core API |
| WYSIWYG | Editor rich-text no Admin (hoje: HTML + preview lado a lado) |

---

## 11. Referências

- [Notificações Core API](../04-core-api/notificacoes.md)
- [Portal — Notificações](../06-portal-frontend/notificacoes.md)
- [Roadmap notificações (base)](../../minha-delpi-ai-api/docs/roadmap/notificacoes-minha-delpi.md)
