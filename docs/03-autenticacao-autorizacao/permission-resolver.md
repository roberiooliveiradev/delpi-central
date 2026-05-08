# Minha DELPI — Permission Resolver

> **Arquivo:** `docs/03-autenticacao-autorizacao/permission-resolver.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** cálculo de permissões efetivas na Core API

---

## 1. Objetivo

Este documento descreve o **Permission Resolver** da Minha DELPI.

O Permission Resolver é o componente responsável por calcular as permissões efetivas de um usuário na Core API.

Ele considera:

- superadmin;
- roles diretas do usuário;
- roles herdadas por grupos;
- permissões associadas às roles;
- overrides individuais em `user_permissions`;
- cache de permissões.

---

## 2. Princípio central

A autorização final da Minha DELPI é baseada nas permissões efetivas calculadas pela Core API.

Regra:

```text
JWT identifica o usuário.
PermissionResolver calcula permissões efetivas.
```

O token emitido pelo Keycloak não deve ser usado como fonte final de permissões da plataforma.

---

## 3. Responsabilidade do Permission Resolver

O Permission Resolver deve responder à pergunta:

```text
Quais permission codes este usuário possui agora?
```

Ele retorna uma lista de códigos de permissão, por exemplo:

```text
apps.view
apps.manage
rbac.manage
dashboard-lmps.access
```

Esses códigos são usados por:

- decorators HTTP;
- `/me`;
- `/me/apps`;
- AppAuthorizationService;
- Portal;
- áreas administrativas;
- validações de acesso em backends.

---

## 4. Entradas do resolver

Entrada conceitual:

```python
resolve(user_id, is_superadmin=False)
```

Parâmetros:

| Parâmetro | Descrição |
|---|---|
| `user_id` | ID local do usuário |
| `is_superadmin` | Indica se o usuário é superadmin |

Saída:

```text
lista ordenada de permission codes
```

---

## 5. Fontes de permissão

O resolver considera quatro fontes principais.

| Fonte | Tabelas |
|---|---|
| Roles diretas | `user_roles`, `role_permissions`, `permissions` |
| Roles por grupos | `user_groups`, `group_roles`, `role_permissions`, `permissions` |
| Overrides individuais | `user_permissions`, `permissions` |
| Superadmin | `permissions` |

---

## 6. Fluxo geral

Fluxo conceitual:

```text
PermissionResolver.resolve(user_id, is_superadmin)
  ↓
Se is_superadmin = true:
    retornar todas as permissões
  ↓
Se usuário comum:
    tentar cache
  ↓
Buscar permissões por roles diretas
  ↓
Buscar permissões por groups → roles
  ↓
Unir permissões
  ↓
Aplicar overrides individuais
  ↓
Salvar no cache
  ↓
Retornar lista
```

---

## 7. Superadmin

Se o usuário possui:

```text
users.is_superadmin = true
```

O resolver retorna todas as permissões cadastradas.

Fluxo:

```text
is_superadmin = true
  ↓
permissions.list_all_codes()
  ↓
return all permission codes
```

Consequência:

- superadmin vê todos os apps ativos;
- superadmin passa por `require_permission`;
- superadmin tem acesso administrativo amplo;
- algumas operações podem exigir explicitamente `require_superadmin`.

Ponto importante:

> Superadmin não significa que apps inativos devem aparecer. O filtro de app ativo continua sendo responsabilidade da consulta de apps.

---

## 8. Roles diretas

Roles diretas são atribuídas por:

```text
user_roles
```

Fluxo:

```text
users.id
  ↓
user_roles.user_id
  ↓
role_permissions.role_id
  ↓
permissions.code
```

Consulta conceitual:

```sql
SELECT p.code
FROM user_roles ur
JOIN role_permissions rp ON rp.role_id = ur.role_id
JOIN permissions p ON p.id = rp.permission_id
WHERE ur.user_id = :user_id;
```

---

## 9. Roles herdadas por grupos

Usuários podem pertencer a grupos.

Grupos podem ter roles.

Fluxo:

```text
users.id
  ↓
user_groups.user_id
  ↓
group_roles.group_id
  ↓
role_permissions.role_id
  ↓
permissions.code
```

Consulta conceitual:

```sql
SELECT p.code
FROM user_groups ug
JOIN group_roles gr ON gr.group_id = ug.group_id
JOIN role_permissions rp ON rp.role_id = gr.role_id
JOIN permissions p ON p.id = rp.permission_id
WHERE ug.user_id = :user_id;
```

---

## 10. União de permissões

Permissões vindas de roles diretas e roles herdadas por grupos são unidas.

Se a mesma permissão vier de múltiplas fontes, ela aparece apenas uma vez.

Exemplo:

```text
Role direta: apps.view, dashboard-lmps.access
Grupo:       apps.view, users.view

União:      apps.view, dashboard-lmps.access, users.view
```

---

## 11. Overrides individuais

Overrides ficam em:

```text
user_permissions
```

Campos relevantes:

```text
user_id
permission_id
granted
```

Regras:

```text
granted = true  → adiciona permissão efetiva
granted = false → remove permissão efetiva
```

Overrides são aplicados depois da união das permissões por roles e grupos.

---

## 12. Exemplo de override concedendo permissão

Usuário não possui `apps.manage` por role/grupo.

Override:

```text
permission = apps.manage
granted = true
```

Resultado:

```text
apps.manage é adicionada às permissões efetivas
```

---

## 13. Exemplo de override removendo permissão

Usuário possui `apps.manage` via role.

Override:

```text
permission = apps.manage
granted = false
```

Resultado:

```text
apps.manage é removida das permissões efetivas
```

---

## 14. Ordem de precedência

Ordem efetiva:

```text
1. Superadmin
2. Roles diretas
3. Roles herdadas por grupos
4. Overrides individuais
```

No caso de superadmin, o fluxo pode retornar todas as permissões sem aplicar overrides.

Para usuário comum, overrides individuais são a última camada.

---

## 15. Cache de permissões

O Permission Resolver usa cache para evitar recalcular permissões em toda requisição.

Cache conhecido:

```text
in-memory
```

Uso:

```text
resolve(user_id)
  ↓
se cache existe, retorna cache
  ↓
se não existe, calcula e salva
```

Benefícios:

- reduz consultas SQL;
- melhora performance em endpoints frequentes;
- acelera `/me` e `/me/apps`.

---

## 16. Limitações do cache atual

O cache em memória tem limitações.

Pontos de atenção:

- não é distribuído entre múltiplas réplicas;
- reinicia ao reiniciar o processo;
- exige invalidação correta após alterações RBAC;
- pode ficar inconsistente se múltiplos containers atualizarem permissões sem coordenação.

Evolução futura possível:

```text
Redis ou cache distribuído
```

---

## 17. Invalidação de cache

Alterações de RBAC devem invalidar cache.

Eventos que exigem invalidação:

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

O `RbacEventHandler` deve reagir a esses eventos.

---

## 18. Invalidação por usuário específico

Quando a alteração impacta apenas um usuário, invalidar somente esse usuário.

Exemplos:

```text
role_added_to_user
role_removed_from_user
roles_replaced
group_added_to_user
group_removed_from_user
groups_replaced
user_superadmin_updated
```

Fluxo:

```text
Evento com target_user_id
  ↓
PermissionCache.invalidate(user_id)
```

---

## 19. Invalidação por role

Quando permissões de uma role mudam, todos os usuários que recebem essa role precisam ser invalidados.

Usuários afetados:

```text
usuários com role direta
+
usuários em grupos que possuem a role
```

Eventos:

```text
permission_added_to_role
permission_removed_from_role
role_permissions_replaced
```

---

## 20. Invalidação por grupo

Quando roles de um grupo mudam, todos os usuários do grupo precisam ser invalidados.

Eventos:

```text
role_added_to_group
role_removed_from_group
group_roles_replaced
```

Fluxo:

```text
Evento contém group_id
  ↓
RbacQueryRepository lista usuários do grupo
  ↓
Cache invalida cada usuário
```

---

## 21. Uso pelo middleware de autenticação

Durante a requisição, o middleware valida JWT e resolve usuário.

Depois, carrega roles, groups e permissions para montar `g.current_user`.

Fluxo:

```text
JWT validado
  ↓
Usuário local identificado
  ↓
PermissionResolver.resolve(user.id, user.is_superadmin)
  ↓
g.current_user.permissions
```

Essas permissões alimentam decorators e controllers.

---

## 22. Uso por `/me`

Endpoint:

```http
GET /me
```

Retorna as permissões efetivas ao Portal.

Uso no Portal:

- UX administrativa;
- exibir/ocultar botões;
- determinar menu administrativo;
- passar contexto a plugins quando necessário.

Ponto de atenção:

> O frontend usa permissões para experiência. A segurança final continua no backend.

---

## 23. Uso por `/me/apps`

Endpoint:

```http
GET /me/apps
```

Fluxo:

```text
PermissionResolver retorna permissions
  ↓
AppQueryRepository retorna apps ativos
  ↓
AppAuthorizationService filtra rotas por permission_code
  ↓
Portal recebe apps autorizados
```

Assim, o Permission Resolver afeta diretamente o menu dinâmico.

---

## 24. Uso pelos decorators

Decorators usam permissões efetivas.

Exemplos:

```python
@require_permission("apps.manage")
@require_any_permission(["users.view", "users.manage"])
@require_all_permissions(["rbac.manage", "roles.manage"])
```

Fluxo:

```text
Decorator lê g.current_user.permissions
  ↓
Confere código exigido
  ↓
Permite ou retorna 403
```

Superadmin geralmente passa por decorators de permissão.

---

## 25. Permission codes

Permission codes seguem padrão estável.

Exemplos:

```text
apps.view
apps.manage
routes.manage
rbac.manage
users.view
users.manage
dashboard-lmps.access
```

Regras recomendadas:

- lowercase;
- namespaces por módulo;
- usar ponto como separador;
- permissões de plugin devem iniciar com o módulo/plugin quando fizer sentido;
- manter `permissions.module` coerente.

---

## 26. Permissões base do sistema

Permissões base conhecidas:

```text
rbac.manage
users.view
users.manage
groups.manage
roles.manage
permissions.manage
apps.manage
apps.view
routes.manage
```

Essas permissões são criadas pelo seed da Core API.

---

## 27. Permissões de plugins

Permissões de plugins são criadas a partir do manifesto.

Exemplo:

```json
{
  "code": "dashboard-lmps.access",
  "name": "Acessar Dashboard LMPs",
  "module": "dashboard-lmps"
}
```

Durante registro, rollback ou unregister, a Core API usa:

```text
permissions.module = plugin_id
```

para gerenciar lifecycle dessas permissões.

---

## 28. Exemplo completo

Usuário:

```text
Ana
```

Roles diretas:

```text
Gestor de Apps
```

Grupos:

```text
Operações
```

Roles do grupo:

```text
Analista LMP
```

Permissões por roles:

```text
Gestor de Apps → apps.view, apps.manage
Analista LMP   → dashboard-lmps.access
```

Overrides:

```text
apps.manage granted=false
users.view granted=true
```

Resultado efetivo:

```text
apps.view
dashboard-lmps.access
users.view
```

---

## 29. Erros e troubleshooting

### 29.1 Usuário autenticado sem permissões

Verificar:

- usuário existe em `users`;
- usuário tem roles diretas;
- usuário pertence a grupos;
- grupos possuem roles;
- roles possuem permissões;
- overrides não removeram permissões;
- cache foi invalidado;
- usuário não está inativo se essa regra for aplicada.

---

### 29.2 App não aparece no Portal

Verificar:

- app está ativo;
- rota está ativa;
- rota tem permission correta;
- usuário possui permission code exigido;
- app tem pelo menos uma rota autorizada;
- `/me/apps` está recarregado;
- cache RBAC foi invalidado.

---

### 29.3 Alterei role, mas usuário não refletiu mudança

Verificar:

- evento foi coletado pelo use case;
- Unit of Work publicou evento após commit;
- RbacEventHandler recebeu evento;
- cache foi invalidado;
- Portal recebeu Socket.IO;
- Portal recarregou `/me` e `/me/apps`.

---

## 30. Boas práticas

1. Manter permission codes estáveis.
2. Usar roles para agrupar permissões.
3. Usar grupos para herança organizacional.
4. Usar overrides individuais com moderação.
5. Invalidar cache em toda mudança RBAC.
6. Não usar roles do Keycloak como autorização final.
7. Não hardcodar permissões no Portal como fonte final.
8. Documentar permissões novas.
9. Associar permissões de plugins por manifesto.
10. Testar perda e ganho de acesso durante sessão.

---

## 31. Checklist de implementação

- [ ] Resolver considera roles diretas.
- [ ] Resolver considera roles por grupos.
- [ ] Resolver aplica overrides individuais.
- [ ] Superadmin retorna todas as permissões.
- [ ] Cache é usado em usuário comum.
- [ ] Cache é invalidado em mudanças de usuário.
- [ ] Cache é invalidado em mudanças de grupo.
- [ ] Cache é invalidado em mudanças de role.
- [ ] `/me` retorna permissões efetivas.
- [ ] `/me/apps` usa permissões efetivas.
- [ ] Decorators usam permissões efetivas.

---

## 32. Pontos de atenção

1. Permission Resolver é peça central do RBAC.
2. Superadmin bypassa permissões comuns, mas apps inativos continuam filtrados.
3. Overrides individuais são aplicados por último para usuário comum.
4. Cache em memória não é distribuído.
5. Eventos RBAC precisam invalidar cache corretamente.
6. Permissões efetivas podem mudar durante a sessão.
7. Portal deve recarregar `/me` e `/me/apps` após eventos relevantes.
8. Permissões de plugin dependem de manifesto correto.
9. `permissions.module` incorreto quebra lifecycle de plugin.
10. JWT não é fonte final de permissões.

---

## 33. Documentos relacionados

```text
docs/03-autenticacao-autorizacao/rbac.md
docs/03-autenticacao-autorizacao/jwt.md
docs/03-autenticacao-autorizacao/keyclo