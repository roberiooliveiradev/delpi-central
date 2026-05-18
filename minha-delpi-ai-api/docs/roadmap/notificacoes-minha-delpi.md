# Roadmap — Notificações Minha DELPI

> **Status:** em implementação (maio/2026)  
> **Escopo:** Core API (persistência e rotas), Portal (tempo real), plugin `minha-delpi-chat` (consumo e administração)

---

## 1. Contexto arquitetural atual

### Onde vive hoje

| Camada | Repositório | Responsabilidade |
|--------|-------------|------------------|
| **Core API** | `core-api/` | Tabela `notifications`, use cases, rotas `/me/notifications` |
| **Portal** | `portal/` | Sino na sidebar, `CoreApi.getNotifications()`, Socket.IO `admin.changed` |
| **Chat** | `plugins/minha-delpi-chat/` | **Não** consumia notificações (lacuna) |
| **AI API** | `minha-delpi-ai-api/` | Chat/LLM; **não** é dona de notificações de plataforma |

### Fluxo existente (usuário final)

```text
Login → GET /core-api/me/notifications
      → Portal renderiza contador/lista
      → POST .../read | .../read-all
```

### Lacunas identificadas

1. `UserNotifiedEvent` não era despachado via Socket.IO (apenas `AdminChangedEvent` é emitido).
2. `NotificationRepository` não expunha `get`, mas `MarkNotificationReadUseCase` dependia disso.
3. Marcar como lida **não validava** ownership do usuário autenticado.
4. Não havia rota para **broadcast** (geral) nem envio **administrativo** multiusuário.
5. Aplicações externas não tinham contrato HTTP dedicado (service token).
6. Plugin do chat não exibia notificações nem painel para disparo administrativo.

### Princípio de design

Notificações permanecem na **Core API** (clean architecture já estabelecida). O chat e apps externos **consomem** ou **disparam** via HTTP, sem duplicar persistência na `minha-delpi-ai-api`.

---

## 2. Objetivos desta onda

| # | Objetivo | Prioridade |
|---|----------|------------|
| A | Criar notificações **gerais** (broadcast para usuários ativos) | Alta |
| B | Criar notificações **direcionadas** (`userIds` / `emails`) | Alta |
| C | Rota **integrations** para apps externos (service token) | Alta |
| D | Rota **admin** para superadmin no painel do chat | Alta |
| E | UI no chat: sino + lista + marcar lida | Alta |
| F | Aba admin no chat para compor/enviar notificações | Média |
| G | Tempo real via `admin.changed` + reload no Portal | Alta |
| H | Testes unitários dos novos use cases | Alta |

---

## 3. Contratos HTTP (planejados)

### 3.1 Usuário autenticado (já existente)

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/me/notifications` | Lista não lidas do usuário |
| POST | `/me/notifications/<id>/read` | Marca uma como lida (com ownership) |
| POST | `/me/notifications/read-all` | Marca todas como lidas |

### 3.2 Administração (novo)

`POST /admin/notifications` — `@require_superadmin()`

```json
{
  "broadcast": true,
  "userIds": ["uuid-opcional"],
  "emails": ["user@empresa.com"],
  "title": "Manutenção",
  "message": "O chat ficará indisponível às 22h.",
  "type": "warning"
}
```

Resposta:

```json
{
  "createdCount": 42,
  "notificationIds": ["..."]
}
```

Regras:

- `broadcast: true` → fan-out para todos os usuários **ativos**.
- Sem broadcast → exige `userIds` e/ou `emails` (união deduplicada).
- `type`: `info` | `success` | `warning` | `error`.

### 3.3 Integrações externas (novo)

`POST /integrations/notifications` — header `X-Delpi-Service-Token`

Mesmo body da rota admin. Variável de ambiente:

```text
CORE_API_INTEGRATIONS_SERVICE_TOKEN
```

Exemplo (curl):

```bash
curl -X POST "$CORE_API_URL/integrations/notifications" \
  -H "Content-Type: application/json" \
  -H "X-Delpi-Service-Token: $TOKEN" \
  -d '{"userIds":["..."], "title":"Novo relatório", "message":"Seu PDF está pronto.", "type":"info"}'
```

---

## 4. Camadas backend (Core API)

```text
interfaces/http/notifications_controller.py
        ↓
application/use_cases/dispatch_notifications_use_case.py
application/use_cases/notify_user_use_case.py (ajuste evento)
application/use_cases/mark_notification_read_use_case.py (ownership)
        ↓
domain/ports/notification_repository.py (+ get)
domain/events/admin_events.py (AdminChangedEvent → socket)
        ↓
infrastructure/persistence/sqlalchemy/notification_repository.py
```

### Evento tempo real

Após cada notificação criada:

```python
AdminChangedEvent(
    entity="notifications",
    action="notification_created",
    payload={"notificationId": "..."},
    target_user_id=user_id,
)
```

Portal e chat recarregam `GET /me/notifications` ao receber `admin.changed` com `entity === "notifications"`.

---

## 5. Frontend (plugin minha-delpi-chat)

| Artefato | Função |
|---------|--------|
| `data/api/coreApi.ts` | Cliente HTTP `/core-api/me/notifications` |
| `state/hooks/useChatNotifications.ts` | Estado, polling leve, ações de leitura |
| `ui/components/notifications/ChatNotificationBell.tsx` | Sino na sidebar do chat |
| `ui/components/admin/notifications/AdminNotificationsTab.tsx` | Formulário broadcast/direcionado |

O plugin recebe `getAccessToken` do Portal (`AppHost`) — mesmo padrão do `chatApi`.

---

## 6. Fases e critérios de aceite

### Fase 1 — Fundação (esta entrega)

- [x] Roadmap documentado
- [x] `DispatchNotificationsUseCase` com broadcast e direcionado
- [x] Rotas `/admin/notifications` e `/integrations/notifications`
- [x] Correção de eventos Socket + ownership em mark read
- [x] UI sino no chat + aba admin
- [x] Testes unitários (`test_dispatch_notifications_use_case`, `test_notifications_controller`)

**Aceite:** superadmin envia broadcast pelo admin do chat; usuário vê no sino; app externo envia com service token; marcar lida só afeta notificações próprias.

### Fase 2 — Evolução (futuro)

- [ ] Paginação `GET /me/notifications?status=all&page=1`
- [ ] Campo `source_app` / `link` / `metadata` (migration)
- [ ] Permissão fina `notifications.manage` (além de superadmin)
- [ ] Rate limit na rota integrations
- [ ] Auditoria de disparos (`audit_logs`)
- [ ] Agendamento (notificação programada)

### Fase 3 — Produto

- [ ] Preferências do usuário (opt-out por tipo)
- [ ] Templates por aplicação
- [ ] Métricas de entrega/leitura no admin

---

## 7. Referências

- [Notificações Core API](../../../docs/04-core-api/notificacoes.md)
- [Clean Architecture](../../../docs/01-arquitetura/clean-architecture.md)
- [Event-driven e Socket](../../../docs/01-arquitetura/event-driven-e-socket.md)
- [Roadmap admin chat](./admin-minha-delpi-chat.md)
