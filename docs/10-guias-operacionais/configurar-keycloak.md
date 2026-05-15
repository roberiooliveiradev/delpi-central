# Guia: configurar Keycloak (desenvolvimento)

> **Arquivo:** `docs/10-guias-operacionais/configurar-keycloak.md`  
> **Status:** documentação oficial  
> **Stack local:** gateway + `KC_HTTP_RELATIVE_PATH=/auth`

---

## 1. Papéis

| Sistema | Função |
|---|---|
| **Keycloak** | Login, emissão de JWT |
| **Core API / API DELPI / AI API** | Validam JWT (issuer, audience, JWKS) |
| **Portal** | Client público OIDC (PKCE S256) |

Autorização de menu e permissões: **Core API** (`/me`, `/me/apps`), não o Keycloak.

---

## 2. Acesso admin

Com a stack up:

```text
http://localhost/auth
```

Credenciais: `KEYCLOAK_ADMIN` e `KEYCLOAK_ADMIN_PASSWORD` do `infra/.env`.

---

## 3. Realm

Criar realm com o mesmo nome de:

```env
KEYCLOAK_REALM=delpi
VITE_KC_REALM=delpi
```

---

## 4. Client do Portal

| Campo | Valor recomendado |
|---|---|
| Client ID | `delpi-central` (= `VITE_KC_CLIENT_ID`) |
| Client authentication | **Off** (público) |
| Standard flow | **On** |
| Valid redirect URIs | `http://localhost/*` |
| Web origins | `http://localhost` ou `+` |

O Portal usa **PKCE** (`pkceMethod: S256` em `keycloakClient.ts`) — client público compatível com SPA.

---

## 5. Audience

A Core API exige claim `aud` contendo:

```env
KEYCLOAK_AUDIENCE=delpi-central
```

No Keycloak 24, adicionar mapper de audience no client ou client scope (ex.: hardcoded `delpi-central` ou audience do client).

Validar decodificando o access token após login.

---

## 6. Issuer e JWKS (dois “mundos”)

| Contexto | URL |
|---|---|
| Browser / token `iss` | `http://localhost/auth/realms/delpi` |
| Core API dentro do Docker | `http://keycloak:8080/auth/realms/delpi/protocol/openid-connect/certs` |

Variáveis no `.env`:

```env
KEYCLOAK_ISSUER=${PUBLIC_BASE_URL}/auth/realms/${KEYCLOAK_REALM}
KEYCLOAK_JWKS_URL=http://keycloak:8080/auth/realms/delpi/protocol/openid-connect/certs
```

Se `iss` no token for `http://localhost/...` mas `KEYCLOAK_ISSUER` apontar só para `keycloak:8080`, a validação falha.

---

## 7. Claims obrigatórias

| Claim | Uso |
|---|---|
| `sub` | UUID do usuário (sala Socket.IO) |
| `email` | Sincronização na Core API |
| `name` | Exibição no Portal |
| `iss` | Validação issuer |
| `aud` | Validação audience |
| `exp` | Expiração |

Garantir scopes **email** e **profile** (ou mappers equivalentes) no client.

---

## 8. Superadmin local

```env
INITIAL_SUPERADMIN_EMAIL=usuario@empresa.com.br
```

Na primeira autenticação com esse e-mail, a Core API pode marcar `users.is_superadmin=true` (bootstrap). Criar o usuário no Keycloak com o **mesmo e-mail**.

---

## 9. Validar integração

1. Login em `http://localhost`
2. DevTools → request `GET /core-api/me` → **200**
3. `GET /core-api/me/apps` → lista de plugins
4. Token em [jwt.io](https://jwt.io): conferir `iss`, `aud`, `email`

```bash
# Health (sem auth)
curl -s http://localhost/core-api/health
```

---

## 10. Client admin backend (opcional)

Service account para automações:

```env
KEYCLOAK_ADMIN_CLIENT_ID=delpi-core-admin
KEYCLOAK_ADMIN_CLIENT_SECRET=<secret>
KEYCLOAK_ADMIN_URL=http://keycloak:8080
```

Nunca expor no frontend.

---

## 11. Após `docker compose down -v`

Volumes do Keycloak são apagados. Refazer: realm, client, mappers, usuários, redirect URIs.

---

## 12. Problemas comuns

| Erro | Correção |
|---|---|
| `Invalid redirect URI` | `http://localhost/*` no client; `VITE_KC_REDIRECT_URI` |
| 401 `invalid_token` | Alinhar `iss` / `aud` / JWKS |
| Token sem `email` | Client scopes + mapper |
| Loop de login | Web origins; cookie third-party (raro em localhost) |
| Issuer mismatch | `KEYCLOAK_ISSUER` = URL pública do realm, não interna |

---

## 13. Checklist

- [ ] Realm `delpi` (ou valor do `.env`)
- [ ] Client `delpi-central` público + Standard flow
- [ ] Redirect `http://localhost/*`
- [ ] Audience `delpi-central` no token
- [ ] JWKS acessível de dentro do container `core-api`
- [ ] Usuário com e-mail do superadmin
- [ ] `/me` e `/me/apps` OK após login

---

## 14. Documentos relacionados

- [../02-infraestrutura/variaveis-de-ambiente.md](../02-infraestrutura/variaveis-de-ambiente.md)
- [../03-autenticacao-autorizacao/keycloak-sso.md](../03-autenticacao-autorizacao/keycloak-sso.md)
- [reset-banco-dev.md](./reset-banco-dev.md)
- [subir-ambiente-dev.md](./subir-ambiente-dev.md)
