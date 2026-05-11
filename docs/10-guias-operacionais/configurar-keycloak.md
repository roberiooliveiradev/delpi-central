# Minha DELPI — Guia Operacional: Configurar Keycloak

> **Arquivo:** `docs/10-guias-operacionais/configurar-keycloak.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** configuração operacional do Keycloak para desenvolvimento da Minha DELPI

---

## 1. Objetivo

Este guia descreve como configurar o Keycloak para autenticação da Minha DELPI.

O Keycloak é responsável por autenticar usuários e emitir tokens JWT. A autorização funcional da plataforma é resolvida pela Core API com RBAC interno.

---

## 2. Acessar Keycloak

Com o ambiente de desenvolvimento rodando, acesse:

```text
http://localhost/auth
```

ou o path configurado em `KC_HTTP_RELATIVE_PATH`.

Entre com as credenciais administrativas definidas em:

```env
KEYCLOAK_ADMIN=
KEYCLOAK_ADMIN_PASSWORD=
```

---

## 3. Criar realm

Criar o realm da plataforma.

Nome recomendado em desenvolvimento:

```text
delpi
```

O valor precisa estar alinhado com:

```env
VITE_KC_REALM=
KEYCLOAK_REALM=
KEYCLOAK_ADMIN_REALM=
```

---

## 4. Criar client do Portal

Criar client para o Portal.

Nome conceitual:

```text
delpi-central
```

ou o valor definido em:

```env
VITE_KC_CLIENT_ID=
```

Tipo:

```text
public
```

O Portal é frontend público e não deve possuir client secret.

---

## 5. Configurar fluxo de autenticação

Habilitar:

```text
Standard flow
```

Se a estratégia local usar PKCE, configurar o client conforme padrão do Keycloak para SPA/public client.

Não habilitar fluxo desnecessário sem justificativa.

---

## 6. Configurar redirect URIs

Adicionar redirect URI compatível com o Portal local.

Exemplos:

```text
http://localhost/*
http://localhost/
```

O valor precisa ser compatível com:

```env
VITE_KC_REDIRECT_URI=
```

Erro comum quando divergente:

```text
Invalid redirect_uri
```

---

## 7. Configurar Web Origins

Em desenvolvimento, configurar a origem do Portal:

```text
http://localhost
```

ou política equivalente definida pelo time.

Em produção, restringir para domínio real.

---

## 8. Configurar audience

A Core API valida audience do JWT.

A variável esperada é:

```env
KEYCLOAK_AUDIENCE=
```

O token emitido pelo Keycloak precisa conter esse valor em `aud`.

Se necessário, configurar audience mapper no client ou client scope.

Checklist:

- [ ] `KEYCLOAK_AUDIENCE` definido no `.env`.
- [ ] Token contém essa audience.
- [ ] Core API aceita o token.
- [ ] `/me` responde após login.

---

## 9. Configurar claims

A Core API precisa das claims:

```text
sub
email
name
iss
aud
exp
```

Regras importantes:

- `sub` deve ser UUID válido;
- `email` deve estar presente;
- `name` deve estar presente ou ter fallback;
- `iss` deve bater com `KEYCLOAK_ISSUER`;
- `aud` deve conter `KEYCLOAK_AUDIENCE`.

Verificar client scopes e mappers para garantir `email` e `name`.

---

## 10. Configurar issuer e JWKS

A Core API usa:

```env
KEYCLOAK_ISSUER=
KEYCLOAK_JWKS_URL=
KEYCLOAK_AUDIENCE=
```

O `KEYCLOAK_ISSUER` deve ser exatamente igual ao claim `iss` do token.

O `KEYCLOAK_JWKS_URL` deve ser acessível de dentro do container da Core API.

Exemplo conceitual de JWKS:

```text
http://keycloak:8080/auth/realms/delpi/protocol/openid-connect/certs
```

O path exato depende de `KC_HTTP_RELATIVE_PATH`.

---

## 11. Criar usuário inicial

Criar um usuário para acessar a plataforma.

Configurar:

- username;
- email;
- first name;
- last name;
- senha temporária ou definitiva;
- email verified, se necessário para o fluxo.

O email deve bater com o superadmin inicial configurado na Core API, quando aplicável:

```env
INITIAL_SUPERADMIN_EMAIL=
INITIAL_SUPERADMIN_NAME=
```

---

## 12. Relação com superadmin local

O superadmin da Minha DELPI é uma flag local na tabela `users` da Core API:

```text
users.is_superadmin
```

O Keycloak autentica o usuário.

A Core API decide se ele é superadmin.

Portanto, criar usuário no Keycloak não é suficiente para conceder superadmin se a Core API não fizer o bootstrap ou atualização correspondente.

---

## 13. Validar login no Portal

Acesse:

```text
http://localhost
```

Fluxo esperado:

```text
Portal
  ↓
Keycloak
  ↓
Login
  ↓
Redirect para Portal
  ↓
Portal chama Core API
  ↓
/me responde
```

---

## 14. Validar token na Core API

Após login, validar:

```http
GET /core-api/me
Authorization: Bearer <token>
```

Se retornar 401, verificar:

- issuer;
- audience;
- JWKS;
- token expirado;
- claims ausentes;
- `sub` inválido;
- redirect/client incorreto.

---

## 15. Configuração administrativa da Core API

A Core API possui variáveis para Keycloak Admin API:

```env
KEYCLOAK_ADMIN_CLIENT_ID=
KEYCLOAK_ADMIN_CLIENT_SECRET=
KEYCLOAK_ADMIN_REALM=
KEYCLOAK_ADMIN_URL=
```

Essas variáveis são de backend.

Não colocar no Portal.

---

## 16. Após reset de banco

Se você executou reset com `down -v`, o Keycloak perdeu:

- realm;
- client;
- usuários;
- mappers;
- audience;
- redirect URIs.

Será necessário refazer a configuração.

---

## 17. Problemas comuns

### 17.1 `Invalid redirect_uri`

Causa:

```text
Redirect URI do Portal não está permitido no client.
```

Correção:

- ajustar `Valid Redirect URIs`;
- ajustar `VITE_KC_REDIRECT_URI`;
- verificar URL pública pelo Gateway.

---

### 17.2 Core API retorna `invalid_token`

Verificar:

- `KEYCLOAK_ISSUER`;
- `KEYCLOAK_JWKS_URL`;
- `KEYCLOAK_AUDIENCE`;
- claim `aud`;
- claim `iss`;
- expiração;
- acesso da Core API ao JWKS.

---

### 17.3 Token sem email

Causa provável:

```text
Client scope/mappers incompletos.
```

Correção:

- incluir email scope;
- adicionar mapper de email;
- validar token decodificado.

---

### 17.4 Token sem audience

Causa provável:

```text
Audience mapper ausente.
```

Correção:

- configurar audience mapper;
- alinhar `KEYCLOAK_AUDIENCE`.

---

## 18. Checklist final

- [ ] Realm criado.
- [ ] Client público do Portal criado.
- [ ] Standard flow habilitado.
- [ ] Redirect URIs configurados.
- [ ] Web Origins configurados.
- [ ] Audience configurada.
- [ ] Token contém `email`.
- [ ] Token contém `name`.
- [ ] Token contém `aud` esperado.
- [ ] Issuer bate com `KEYCLOAK_ISSUER`.
- [ ] JWKS acessível pela Core API.
- [ ] Usuário inicial criado.
- [ ] Portal autentica.
- [ ] `/me` responde.
- [ ] `/me/apps` responde.

---

## 19. Pontos de atenção

1. Keycloak autentica, Core API autoriza.
2. Portal usa client público.
3. `VITE_*` não pode conter segredo.
4. Admin client é de backend.
5. Audience divergente causa 401.
6. Issuer divergente causa 401.
7. JWKS precisa ser acessível pelo container.
8. `sub` precisa ser UUID válido.
9. Reset de volume apaga configuração do Keycloak.
10. Produção exige HTTPS e redirect URIs restritos.

---

## 20. Documentos relacionados

```text
docs/03-autenticacao-autorizacao/keycloak-sso.md
docs/03-autenticacao-autorizacao/jwt.md
docs/10-guias-operacionais/reset-banco-dev.md
docs/02-infraestrutura/docker-compose.md
```
