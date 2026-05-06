# Minha DELPI — Menu Dinâmico do Portal

> **Arquivo:** `docs/06-portal-frontend/menu-dinamico.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** construção do menu do Portal a partir dos apps e rotas autorizados

---

## 1. Objetivo

Este documento descreve como o **Portal** da Minha DELPI deve montar seu menu dinâmico a partir dos dados retornados pela Core API.

O menu dinâmico é um dos principais mecanismos de integração entre Portal, Core API, RBAC e Plugin System.

Ele garante que cada usuário visualize apenas os apps e rotas aos quais tem acesso.

---

## 2. Princípio central

O Portal não deve manter uma lista fixa definitiva de apps e rotas plugáveis.

A fonte oficial para apps e rotas disponíveis ao usuário é:

```http
GET /me/apps
```

A Core API retorna uma visão já filtrada por autorização.

Regra:

> O Portal monta o menu com base em `/me/apps`. A Core API decide quais apps e rotas o usuário pode acessar.

---

## 3. Fonte de dados

Endpoint:

```http
GET /me/apps
```

Proteção:

```text
usuário autenticado
```

Responsável na Core API:

```text
ListUserAppsUseCase
AppQueryRepository
AppAuthorizationService
```

Fluxo:

```text
Portal chama /me/apps
  ↓
Core API lista apps ativos com rotas
  ↓
Core API filtra rotas por permissões efetivas
  ↓
Core API retorna apps autorizados
  ↓
Portal monta menu
```

---

## 4. Formato conceitual de resposta

Exemplo:

```json
[
  {
    "id": "dashboard-lmps",
    "name": "Dashboard LMPs",
    "basePath": "/apps/dashboard-lmps",
    "icon": "bar-chart3",
    "type": "microfrontend",
    "entryUrl": "/apps/dashboard-lmps/assets/remoteEntry.js",
    "renderMode": "federated",
    "routes": [
      {
        "app": "dashboard-lmps",
        "app_name": "Dashboard LMPs",
        "app_icon": "bar-chart3",
        "path": "/apps/dashboard-lmps",
        "permission": "dashboard-lmps.access",
        "label": "Dashboard LMPs",
        "icon": "bar-chart3",
        "showInMenu": true,
        "order": 1,
        "entry": null
      }
    ]
  }
]
```

---

## 5. Campos usados pelo menu

### 5.1 Campos do app

| Campo | Uso |
|---|---|
| `id` | Identificador do app/plugin |
| `name` | Nome do app |
| `basePath` | Caminho base |
| `icon` | Ícone padrão do app |
| `type` | Estratégia de renderização |
| `entryUrl` | Entry point do plugin |
| `renderMode` | Modo de renderização |
| `routes` | Rotas autorizadas |

---

### 5.2 Campos da rota

| Campo | Uso |
|---|---|
| `path` | Caminho de navegação |
| `label` | Texto exibido no menu |
| `icon` | Ícone específico da rota |
| `permission` | Permissão associada à rota |
| `showInMenu` | Define se aparece no menu |
| `order` | Ordem de exibição |
| `entry` | Entry específico da rota, quando existir |
| `app` | ID do app dono da rota |
| `app_name` | Nome do app dono |
| `app_icon` | Ícone padrão do app |

---

## 6. Regra de exibição

Uma rota deve aparecer no menu quando:

```text
showInMenu = true
```

E quando ela veio retornada em `/me/apps`.

O Portal não precisa revalidar a permissão para decidir se a rota aparece, porque a Core API já filtrou as rotas.

Fluxo:

```text
apps = GET /me/apps
  ↓
para cada app
  ↓
para cada route em app.routes
  ↓
se route.showInMenu === true
  ↓
exibir item no menu
```

---

## 7. Rotas ocultas do menu

Uma rota pode ser autorizada, mas não aparecer no menu.

Exemplo:

```json
{
  "path": "/apps/dashboard-lmps/detalhes",
  "label": "Detalhes",
  "permission": "dashboard-lmps.access",
  "showInMenu": false
}
```

Uso possível:

- páginas de detalhe;
- telas acessadas por link interno;
- subfluxos;
- rotas técnicas;
- rotas que não devem poluir a navegação principal.

Regra:

> `showInMenu=false` não significa rota proibida. Significa apenas rota não exibida no menu.

---

## 8. Ordenação

O campo `order` define a ordem de exibição.

Regra recomendada:

```text
1. Ordenar por order ascendente quando existir.
2. Rotas sem order podem ficar após as ordenadas.
3. Em empate, ordenar por label.
```

Exemplo:

```json
[
  { "label": "Dashboard", "order": 1 },
  { "label": "Indicadores", "order": 2 },
  { "label": "Qualidade", "order": 10 }
]
```

---

## 9. Ícones

A rota pode ter ícone próprio.

Se não tiver, o Portal pode usar o ícone do app.

Regra recomendada:

```text
route.icon || app.icon || ícone padrão
```

Exemplo:

```json
{
  "app_icon": "layout-dashboard",
  "icon": "bar-chart3"
}
```

---

## 10. Agrupamento de menu

O schema de manifesto permite `menuGroup` nas rotas.

A resposta atual de `/me/apps` pode não expor explicitamente `menuGroup` dependendo da implementação do DTO.

Regra recomendada para evolução:

- se `menuGroup` for exposto, o Portal pode agrupar rotas;
- se não for exposto, agrupar por app ou categoria;
- evitar lógica hardcoded de grupos no frontend.

Exemplo futuro:

```json
{
  "label": "Dashboard LMPs",
  "menuGroup": "Dashboards"
}
```

---

## 11. Apps sem rotas de menu

Um app pode ter rotas autorizadas, mas todas com `showInMenu=false`.

Nesse caso:

- o app pode continuar acessível por navegação interna;
- o app pode não aparecer no menu principal;
- o app pode aparecer em outro launcher, se houver regra específica;
- a decisão deve ser consciente no Portal.

Regra para menu lateral:

```text
Se app não possui nenhuma route.showInMenu=true, não exibir no menu lateral.
```

---

## 12. Apps backend-only

Plugins `backend-only` não possuem rotas.

Normalmente, não aparecem no menu.

Uso deles:

- governança de backend;
- permissões;
- dependências;
- metadados técnicos.

Regra:

```text
Não renderizar backend-only como item de navegação.
```

---

## 13. Apps desativados

Apps desativados não devem ser retornados por `/me/apps`.

A Core API filtra apps ativos no `AppQueryRepository`.

Consequência:

- o Portal não precisa exibir estado de app desativado no menu comum;
- área administrativa pode listar apps inativos separadamente;
- se app atual for desativado, Portal deve redirecionar usuário para rota segura.

---

## 14. Permissões e menu

A Core API filtra rotas por permissão.

Regra da autorização:

- superadmin recebe tudo;
- rota sem permissão é permitida;
- rota com permissão exige que a permissão esteja nas permissões efetivas do usuário;
- app sem rotas autorizadas é removido.

O Portal pode usar `permission` para UX, mas não deve usá-lo como fonte final de autorização.

---

## 15. Menu administrativo

O Portal pode possuir menu administrativo interno.

Esse menu pode ser baseado nas permissões retornadas em `/me`.

Exemplos:

| Item | Permissão sugerida |
|---|---|
| Usuários | `users.view` ou `users.manage` |
| RBAC | `rbac.manage` |
| Apps | `apps.view` ou `apps.manage` |
| Rotas | `routes.manage` |
| Permissões | `permissions.manage` |

Mesmo que o item seja ocultado no frontend, os endpoints administrativos continuam protegidos na Core API.

---

## 16. Rota atual e autorização

O Portal deve validar se a rota atual ainda existe após mudanças administrativas.

Cenários:

- usuário perdeu permissão;
- role foi removida;
- grupo foi alterado;
- plugin foi desativado;
- rota foi removida;
- rollback mudou o conjunto de rotas;
- app foi removido.

Comportamento recomendado:

```text
Evento relevante ou reload de sessão
  ↓
Recarrega /me/apps
  ↓
Verifica se pathname atual existe nas rotas autorizadas
  ↓
Se não existir, redireciona para home/dashboard
```

---

## 17. Eventos que exigem reload do menu

O Portal deve recarregar `/me/apps` em eventos como:

```text
plugin_registered
plugin_unregistered
plugin_manifest_updated
plugin_version_rolled_back
plugin_activated
plugin_deactivated
plugins_activation_changed
plugins_unregistered
route_created
route_updated
route_deleted
routes_bulk_deleted
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

Nem todos os eventos exigem a mesma reação, mas todos podem afetar apps, rotas ou permissões.

---

## 18. Estados de carregamento

O menu deve considerar estados:

- carregando apps;
- erro ao carregar apps;
- nenhum app disponível;
- usuário sem permissões;
- sessão expirada;
- Core API indisponível.

Exemplo de comportamento:

```text
GET /me/apps falhou com 401
  ↓
Renovar token ou redirecionar para login
```

```text
GET /me/apps retorna []
  ↓
Exibir mensagem amigável ou dashboard vazio
```

---

## 19. Roteamento frontend

O roteamento frontend deve ser derivado das rotas autorizadas.

Exemplo conceitual:

```text
/apps/dashboard-lmps
/apps/strategic-indicators
/apps/sistema-externo
```

Para cada rota:

- identificar app dono;
- identificar tipo do app;
- identificar renderMode;
- carregar plugin apropriado;
- passar contexto necessário.

---

## 20. Pseudocódigo de montagem

Exemplo conceitual:

```typescript
type MenuItem = {
  label: string
  path: string
  icon?: string
  order?: number
  appId: string
}

function buildMenu(apps): MenuItem[] {
  const items = []

  for (const app of apps) {
    for (const route of app.routes || []) {
      if (!route.showInMenu) continue

      items.push({
        label: route.label || app.name,
        path: route.path,
        icon: route.icon || app.icon,
        order: route.order ?? 9999,
        appId: app.id,
      })
    }
  }

  return items.sort((a, b) => {
    if (a.order !== b.order) return a.order - b.order
    return a.label.localeCompare(b.label)
  })
}
```

---

## 21. Boas práticas

1. Buscar `/me/apps` após login.
2. Não hardcodar plugins no menu principal.
3. Usar `showInMenu` para controlar exibição.
4. Usar `order` para ordenação.
5. Usar fallback de ícone.
6. Recarregar menu em eventos administrativos relevantes.
7. Validar rota atual após reload.
8. Separar menu administrativo de menu de apps plugáveis.
9. Não confiar no frontend como segurança final.
10. Tratar estado vazio e erros de API.

---

## 22. Checklist de implementação

- [ ] Portal chama `/me/apps` após login.
- [ ] Menu usa apenas rotas retornadas.
- [ ] Rotas com `showInMenu=false` não aparecem.
- [ ] Ordenação por `order` está implementada.
- [ ] Fallback de ícone está implementado.
- [ ] Apps backend-only não aparecem como menu.
- [ ] Eventos administrativos recarregam menu.
- [ ] Rota atual é validada após reload.
- [ ] Área admin respeita permissões de `/me`.
- [ ] Erros de carregamento têm feedback visual.

---

## 23. Pontos de atenção

1. `/me/apps` já vem filtrado; não refazer regra complexa no frontend.
2. `showInMenu=false` não significa não autorizado.
3. App sem rota autorizada não deve aparecer.
4. Backend-only normalmente não aparece no menu.
5. Eventos RBAC podem mudar o menu de um usuário sem novo login.
6. Rollback de plugin pode remover rota atual.
7. Desativação de plugin pode invalidar rota atual.
8. Ícones devem ter fallback seguro.
9. Menu administrativo pode usar permissões de `/me`, mas endpoints continuam protegidos.
10. Evitar cache local prolongado de `/me/apps` sem invalidação.

---

## 24. Documentos relacionados

```text
docs/06-portal-frontend/visao-geral-portal.md
docs/06-portal-frontend/consumo-de-plugins.md
docs/06-portal-frontend/app-authorization.md
docs/03-autenticacao-autorizacao/rbac.md
docs/05-plugin-system/manifesto-plugin.md
docs/05-plugin-system/microfrontends.md
```

