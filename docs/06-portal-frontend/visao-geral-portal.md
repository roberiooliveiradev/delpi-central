# Minha DELPI — Visão Geral do Portal Frontend

> **Arquivo:** `docs/06-portal-frontend/visao-geral-portal.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** visão técnica e funcional do Portal frontend

---

## 1. Objetivo

Este documento descreve o papel do **Portal** na arquitetura da Minha DELPI.

O Portal é o frontend principal da plataforma. Ele autentica o usuário via Keycloak, consome a Core API, monta a navegação dinâmica e carrega apps/plugins autorizados.

Este documento apresenta a visão geral. Documentos específicos devem detalhar autenticação frontend, menu dinâmico, favoritos e consumo de plugins.

---

## 2. Papel do Portal

O Portal é o shell visual da Minha DELPI.

Responsabilidades principais:

- exibir a interface principal da plataforma;
- iniciar autenticação via Keycloak;
- armazenar e fornecer o token de acesso para chamadas HTTP;
- consultar dados do usuário atual;
- consultar apps e rotas autorizadas;
- montar menu dinâmico;
- exibir favoritos;
- exibir notificações;
- conectar ao Socket.IO para eventos administrativos;
- carregar microfrontends e iframes;
- servir como experiência unificada para módulos internos.

O Portal não é responsável por calcular permissões efetivas.

A autorização é resolvida pela Core API.

---

## 3. Stack técnica

O Portal é desenvolvido com:

```text
React
Vite
TypeScript/JavaScript conforme implementação
Keycloak JS / OIDC client
HTTP client para Core API
Socket.IO client
```

Serviço Docker:

```text
portal
```

Container:

```text
delpi-portal
```

Build de produção:

```text
portal/Dockerfile.prod
```

Build de desenvolvimento:

```text
portal/Dockerfile.dev
```

---

## 4. Relação com outros serviços

O Portal se comunica principalmente com:

| Serviço | Uso |
|---|---|
| Keycloak | Login, logout e obtenção de token |
| Core API | Usuário atual, apps, rotas, favoritos, notificações |
| Gateway | Entrada única e roteamento |
| Plugins | Carregamento visual de microfrontends/iframes |
| API DELPI | Dados operacionais consumidos por telas ou plugins, quando aplicável |

Fluxo simplificado:

```text
Usuário
  ↓
Gateway
  ↓
Portal
  ↓
Keycloak
  ↓
Core API
  ↓
Plugins / API DELPI
```

---

## 5. Configuração via ambiente

O Portal recebe variáveis relacionadas ao Keycloak.

Variáveis principais:

```env
VITE_KC_URL=
VITE_KC_REALM=
VITE_KC_CLIENT_ID=
VITE_KC_REDIRECT_URI=
```

No Docker Compose de produção, essas variáveis são passadas como `build args`.

No Docker Compose de desenvolvimento, essas variáveis são passadas como variáveis de ambiente do container.

---

## 6. Fluxo de autenticação

O Portal inicia o login via Keycloak.

Fluxo:

```text
Usuário acessa Portal
  ↓
Portal verifica sessão/token
  ↓
Se não autenticado, redireciona para Keycloak
  ↓
Usuário faz login
  ↓
Keycloak retorna access token
  ↓
Portal armazena token no contexto de autenticação
  ↓
Portal usa token para chamar Core API
```

O token é enviado para APIs protegidas no header:

```http
Authorization: Bearer <access_token>
```

---

## 7. Fluxo de inicialização pós-login

Após autenticação, o Portal deve carregar o estado inicial do usuário.

Fluxo recomendado:

```text
Login concluído
  ↓
GET /me
  ↓
GET /me/apps
  ↓
GET /me/apps/favorites
  ↓
GET /me/notifications
  ↓
Conectar Socket.IO
  ↓
Renderizar layout e menu
```

A ordem pode variar conforme implementação, mas a lógica deve garantir que menu e apps sejam baseados na Core API.

---

## 8. Endpoint `/me`

O endpoint `/me` retorna dados do usuário atual.

Uso pelo Portal:

- exibir nome/email;
- identificar superadmin;
- manter permissões efetivas disponíveis no frontend;
- habilitar ou ocultar áreas administrativas.

Formato conceitual:

```json
{
  "id": "uuid",
  "name": "Nome do Usuário",
  "email": "usuario@empresa.com",
  "is_superadmin": false,
  "permissions": [
    "apps.view",
    "dashboard-lmps.access"
  ]
}
```

Observação:

> O Portal pode usar permissões para experiência visual, mas decisões críticas devem continuar protegidas no backend.

---

## 9. Endpoint `/me/apps`

O endpoint `/me/apps` é a principal fonte do menu dinâmico.

Ele retorna apps e rotas já autorizados pela Core API.

Fluxo:

```text
Portal chama /me/apps
  ↓
Core API lista apps ativos
  ↓
Core API filtra rotas por permissão
  ↓
Portal recebe somente apps autorizados
  ↓
Portal monta navegação
```

Formato conceitual:

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

## 10. Menu dinâmico

O menu do Portal deve ser construído a partir de `/me/apps`.

Regras:

- usar apenas apps retornados pela Core API;
- considerar apenas rotas retornadas pela Core API;
- exibir no menu apenas rotas com `showInMenu = true`;
- ordenar por `order` quando disponível;
- usar `label` e `icon` vindos da Core API;
- não manter lista fixa definitiva de apps no frontend.

O Portal pode ter rotas internas próprias, como:

- home;
- perfil;
- administração;
- fallback/not found.

Mas apps plugáveis devem vir da Core API.

---

## 11. Favoritos

O Portal permite favoritar apps.

Endpoints:

```http
GET    /me/apps/favorites
POST   /me/apps/favorites/<app_id>
DELETE /me/apps/favorites/<app_id>
```

Regras:

- favoritos são persistidos por usuário;
- somente apps autorizados devem aparecer na listagem final;
- adicionar favorito valida se o app existe entre apps ativos;
- eventos direcionados ao usuário podem notificar alteração.

Fluxo:

```text
Usuário favorita app
  ↓
POST /me/apps/favorites/<app_id>
  ↓
Core API persiste favorito
  ↓
Evento favorite_added para usuário
  ↓
Portal atualiza UI
```

---

## 12. Notificações

O Portal consome notificações da Core API.

Endpoints:

```http
GET  /me/notifications
POST /me/notifications/<notification_id>/read
POST /me/notifications/read-all
```

Possível endpoint de teste em desenvolvimento:

```http
POST /me/notifications/test
```

Fluxo:

```text
Portal lista notificações não lidas
  ↓
Usuário marca uma como lida
  ↓
Core API atualiza read_at
  ↓
Evento de domínio é coletado
  ↓
Portal atualiza contadores/UI
```

---

## 13. Socket.IO

O Portal pode conectar ao Socket.IO da Core API para receber eventos em tempo real.

Durante conexão, deve enviar token:

```javascript
io("/", {
  auth: {
    token: accessToken
  }
})
```

A Core API valida o token e coloca o cliente em uma sala baseada no `sub` do usuário.

Evento principal:

```text
admin.changed
```

Exemplo de payload:

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

---

## 14. Reação a eventos

O Portal deve reagir a eventos administrativos relevantes.

Exemplos:

| Evento | Ação recomendada no Portal |
|---|---|
| `plugin_registered` | Recarregar apps/rotas |
| `plugin_unregistered` | Recarregar apps/rotas e validar rota atual |
| `plugin_manifest_updated` | Recarregar menu/metadados |
| `plugin_activated` | Recarregar apps/rotas |
| `plugin_deactivated` | Recarregar apps/rotas e sair se rota atual foi removida |
| `route_created` | Recarregar apps/rotas |
| `route_updated` | Recarregar menu |
| `route_deleted` | Recarregar apps/rotas |
| `role_added_to_user` | Recarregar `/me` e `/me/apps` |
| `role_removed_from_user` | Recarregar `/me` e `/me/apps` |
| `groups_replaced` | Recarregar `/me` e `/me/apps` |
| `favorite_added` | Recarregar favoritos |
| `favorite_removed` | Recarregar favoritos |

---

## 15. Carregamento de plugins

O Portal carrega plugins com base em:

```text
app.type
app.entryUrl
app.renderMode
route.entry
route.path
```

Tipos:

| Tipo | Estratégia esperada |
|---|---|
| `microfrontend` | Carregar módulo/entry integrado |
| `iframe` | Renderizar URL em iframe ou abrir externo |
| `backend-only` | Não renderizar UI |

---

## 16. Microfrontends

Para microfrontends, o Portal usa:

```text
entryUrl
renderMode
routes[].entry opcional
```

Exemplo:

```json
{
  "type": "microfrontend",
  "entryUrl": "/apps/dashboard-lmps/assets/remoteEntry.js",
  "renderMode": "federated"
}
```

O comportamento exato depende da implementação do carregador frontend.

Regra:

> O microfrontend deve ser servido pelo Gateway no path compatível com `basePath` e `entryUrl`.

---

## 17. Iframes

Para iframes, o Portal usa:

```text
entryUrl
renderMode
```

Se `renderMode = embedded`, o Portal pode renderizar:

```html
<iframe src="entryUrl"></iframe>
```

Se `renderMode = external`, pode abrir a URL fora do shell.

A aplicação externa precisa permitir iframe quando embutida.

---

## 18. Backend-only

Plugins `backend-only` não devem gerar tela navegável.

Eles podem existir para:

- registrar permissões;
- representar backend;
- declarar dependências;
- governar APIs;
- apoiar plugins visuais.

Como não possuem rotas, normalmente não aparecem no menu.

---

## 19. Administração no Portal

O Portal pode ter uma área administrativa que consome endpoints da Core API.

Funcionalidades possíveis:

- listar usuários;
- listar roles;
- listar groups;
- listar permissions;
- editar vínculos RBAC;
- listar apps/plugins;
- registrar plugin;
- editar metadata;
- gerenciar rotas;
- ativar/desativar apps;
- rollback;
- unregister.

A exibição dessas áreas deve depender de permissões como:

```text
rbac.manage
users.view
users.manage
apps.view
apps.manage
routes.manage
```

O backend deve continuar protegendo os endpoints.

---

## 20. Separação de responsabilidades

### O Portal deve fazer

- renderizar interface;
- consumir APIs;
- montar menu a partir de `/me/apps`;
- reagir a eventos;
- carregar plugins;
- melhorar experiência do usuário.

### O Portal não deve fazer

- decidir permissões efetivas;
- consultar banco diretamente;
- registrar app sem Core API;
- confiar apenas em esconder botões como segurança;
- duplicar regras complexas de RBAC;
- manter lista fixa de plugins como fonte final.

---

## 21. Tratamento de rota atual

Quando eventos administrativos mudam apps/rotas/permissões, o Portal deve verificar se a rota atual ainda é válida.

Cenários:

- plugin foi desativado;
- rota foi removida;
- usuário perdeu permissão;
- plugin foi removido;
- rollback removeu rota atual.

Comportamento recomendado:

```text
Evento relevante recebido
  ↓
Recarregar /me/apps
  ↓
Verificar se rota atual ainda existe/autorizada
  ↓
Se não existir, redirecionar para home ou página segura
```

---

## 22. Estados de carregamento e erro

O Portal deve tratar estados como:

- carregando autenticação;
- carregando usuário;
- carregando apps;
- erro de autenticação;
- erro de autorização;
- sessão expirada;
- plugin indisponível;
- entryUrl inacessível;
- rota não autorizada;
- erro de conexão Socket.IO.

Cada estado deve ter feedback visual adequado.

---

## 23. Segurança no frontend

Regras:

1. Não armazenar segredos no frontend.
2. Não expor client secret no Portal.
3. Não confiar em ocultação de botão como controle final.
4. Sempre enviar token para APIs protegidas.
5. Renovar ou tratar expiração de token.
6. Proteger rotas administrativas visualmente e no backend.
7. Não colocar tokens sensíveis em query string para iframes.
8. Sanitizar dados renderizados quando necessário.

---

## 24. Desenvolvimento local

No Docker Compose dev, o Portal usa:

```yaml
build:
  context: ../portal
  dockerfile: Dockerfile.dev
```

Volumes:

```yaml
../portal:/app
/app/node_modules
```

Variáveis:

```env
VITE_KC_URL=
VITE_KC_REALM=
VITE_KC_CLIENT_ID=
VITE_KC_REDIRECT_URI=
```

Dependência:

```yaml
depends_on:
  - core-api
```

---

## 25. Produção

No Docker Compose de produção, o Portal usa:

```yaml
build:
  context: ../portal
  dockerfile: Dockerfile.prod
```

Args:

```env
VITE_KC_URL=
VITE_KC_REALM=
VITE_KC_CLIENT_ID=
VITE_KC_REDIRECT_URI=
```

O Portal fica atrás do Gateway, que expõe a porta `80`.

---

## 26. Checklist funcional do Portal

- [ ] Login via Keycloak funciona.
- [ ] Token é enviado para Core API.
- [ ] `/me` retorna usuário atual.
- [ ] `/me/apps` retorna apps autorizados.
- [ ] Menu usa apps/rotas da Core API.
- [ ] Favoritos são listados e atualizados.
- [ ] Notificações são listadas.
- [ ] Socket.IO conecta com token.
- [ ] Eventos administrativos recarregam estado.
- [ ] Microfrontends carregam corretamente.
- [ ] Iframes funcionam quando configurados.
- [ ] Rotas não autorizadas são bloqueadas ou redirecionadas.
- [ ] Área administrativa respeita permissões.

---

## 27. Pontos de atenção

1. O Portal não é fonte de verdade de permissões.
2. Apps e rotas devem vir da Core API.
3. Backend-only não deve ser renderizado como tela.
4. Microfrontends dependem de entryUrl acessível pelo Gateway.
5. Iframes podem ser bloqueados por headers da aplicação externa.
6. Eventos podem alterar a validade da rota atual.
7. Permissões no frontend são úteis para UX, não para segurança final.
8. O token precisa ser renovado ou tratado ao expirar.
9. Build de produção recebe variáveis Vite como build args.
10. Dev usa volumes para hot reload/ciclo rápido.

---

## 28. Documentos relacionados

```text
docs/06-portal-frontend/autenticacao-frontend.md
docs/06-portal-frontend/menu-dinamico.md
docs/06-portal-frontend/app-authorization.md
docs/06-portal-frontend/favoritos.md
docs/06-portal-frontend/consumo-de-plugins.md
docs/03-autenticacao-autorizacao/rbac.md
docs/05-plugin-system/microfrontends.md
docs/05-plugin-system/iframe.md
```

