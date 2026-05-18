# Minha DELPI — Core API: Notificações

> **Arquivo:** `docs/04-core-api/notificacoes.md`  
> **Status:** documentação oficial (maio/2026)  
> **Produto:** Minha DELPI  
> **Escopo:** notificações de usuário na Core API e integração com Portal  
> **Evolução rica:** ver [Roadmap notificações ricas](../12-roadmap-e-evolucao/notificacoes-ricas.md)

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

## 3. Tabela principal

Tabela:

```text
notifications
```

Campos principais:

| Campo | Descrição |
|---|---|
| `id` | UUID da notificação |
| `user_id` | Usuário destinatário |
| `title` | Título opcional |
| `message` | Mensagem da notificação |
| `type` | Tipo/categoria |
| `read_at` | Data/hora de leitura (`NULL` = não lida) |
| `created_at` | Data/hora de criação |

Model: `app/infrastructure/db/models/notification.py`.

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
| POST | `/me/notifications/test` | `NotifyUserUseCase` (dev) |

Admin e integrações: `POST /admin/notifications`, `POST /integrations/notifications`, templates em `/admin/notifications/templates`, auditoria em `GET /admin/notifications/dispatches`, processamento de agendados em `POST .../dispatches/process-pending` — ver [roadmap](../12-roadmap-e-evolucao/notificacoes-ricas.md).

Resposta de listagem (campos expostos ao Portal):

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Título",
  "message": "Texto",
  "type": "info",
  "read": false,
  "isImportant": false,
  "createdAt": "2026-05-15T12:00:00Z"
}
```

`read` é derivado de `read_at IS NOT NULL` no repository. Registros com `deleted_at` preenchido não aparecem nas listagens do usuário.

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

Ponto de atenção técnico:

> A implementação conhecida chama `self.uow.notifications.get(notification_id)`. Confirmar se o repository concreto e o port possuem esse método. Caso não possuam, ajustar o contrato ou o use case.

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

Finalidade:

```text
Criar notificação de teste para o usuário atual.
```

Proteção:

```text
require_auth
```

Use case provável:

```text
NotifyUserUseCase
```

Uso:

- desenvolvimento;
- validação do Portal;
- validação de eventos;
- testes manuais.

Ponto de atenção:

> Avaliar se este endpoint deve permanecer habilitado em produção ou ser condicionado por ambiente/permissão.

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

Repository exposto pelo Unit of Work:

```text
notifications
```

Operações esperadas:

```text
create(data)
list_unread(user_id)
mark_read(notification_id, user_id)
mark_all_read(user_id)
get(notification_id)
```

Ponto de atenção:

> Confirmar se todos esses métodos existem no port e na implementação concreta. O método `get` é especialmente importante por ser usado no use case de marcar uma notificação como lida.

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

O Portal deve:

1. Buscar notificações após login.
2. Exibir contador de não lidas.
3. Exibir lista de notificações.
4. Permitir marcar uma como lida.
5. Permitir marcar todas como lidas.
6. Recarregar notificações ao receber evento relacionado.
7. Tratar erro de sessão expirada.
8. Não exibir notificações de outro usuário.

Fluxo inicial:

```text
Login concluído
  ↓
GET /me/notifications
  ↓
Renderiza contador/lista
```

Fluxo por evento:

```text
admin.changed notifications.* recebido
  ↓
GET /me/notifications
  ↓
Atualiza UI
```

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

## 19. Considerações de paginação

O endpoint atual conhecido lista notificações não lidas.

Se o volume crescer, considerar:

```text
GET /me/notifications?page=1&page_size=20
GET /me/notifications?status=unread
GET /me/notifications?status=all
```

A paginação deve seguir o padrão geral da Core API.

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

- [ ] `GET /me/notifications` lista apenas notificações do usuário.
- [ ] `POST /me/notifications/<id>/read` valida ownership.
- [ ] `POST /me/notifications/read-all` atualiza apenas o usuário atual.
- [ ] `read_at` é preenchido ao marcar como lida.
- [ ] Operações são idempotentes quando aplicável.
- [ ] Eventos direcionados são emitidos para o usuário.
- [ ] Portal recarrega notificações em eventos.
- [ ] Endpoint de teste é protegido ou condicionado por ambiente.
- [ ] Repository possui métodos usados pelos use cases.
- [ ] Erros seguem `{ errors: [...] }`.

---

## 22. Pontos de atenção

1. Confirmar FK de `notifications.user_id` no model final.
2. Confirmar existência de `notifications.get`.
3. Definir política de uso do endpoint de teste em produção.
4. Definir enum ou convenção para `type`.
5. Considerar paginação/histórico em evolução futura.
6. Não colocar conteúdo sensível em notificações.
7. Eventos devem ser direcionados ao usuário correto.
8. Marcar notificação de outro usuário deve ser bloqueado.
9. Portal deve tratar sessão expirada ao listar notificações.
10. Notificação é preferência/comunicação, não autorização.

---

## 23. Documentos relacionados

```text
docs/04-core-api/visao-geral-core-api.md
docs/04-core-api/use-cases.md
docs/04-core-api/repositories.md
docs/04-core-api/erros-api.md
docs/06-portal-frontend/visao-geral-portal.md
docs/06-portal-frontend/favoritos.md
```

