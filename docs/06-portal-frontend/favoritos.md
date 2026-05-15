# Minha DELPI — Favoritos no Portal

> **Arquivo:** `docs/06-portal-frontend/favoritos.md`  
> **Status:** documentação oficial  
> **Implementação:** `AuthContext.addFavorite/removeFavorite`, `coreApi.ts`, `Sidebar` / `AppLauncher`  
> **Produto:** Minha DELPI  
> **Escopo:** favoritos de apps no Portal e Core API

---

## 1. Objetivo

Este documento descreve como funciona o recurso de **favoritos** da Minha DELPI.

Favoritos permitem que cada usuário marque apps da plataforma para acesso rápido no Portal.

O recurso é governado pela Core API e consumido pelo Portal.

---

## 2. Conceito

Favorito é um vínculo entre usuário e app.

Ele indica que determinado app deve aparecer em uma área de acesso rápido para aquele usuário.

Modelo conceitual:

```text
User
  ↓ favorita
App
```

Tabela principal:

```text
user_favorite_apps
```

Chave composta:

```text
user_id + app_id
```

---

## 3. Responsabilidades

| Responsabilidade | Portal | Core API |
|---|---:|---:|
| Exibir favoritos | Sim | Fornece dados |
| Adicionar favorito | Solicita | Valida e persiste |
| Remover favorito | Solicita | Remove vínculo |
| Validar usuário autenticado | Envia token | Valida JWT |
| Validar app existente | Não | Sim |
| Filtrar favoritos autorizados | Não | Sim |
| Emitir evento de alteração | Não | Sim |
| Atualizar UI em tempo real | Sim | Emite evento |

---

## 4. Endpoints

Endpoints usados pelo Portal:

```http
GET    /me/apps/favorites
POST   /me/apps/favorites/<app_id>
DELETE /me/apps/favorites/<app_id>
```

Todos exigem usuário autenticado.

---

## 5. Listar favoritos

Endpoint:

```http
GET /me/apps/favorites
```

Fluxo:

```text
Portal chama /me/apps/favorites
  ↓
Core API identifica usuário atual
  ↓
Lista favoritos persistidos do usuário
  ↓
Lista apps ativos com rotas
  ↓
Filtra apps autorizados pelo usuário
  ↓
Retorna apenas favoritos autorizados
```

Regra importante:

> Um favorito persistido só deve aparecer no Portal se o usuário ainda tiver acesso ao app.

---

## 6. Formato conceitual de resposta

Exemplo:

```json
[
  {
    "id": "dash-lmps",
    "name": "Dashboard LMPs",
    "description": "Painel de acompanhamento de LMPs.",
    "basePath": "/dash-lmps",
    "icon": "bar-chart3",
    "type": "microfrontend",
    "version": "1.0.0",
    "orderIndex": 0
  }
]
```

O formato exato depende do DTO retornado pelo repository de favoritos.

---

## 7. Adicionar favorito

Endpoint:

```http
POST /me/apps/favorites/<app_id>
```

Use case:

```text
AddFavoriteAppUseCase
```

Fluxo:

```text
Recebe user_id e app_id
  ↓
Valida se app existe entre apps ativos com rotas
  ↓
Verifica se favorito já existe
  ↓
Se já existe, retorna ok idempotente
  ↓
Se não existe, cria favorito
  ↓
Publica evento favorite_added direcionado ao usuário
```

Resposta esperada:

```json
{
  "ok": true
}
```

---

## 8. Idempotência ao adicionar

Adicionar favorito é idempotente.

Se o vínculo já existir:

```text
user_id + app_id já existe
```

A Core API retorna:

```json
{
  "ok": true
}
```

sem criar duplicidade.

---

## 9. App inexistente ou inativo

Ao adicionar favorito, a Core API valida se o app existe entre apps ativos com rotas.

Se não existir, o use case lança erro com mensagem conceitual:

```text
App não encontrada
```

Comportamento esperado no Portal:

- exibir mensagem amigável;
- recarregar lista de apps/favoritos;
- não marcar visualmente como favorito.

---

## 10. Remover favorito

Endpoint:

```http
DELETE /me/apps/favorites/<app_id>
```

Use case:

```text
RemoveFavoriteAppUseCase
```

Fluxo:

```text
Recebe user_id e app_id
  ↓
Remove favorito
  ↓
Publica evento favorite_removed direcionado ao usuário
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

## 11. Eventos de favoritos

Favoritos publicam eventos administrativos direcionados ao usuário.

### 11.1 Favorito adicionado

```python
AdminChangedEvent(
    entity="favorites",
    action="favorite_added",
    payload={
        "appId": app_id,
    },
    target_user_id=user_id,
)
```

### 11.2 Favorito removido

```python
AdminChangedEvent(
    entity="favorites",
    action="favorite_removed",
    payload={
        "userId": user_id,
        "appId": app_id,
    },
    target_user_id=user_id,
)
```

Como `target_user_id` é informado, o evento é emitido apenas para a sala Socket.IO do usuário.

---

## 12. Reação do Portal a eventos

O Portal deve reagir aos eventos:

```text
favorite_added
favorite_removed
```

Ação recomendada:

```text
Evento recebido
  ↓
Recarregar /me/apps/favorites
  ↓
Atualizar área de favoritos
```

Também é aceitável fazer atualização otimista na UI, desde que haja correção após confirmação da API.

---

## 13. Autorização e favoritos

Favoritos não devem furar autorização.

Cenário:

```text
Usuário favorita dash-lmps
  ↓
Depois perde dash-lmps.access
  ↓
Favorito permanece persistido
  ↓
ListFavoriteAppsUseCase filtra contra apps autorizados
  ↓
Portal não recebe dash-lmps nos favoritos
```

Se o usuário recuperar a permissão, o favorito pode voltar a aparecer.

---

## 14. Relação com `/me/apps`

A listagem de favoritos depende da autorização de apps.

Fluxo:

```text
Favoritos persistidos
  ↓
Apps ativos com rotas
  ↓
AppAuthorizationService
  ↓
Somente favoritos cujo app está autorizado
```

Portanto, a UI de favoritos deve estar alinhada à UI do menu.

Um app não autorizado não deve aparecer nem no menu nem nos favoritos.

---

## 15. Ordenação de favoritos

A tabela `user_favorite_apps` possui campo:

```text
order_index
```

Esse campo permite ordenar favoritos por usuário.

Uso esperado:

- manter ordem de exibição;
- permitir futura reorganização por drag and drop;
- exibir favoritos em ordem consistente.

Se ainda não houver endpoint de reordenação, o Portal deve apenas respeitar a ordem retornada pela Core API.

---

## 16. Modelo de banco

Tabela:

```text
user_favorite_apps
```

Campos principais:

| Campo | Descrição |
|---|---|
| `user_id` | UUID do usuário |
| `app_id` | ID do app/plugin |
| `order_index` | Ordem do favorito |
| `created_at` | Data de criação |
| `updated_at` | Data de atualização |

Chave primária:

```text
user_id + app_id
```

Relacionamentos:

```text
user_favorite_apps.user_id → users.id
user_favorite_apps.app_id  → apps.id
```

---

## 17. Comportamento recomendado no Portal

### 17.1 Adicionar favorito

```text
Usuário clica em favoritar
  ↓
UI mostra estado carregando ou otimista
  ↓
POST /me/apps/favorites/<app_id>
  ↓
Se sucesso, marcar favorito
  ↓
Se erro, desfazer e mostrar mensagem
```

### 17.2 Remover favorito

```text
Usuário clica em desfavoritar
  ↓
UI mostra estado carregando ou otimista
  ↓
DELETE /me/apps/favorites/<app_id>
  ↓
Se sucesso, remover favorito da UI
  ↓
Se erro, restaurar e mostrar mensagem
```

---

## 18. Estados de UI

A UI deve tratar:

- carregando favoritos;
- nenhum favorito;
- erro ao carregar favoritos;
- adicionando favorito;
- removendo favorito;
- app sem permissão;
- app removido/desativado;
- sessão expirada.

Exemplo de estado vazio:

```text
Você ainda não possui apps favoritos.
```

---

## 19. Sincronização com menu

Se o menu for atualizado por eventos de RBAC ou plugin, favoritos também podem ser impactados.

Eventos que podem exigir recarregar favoritos:

```text
role_added_to_user
role_removed_from_user
roles_replaced
group_added_to_user
group_removed_from_user
groups_replaced
plugin_deactivated
plugin_unregistered
plugin_version_rolled_back
route_deleted
permission_removed_from_role
role_permissions_replaced
```

Ação recomendada:

```text
Recarregar /me/apps
Recarregar /me/apps/favorites
```

---

## 20. Segurança

Favoritos são uma preferência de usuário, não uma autorização.

Regras:

1. Favoritar não concede permissão.
2. Remover favorito não remove permissão.
3. App favorito ainda precisa estar autorizado.
4. Backend deve validar usuário autenticado.
5. Portal não deve exibir favorito não retornado pela Core API.

---

## 21. Possíveis evoluções futuras

Possíveis melhorias:

- endpoint para reordenar favoritos;
- favoritos por rota, não apenas por app;
- limite máximo de favoritos;
- grupos de favoritos;
- sincronização entre dispositivos;
- favoritos sugeridos por perfil/grupo;
- auditoria de alterações de favoritos.

---

## 22. Checklist de implementação

- [ ] Portal chama `GET /me/apps/favorites` após login.
- [ ] Favoritos são exibidos apenas se retornados pela Core API.
- [ ] Botão de favoritar chama `POST /me/apps/favorites/<app_id>`.
- [ ] Botão de remover chama `DELETE /me/apps/favorites/<app_id>`.
- [ ] UI trata loading e erro.
- [ ] Eventos `favorite_added` e `favorite_removed` recarregam favoritos.
- [ ] Eventos de RBAC/plugin também podem recarregar favoritos.
- [ ] Favorito não concede acesso.
- [ ] App sem autorização não aparece como favorito.
- [ ] Ordem retornada pela API é respeitada.

---

## 23. Pontos de atenção

1. Favoritos são por usuário.
2. A chave é `user_id + app_id`.
3. Adicionar favorito é idempotente.
4. Favorito não contorna RBAC.
5. Listagem de favoritos filtra apps autorizados.
6. App desativado/removido pode sumir dos favoritos.
7. Perda de permissão pode ocultar favorito sem apagá-lo.
8. Eventos de favoritos são direcionados ao usuário.
9. Não há garantia de reordenação se não houver endpoint específico.
10. O Portal deve tratar estado vazio.

---

## 24. Documentos relacionados

```text
docs/06-portal-frontend/visao-geral-portal.md
docs/06-portal-frontend/menu-dinamico.md
docs/06-portal-frontend/app-authorization.md
docs/04-core-api/notificacoes.md
docs/03-autenticacao-autorizacao/rbac.md
```

