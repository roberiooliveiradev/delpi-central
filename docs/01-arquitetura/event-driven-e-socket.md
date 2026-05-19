# Minha DELPI — Event-driven e Socket.IO

> **Arquivo:** `docs/01-arquitetura/event-driven-e-socket.md`  
> **Status:** documentação oficial (maio/2026)  
> **Produto:** Minha DELPI  
> **Escopo:** eventos internos, publicação pós-commit, Socket.IO e atualização em tempo real do Portal

---

## 1. Objetivo

Este documento descreve a arquitetura **event-driven interna** da Minha DELPI e sua integração com **Socket.IO**.

A Core API usa eventos para desacoplar ações administrativas de efeitos colaterais, como:

- invalidação de cache RBAC;
- atualização do Portal;
- notificação de usuários;
- sincronização futura de integrações.

---

## 2. Princípio central

Regra principal:

```text
Persistir primeiro. Publicar evento depois do commit.
```

Motivo:

> O Portal não deve receber evento de uma mudança que falhou no banco.

Fluxo correto:

```text
Use case
  ↓
altera dados
  ↓
coleta evento
  ↓
Unit of Work commit
  ↓
EventBus publica
  ↓
Handlers executam efeitos
```

---

## 3. Componentes envolvidos

| Componente | Responsabilidade |
|---|---|
| `AdminChangedEvent` | Representar mudança administrativa ou de usuário |
| `Unit of Work` | Coletar eventos e publicar após commit |
| `EventBus` | Distribuir eventos para handlers |
| `RbacEventHandler` | Invalidar cache/identificar usuários afetados |
| `SocketIOEventDispatcher` | Emitir eventos para o Portal |
| `socket_handlers.py` | Autenticar conexão Socket.IO e colocar usuário em sala |
| Portal | Reagir a eventos e recarregar dados |

---

## 4. Evento administrativo padrão

Formato conceitual:

```python
AdminChangedEvent(
    entity="plugins",
    action="plugin_registered",
    payload={
        "pluginId": "dashboard-lmps",
        "version": "1.0.0",
    },
    target_user_id=None,
)
```

Campos:

| Campo | Descrição |
|---|---|
| `entity` | Domínio afetado |
| `action` | Ação executada |
| `payload` | Dados úteis para reação |
| `target_user_id` | Usuário alvo opcional |

---

## 5. Eventos globais versus direcionados

### 5.1 Evento global

Usado quando todos os usuários conectados podem ser afetados.

Exemplos:

```text
plugin_registered
plugin_unregistered
plugin_manifest_updated
plugin_version_rolled_back
route_created
route_deleted
```

Comportamento:

```text
Socket.IO broadcast
```

---

### 5.2 Evento direcionado

Usado quando apenas um usuário é afetado.

Exemplos:

```text
role_added_to_user
role_removed_from_user
favorite_added
favorite_removed
notification_created
```

Comportamento:

```text
emit para room = target_user_id
```

---

## 6. Coleta de eventos no use case

Use cases coletam eventos, mas não publicam diretamente.

Exemplo conceitual:

```python
self.uow.collect_event(
    AdminChangedEvent(
        entity="favorites",
        action="favorite_added",
        payload={"appId": app_id},
        target_user_id=user_id,
    )
)
```

Regra:

> Use case decide o evento de negócio; infraestrutura decide como publicar.

---

## 7. Unit of Work e publicação pós-commit

Fluxo do Unit of Work:

```text
__enter__
  ↓
use case executa
  ↓
collect_event(...)
  ↓
__exit__ sem exceção
  ↓
commit()
  ↓
EventBus.publish(events)
```

Se houver exceção:

```text
rollback()
  ↓
eventos descartados
```

Esse padrão protege o Portal contra eventos inconsistentes.

---

## 8. EventBus

O EventBus recebe a lista de eventos após commit.

Responsabilidades:

- iterar eventos;
- chamar handlers;
- isolar efeitos colaterais da regra principal;
- permitir evolução para novos handlers.

Fluxo conceitual:

```text
EventBus.publish(events)
  ↓
RbacEventHandler
  ↓
SocketIOEventDispatcher
```

---

## 9. RbacEventHandler

O `RbacEventHandler` reage a mudanças que afetam permissões.

Responsabilidades:

- invalidar cache de permissões;
- descobrir usuários afetados por mudanças em roles/grupos;
- manter coerência de `/me` e `/me/apps`;
- preparar o Portal para refletir ganho/perda de acesso.

Eventos relevantes:

```text
role_added_to_user
role_removed_from_user
roles_replaced
group_added_to_user
group_removed_from_user
groups_replaced
role_added_to_group
role_removed_from_group
group_roles_replaced
permission_added_to_role
permission_removed_from_role
role_permissions_replaced
user_superadmin_updated
```

---

## 10. Socket.IO Dispatcher

O dispatcher é o adapter de infraestrutura responsável por emitir eventos ao Portal.

Evento emitido:

```text
admin.changed
```

Payload conceitual:

```json
{
  "entity": "plugins",
  "action": "plugin_registered",
  "payload": {
    "pluginId": "dashboard-lmps",
    "version": "1.0.0"
  }
}
```

Se `target_user_id` existir:

```text
emit para sala do usuário
```

Se não existir:

```text
broadcast global
```

---

## 11. Conexão Socket.IO

O Portal deve conectar enviando token:

```javascript
io("/", {
  auth: {
    token: accessToken
  }
})
```

Fluxo na Core API:

```text
connect
  ↓
extrai auth.token
  ↓
fallback opcional para query token
  ↓
validate_token(token)
  ↓
extrai sub
  ↓
join_room(sub)
```

Se token estiver ausente, inválido ou sem `sub`, a conexão é recusada.

---

## 12. Rooms por usuário

Cada conexão autenticada entra em uma room identificada pelo `sub` do JWT.

```text
room = sub
```

Isso permite eventos direcionados:

```text
target_user_id → room do usuário
```

Uso:

- favoritos;
- notificações;
- alteração de roles do usuário;
- alteração de grupos do usuário;
- alteração de superadmin;
- perda/ganho de acesso.

---

## 12.1 Presença online (portal aberto)

Com `USER_PRESENCE_ENABLED=true` (padrão), a Core API registra conexões Socket.IO:

| Evento | Ação |
|--------|------|
| `connect` | `register(user_id=sub, session_id=sid)` |
| `disconnect` | `unregister(sid)` |
| `presence.ping` (portal a cada ~45 s) | `touch(sid)` — renova TTL |

Consulta Admin (superadmin): `GET /admin/users/presence` — lista usuários com portal conectado, `connectionCount`, `connectedAt`, `lastSeenAt`.

| Variável | Default | Descrição |
|----------|---------|-----------|
| `USER_PRESENCE_ENABLED` | `true` | Liga/desliga presença |
| `USER_PRESENCE_TTL_SECONDS` | `90` | Sem ping, sessão expira |
| `USER_PRESENCE_STORE` | `memory` | `memory` ou `redis` (com `REDIS_URL`) |

Em múltiplas réplicas da Core API, use `USER_PRESENCE_STORE=redis` e `REDIS_URL` compartilhado.

---

## 13. Eventos e Portal

O Portal deve reagir a eventos recarregando dados da Core API.

Exemplos:

| Evento | Reação recomendada |
|---|---|
| `plugin_registered` | Recarregar `/me/apps` |
| `plugin_unregistered` | Recarregar `/me/apps` e validar rota atual |
| `plugin_manifest_updated` | Recarregar menu/apps |
| `plugin_version_rolled_back` | Recarregar apps/rotas |
| `role_added_to_user` | Recarregar `/me` e `/me/apps` |
| `role_removed_from_user` | Recarregar `/me` e `/me/apps` |
| `favorite_added` | Recarregar favoritos |
| `favorite_removed` | Recarregar favoritos |
| `notification_created` | Recarregar notificações |

---

## 14. Eventos de Plugin System

Eventos conhecidos:

```text
plugin_registered
plugin_unregistered
plugin_manifest_updated
plugin_version_rolled_back
plugin_activated
plugin_deactivated
plugins_activation_changed
plugins_unregistered
```

Impacto:

- menu pode mudar;
- rotas podem mudar;
- permissões podem mudar;
- plugin atual pode ficar indisponível;
- favoritos podem precisar ser filtrados novamente.

---

## 15. Eventos de rotas

Eventos conhecidos:

```text
route_created
route_updated
route_deleted
routes_bulk_deleted
```

Impacto:

- menu pode mudar;
- rota atual pode deixar de existir;
- autorização de app pode mudar;
- `/me/apps` deve ser recarregado.

---

## 16. Eventos de RBAC

Eventos conhecidos:

```text
role_added_to_user
role_removed_from_user
roles_replaced
group_added_to_user
group_removed_from_user
groups_replaced
role_added_to_group
role_removed_from_group
group_roles_replaced
permission_added_to_role
permission_removed_from_role
role_permissions_replaced
user_superadmin_updated
```

Impacto:

- permissões efetivas mudam;
- cache deve ser invalidado;
- `/me` deve ser recarregado;
- `/me/apps` deve ser recarregado;
- rota atual pode ser invalidada.

---

## 17. Eventos de favoritos

Eventos:

```text
favorite_added
favorite_removed
```

Normalmente direcionados ao usuário.

Impacto:

```text
Portal recarrega /me/apps/favorites
```

---

## 18. Eventos de notificações

Eventos possíveis:

```text
notification_created
notification_marked_read
all_notifications_marked_read
```

Impacto:

```text
Portal recarrega /me/notifications
```

---

## 19. Segurança do Socket.IO

Regras:

1. Exigir token no handshake.
2. Validar assinatura, issuer, audience e expiração.
3. Recusar conexão sem `sub`.
4. Usar room por usuário.
5. Evitar token em query string quando possível.
6. Não enviar dados sensíveis desnecessários no payload.
7. Revalidar autorização via HTTP ao recarregar dados.

O Socket.IO notifica mudança. Ele não substitui autorização HTTP.

---

## 20. Resiliência

Se a publicação pós-commit falhar:

```text
Dado já foi persistido.
Evento pode não chegar ao Portal.
Portal deve continuar consistente após refresh manual.
```

Comportamento atual recomendado:

- logar erro pós-commit;
- não quebrar request já persistida;
- permitir recuperação por reload do Portal;
- avaliar fila persistente em evolução futura.

---

## 21. Limitações atuais

Limitações comuns da arquitetura atual:

- eventos em memória/processo;
- Socket.IO sem broker distribuído;
- cache RBAC em memória;
- múltiplas réplicas exigiriam Redis/message broker;
- perda de evento não impede persistência;
- sem replay de eventos.

Evolução futura:

```text
Redis adapter para Socket.IO
Redis para cache RBAC
fila/event broker para eventos críticos
outbox pattern para publicação garantida
```

---

## 22. Boas práticas

1. Coletar evento no use case.
2. Publicar evento apenas após commit.
3. Usar evento direcionado quando só um usuário for afetado.
4. Usar broadcast quando menu/apps globais puderem mudar.
5. Manter payload pequeno.
6. Não enviar segredo ou token em evento.
7. Portal deve recarregar dados oficiais via HTTP.
8. Rota atual deve ser validada após reload de `/me/apps`.
9. Handler de RBAC deve invalidar cache corretamente.
10. Falha de Socket.IO não deve corromper transação já persistida.

---

## 23. Checklist para novo evento

- [ ] O evento representa uma mudança real de negócio.
- [ ] O evento é coletado no use case.
- [ ] O evento não é publicado antes do commit.
- [ ] `entity` está claro.
- [ ] `action` está estável.
- [ ] `payload` não contém segredo.
- [ ] `target_user_id` foi definido quando necessário.
- [ ] Portal sabe como reagir.
- [ ] Cache RBAC é invalidado se necessário.
- [ ] O evento foi documentado.

---

## 24. Pontos de atenção

1. Socket.IO é mecanismo de atualização, não fonte de verdade.
2. A fonte de verdade continua sendo a Core API via HTTP.
3. Eventos precisam refletir estado persistido.
4. RBAC precisa invalidar cache após mudanças.
5. Eventos globais podem gerar reload em vários clientes.
6. Eventos direcionados reduzem ruído.
7. Token no Socket.IO deve ser validado.
8. Rooms usam `sub` do JWT.
9. Falhas pós-commit devem ser observáveis.
10. Evolução multi-réplica exigirá infraestrutura adicional.

---

## 25. Documentos relacionados

```text
docs/01-arquitetura/fluxo-de-requisicao.md
docs/04-core-api/unit-of-work.md
docs/04-core-api/notificacoes.md
docs/03-autenticacao-autorizacao/jwt.md
docs/06-portal-frontend/visao-geral-portal.md
docs/06-portal-frontend/favoritos.md
```
