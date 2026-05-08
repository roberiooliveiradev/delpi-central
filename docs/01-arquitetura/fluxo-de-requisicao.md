# Minha DELPI — Fluxo de Requisição

> **Arquivo:** `docs/01-arquitetura/fluxo-de-requisicao.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** fluxo de requisições HTTP, autenticação, autorização, Core API, Portal, plugins e eventos

---

## 1. Objetivo

Este documento descreve os principais fluxos de requisição da **Minha DELPI**.

Ele apresenta como uma chamada sai do navegador, passa pelo Gateway, chega ao Portal, Core API, API DELPI ou plugins, e como autenticação, autorização, eventos e Socket.IO participam do processo.

---

## 2. Visão geral do fluxo

Fluxo macro:

```text
Navegador
  ↓
Gateway Nginx
  ↓
Portal / Core API / API DELPI / Keycloak / Plugins
```

O Gateway é a entrada HTTP única. Ele roteia as requisições por path para os serviços internos.

---

## 3. Fluxo de acesso inicial ao Portal

```text
Usuário acessa /
  ↓
Gateway roteia para portal
  ↓
Portal inicializa aplicação React
  ↓
Portal verifica sessão Keycloak
  ↓
Se não autenticado, redireciona para Keycloak
```

Responsabilidades:

| Componente | Responsabilidade |
|---|---|
| Gateway | Entregar Portal ao navegador |
| Portal | Inicializar shell frontend e autenticação |
| Keycloak | Autenticar usuário |
| Core API | Autorizar depois do login |

---

## 4. Fluxo de login SSO

```text
Portal
  ↓ redireciona
Keycloak
  ↓ autentica usuário
Keycloak
  ↓ retorna tokens
Portal
  ↓ armazena token no contexto de autenticação
Portal
  ↓ chama Core API com Bearer token
```

Header usado em chamadas protegidas:

```http
Authorization: Bearer <access_token>
```

Regra:

> Keycloak autentica. Core API autoriza.

---

## 5. Fluxo de chamada para `/me`

```text
Portal
  ↓ GET /me com Bearer token
Gateway
  ↓ roteia para Core API
Core API before_request
  ↓ auth_middleware.authenticate()
JWT validator
  ↓ valida token
Core API
  ↓ sincroniza usuário local
Core API
  ↓ carrega roles, groups e permissions
Controller /me
  ↓ retorna usuário atual
Portal
  ↓ atualiza estado autenticado
```

O middleware da Core API lê o header `Authorization`, valida o JWT, exige `sub` e `email`, valida `sub` como UUID, cria o usuário local caso não exista, atualiza `last_login_at` e popula `g.current_user`.

---

## 6. Fluxo de chamada para `/me/apps`

```text
Portal
  ↓ GET /me/apps
Gateway
  ↓ Core API
Auth middleware
  ↓ g.current_user
ListUserAppsUseCase
  ↓ AppQueryRepository
Apps ativos + rotas
  ↓ AppAuthorizationService
Filtro por permissions/is_superadmin
  ↓
Portal recebe apps e rotas autorizadas
```

O resultado alimenta:

- menu dinâmico;
- roteamento frontend;
- carregamento de plugins;
- favoritos;
- validação de rota atual.

---

## 7. Fluxo de renderização de plugin

```text
Usuário acessa rota /apps/<plugin>
  ↓
Portal procura rota em /me/apps
  ↓
Portal identifica app dono da rota
  ↓
Portal lê type, entryUrl e renderMode
  ↓
Se microfrontend, carrega módulo/entry
  ↓
Se iframe, renderiza ou abre URL
  ↓
Se backend-only, não renderiza UI
```

Regra:

> O Portal não deve renderizar plugin cuja rota não tenha vindo de `/me/apps`.

---

## 8. Fluxo de chamada para API DELPI

```text
Plugin ou Portal
  ↓ chamada HTTP com Bearer token
Gateway
  ↓ API DELPI
API DELPI
  ↓ valida JWT
API DELPI
  ↓ aplica permissão quando necessário
API DELPI
  ↓ consulta TOTVS / postgres-plugins / Portal RH
API DELPI
  ↓ retorna dados operacionais
```

A API DELPI é usada para dados e regras de domínio. Governança de usuários, apps e permissões pertence à Core API.

---

## 9. Fluxo de endpoint administrativo da Core API

Exemplo: registrar plugin.

```text
Portal Admin
  ↓ POST /admin/apps/register
Gateway
  ↓ Core API
Auth middleware
  ↓ valida token e popula g.current_user
Decorator
  ↓ exige apps.manage
Controller
  ↓ instancia Unit of Work
RegisterPluginUseCase
  ↓ valida manifesto
Repositories
  ↓ persiste app, manifesto, versão, permissões e rotas
Unit of Work
  ↓ commit
EventBus
  ↓ publica evento
Socket.IO
  ↓ notifica Portal
```

Esse padrão se aplica a outras ações administrativas:

- alterar RBAC;
- ativar plugin;
- atualizar manifesto;
- rollback;
- remover plugin;
- alterar favoritos;
- marcar notificação como lida.

---

## 10. Fluxo transacional com Unit of Work

```text
Controller
  ↓
with SqlAlchemyUnitOfWork() as uow:
  ↓
UseCase.execute()
  ↓
Repositories
  ↓
uow.collect_event(...)
  ↓
saída do contexto
  ↓
commit
  ↓
EventBus.publish(events)
```

Se houver exceção:

```text
exceção
  ↓
rollback
  ↓
eventos descartados
```

Regra:

> Evento só deve representar mudança persistida.

---

## 11. Fluxo de evento administrativo

```text
Use case
  ↓ collect_event(AdminChangedEvent)
Unit of Work
  ↓ commit
EventBus
  ↓ RbacEventHandler
  ↓ SocketIOEventDispatcher
Portal
  ↓ recebe admin.changed
Portal
  ↓ recarrega /me, /me/apps ou favoritos/notificações
```

Eventos podem ser globais ou direcionados a um usuário.

Exemplos de eventos:

```text
plugin_registered
plugin_unregistered
plugin_manifest_updated
plugin_version_rolled_back
role_added_to_user
role_removed_from_user
groups_replaced
favorite_added
favorite_removed
```

---

## 12. Fluxo Socket.IO

```text
Portal
  ↓ conecta Socket.IO com auth.token
Core API Socket handler
  ↓ valida JWT
  ↓ extrai sub
  ↓ join_room(sub)
Eventos direcionados
  ↓ emit para room do usuário
Eventos globais
  ↓ broadcast
```

Se o token não existir, não tiver `sub` ou for inválido, a conexão é recusada.

---

## 13. Fluxo de alteração de RBAC durante a sessão

```text
Administrador altera role/grupo/permissão
  ↓
Use case coleta evento
  ↓
Commit
  ↓
RbacEventHandler invalida cache de permissões
  ↓
Socket.IO notifica usuário ou todos
  ↓
Portal recarrega /me e /me/apps
  ↓
Menu e rota atual são reavaliados
```

Se o usuário perder acesso à rota atual, o Portal deve redirecionar para uma rota segura.

---

## 14. Fluxo de erro de autenticação

```text
Requisição protegida sem token
  ↓
Decorator require_auth
  ↓
401 unauthorized
```

```text
Token inválido
  ↓
auth_middleware
  ↓
401 invalid_token
```

```text
Token válido, mas sem permissão
  ↓
Decorator require_permission
  ↓
403 forbidden
```

---

## 15. Fluxo de favoritos

```text
Portal
  ↓ POST /me/apps/favorites/<app_id>
Core API
  ↓ valida usuário
  ↓ valida app
  ↓ cria favorito se não existir
  ↓ coleta favorite_added
  ↓ commit
Socket.IO
  ↓ evento para usuário
Portal
  ↓ recarrega favoritos
```

Listagem de favoritos deve respeitar apps autorizados.

---

## 16. Fluxo de notificações

```text
Portal
  ↓ GET /me/notifications
Core API
  ↓ lista notificações não lidas do usuário
Portal
  ↓ exibe contador/lista
```

Marcar como lida:

```text
Portal
  ↓ POST /me/notifications/<id>/read
Core API
  ↓ valida ownership
  ↓ preenche read_at
  ↓ retorna ok
```

---

## 17. Fluxo de registro de plugin

```text
POST /admin/apps/register
  ↓
Validação de manifesto
  ↓
Cálculo de checksum
  ↓
Criação/atualização de apps
  ↓
Persistência de app_manifests
  ↓
Criação de app_versions
  ↓
Criação de permissions
  ↓
Criação de app_routes
  ↓
Evento plugin_registered
```

Mudanças estruturais devem usar nova versão.

---

## 18. Fluxo de rollback de plugin

```text
POST /admin/apps/<plugin_id>/rollback
  ↓
Busca plugin
  ↓
Busca app_versions por versão alvo
  ↓
Restaura apps.version
  ↓
Restaura app_manifests
  ↓
Remove rotas/permissões atuais
  ↓
Recria permissões/rotas do manifesto histórico
  ↓
Evento plugin_version_rolled_back
```

---

## 19. Fluxo de unregister de plugin

```text
DELETE /admin/apps/<plugin_id>
  ↓
Busca plugin
  ↓
Verifica dependentes em manifestos
  ↓
Se houver dependentes, bloqueia
  ↓
Remove versões
  ↓
Remove rotas
  ↓
Remove permissões por module
  ↓
Remove manifesto
  ↓
Remove app
  ↓
Evento plugin_unregistered
```

---

## 20. Pontos de atenção

1. O Gateway roteia, mas não decide autorização de negócio.
2. O Portal renderiza somente o que a Core API autoriza.
3. O JWT identifica o usuário; RBAC interno decide permissões.
4. Controllers devem delegar regra para use cases.
5. Use cases devem usar Unit of Work.
6. Eventos devem ser publicados após commit.
7. Socket.IO exige token válido no handshake.
8. API DELPI deve validar JWT em endpoints protegidos.
9. Plugins não devem furar `/me/apps`.
10. Alterações de RBAC podem mudar a sessão sem novo login.

---

## 21. Documentos relacionados

```text
docs/01-arquitetura/arquitetura-geral.md
docs/01-arquitetura/event-driven-e-socket.md
docs/03-autenticacao-autorizacao/jwt.md
docs/03-autenticacao-autorizacao/rbac.md
docs/04-core-api/controllers-e-rotas.md
docs/04-core-api/unit-of-work.md
docs/06-portal-frontend/consumo-de-plugins.md
```
