# Minha DELPI — Core API: Notificações

> **Arquivo:** `docs/04-core-api/notificacoes.md`  
> **Status:** documentação oficial (maio/2026)  
> **Produto:** Minha DELPI  
> **Escopo:** notificações de usuário na Core API e integração com Portal  
> **Evolução rica:** [Roadmap notificações ricas](../12-roadmap-e-evolucao/notificacoes-ricas.md)  
> **Portal (UI):** [Notificações no frontend](../06-portal-frontend/notificacoes.md)

---

## 1. Objetivo

Este documento descreve o sistema de **notificações** da Core API da Minha DELPI.

As notificações permitem que a plataforma registre mensagens direcionadas a usuários, liste notificações não lidas, marque notificações como lidas e atualize o Portal quando houver mudanças relevantes.

---

## 2. Papel das notificações

Notificações são mensagens persistidas por usuário.

Elas podem ser usadas para:

- avisos administrativos;
- mensagens de sistema;
- alertas de alterações relevantes;
- confirmações de eventos;
- notificações de teste em desenvolvimento;
- comunicação futura entre módulos e usuários.

O sistema atual é simples e centrado no usuário autenticado.

---

## 3. Tabelas e modelo

### 3.1 `notifications`

Model: `app/infrastructure/db/models/notification.py`.

| Campo | Descrição |
|-------|-----------|
| `id` | UUID |
| `user_id` | Destinatário (FK usuário) |
| `title` | Título opcional |
| `message` | Texto principal / fallback |
| `type` | Severidade visual: `info`, `success`, `warning`, `error` |
| `category` | `system`, `welcome`, `birthday`, `company_event`, `announcement`, `custom` |
| `presentation` | `text`, `html`, `template` |
| `html_content` | HTML sanitizado (`bleach`) |
| `action_type`, `action_label`, `action_target` | CTA (`portal_route`, `external_url`) |
| `icon`, `metadata` | Metadados de UI |
| `expires_at` | Expiração opcional |
| `is_important` | Destaque na listagem |
| `read_at` | Leitura (`NULL` = não lida) |
| `deleted_at` | Soft delete (não listado para o usuário) |
| `created_at` | Criação |

Migrations relevantes (ordem): `c9d0e1f2a3b4` (campos ricos), `e1f2a3b4c5d6` (`is_important`, `deleted_at`), `f2a3b4c5d6e7` (preferências), `g3b4c5d6e7f8` (`users.birth_date`).

### 3.2 `user_notification_preferences`

| Campo | Descrição |
|-------|-----------|
| `user_id` | PK / FK usuário |
| `muted_categories` | JSON — categorias silenciadas (sem `system`) |

### 3.3 `notification_dispatches`

Auditoria e agendamento de campanhas (payload, `scheduled_at`, status, contadores). Ver [roadmap](../12-roadmap-e-evolucao/notificacoes-ricas.md).

---

## 4. API HTTP (`me_controller`)

Todas exigem `@require_auth()`.

| Método | Path | Use case |
|---|---|---|
| GET | `/me/notifications` | `ListUnreadNotificationsUseCase` (não lidas, não expiradas, não excluídas) |
| GET | `/me/notifications/history` | `ListNotificationsUseCase` (paginado; ver query abaixo) |
| POST | `/me/notifications/<id>/read` | `MarkNotificationReadUseCase` |
| POST | `/me/notifications/read-all` | `MarkAllNotificationsReadUseCase` |
| PATCH | `/me/notifications/<id>/important` | `SetNotificationImportantUseCase` — body `{ "isImportant": true \| false }` |
| DELETE | `/me/notifications/<id>` | `DeleteNotificationUseCase` (soft delete: `deleted_at`) |
| GET | `/me/notifications/preferences` | `GetNotificationPreferencesUseCase` |
| PATCH | `/me/notifications/preferences` | `UpdateNotificationPreferencesUseCase` — body `{ "mutedCategories": ["announcement", ...] }` |
| POST | `/me/notifications/test` | `NotifyUserUseCase` (desabilitado quando `FLASK_ENV=production`) |

No dispatch (`POST /admin/notifications` e integrações), usuários que silenciaram a `category` do envio são ignorados. A categoria `system` não pode ser silenciada.

Destinatários adicionais no body: `roleIds` (papel direto + via grupo), `groupIds` (membros do grupo).

### Automação (integrações, service token)

| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/integrations/notifications/automation/birthdays` | Envia `birthday_v1` para usuários ativos com `birth_date` = hoje (idempotente por dia) |

Boas-vindas: no **primeiro login** (criação do usuário local), dispara `welcome_v1` automaticamente (respeita preferências).

`users.birth_date` (YYYY-MM-DD): editável no Admin → usuário → data de nascimento.

### Rate limit (integrações)

Rotas sob `/integrations/notifications` usam limite por IP e path (padrão **60 req / 60s**). Variáveis:

- `NOTIFICATIONS_INTEGRATION_RATE_LIMIT`
- `NOTIFICATIONS_INTEGRATION_RATE_WINDOW_SECONDS`

Resposta `429` com `{ "error": "Too Many Requests", ... }`.

Admin e integrações: `POST /admin/notifications`, `POST /integrations/notifications`, templates em `/admin/notifications/templates`, auditoria em `GET /admin/notifications/dispatches`, edição de agendados em `GET/PUT /admin/notifications/dispatches/:id` (somente `status=pending` com `scheduled_at` futuro), processamento em `POST .../dispatches/process-pending` — ver [roadmap](../12-roadmap-e-evolucao/notificacoes-ricas.md).

Resposta de listagem (`serialize_notification`):

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Título",
  "message": "Texto",
  "type": "info",
  "category": "announcement",
  "presentation": "text",
  "htmlContent": null,
  "icon": null,
  "metadata": null,
  "read": false,
  "isImportant": false,
  "createdAt": "2026-05-15T12:00:00Z",
  "expiresAt": null,
  "action": { "type": "portal_route", "label": "Abrir", "target": "/apps/..." }
}
```

`read` deriva de `read_at IS NOT NULL`. Registros com `deleted_at` não aparecem nas listagens do usuário.

### `PUT /admin/rbac/users/<user_id>`

Usado pelo modal RBAC do Portal para papéis, grupos e data de nascimento. Body parcial:

```json
{
  "roleIds": ["uuid", "..."],
  "groupIds": ["uuid", "..."],
  "birthDate": "1990-05-18",
  "is_superadmin": false
}
```

`birthDate` vazio ou `null` limpa o campo. Handler: `update_user` em `rbac_controller.py` (não confundir com helper `_parse_birth_date`).

### `GET /me/notifications/history` — query

| Parâmetro | Valores | Default |
|-----------|---------|---------|
| `status` | `all`, `unread`, `read` | `all` |
| `category` | `system`, `welcome`, `birthday`, `company_event`, `announcement`, `custom` | — |
| `important` | `true` (somente importantes) | — |
| `limit` | 1–100 | `20` |
| `offset` | ≥ 0 | `0` |

Ordenação: importantes primeiro, depois `created_at` descendente.

---

## 5. Estado de leitura

Uma notificação é considerada não lida quando:

```text
read_at IS NULL
```

Uma notificação é considerada lida quando:

```text
read_at IS NOT NULL
```

Ao marcar como lida, a Core API deve preencher `read_at` com o timestamp atual.

---

## 6. `GET /me/notifications`

Finalidade:

```text
Listar notificações não lidas do usuário atual.
```

Proteção:

```text
require_auth
```

Use case:

```text
ListUnreadNotificationsUseCase
```

Fluxo:

```text
Usuário autenticado
  ↓
Core API obtém user_id
  ↓
Repository busca notifications onde user_id = usuário e read_at IS NULL
  ↓
Retorna lista ao Portal
```

Resposta (implementação atual):

```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "title": "Título",
    "message": "Mensagem",
    "type": "info",
    "read": false,
    "createdAt": "2026-05-07T10:30:00Z"
  }
]
```

---

## 7. `POST /me/notifications/<notification_id>/read`

Finalidade:

```text
Marcar uma notificação específica como lida.
```

Proteção:

```text
require_auth
```

Use case:

```text
MarkNotificationReadUseCase
```

Fluxo esperado:

```text
Recebe notification_id
  ↓
Busca notificação
  ↓
Valida se pertence ao usuário atual
  ↓
Preenche read_at
  ↓
Coleta evento de notificação lida
  ↓
Retorna ok
```

Resposta esperada:

```json
{
  "ok": true
}
```

---

## 8. `POST /me/notifications/read-all`

Finalidade:

```text
Marcar todas as notificações não lidas do usuário atual como lidas.
```

Proteção:

```text
require_auth
```

Use case:

```text
MarkAllNotificationsReadUseCase
```

Fluxo:

```text
Usuário autenticado
  ↓
Busca notificações não lidas do usuário
  ↓
Atualiza read_at de todas
  ↓
Coleta evento
  ↓
Retorna ok
```

Resposta esperada:

```json
{
  "ok": true
}
```

---

## 9. `POST /me/notifications/test`

Cria notificação de teste para o usuário atual (`NotifyUserUseCase`).

- Exige `@require_auth()`.
- **Produção:** retorna `403` quando `FLASK_ENV=production` (`forbidden` — test notifications are disabled in production).
- Uso: desenvolvimento, validação do sino e eventos Socket.IO.

---

## 10. Use cases

### 10.1 `ListUnreadNotificationsUseCase`

Responsabilidade:

```text
Listar notificações não lidas de um usuário.
```

Entrada:

```text
user_id
```

Saída:

```text
lista de notificações serializáveis
```

---

### 10.2 `NotifyUserUseCase`

Responsabilidade:

```text
Criar uma notificação para um usuário.
```

Entrada conceitual:

```text
user_id
title
message
type
```

Fluxo:

```text
Cria registro em notifications
  ↓
Coleta evento UserNotifiedEvent ou AdminChangedEvent equivalente
```

---

### 10.3 `MarkNotificationReadUseCase`

Responsabilidade:

```text
Marcar uma notificação como lida.
```

Validações esperadas:

- notificação existe;
- notificação pertence ao usuário atual;
- operação deve ser idempotente quando já estiver lida.

---

### 10.4 `MarkAllNotificationsReadUseCase`

Responsabilidade:

```text
Marcar todas as notificações do usuário como lidas.
```

Validações esperadas:

- usuário autenticado;
- atualizar somente notificações do próprio usuário.

---

## 11. Repository de notificações

Port: `app/domain/ports/notification_repository.py` — implementação: `notification_repository.py`.

Operações principais:

| Método | Uso |
|--------|-----|
| `create` / dispatch em lote | Envio admin e integrações |
| `list_unread` | `GET /me/notifications` |
| `list_for_user` (paginado, filtros) | `GET /me/notifications/history` |
| `get` | Validação de ownership em read/delete/important |
| `mark_read`, `mark_all_read` | Leitura |
| `soft_delete` | `DELETE /me/notifications/:id` |
| `set_important` | `PATCH .../important` |
| `filter_user_ids_accepting_category` | Dispatch respeita preferências |

Preferências: `user_notification_preferences` no UoW (`get` / `upsert` muted categories).

---

## 12. Eventos de notificações

Eventos conceituais relacionados:

```text
UserNotifiedEvent
NotificationMarkedReadEvent
AllNotificationsMarkedReadEvent
```

Dependendo da implementação atual, eventos podem ser publicados como eventos de domínio específicos ou como `AdminChangedEvent` direcionado.

Padrão recomendado para eventos direcionados:

```python
AdminChangedEvent(
    entity="notifications",
    action="notification_created",
    payload={
        "notificationId": "uuid"
    },
    target_user_id=user_id,
)
```

---

## 13. Socket.IO

O Portal pode receber eventos em tempo real via Socket.IO.

Fluxo:

```text
Portal conecta com token
  ↓
Core API valida JWT
  ↓
Socket entra na sala do usuário
  ↓
Evento direcionado é emitido para target_user_id
```

Evento emitido pelo dispatcher:

```text
admin.changed
```

Exemplo de payload:

```json
{
  "entity": "notifications",
  "action": "notification_created",
  "payload": {
    "notificationId": "uuid"
  }
}
```

---

## 14. Comportamento esperado do Portal

Documentação detalhada da UI: [Portal — Notificações](../06-portal-frontend/notificacoes.md).

Resumo:

| Superfície | API principal |
|------------|----------------|
| Sino / Home | `GET /me/notifications` + ações no card |
| `/notifications` — aba **Histórico** | `GET /me/notifications/history` (filtros + paginação) |
| `/notifications` — aba **Preferências** | `GET/PATCH /me/notifications/preferences` |
| Admin → Notificações | `POST /admin/notifications`, templates, dispatches |
| Admin → Usuário (RBAC) | `PUT /admin/rbac/users/:id` (`roleIds`, `birthDate`) |

Fluxo após login: `AuthContext` carrega notificações → contador no sino.

Fluxo Socket.IO: evento `admin.changed` com `entity: "notifications"` → `reloadNotifications()`.

---

## 15. Regras de autorização

Notificações são sempre escopadas ao usuário.

Regras:

- usuário só lista suas próprias notificações;
- usuário só marca suas próprias notificações como lidas;
- notificação de outro usuário deve retornar 403 ou 404 seguro;
- endpoints exigem autenticação.

Recomendação:

> Para evitar vazamento de existência de notificação de outro usuário, pode-se retornar 404 em vez de 403 quando a notificação não pertence ao usuário atual.

---

## 16. Tipos de notificação

O campo `type` pode representar categoria visual ou semântica.

Valores sugeridos:

```text
info
success
warning
error
system
```

A documentação do frontend deve definir como cada tipo é renderizado.

Ponto de atenção:

> Se `type` ainda não for validado por enum, padronizar valores no uso da aplicação para evitar variações inconsistentes.

---

## 17. Erros comuns

### 17.1 Não autenticado

```json
{
  "errors": [
    {
      "code": "unauthorized",
      "message": "Authentication required",
      "path": "_global"
    }
  ]
}
```

Status:

```text
401 Unauthorized
```

---

### 17.2 Notificação não encontrada

```json
{
  "errors": [
    {
      "code": "notification.not_found",
      "message": "Notification not found",
      "path": "notification_id"
    }
  ]
}
```

Status:

```text
404 Not Found
```

---

### 17.3 Sem permissão para notificação

```json
{
  "errors": [
    {
      "code": "forbidden",
      "message": "Permission denied",
      "path": "_global"
    }
  ]
}
```

Status:

```text
403 Forbidden
```

---

## 18. Considerações de retenção

O modelo atual documentado não define política de retenção.

Possíveis políticas futuras:

- remover notificações lidas após X dias;
- arquivar notificações antigas;
- limitar quantidade de notificações por usuário;
- paginar histórico de notificações;
- separar não lidas de histórico completo;
- criar job de limpeza.

---

## 19. Paginação e histórico

- **Não lidas (sino):** `GET /me/notifications` — array sem paginação (somente não lidas, não expiradas, não excluídas).
- **Histórico completo:** `GET /me/notifications/history` — `limit`/`offset` + filtros (`status`, `category`, `important`).

---

## 20. Boas práticas

1. Notificações devem ser escopadas por usuário.
2. Não retornar notificações de outros usuários.
3. Marcar como lida deve ser idempotente.
4. Eventos devem ser direcionados ao usuário quando possível.
5. Portal deve recarregar notificações ao receber evento.
6. Evitar endpoint de teste em produção sem proteção.
7. Não armazenar dados sensíveis em mensagens de notificação.
8. Padronizar valores de `type`.
9. Avaliar paginação se volume aumentar.
10. Confirmar contrato repository/use case para `get`.

---

## 21. Checklist de implementação

- [x] `GET /me/notifications` — escopo do usuário, não lidas.
- [x] `GET /me/notifications/history` — paginação e filtros.
- [x] `POST /me/notifications/<id>/read` — ownership.
- [x] `DELETE`, `PATCH .../important`, preferências por categoria.
- [x] `read_at` ao marcar lida; soft delete com `deleted_at`.
- [x] Eventos Socket.IO direcionados; Portal recarrega sino.
- [x] `POST /me/notifications/test` bloqueado em produção.
- [x] Dispatch com `roleIds`/`groupIds`, welcome e aniversário.
- [x] Rate limit em `/integrations/notifications`.
- [ ] Política de retenção/arquivamento de histórico antigo (opcional).
- [ ] Rate limit multi-instância via Redis (evolução).

---

## 22. Pontos de atenção

1. Não armazenar dados sensíveis em `message` / `htmlContent`.
2. HTML sempre sanitizado no backend antes de persistir.
3. Categoria `system` não pode ser silenciada nas preferências.
4. Cron: `scripts/process-pending-notifications.sh`, `run-birthday-notifications.sh`, `run-notification-maintenance.sh`.
5. `users.birth_date` deve estar preenchido no Admin para automação de aniversário.
6. Notificação comunica estado ao usuário — **não** substitui RBAC/permissões.
7. Rate limit in-memory não escala horizontalmente sem Redis compartilhado.

---

## 23. Documentos relacionados

| Documento | Conteúdo |
|-----------|----------|
| [Roadmap notificações ricas](../12-roadmap-e-evolucao/notificacoes-ricas.md) | Fases, Admin, cron, templates |
| [Portal — Notificações](../06-portal-frontend/notificacoes.md) | UI `/notifications`, sino, `coreApi` |
| [Controllers e rotas](./controllers-e-rotas.md) | Índice de rotas HTTP |
| [RBAC](../03-autenticacao-autorizacao/rbac.md) | Papéis e `PUT` usuário |

