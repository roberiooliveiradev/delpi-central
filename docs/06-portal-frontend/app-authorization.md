# Minha DELPI — Autorização de Apps no Portal

> **Arquivo:** `docs/06-portal-frontend/app-authorization.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** autorização de apps e rotas consumidas pelo Portal

---

## 1. Objetivo

Este documento descreve como a autorização de apps e rotas funciona para o Portal da Minha DELPI.

Ele explica a diferença entre:

- autorização efetiva calculada pela Core API;
- filtragem de apps e rotas no backend;
- uso das permissões pelo Portal para experiência de usuário;
- proteção real de endpoints e recursos.

---

## 2. Princípio central

O Portal não calcula autorização efetiva.

A Core API é a fonte oficial para decidir quais apps e rotas o usuário pode acessar.

Regra:

```text
Core API autoriza.
Portal renderiza a experiência autorizada.
```

A fonte oficial para apps autorizados é:

```http
GET /me/apps
```

---

## 3. Responsabilidades

| Responsabilidade | Portal | Core API |
|---|---:|---:|
| Autenticar usuário no Keycloak | Sim | Valida token recebido |
| Resolver permissões efetivas | Não | Sim |
| Filtrar apps por permissão | Não | Sim |
| Filtrar rotas por permissão | Não | Sim |
| Montar menu visual | Sim | Não |
| Ocultar itens não retornados | Sim | Sim, por não retornar |
| Proteger endpoints administrativos | Não | Sim |
| Melhorar UX com permissões de `/me` | Sim | Fornece dados |

---

## 4. Fluxo completo de autorização de apps

```text
Usuário faz login
  ↓
Portal recebe access token
  ↓
Portal chama /me
  ↓
Core API retorna permissões efetivas
  ↓
Portal chama /me/apps
  ↓
Core API lista apps ativos com rotas
  ↓
Core API aplica AppAuthorizationService
  ↓
Core API retorna somente apps/rotas autorizados
  ↓
Portal monta menu e rotas
```

---

## 5. Permission Resolver

A Core API calcula permissões efetivas usando o `PermissionResolver`.

Fontes consideradas:

- superadmin;
- roles diretas do usuário;
- roles herdadas por grupos;
- permissões das roles;
- overrides individuais em `user_permissions`;
- cache RBAC.

Fluxo:

```text
PermissionResolver.resolve(user_id, is_superadmin)
  ↓
Se superadmin, retorna todas as permissões
  ↓
Se usuário comum, tenta cache
  ↓
Busca permissões por roles diretas
  ↓
Busca permissões por roles de grupos
  ↓
Aplica overrides individuais
  ↓
Retorna permissions[]
```

Essas permissões são disponibilizadas ao Portal pelo endpoint `/me` e usadas internamente pela Core API para filtrar apps.

---

## 6. AppAuthorizationService

A filtragem de apps e rotas é feita na Core API por:

```text
AppAuthorizationService
```

Esse serviço não acessa banco e não resolve permissões. Ele apenas recebe:

```text
apps
permissions
is_superadmin
```

E retorna a lista filtrada.

---

## 7. Regra para superadmin

Se o usuário é superadmin:

```text
return apps
```

Ou seja, superadmin recebe todos os apps e rotas retornados pela consulta de apps ativos.

Observação:

> Superadmin ainda depende de apps ativos. Apps inativos não devem aparecer no fluxo comum de `/me/apps`.

---

## 8. Regra para usuário comum

Para usuário comum, a Core API avalia rota por rota.

Regra:

```text
Se route.permission_code é None:
    rota é permitida

Se route.permission_code está em permissions:
    rota é permitida

Caso contrário:
    rota é removida
```

Depois disso:

```text
Se app ficou com pelo menos uma rota autorizada:
    app é retornado
Caso contrário:
    app é removido
```

---

## 9. Consequência prática

O Portal só recebe apps que possuem pelo menos uma rota autorizada.

Exemplo:

```text
App dashboard-lmps possui rota com permission dashboard-lmps.access
Usuário não possui dashboard-lmps.access
  ↓
Core API remove rota
  ↓
App fica sem rotas
  ↓
Core API remove app da resposta
  ↓
Portal não mostra dashboard-lmps
```

---

## 10. Rotas sem permissão

Rotas sem `permission_code` são permitidas para usuários comuns.

Uso possível:

- página pública autenticada;
- rota informativa;
- tela comum a todos os usuários autenticados;
- home de um app quando o app deve aparecer para todos.

Atenção:

> Rota sem permissão não é pública para usuários anônimos. Ela apenas não exige permission code adicional depois da autenticação.

---

## 11. Relação com `/me`

O endpoint `/me` retorna dados do usuário e permissões efetivas.

Exemplo:

```json
{
  "id": "uuid",
  "name": "Usuário",
  "email": "usuario@empresa.com",
  "is_superadmin": false,
  "permissions": [
    "apps.view",
    "dashboard-lmps.access"
  ]
}
```

O Portal pode usar essas permissões para:

- esconder botões;
- exibir menus administrativos internos;
- adaptar experiência;
- evitar chamadas desnecessárias.

Mas isso não substitui autorização no backend.

---

## 12. Relação com `/me/apps`

O endpoint `/me/apps` retorna apps e rotas já autorizados.

Exemplo:

```json
[
  {
    "id": "dashboard-lmps",
    "name": "Dashboard LMPs",
    "basePath": "/apps/dashboard-lmps",
    "type": "microfrontend",
    "entryUrl": "/apps/dashboard-lmps/assets/remoteEntry.js",
    "renderMode": "federated",
    "routes": [
      {
        "path": "/apps/dashboard-lmps",
        "permission": "dashboard-lmps.access",
        "label": "Dashboard LMPs",
        "showInMenu": true,
        "order": 1
      }
    ]
  }
]
```

O Portal deve montar menu e rotas plugáveis com base nessa resposta.

---

## 13. Não renderizar rota não autorizada

Se o usuário acessa uma URL manualmente, o Portal deve verificar se o path existe na lista de rotas autorizadas.

Fluxo:

```text
Usuário acessa /apps/dashboard-lmps
  ↓
Portal procura path em /me/apps
  ↓
Se encontrar, renderiza
  ↓
Se não encontrar, mostra fallback seguro
```

Fallback recomendado:

```text
Página não encontrada ou acesso não permitido.
```

---

## 14. Diferença entre ocultação visual e segurança

Ocultar um item no menu melhora a experiência, mas não é controle de segurança final.

Exemplo:

```text
Botão "Gerenciar usuários" oculto no Portal
```

Isso evita uso indevido pela UI, mas o endpoint ainda precisa estar protegido por:

```python
@require_permission("users.manage")
```

Regra:

> Toda ação sensível deve ser protegida na Core API ou no backend correspondente.

---

## 15. Administração no Portal

Menus administrativos do Portal podem usar permissões de `/me`.

Sugestão:

| Área | Permissão mínima sugerida |
|---|---|
| Apps | `apps.view` |
| Gerenciar apps | `apps.manage` |
| Rotas | `routes.manage` |
| Usuários | `users.view` |
| Editar usuários | `users.manage` |
| RBAC | `rbac.manage` |
| Roles | `roles.manage` |
| Groups | `groups.manage` |
| Permissions | `permissions.manage` |

Essas permissões devem refletir as proteções reais dos endpoints.

---

## 16. Eventos que afetam autorização

A autorização pode mudar durante a sessão do usuário.

Eventos que podem afetar apps/rotas:

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
plugin_registered
plugin_unregistered
plugin_manifest_updated
plugin_version_rolled_back
plugin_activated
plugin_deactivated
route_created
route_updated
route_deleted
```

Ao receber eventos relevantes, o Portal deve recarregar:

```http
GET /me
GET /me/apps
```

---

## 17. Perda de acesso durante a sessão

Cenário:

```text
Usuário está em /apps/dashboard-lmps
Administrador remove dashboard-lmps.access da role do usuário
Evento chega ao Portal
Portal recarrega /me/apps
Rota atual não existe mais
Portal redireciona usuário para home
```

Esse comportamento evita que o usuário continue navegando em uma tela que não deveria mais acessar.

O backend do plugin/API também deve negar chamadas subsequentes.

---

## 18. Ganho de acesso durante a sessão

Cenário:

```text
Administrador adiciona dashboard-lmps.access ao usuário
Evento chega ao Portal
Portal recarrega /me e /me/apps
Novo app aparece no menu
```

Esse comportamento permite refletir mudanças sem novo login.

---

## 19. Favoritos e autorização

Favoritos também devem respeitar autorização.

A Core API lista favoritos e depois filtra contra apps autorizados.

Consequência:

```text
Usuário favoritou dashboard-lmps
Depois perdeu permissão
  ↓
Favorito pode continuar persistido
  ↓
Mas não deve aparecer na listagem autorizada
```

Se a permissão voltar, o favorito pode reaparecer.

---

## 20. Apps inativos

Apps inativos não devem aparecer para o usuário comum via `/me/apps`.

Cenário:

```text
Plugin desativado
  ↓
Core API não retorna em /me/apps
  ↓
Portal remove menu/rota
```

Se o usuário estiver na rota do app desativado, o Portal deve redirecionar.

---

## 21. Rotas inativas

Rotas inativas também não devem aparecer em `/me/apps`.

Consequência:

- menu remove a rota;
- navegação direta deve ser bloqueada pelo Portal;
- backend deve continuar validando segurança se houver endpoint associado.

---

## 22. Pseudocódigo de autorização no Portal

O Portal não calcula permissões, mas pode verificar se a rota está autorizada pela resposta recebida.

```typescript
function findAuthorizedRoute(apps, pathname) {
  for (const app of apps) {
    for (const route of app.routes || []) {
      if (route.path === pathname) {
        return { app, route }
      }
    }
  }

  return null
}

function canRenderRoute(apps, pathname) {
  return Boolean(findAuthorizedRoute(apps, pathname))
}
```

---

## 23. O que não fazer

Evitar:

```text
Hardcodar lista final de plugins no frontend.
Renderizar app que não veio em /me/apps.
Confiar apenas em permissões salvas localmente.
Persistir /me/apps indefinidamente sem invalidação.
Passar por cima da Core API para montar menu.
Usar frontend como única barreira de segurança.
```

---

## 24. Checklist de implementação

- [ ] Portal chama `/me` após login.
- [ ] Portal chama `/me/apps` após login.
- [ ] Menu usa apenas apps retornados.
- [ ] Rotas diretas são validadas contra `/me/apps`.
- [ ] Eventos RBAC recarregam `/me` e `/me/apps`.
- [ ] Eventos de plugin/rota recarregam `/me/apps`.
- [ ] Perda de acesso redireciona rota atual.
- [ ] Ganho de acesso atualiza menu.
- [ ] Favoritos são filtrados pela Core API.
- [ ] Endpoints backend continuam protegidos.

---

## 25. Pontos de atenção

1. `/me/apps` já vem autorizado.
2. `/me.permissions` ajuda UX, mas não substitui backend.
3. Rota sem permissão ainda exige usuário autenticado.
4. App sem rota autorizada não aparece.
5. Apps inativos não devem aparecer.
6. Eventos podem mudar autorização durante sessão.
7. Perda de acesso deve invalidar rota atual.
8. Favoritos não devem furar autorização.
9. Backend-only não gera UI.
10. Segurança final deve estar no backend.

---

## 26. Documentos relacionados

```text
docs/06-portal-frontend/visao-geral-portal.md
docs/06-portal-frontend/menu-dinamico.md
docs/06-portal-frontend/consumo-de-plugins.md
docs/03-autenticacao-autorizacao/rbac.md
docs/03-autenticacao-autorizacao/permission-resolver.md
docs/05-plugin-system/manifesto-plugin.md
```

