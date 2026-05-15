# Minha DELPI — JWT, Claims e Validação de Token

> **Arquivo:** `docs/03-autenticacao-autorizacao/jwt.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** validação de JWT, claims, JWKS, issuer, audience e integração com Keycloak

---

## 1. Objetivo

Este documento descreve como a **Minha DELPI** utiliza tokens JWT para autenticação entre Portal, Keycloak, Core API, API DELPI e plugins.

Ele explica:

- o papel do JWT;
- quais claims são esperadas;
- como a Core API valida o token;
- como a API DELPI deve validar tokens;
- como o Portal envia o token;
- quais variáveis configuram issuer, audience e JWKS;
- erros comuns de autenticação.

---

## 2. Princípio central

O JWT autentica o usuário, mas não é a fonte final de autorização da plataforma.

```text
JWT → identifica o usuário
Core API → resolve permissões efetivas
```

Regra fundamental:

> O token confirma quem é o usuário. As permissões finais usadas pela Minha DELPI são calculadas pela Core API com base no RBAC interno.

---

## 3. Emissor do token

O emissor dos tokens é o **Keycloak**.

Fluxo:

```text
Portal redireciona usuário para Keycloak
  ↓
Usuário autentica
  ↓
Keycloak emite access token JWT
  ↓
Portal envia JWT para APIs protegidas
```

A Core API e a API DELPI validam o token antes de aceitar chamadas protegidas.

---

## 4. Serviços que usam JWT

| Serviço | Uso do JWT |
|---|---|
| Portal | Obtém e envia token |
| Core API | Valida token, sincroniza usuário e resolve permissões |
| API DELPI | Valida token (`delpi_auth`) em rotas protegidas |
| Minha DELPI AI API | Valida token via `KeycloakJwtValidator` (JWKS + issuer + audience) |
| Socket.IO | Valida token no handshake (`auth.token`) |
| Plugins | Recebem token do Portal para chamar APIs |
| Keycloak | Emite tokens e expõe JWKS |

---

## 5. Variáveis de ambiente da Core API

A Core API usa variáveis para validar tokens do Keycloak:

```env
KEYCLOAK_JWKS_URL=http://keycloak:8080/auth/realms/delpi/protocol/openid-connect/certs
KEYCLOAK_ISSUER=http://localhost/auth/realms/delpi
KEYCLOAK_AUDIENCE=delpi-central
JWT_ALGORITHMS=RS256
```

| Variável | Descrição |
|---|---|
| `KEYCLOAK_JWKS_URL` | JWKS **na rede Docker** (`keycloak:8080`) |
| `KEYCLOAK_ISSUER` | Issuer **público** — deve igualar o claim `iss` do token (`localhost/auth/...`) |
| `KEYCLOAK_AUDIENCE` | Valor esperado em `aud` (ex.: `delpi-central`) |
| `JWT_ALGORITHMS` | Ex.: `RS256` |

**Dois mundos:** o browser recebe token com `iss` via gateway; containers buscam chaves em `keycloak:8080`. Detalhes: [../02-infraestrutura/variaveis-de-ambiente.md](../02-infraestrutura/variaveis-de-ambiente.md).

---

## 6. Variáveis de ambiente da API DELPI

A API DELPI também recebe variáveis de JWT/OIDC:

```env
KEYCLOAK_JWKS_URL=
KEYCLOAK_ISSUER=
KEYCLOAK_AUDIENCE=
JWT_ALGORITHMS=RS256
```

Validação principal: pacote **`delpi_auth`** (middleware FastAPI) com JWKS, issuer e audience — mesmo padrão da Core API.

`API_DELPI_JWT_SECRET` / `JWT_SECRET` no Compose são legado/auxiliar; não substituem validação OIDC em rotas protegidas atuais.

---

## 6.1 Minha DELPI AI API

`minha-delpi-ai-api/app/infrastructure/security/jwt_validator.py`:

- `KEYCLOAK_JWKS_URL`, `KEYCLOAK_ISSUER`, `KEYCLOAK_AUDIENCE`
- `PyJWKClient` + `jwt.decode` com algoritmos permitidos

Rotas do chat exigem `Authorization: Bearer` igual às demais APIs.

---

## 7. Claims obrigatórias na Core API

A Core API espera claims suficientes para identificar e sincronizar o usuário local.

Claims principais:

| Claim | Uso |
|---|---|
| `sub` | ID único do usuário, usado como UUID local |
| `email` | Email do usuário, usado para busca/sincronização |
| `name` | Nome do usuário |
| `iss` | Issuer validado contra `KEYCLOAK_ISSUER` |
| `aud` | Audience validada contra `KEYCLOAK_AUDIENCE` |
| `exp` | Expiração do token |

Ponto crítico:

> A Core API valida o `sub` como UUID. Se o `sub` não for UUID válido, a autenticação falha.

---

## 8. Claim `sub`

O claim `sub` representa o identificador único do usuário no Keycloak.

Na Core API, ele é usado como ID local do usuário.

Regra atual:

```text
sub deve ser UUID válido
```

Fluxo:

```text
JWT.sub
  ↓
validar UUID
  ↓
users.id
```

Erro se inválido:

```json
{
  "errors": [
    {
      "code": "invalid_uuid",
      "message": "Invalid user identifier",
      "path": "sub"
    }
  ]
}
```

---

## 9. Claim `email`

O email é usado para localizar ou criar o usuário local.

Fluxo:

```text
JWT.email
  ↓
busca users.email
  ↓
se existe, usa usuário
  ↓
se não existe, cria usuário local
```

Regra:

> O email precisa estar presente e ser confiável no token emitido pelo Keycloak.

---

## 10. Claim `name`

O claim `name` é usado para preencher o nome local do usuário quando ele é criado.

Se ausente, a aplicação pode usar fallback baseado no email, conforme implementação.

Recomendação:

```text
Configurar Keycloak para incluir name e email no access token do client do Portal.
```

---

## 11. Validação de assinatura

A assinatura do token deve ser validada usando JWKS.

Fluxo:

```text
Recebe JWT
  ↓
Lê header kid
  ↓
Busca chave pública correspondente no JWKS
  ↓
Valida assinatura
  ↓
Valida claims
```

O endpoint JWKS vem de:

```env
KEYCLOAK_JWKS_URL
```

---

## 12. Validação de issuer

O claim `iss` precisa corresponder ao valor configurado:

```env
KEYCLOAK_ISSUER
```

Exemplo conceitual:

```text
http://localhost/auth/realms/delpi
```

Se o token foi emitido por outro realm ou URL, deve ser rejeitado.

Erro comum:

```text
invalid_token
```

---

## 13. Validação de audience

O claim `aud` precisa conter a audience esperada:

```env
KEYCLOAK_AUDIENCE
```

Exemplo conceitual:

```text
delpi-central
```

Ponto de atenção:

> Inconsistências entre client ID, audience mapper e `KEYCLOAK_AUDIENCE` são uma causa comum de 401.

---

## 14. Validação de expiração

O claim `exp` define quando o token expira.

Se expirado, a API deve retornar:

```text
401 Unauthorized
```

Com erro:

```json
{
  "errors": [
    {
      "code": "invalid_token",
      "message": "Invalid token",
      "path": "_global"
    }
  ]
}
```

O Portal deve renovar token ou redirecionar para login.

---

## 15. Middleware de autenticação da Core API

Arquivo:

```text
app/interfaces/http/auth_middleware.py
```

Fluxo:

```text
before_request
  ↓
Se TESTING, ignora autenticação
  ↓
Lê Authorization header
  ↓
Se não houver Bearer token, retorna None
  ↓
Valida JWT
  ↓
Extrai sub, email e name
  ↓
Valida sub como UUID
  ↓
Busca usuário por email
  ↓
Cria usuário se não existir
  ↓
Atualiza last_login_at
  ↓
Busca roles, groups e permissions
  ↓
Define g.current_user
```

---

## 16. Header Authorization

Chamadas protegidas devem enviar:

```http
Authorization: Bearer <access_token>
```

Exemplo:

```bash
curl -H "Authorization: Bearer <token>" http://localhost/core-api/me
```

Sem esse header, endpoints com `require_auth()` retornam 401.

---

## 17. `g.current_user`

Após validação do token e sincronização do usuário, a Core API define:

```python
g.current_user
```

Estrutura conceitual:

```python
g.current_user = SimpleNamespace(
    id=str(user.id),
    email=user.email,
    name=user.name,
    roles=roles,
    groups=groups,
    permissions=permissions,
    is_superadmin=user.is_superadmin,
)
```

Controllers e decorators usam esse objeto para autenticação/autorização.

---

## 18. Token ausente versus endpoint público

O middleware não bloqueia automaticamente requisições sem token.

Regra:

```text
Sem token → middleware retorna None
```

Isso permite endpoints públicos, como `/health`.

Porém, endpoints protegidos devem usar decorators:

```python
@require_auth()
@require_permission("apps.view")
```

Ponto de atenção:

> A segurança de endpoints protegidos depende do uso correto dos decorators.

---

## 19. Decorators que dependem do JWT

Decorators principais:

```text
require_auth
require_permission
require_any_permission
require_all_permissions
require_superadmin
```

Eles verificam:

- se `g.current_user` existe;
- se o usuário possui permissão exigida;
- se o usuário é superadmin;
- se o usuário possui uma ou todas as permissões necessárias.

---

## 20. Socket.IO e JWT

Socket.IO também usa JWT.

O Portal deve enviar token no handshake:

```javascript
io("/", {
  auth: {
    token: accessToken
  }
})
```

Fallback possível:

```text
query string token
```

Fluxo no Socket.IO:

```text
connect
  ↓
extrai token
  ↓
valida JWT
  ↓
extrai sub
  ↓
join_room(sub)
```

Recomendação:

> Preferir `auth.token` e evitar token em query string sempre que possível.

---

## 21. JWT em plugins e microfrontends

Microfrontends podem precisar consumir APIs protegidas.

Opções:

- receber token pelo contexto do Portal;
- usar client HTTP compartilhado;
- receber função para obter token atualizado;
- delegar chamadas ao shell quando aplicável.

Regras:

- não colocar token em query string;
- não persistir token desnecessariamente;
- não expor token a plugins que não precisam dele;
- backend chamado pelo plugin deve validar o JWT.

---

## 22. JWT em iframes

Iframes têm cuidados adicionais.

Não recomendado:

```text
https://sistema.externo.com?token=<access_token>
```

Motivos:

- token pode ficar em histórico;
- token pode aparecer em logs;
- token pode vazar por referer;
- token pode ser copiado ou compartilhado.

Alternativas:

- SSO próprio no sistema iframe;
- Keycloak compartilhado;
- sessão segura no domínio do sistema externo;
- integração backend-to-backend quando necessário.

---

## 23. JWT na API DELPI

A API DELPI deve validar tokens em endpoints protegidos.

Validações esperadas:

- assinatura;
- issuer;
- audience;
- expiração;
- algoritmo permitido;
- claims necessárias.

Além disso, endpoints sensíveis devem validar permissões quando aplicável.

Cenário recomendado:

```text
Plugin chama API DELPI com Bearer token
  ↓
API DELPI valida JWT
  ↓
API DELPI valida permissão exigida
  ↓
Executa regra operacional
```

---

## 24. Erros comuns

### 24.1 `invalid_token`

Causas:

- token expirado;
- assinatura inválida;
- issuer divergente;
- audience divergente;
- JWKS URL errada;
- token emitido por outro realm;
- algoritmo não aceito.

Resposta:

```text
401 Unauthorized
```

---

### 24.2 `invalid_claims`

Causas:

- token sem email;
- token sem sub;
- token sem claims esperadas;
- mappers do Keycloak incompletos.

Resposta:

```text
401 Unauthorized
```

---

### 24.3 `invalid_uuid`

Causa:

```text
sub não é UUID válido
```

Resposta:

```text
401 Unauthorized
```

---

### 24.4 `unauthorized`

Causas:

- ausência de token;
- endpoint protegido chamado sem autenticação;
- Socket.IO sem token.

Resposta:

```text
401 Unauthorized
```

---

### 24.5 `forbidden`

Causa:

```text
Usuário autenticado, mas sem permissão exigida
```

Resposta:

```text
403 Forbidden
```

---

## 25. Troubleshooting

### 25.1 Token válido no Portal, mas Core API retorna 401

Verificar:

- `KEYCLOAK_JWKS_URL` está correto;
- `KEYCLOAK_ISSUER` é igual ao claim `iss`;
- `KEYCLOAK_AUDIENCE` está presente em `aud`;
- token ainda não expirou;
- Core API consegue acessar JWKS;
- container usa hostname correto para Keycloak;
- client do Keycloak possui audience mapper.

---

### 25.2 Usuário autentica, mas não aparece app nenhum

Verificar:

- `/me` retorna permissions;
- usuário possui roles/grupos;
- roles possuem permissions;
- app está ativo;
- rotas estão ativas;
- rota exige permission que o usuário possui;
- `is_superadmin` está correto;
- cache RBAC foi invalidado após alteração.

---

### 25.3 Socket.IO não conecta

Verificar:

- token está sendo enviado no handshake;
- token não expirou;
- Socket.IO está apontando para URL correta;
- Core API consegue validar JWT;
- CORS/headers do gateway;
- namespace/path configurado corretamente.

---

## 26. Boas práticas

1. Validar JWT em todo backend protegido.
2. Não confiar apenas no frontend.
3. Não colocar token em query string.
4. Usar JWKS para validação de assinatura.
5. Validar issuer e audience.
6. Configurar claims `sub`, `email` e `name` no Keycloak.
7. Tratar expiração no Portal.
8. Recarregar `/me` e `/me/apps` após mudanças RBAC relevantes.
9. Não armazenar segredos no frontend.
10. Não usar JWT como fonte final de permissões da Minha DELPI.

---

## 27. Checklist de configuração

- [ ] Keycloak emite access token para o client do Portal.
- [ ] Token contém `sub` UUID.
- [ ] Token contém `email`.
- [ ] Token contém `name` ou fallback definido.
- [ ] `KEYCLOAK_JWKS_URL` acessível pela Core API.
- [ ] `KEYCLOAK_ISSUER` igual ao `iss` do token.
- [ ] `KEYCLOAK_AUDIENCE` presente no token.
- [ ] Portal envia `Authorization: Bearer`.
- [ ] Core API valida token e cria usuário local.
- [ ] Socket.IO recebe token no handshake.
- [ ] API DELPI valida JWT em endpoints protegidos.

---

## 28. Pontos de atenção

1. Keycloak autentica, Core API autoriza.
2. `sub` precisa ser UUID válido na Core API atual.
3. Audience divergente causa 401.
4. Issuer divergente causa 401.
5. JWKS precisa ser acessível do container da API.
6. Token expirado deve acionar renovação no Portal.
7. Socket.IO também precisa de token válido.
8. Iframes não devem receber token por URL.
9. APIs operacionais devem validar token independentemente do menu do Portal.
10. Permissões efetivas vêm do RBAC, não diretamente do JWT.

---

## 29. Documentos relacionados

- [rbac.md](./rbac.md)
- [keycloak-sso.md](./keycloak-sso.md)
- [permission-resolver.md](./permission-resolver.md)
- [../02-infraestrutura/variaveis-de-ambiente.md](../02-infraestrutura/variaveis-de-ambiente.md)
- [../10-guias-operacionais/configurar-keycloak.md](../10-guias-operacionais/configurar-keycloak.md)
- [../06-portal-frontend/autenticacao-frontend.md](../06-portal-frontend/autenticacao-frontend.md)
- [../04-core-api/controllers-e-rotas.md](../04-core-api/controllers-e-rotas.md)

