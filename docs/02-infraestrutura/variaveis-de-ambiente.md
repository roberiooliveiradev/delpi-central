# Minha DELPI — Variáveis de Ambiente

> **Arquivo:** `docs/02-infraestrutura/variaveis-de-ambiente.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** variáveis de ambiente usadas por Docker Compose, Core API, Portal, Keycloak, API DELPI e bancos

---

## 1. Objetivo

Este documento consolida as variáveis de ambiente usadas pela infraestrutura atual da Minha DELPI.

As variáveis aparecem principalmente em:

```text
infra/.env
infra/docker-compose.yml
infra/docker-compose.dev.yml
core-api/app/infrastructure/config/settings.py
```

Este documento não deve conter valores reais de produção.

---

## 2. Regra de segurança

Nunca versionar secrets reais.

Variáveis sensíveis incluem:

```text
POSTGRES_*_PASSWORD
DB_PASSWORD
SECRET_KEY
KEYCLOAK_ADMIN_PASSWORD
KEYCLOAK_ADMIN_CLIENT_SECRET
API_DELPI_JWT_SECRET
TOTVS_DB_PASSWORD
PLUGINS_DB_PASSWORD
PORTAL_RH_DB_PASSWORD
```

Usar exemplos seguros em `.env.example`.

---

## 3. Variáveis gerais

```env
TZ=America/Sao_Paulo
LOG_LEVEL=
```

| Variável | Uso |
|---|---|
| `TZ` | Timezone dos containers |
| `LOG_LEVEL` | Nível de log da API DELPI e serviços que adotarem essa variável |

---

## 4. PostgreSQL da Core API — criação do container

Usadas pelo serviço `postgres-core`:

```env
POSTGRES_CORE_DB=
POSTGRES_CORE_USER=
POSTGRES_CORE_PASSWORD=
```

| Variável | Descrição |
|---|---|
| `POSTGRES_CORE_DB` | Nome do banco criado no container |
| `POSTGRES_CORE_USER` | Usuário PostgreSQL do banco core |
| `POSTGRES_CORE_PASSWORD` | Senha do usuário PostgreSQL do banco core |

Em produção, o Compose também define:

```env
POSTGRES_HOST_AUTH_METHOD=scram-sha-256
```

---

## 5. Core API — conexão com banco

Usadas pelo serviço `core-api`:

```env
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
```

No código da Core API, a URI é montada como:

```text
postgresql://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:<DB_PORT>/<DB_NAME>
```

Essas variáveis devem apontar para `postgres-core`.

Exemplo conceitual em Docker:

```env
DB_HOST=postgres-core
DB_PORT=5432
```

---

## 6. Core API — Flask e segurança

```env
FLASK_APP=app.create_app:create_app
FLASK_ENV=development|production
SECRET_KEY=
```

| Variável | Uso |
|---|---|
| `FLASK_APP` | Factory Flask usada pelo container |
| `FLASK_ENV` | Modo da aplicação |
| `SECRET_KEY` | Chave de segurança usada pelo Flask/aplicação |

Regra:

> `SECRET_KEY` deve ser forte e exclusiva por ambiente.

---

## 7. Core API — Keycloak/JWT

```env
KEYCLOAK_JWKS_URL=
KEYCLOAK_ISSUER=
KEYCLOAK_AUDIENCE=
```

| Variável | Uso |
|---|---|
| `KEYCLOAK_JWKS_URL` | Endpoint JWKS usado para validar assinatura JWT |
| `KEYCLOAK_ISSUER` | Issuer esperado no claim `iss` |
| `KEYCLOAK_AUDIENCE` | Audience esperada no claim `aud` |

Pontos de atenção:

- `KEYCLOAK_JWKS_URL` precisa ser acessível de dentro do container da Core API;
- `KEYCLOAK_ISSUER` precisa bater exatamente com o `iss` do token;
- `KEYCLOAK_AUDIENCE` precisa estar no token emitido pelo Keycloak.

---

## 8. Core API — bootstrap inicial

```env
INITIAL_SUPERADMIN_EMAIL=
INITIAL_SUPERADMIN_NAME=
```

Uso esperado:

- identificar/criar superadmin inicial;
- permitir bootstrap de governança;
- evitar ambiente sem usuário administrativo.

Regras:

- email deve corresponder ao usuário autenticado via Keycloak;
- não usar conta genérica sem controle;
- validar após primeiro login.

---

## 9. Core API — Admin API do Keycloak

```env
KEYCLOAK_ADMIN_CLIENT_ID=
KEYCLOAK_ADMIN_CLIENT_SECRET=
KEYCLOAK_ADMIN_REALM=
KEYCLOAK_ADMIN_URL=
```

Uso esperado:

- integração backend com Admin API do Keycloak;
- automações administrativas futuras;
- service account controlado.

Segurança:

> Essas variáveis são de backend. Nunca expor no Portal ou em variáveis `VITE_*`.

---

## 10. Keycloak DB

Usadas pelo serviço `keycloak-db`:

```env
POSTGRES_KC_DB=
POSTGRES_KC_USER=
POSTGRES_KC_PASSWORD=
```

Essas variáveis criam o banco usado internamente pelo Keycloak.

---

## 11. Keycloak runtime

Usadas pelo serviço `keycloak`:

```env
KC_DB=postgres
KC_DB_URL=
KC_DB_USERNAME=
KC_DB_PASSWORD=
KEYCLOAK_ADMIN=
KEYCLOAK_ADMIN_PASSWORD=
KC_HTTP_ENABLED=
KC_HTTP_PORT=
KC_HTTP_RELATIVE_PATH=
KC_HOSTNAME=
KC_HOSTNAME_STRICT=
KC_HOSTNAME_STRICT_HTTPS=
KC_PROXY=
KC_PROXY_HEADERS=
```

| Grupo | Variáveis |
|---|---|
| Banco | `KC_DB`, `KC_DB_URL`, `KC_DB_USERNAME`, `KC_DB_PASSWORD` |
| Admin | `KEYCLOAK_ADMIN`, `KEYCLOAK_ADMIN_PASSWORD` |
| HTTP/path | `KC_HTTP_ENABLED`, `KC_HTTP_PORT`, `KC_HTTP_RELATIVE_PATH` |
| Hostname/proxy | `KC_HOSTNAME`, `KC_HOSTNAME_STRICT`, `KC_HOSTNAME_STRICT_HTTPS`, `KC_PROXY`, `KC_PROXY_HEADERS` |

Ponto crítico:

> Configuração incorreta de hostname/proxy pode gerar issuer errado e quebrar validação JWT na Core API/API DELPI.

---

## 12. Portal frontend

Variáveis usadas pelo Portal:

```env
VITE_KC_URL=
VITE_KC_REALM=
VITE_KC_CLIENT_ID=
VITE_KC_REDIRECT_URI=
```

| Variável | Uso |
|---|---|
| `VITE_KC_URL` | URL pública do Keycloak usada no navegador |
| `VITE_KC_REALM` | Realm do Keycloak |
| `VITE_KC_CLIENT_ID` | Client público do Portal |
| `VITE_KC_REDIRECT_URI` | URL de retorno após login |

Regra:

> Variáveis `VITE_*` são públicas e embutidas no build. Não usar secrets.

---

## 13. API DELPI — runtime

```env
API_DELPI_PORT=
API_DELPI_ENV=
API_DELPI_JWT_SECRET=
```

No container, o Compose mapeia:

```env
PORT=${API_DELPI_PORT}
ENV=${API_DELPI_ENV}
JWT_SECRET=${API_DELPI_JWT_SECRET}
```

---

## 14. API DELPI — Keycloak/JWT

```env
KEYCLOAK_REALM=
KEYCLOAK_AUDIENCE=
KEYCLOAK_JWKS_URL=
KEYCLOAK_ISSUER=
JWT_ALGORITHMS=
```

Uso:

- validar token em endpoints protegidos;
- garantir issuer/audience corretos;
- selecionar algoritmos aceitos.

---

## 15. API DELPI — TOTVS

Variáveis externas:

```env
TOTVS_DB_HOST=
TOTVS_DB_PORT=
TOTVS_DB_USER=
TOTVS_DB_PASSWORD=
TOTVS_DB_DATABASE=
```

Dentro do container `api-delpi`, o Compose mapeia para:

```env
DB_HOST=${TOTVS_DB_HOST}
DB_PORT=${TOTVS_DB_PORT}
DB_USER=${TOTVS_DB_USER}
DB_PASSWORD=${TOTVS_DB_PASSWORD}
DB_DATABASE=${TOTVS_DB_DATABASE}
```

Atenção:

> Na API DELPI, `DB_*` é TOTVS. Na Core API, `DB_*` é `postgres-core`.

---

## 16. PostgreSQL de plugins

Criação do container `postgres-plugins`:

```env
PLUGINS_DB_NAME=
PLUGINS_DB_USER=
PLUGINS_DB_PASSWORD=
```

Conexão usada pela API DELPI:

```env
PLUGINS_DB_HOST=
PLUGINS_DB_PORT=
PLUGINS_DB_NAME=
PLUGINS_DB_USER=
PLUGINS_DB_PASSWORD=
PLUGINS_DB_CONNECT_TIMEOUT=
PLUGINS_DB_SSLMODE=
```

Em Docker, o host esperado normalmente é:

```env
PLUGINS_DB_HOST=postgres-plugins
PLUGINS_DB_PORT=5432
```

---

## 17. Portal RH DB

Variáveis usadas pela API DELPI:

```env
PORTAL_RH_DB_HOST=
PORTAL_RH_DB_PORT=
PORTAL_RH_DB_NAME=
PORTAL_RH_DB_USER=
PORTAL_RH_DB_PASSWORD=
PORTAL_RH_DB_CONNECT_TIMEOUT=
PORTAL_RH_DB_SSLMODE=
```

Uso esperado:

- integração com banco do Portal RH;
- rotas e módulos operacionais da API DELPI.

O código real da API DELPI deve ser consultado para documentar as rotas que usam essas variáveis.

---

## 18. Variáveis por serviço

### 18.1 `postgres-core`

```env
POSTGRES_CORE_DB=
POSTGRES_CORE_USER=
POSTGRES_CORE_PASSWORD=
TZ=
```

### 18.2 `core-api`

```env
FLASK_APP=
FLASK_ENV=
TZ=
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
SECRET_KEY=
KEYCLOAK_JWKS_URL=
KEYCLOAK_ISSUER=
KEYCLOAK_AUDIENCE=
INITIAL_SUPERADMIN_EMAIL=
INITIAL_SUPERADMIN_NAME=
KEYCLOAK_ADMIN_CLIENT_ID=
KEYCLOAK_ADMIN_CLIENT_SECRET=
KEYCLOAK_ADMIN_REALM=
KEYCLOAK_ADMIN_URL=
```

### 18.3 `portal`

```env
TZ=
VITE_KC_URL=
VITE_KC_REALM=
VITE_KC_CLIENT_ID=
VITE_KC_REDIRECT_URI=
```

### 18.4 `api-delpi`

```env
DB_HOST=
DB_PORT=
DB_USER=
DB_PASSWORD=
DB_DATABASE=
PORT=
ENV=
JWT_SECRET=
KEYCLOAK_REALM=
KEYCLOAK_AUDIENCE=
KEYCLOAK_JWKS_URL=
KEYCLOAK_ISSUER=
JWT_ALGORITHMS=
LOG_LEVEL=
TZ=
PLUGINS_DB_HOST=
PLUGINS_DB_PORT=
PLUGINS_DB_NAME=
PLUGINS_DB_USER=
PLUGINS_DB_PASSWORD=
PLUGINS_DB_CONNECT_TIMEOUT=
PLUGINS_DB_SSLMODE=
PORTAL_RH_DB_HOST=
PORTAL_RH_DB_PORT=
PORTAL_RH_DB_NAME=
PORTAL_RH_DB_USER=
PORTAL_RH_DB_PASSWORD=
PORTAL_RH_DB_CONNECT_TIMEOUT=
PORTAL_RH_DB_SSLMODE=
```

---

## 19. Checklist de `.env.example`

Um `.env.example` deve conter todas as variáveis sem valores reais.

Checklist:

- [ ] Variáveis do `postgres-core`.
- [ ] Variáveis de conexão da Core API.
- [ ] `SECRET_KEY` sem valor real.
- [ ] Variáveis de Keycloak runtime.
- [ ] Variáveis de JWT/OIDC.
- [ ] Variáveis Vite do Portal.
- [ ] Variáveis da API DELPI.
- [ ] Variáveis TOTVS.
- [ ] Variáveis do `postgres-plugins`.
- [ ] Variáveis Portal RH.
- [ ] Comentários sobre quais valores são públicos e quais são secrets.

---

## 20. Troubleshooting

### 20.1 Core API não conecta ao banco

Verificar:

- `DB_HOST` aponta para `postgres-core` dentro do Docker;
- `DB_PORT=5432` dentro da rede Docker;
- `DB_NAME` bate com `POSTGRES_CORE_DB`;
- usuário e senha conferem;
- volume não está corrompido;
- migrations foram aplicadas.

### 20.2 Login funciona, mas Core API retorna 401

Verificar:

- `KEYCLOAK_JWKS_URL` acessível pela Core API;
- `KEYCLOAK_ISSUER` igual ao `iss` do token;
- `KEYCLOAK_AUDIENCE` presente no token;
- token não expirou;
- `KC_HTTP_RELATIVE_PATH` e hostname estão coerentes.

### 20.3 Portal não redireciona corretamente

Verificar:

- `VITE_KC_URL` é a URL pública correta;
- `VITE_KC_REALM` existe;
- `VITE_KC_CLIENT_ID` é client público;
- `VITE_KC_REDIRECT_URI` está cadastrado no Keycloak;
- produção foi rebuildada após alterar `VITE_*`.

### 20.4 API DELPI conecta no banco errado

Verificar:

- `TOTVS_DB_*` está correto;
- mapeamento para `DB_*` no Compose está claro;
- `PLUGINS_DB_*` aponta para `postgres-plugins`;
- não confundir Core API `DB_*` com API DELPI `DB_*`.

---

## 21. Boas práticas

1. Usar `.env.example` sem secrets.
2. Usar valores diferentes por ambiente.
3. Não misturar variáveis da Core API com variáveis da API DELPI.
4. Não colocar secrets em `VITE_*`.
5. Validar issuer/audience com token real.
6. Usar nomes de host Docker para comunicação entre containers.
7. Expor portas de banco apenas em desenvolvimento.
8. Rotacionar secrets quando necessário.
9. Documentar novas variáveis no mesmo PR que adiciona código.
10. Revisar logs para garantir que secrets não são impressos.

---

## 22. Documentos relacionados

```text
docs/02-infraestrutura/docker-compose.md
docs/02-infraestrutura/ambientes-dev-prod.md
docs/02-infraestrutura/bancos-de-dados.md
docs/03-autenticacao-autorizacao/jwt.md
docs/03-autenticacao-autorizacao/keycloak-sso.md
docs/07-api-delpi/visao-geral-api-delpi.md
```
