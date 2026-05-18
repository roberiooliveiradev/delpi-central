# Portal — Notificações (usuário)

> **Código:** `portal/src/ui/NotificationsPage.tsx`, `portal/src/components/notifications/`  
> **API:** `portal/src/data/coreApi.ts` → `/core-api/me/notifications*`  
> **Backend:** [Notificações Core API](../04-core-api/notificacoes.md)

---

## 1. Superfícies

| Superfície | Rota / local | Comportamento |
|------------|--------------|---------------|
| **Sino (Sidebar)** | `Sidebar.tsx` | Até as não lidas do contexto; marcar lida, importante, excluir; link “Ver todas” |
| **Home** | `/` | Resumo com até 4 cards e mesmas ações rápidas |
| **Centro de notificações** | `/notifications` | Histórico paginado + preferências em abas |
| **Admin** | `/admin` → Notificações | Envio, templates, agendamento, histórico de campanhas — ver [roadmap](../12-roadmap-e-evolucao/notificacoes-ricas.md) |

---

## 2. Página `/notifications`

### Abas principais

| Aba | Conteúdo |
|-----|----------|
| **Histórico** | Filtros de status (Todas / Não lidas / Lidas), categoria, toggle “Importantes”, lista paginada (`PAGE_SIZE=12`), ações no card |
| **Preferências** | Silenciar categorias mutáveis (`mutedCategories`); categoria `system` não pode ser desativada |

O subtítulo do cabeçalho muda conforme a aba ativa. Após salvar preferências, o sino recarrega via `reloadNotifications()` do `AuthContext`.

### Layout

- Container com `max-width: 920px`, padding alinhado à Home.
- Classe `align-self: flex-start` evita que `.content` (flex) estique a página e distorça a barra de abas.

### Componentes

| Arquivo | Papel |
|---------|--------|
| `NotificationCard` | Variantes `compact` (sino/home) e `page` (histórico) |
| `useNotificationActions` | Marcar lida, excluir (com confirmação), alternar importante |
| `NotificationPreferencesPanel` | Variante `page` na aba Preferências; `embedded` se reutilizado |
| `notificationHtmlPreview.ts` | Preview HTML no Admin (variáveis de exemplo) |

---

## 3. `coreApi.ts` — métodos do usuário

| Método | HTTP | Observação |
|--------|------|------------|
| `getNotifications()` | GET `/me/notifications` | Ordena importantes primeiro, depois `createdAt` desc |
| `getNotificationHistory(params)` | GET `/me/notifications/history` | Retorna `{ items, total, limit, offset }` |
| `markNotificationRead(id)` | POST `/me/notifications/:id/read` | |
| `markAllNotificationsRead()` | POST `/me/notifications/read-all` | |
| `deleteNotification(id)` | DELETE `/me/notifications/:id` | Soft delete no backend |
| `setNotificationImportant(id, flag)` | PATCH `/me/notifications/:id/important` | Body `{ isImportant }` |
| `getNotificationPreferences()` | GET `/me/notifications/preferences` | |
| `updateNotificationPreferences(muted)` | PATCH `/me/notifications/preferences` | Body `{ mutedCategories }` |

---

## 4. Tempo real

O `AuthContext` escuta eventos Socket.IO com `entity === "notifications"` e chama `loadNotificationsData()` para atualizar o sino sem recarregar a página.

---

## 5. Admin — data de nascimento (automação)

No modal **Editar RBAC** (`UserRbacModal`), o campo **Data de nascimento** é enviado no `PUT /admin/rbac/users/:id` como `birthDate` (ISO `YYYY-MM-DD` ou `null` para limpar). Necessário para o cron de aniversários (`birthday_v1`).

Salvar papéis/grupos no mesmo modal usa o mesmo `PUT` com `roleIds` e `groupIds`.

---

## 6. Build e deploy

```bash
cd portal
npm run build   # tsc -b && vite build
```

Em Docker (pasta `infra/`):

```bash
docker compose -f docker-compose.yml --env-file .env build portal
docker compose -f docker-compose.yml --env-file .env up -d portal
```

---

## 7. Relacionados

- [Notificações Core API](../04-core-api/notificacoes.md)
- [Roadmap notificações ricas](../12-roadmap-e-evolucao/notificacoes-ricas.md)
- [Controllers e rotas](../04-core-api/controllers-e-rotas.md)
