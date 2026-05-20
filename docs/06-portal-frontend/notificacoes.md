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
| **Histórico** | Filtros de status (Todas / Não lidas / Lidas), categoria, toggle “Importantes”, lista paginada (`PAGE_SIZE=12`), ações no card, **seleção múltipla** (marcar lidas / excluir em lote na página atual) |
| **Preferências** | Silenciar categorias mutáveis (`mutedCategories`); categoria `system` não pode ser desativada |

O subtítulo do cabeçalho muda conforme a aba ativa. Após salvar preferências, o sino recarrega via `reloadNotifications()` do `AuthContext`.

### Layout

- Container com `max-width: 920px`, padding alinhado à Home.
- Classe `align-self: flex-start` evita que `.content` (flex) estique a página e distorça a barra de abas.

### Componentes

| Arquivo | Papel |
|---------|--------|
| `NotificationCard` | Variantes `compact` (sino/home) e `page` (histórico) |
| `useNotificationActions` | Marcar lida, excluir, alternar importante; `bulkMarkRead` / `bulkDelete` na página Histórico |
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

O `AuthContext` atualiza o sino por três caminhos:

1. **Socket.IO** — evento `admin.changed` com `entity === "notifications"` dispara `loadNotificationsData()`.
2. **Polling** — a cada 60 s (aba visível) recarrega a lista do sino.
3. **Foco da aba** — ao voltar para a aba (`visibilitychange`) e ao abrir o dropdown do sino na Sidebar.

Não é necessário recarregar a página manualmente após um envio agendado.

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

## 7. Apps iframe — deep link ao clicar

Quando `metadata.deepPath` está presente (ex.: notificações do Controle MP), o portal:

1. Navega para `buildPortalEmbeddedPath(basePath, deepPath)` — ex.: `/controle-mp/conversations/109` (rota wildcard `embedded`).
2. Envia `postMessage` `{ type: "DELPI_NAVIGATE", path: deepPath }` ao iframe.
3. Mantém o deep link em `sessionStorage` até o iframe confirmar recebimento.
4. Escuta `DELPI_EMBEDDED_ROUTE` do filho para manter a barra de URL sincronizada ao navegar dentro do app.
5. Envia `DELPI_THEME` para o iframe seguir claro/escuro/sistema do menu do portal (genérico para todo app embedded; o filho implementa o listener).

Código: `embeddedAppNotification.ts`, `notificationNavigation.ts`, `App.tsx`, `AppHost.tsx`, `NotificationCard.tsx`, `utils/theme.ts`.

Tutorial: [conectar-aplicacao-iframe.md](../10-guias-operacionais/conectar-aplicacao-iframe.md) · Contrato: [embedded-app-deep-links.md](../05-portal/embedded-app-deep-links.md).

---

## 8. Relacionados

- [Notificações Core API](../04-core-api/notificacoes.md)
- [Roadmap notificações ricas](../12-roadmap-e-evolucao/notificacoes-ricas.md)
- [Controllers e rotas](../04-core-api/controllers-e-rotas.md)
