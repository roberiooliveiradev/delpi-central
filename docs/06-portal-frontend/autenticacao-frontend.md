# Minha DELPI — Autenticação Frontend

> **Arquivo:** `docs/06-portal-frontend/autenticacao-frontend.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** autenticação do Portal com Keycloak e uso de token nas APIs

---

## 1. Objetivo

Este documento descreve como o **Portal** da Minha DELPI deve lidar com autenticação no frontend.

Ele explica:

- o papel do Keycloak no frontend;
- quais variáveis configuram o client;
- como o token é obtido;
- como o token é enviado para a Core API;
- como tratar expiração e renovação;
- quais cuidados de segurança devem ser seguidos.

---

## 2. Princípio central

O Portal autentica o usuário via Keycloak e usa o access token para consumir APIs protegidas.

```text
Portal → Keycloak → access token → Core API / API DELPI / plugins
```

A autenticação acontece no Keycloak.

A autorização funcional da plataforma é calculada pela Core API.

Regra:

> O frontend não deve considerar o JWT como fonte final de autorização. Ele deve consultar `/me` e `/me/apps` na Core API.

---

## 3. Componentes envolvidos

| Componente | Responsabilidade |
|---|---|
| Portal | Iniciar login, manter sessão frontend, enviar token |
| Keycloak | Autenticar usuário e emitir tokens |
| Core API | Validar token, sincronizar usuário e resolver permissões |
| API DELPI | Validar token em endpoints operacionais protegidos |
| Gateway | Roteamento HTTP entre navegador e serviços |

---

## 4. Variáveis de ambiente

O Portal usa variáveis Vite para configurar o client Keycloak.

```env
VITE_KC_URL=
VITE_KC_REALM=
VITE_KC_CLIENT_ID=
VITE_KC_REDIRECT_URI=
```

Descrição:

| Variável | Descrição |
|---|---|
| `VITE_KC_URL` | URL base do Keycloak exposta ao navegador |
| `VITE_KC_REALM` | Realm usado pela Minha DELPI |
| `VITE_KC_CLIENT_ID` | Client público do Portal |
| `VITE_KC_REDIRECT_URI` | URI de redirecionamento após login |

Atenção:

> Variáveis `VITE_*` são embutidas no build frontend. Não colocar segredos nelas.

---

## 5. Fluxo de login

Fluxo geral:

```text
Usuário acessa Portal
  ↓
Portal inicializa client Keycloak
  ↓
Portal verifica se há sessão ativa
  ↓
Se não autenticado, redireciona para login
  ↓
Usuário autentica no Keycloak
  ↓
Keycloak redireciona para Portal
  ↓
Portal recebe tokens
  ↓
Portal chama Core API
```

---

## 6. Fluxo pós-login

Após login, o Portal deve inicializar o estado da plataforma.

Fluxo recomendado:

```text
Token disponível
  ↓
GET /me
  ↓
GET /me/apps
  ↓
GET /me/apps/favorites
  ↓
GET /me/notifications
  ↓
Conectar Socket.IO com token
  ↓
Renderizar shell autenticado
```

O Portal deve evitar renderizar áreas autenticadas antes de confirmar o estado mínimo do usuário.

---

## 7. Envio do token para APIs

Todas as chamadas protegidas devem enviar o token no header:

```http
Authorization: Bearer <access_token>
```

Exemplo conceitual:

```typescript
fetch("/core-api/me", {
  headers: {
    Authorization: `Bearer ${accessToken}`,
  },
})
```

O mesmo padrão deve ser usado para Core API, API DELPI e APIs de plugins que exigem autenticação.

---

## 8. Endpoint `/me`

Após autenticação, o Portal deve consultar:

```http
GET /me
```

Esse endpoint retorna a identidade local e as permissões efetivas calculadas pela Core API.

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

Uso no Portal:

- exibir usuário;
- habilitar áreas administrativas;
- adaptar UI;
- passar contexto a plugins quando necessário.

---

## 9. Endpoint `/me/apps`

Após `/me`, o Portal deve consultar:

```http
GET /me/apps
```

Esse endpoint retorna apps e rotas autorizados.

O Portal deve montar menu e rotas plugáveis a partir dessa resposta.

Regra:

> A lista de apps autorizados vem da Core API, não do token nem de configuração fixa no frontend.

---

## 10. Expiração do token

O Portal deve tratar expiração de token.

Cenários:

- access token expirou;
- refresh falhou;
- sessão Keycloak expirou;
- usuário fez logout em outra aba;
- Core API retornou 401.

Comportamento recomendado:

```text
Antes de chamada protegida
  ↓
Verificar/renovar token se necessário
  ↓
Se renovação falhar, redirecionar para login
```

---

## 11. Renovação de token

Se o client Keycloak usado no Portal suportar renovação, o Portal deve renovar token antes de chamadas protegidas ou periodicamente.

Fluxo conceitual:

```text
Token perto de expirar
  ↓
updateToken / refresh
  ↓
Se sucesso, atualizar token em memória
  ↓
Se falha, limpar sessão e redirecionar login
```

A política exata depende da biblioteca usada no frontend.

---

## 12. Tratamento de 401

Se uma chamada protegida retorna 401:

```text
API retorna 401
  ↓
Portal tenta renovar token, se possível
  ↓
Repete chamada uma vez
  ↓
Se continuar 401, redireciona para login
```

Evitar loops infinitos de retry.

---

## 13. Tratamento de 403

Se uma chamada retorna 403:

```text
Usuário autenticado, mas sem permissão
```

Comportamento recomendado:

- exibir mensagem de acesso negado;
- não redirecionar necessariamente para login;
- recarregar `/me` e `/me/apps` se a autorização pode ter mudado;
- redirecionar para rota segura se a rota atual não for mais autorizada.

---

## 14. Logout

O logout deve encerrar a sessão no Portal e no Keycloak.

Fluxo:

```text
Usuário clica sair
  ↓
Portal chama logout do Keycloak
  ↓
Portal limpa estado local
  ↓
Redireciona para tela pública/login
```

O Portal deve limpar:

- dados do usuário;
- apps carregados;
- favoritos;
- notificações;
- conexão Socket.IO;
- cache em memória relacionado à sessão.

---

## 15. Socket.IO autenticado

O Portal deve conectar ao Socket.IO usando token.

Exemplo conceitual:

```typescript
const socket = io("/", {
  auth: {
    token: accessToken,
  },
})
```

A Core API valida o token no handshake e coloca o cliente em uma sala baseada no `sub` do usuário.

Se o token expirar, o Portal deve reconectar com token válido.

---

## 16. Armazenamento do token

O armazenamento do token deve minimizar exposição.

Recomendações:

- preferir token em memória quando possível;
- evitar localStorage se não for necessário;
- não armazenar client secret;
- não expor token em URL/query string;
- limpar token no logout;
- tratar múltiplas abas com cuidado.

Atenção:

> Como aplicação frontend pública, o Portal não deve conter segredos. O client Keycloak do Portal deve ser público.

---

## 17. Tokens em plugins

Microfrontends podem precisar chamar APIs protegidas.

Opções:

- receber token via contexto do Portal;
- usar um client HTTP compartilhado;
- receber callback para obter token atualizado;
- depender de APIs chamadas pelo shell.

Regra:

> Evitar passar token para plugins sem necessidade. Quando necessário, passar de forma controlada e documentada.

Para iframes, evitar token em query string.

---

## 18. Separação entre autenticação e autorização

O Portal pode autenticar o usuário, mas não deve decidir sozinho permissões finais.

Fluxo correto:

```text
JWT válido
  ↓
Core API sincroniza usuário
  ↓
Core API resolve permissões
  ↓
Portal recebe /me e /me/apps
```

Fluxo incorreto:

```text
Portal lê roles do token
  ↓
Portal decide sozinho apps e rotas
```

Esse fluxo é incorreto porque a autorização vigente está no RBAC interno da Core API.

---

## 19. Proteção de rotas frontend

Rotas autenticadas devem exigir sessão válida.

Rotas plugáveis devem exigir que o path esteja presente em `/me/apps`.

Pseudocódigo:

```typescript
if (!auth.isAuthenticated) {
  redirectToLogin()
}

const match = findAuthorizedRoute(apps, location.pathname)

if (!match) {
  showNotFoundOrForbidden()
}
```

---

## 20. Proteção de áreas administrativas

Áreas administrativas do Portal podem usar permissões de `/me` para UX.

Exemplo:

```typescript
const canManageApps = user.permissions.includes("apps.manage")
```

Mas o backend deve continuar protegendo endpoints administrativos.

Regra:

> Ocultar botão no frontend não substitui `@require_permission` no backend.

---

## 21. Estados de autenticação

O Portal deve tratar estados:

```text
initializing
authenticated
unauthenticated
refreshing_token
expired
error
```

Estados recomendados de UI:

- tela de carregamento durante inicialização;
- redirecionamento para login quando não autenticado;
- mensagem de erro se Keycloak indisponível;
- reconexão ou logout se token expirou.

---

## 22. Erros comuns

### 22.1 `invalid_token`

Possíveis causas:

- token expirado;
- issuer errado;
- audience errada;
- JWKS inacessível;
- token de outro realm/client.

Ação:

- renovar token;
- validar variáveis Keycloak;
- verificar configuração da Core API.

---

### 22.2 `unauthorized`

Possíveis causas:

- header ausente;
- token ausente;
- sessão expirada;
- handshake Socket.IO sem token.

Ação:

- enviar `Authorization: Bearer`;
- redirecionar login;
- reconectar socket.

---

### 22.3 `forbidden`

Possíveis causas:

- usuário autenticado sem permissão;
- role/grupo não atribuído;
- app/rota exige permissão ausente;
- usuário perdeu acesso durante a sessão.

Ação:

- recarregar `/me` e `/me/apps`;
- exibir acesso negado;
- redirecionar para rota segura.

---

## 23. Desenvolvimento local

No Docker Compose dev, o Portal recebe:

```env
VITE_KC_URL=
VITE_KC_REALM=
VITE_KC_CLIENT_ID=
VITE_KC_REDIRECT_URI=
```

O Keycloak roda com:

```text
start-dev
```

O Gateway expõe a plataforma em:

```text
http://localhost/
```

O redirect URI deve ser compatível com a URL usada no navegador.

---

## 24. Produção

Em produção, o Portal recebe variáveis Vite como build args.

Atenção:

> Mudanças em variáveis `VITE_*` podem exigir rebuild do Portal, porque são incorporadas no build.

Keycloak roda com:

```text
start
```

E deve ter hostname, proxy e redirect URIs configurados corretamente.

---

## 25. Checklist de implementação

- [ ] Keycloak inicializa corretamente no Portal.
- [ ] Login redireciona para realm correto.
- [ ] Redirect URI está configurada no client.
- [ ] Token é enviado em `Authorization: Bearer`.
- [ ] `/me` é chamado após login.
- [ ] `/me/apps` é chamado após login.
- [ ] 401 dispara renovação ou login.
- [ ] 403 exibe acesso negado, não login automático.
- [ ] Logout limpa estado local.
- [ ] Socket.IO envia token no handshake.
- [ ] Token não é colocado em query string de iframe.
- [ ] Áreas admin usam permissões de `/me` para UX.

---

## 26. Pontos de atenção

1. `VITE_*` não pode conter segredo.
2. O client do Portal deve ser público.
3. Keycloak autentica, Core API autoriza.
4. `/me` é a fonte do usuário efetivo na plataforma.
5. `/me/apps` é a fonte dos apps autorizados.
6. Token expirado deve ser tratado sem loop infinito.
7. Iframes não devem receber token em URL.
8. Microfrontends devem receber contexto de forma controlada.
9. Logout deve fechar Socket.IO.
10. Mudança de variáveis Vite em produção pode exigir rebuild.

---

## 27. Documentos relacionados

```text
docs/06-portal-frontend/visao-geral-portal.md
docs/06-portal-frontend/menu-dinamico.md
docs/06-portal-frontend/app-authorization.md
docs/06-portal-frontend/consumo-de-plugins.md
docs/03-autenticacao-autorizacao/rbac.md
docs/03-autenticacao-autorizacao/jwt.md
docs/03-autenticacao-autorizacao/keycloak-sso.md
```

