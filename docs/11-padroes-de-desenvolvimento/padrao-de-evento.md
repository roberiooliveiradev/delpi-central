# Minha DELPI — Padrão de Evento

> **Arquivo:** `docs/11-padroes-de-desenvolvimento/padrao-de-evento.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** padrão para eventos administrativos, domínio e Socket.IO

---

## 1. Objetivo

Este documento define o padrão de eventos na Minha DELPI.

Eventos são usados para comunicar mudanças relevantes entre a camada de aplicação, handlers internos e o Portal em tempo real.

---

## 2. Princípio central

Eventos devem representar fatos já ocorridos.

Exemplo:

```text
plugin_registered
role_added_to_user
notification_created
```

Evitar nomes imperativos:

```text
register_plugin
add_role
create_notification
```

---

## 3. Fluxo padrão na Core API

Fluxo correto:

```text
Use case executa alteração
  ↓
uow.collect_event(...)
  ↓
Unit of Work commita
  ↓
EventBus publica eventos
  ↓
Handlers internos reagem
  ↓
Socket.IO emite para Portal
```

Eventos não devem ser publicados antes do commit.

---

## 4. Evento administrativo

Formato conceitual:

```python
AdminChangedEvent(
    entity="plugins",
    action="plugin_registered",
    payload={"pluginId": "dashboard-lmps"},
    target_user_id=None
)
```

Campos:

| Campo | Descrição |
|---|---|
| `entity` | Domínio afetado |
| `action` | Ação ocorrida |
| `payload` | Dados adicionais |
| `target_user_id` | Usuário alvo opcional |

---

## 5. Nome de `entity`

Usar nomes por domínio.

Exemplos:

```text
apps
plugins
routes
rbac
users
roles
groups
permissions
favorites
notifications
```

---

## 6. Nome de `action`

Usar passado ou fato ocorrido.

Exemplos:

```text
plugin_registered
plugin_manifest_updated
plugin_version_rolled_back
role_added_to_user
role_permissions_replaced
favorite_added
notification_created
user_superadmin_updated
```

---

## 7. Payload

Payload deve ser pequeno e suficiente.

Bom:

```json
{
  "pluginId": "dashboard-lmps",
  "version": "1.0.0"
}
```

Evitar:

- objeto gigante;
- token;
- senha;
- segredo;
- dados pessoais desnecessários;
- dump completo de request.

---

## 8. Eventos direcionados

Quando a mudança afeta um usuário específico, preencher:

```text
target_user_id
```

Exemplos:

```text
role_added_to_user
role_removed_from_user
favorite_added
favorite_removed
notification_created
```

Isso permite emissão Socket.IO para a sala do usuário.

---

## 9. Eventos globais

Quando a mudança afeta a plataforma, deixar `target_user_id=None`.

Exemplos:

```text
plugin_registered
plugin_unregistered
plugin_activated
route_updated
role_permissions_replaced
```

O handler pode decidir broadcast ou localizar usuários afetados.

---

## 10. RBAC e cache

Eventos RBAC devem invalidar cache de permissões.

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

## 11. Socket.IO

Evento emitido ao Portal:

```text
admin.changed
```

Payload conceitual:

```json
{
  "entity": "plugins",
  "action": "plugin_registered",
  "payload": {
    "pluginId": "dashboard-lmps"
  }
}
```

O Portal deve reagir recarregando dados relevantes, como:

- `/me`;
- `/me/apps`;
- notificações;
- listas administrativas.

---

## 12. Onde coletar evento

Eventos devem ser coletados no use case.

Exemplo:

```python
self.uow.collect_event(AdminChangedEvent(...))
```

Não coletar evento no repository.

Não publicar evento na rota.

---

## 13. Quando publicar evento

Publicar somente após commit.

Motivo:

> Se o banco falhar e o evento já tiver sido emitido, o Portal pode reagir a uma mudança que não aconteceu.

---

## 14. Checklist para novo evento

- [ ] Nome representa fato ocorrido.
- [ ] `entity` está claro.
- [ ] `action` está claro.
- [ ] Payload é mínimo.
- [ ] Não contém segredo.
- [ ] É coletado no use case.
- [ ] É publicado após commit.
- [ ] Handler interno foi atualizado, se necessário.
- [ ] Portal sabe como reagir, se necessário.
- [ ] Teste cobre emissão/efeito.

---

## 15. Anti-padrões

Evitar:

```text
Evento publicado antes do commit.
Evento enviado direto do repository.
Evento enviado direto da rota.
Payload com request inteiro.
Payload com token.
Nome imperativo.
Evento sem consumidor claro.
Evento que substitui regra de negócio.
```

---

## 16. Documentos relacionados

```text
docs/01-arquitetura/event-driven-e-socket.md
docs/04-core-api/unit-of-work.md
docs/04-core-api/notificacoes.md
docs/11-padroes-de-desenvolvimento/padrao-de-use-case.md
```
