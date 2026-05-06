# Minha DELPI — Docker Compose e Infraestrutura Local

> **Arquivo:** `docs/02-infraestrutura/docker-compose.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** Docker Compose, serviços, redes, volumes e diferenças entre desenvolvimento e produção

---

## 1. Objetivo

Este documento descreve a infraestrutura Docker Compose da **Minha DELPI**, explicando como os serviços são organizados, quais containers compõem a plataforma, quais bancos são utilizados, quais volumes são persistidos e quais diferenças existem entre os arquivos de produção e desenvolvimento.

Este documento deve ser usado por desenvolvedores e operadores para entender como a plataforma é executada localmente e como a stack é estruturada.

---

## 2. Localização dos arquivos

A infraestrutura fica na pasta:

```text
infra/
```

A pasta `infra` fica no mesmo nível de:

```text
core-api/
portal/
api-delpi/
gateway/
plugins/
```

Estrutura esperada:

```text
/minha-delpi
  /api-delpi
  /core-api
  /gateway
  /infra
    docker-compose.yml
    docker-compose.dev.yml
    /docker
      /postgres
        init.sql
        plugins-init.sql
    /keycloak
      /themes
  /plugins
    /dashboard-delpi
    /dashboard-lmps
    /strategic-indicators
  /portal
```

Os arquivos Compose usam caminhos relativos a partir de `infra`.

Exemplos:

```text
../core-api
../portal
../api-delpi
../gateway
../plugins/dashboard-lmps
```

---

## 3. Arquivos Compose

A plataforma possui dois arquivos principais:

```text
infra/docker-compose.yml
infra/docker-compose.dev.yml
```

### 3.1 `docker-compose.yml`

Arquivo voltado ao ambiente de produção ou execução mais próxima de produção.

Características principais:

- usa Dockerfiles de produção;
- Keycloak executa com `start`;
- não monta volumes de código principais;
- usa política `restart: unless-stopped`;
- configura rotação de logs em serviços relevantes;
- gateway expõe a porta `80`;
- serviços comunicam pela rede interna `delpi-network`.

### 3.2 `docker-compose.dev.yml`

Arquivo voltado ao desenvolvimento local.

Características principais:

- usa Dockerfiles de desenvolvimento;
- Keycloak executa com `start-dev`;
- monta código local como volume;
- expõe bancos localmente;
- gateway usa configuração de desenvolvimento;
- facilita hot reload e alterações locais.

---

## 4. Serviços da stack

A stack atual contém os seguintes serviços:

| Serviço | Ambiente | Responsabilidade |
|---|---|---|
| `postgres-core` | prod/dev | Banco da Core API |
| `keycloak-db` | prod/dev | Banco do Keycloak |
| `keycloak` | prod/dev | Identity Provider |
| `core-api` | prod/dev | API de governança da plataforma |
| `portal` | prod/dev | Frontend principal |
| `dashboard-delpi` | prod/dev | Plugin/microfrontend |
| `strategic-indicators` | prod/dev | Plugin/microfrontend |
| `dashboard-lmps` | prod/dev | Plugin/microfrontend |
| `postgres-plugins` | prod/dev | Banco dos plugins/domínios |
| `api-delpi` | prod/dev | API operacional/TOTVS/domínios |
| `gateway` | prod/dev | Reverse proxy Nginx |

---

## 5. Rede Docker

Todos os serviços participam da mesma rede Docker:

```yaml
networks:
  delpi-network:
    driver: bridge
```

Essa rede permite comunicação interna por nome de serviço.

Exemplos:

```text
core-api → postgres-core
core-api → keycloak
api-delpi → postgres-plugins
api-delpi → keycloak
gateway → portal
gateway → core-api
gateway → keycloak
gateway → api-delpi
```

O serviço `keycloak` possui alias explícito:

```yaml
aliases:
  - keycloak
```

Esse alias é importante para o gateway resolver o Keycloak de forma estável.

---

## 6. Volumes persistentes

A stack define três volumes principais:

```yaml
volumes:
  postgres_core_data:
  keycloak_data:
  postgres_plugins_data:
```

| Volume | Serviço | Conteúdo |
|---|---|---|
| `postgres_core_data` | `postgres-core` | Dados da Core API |
| `keycloak_data` | `keycloak-db` | Dados do Keycloak |
| `postgres_plugins_data` | `postgres-plugins` | Dados de plugins/domínios |

Esses volumes preservam dados entre reinicializações dos containers.

Para apagar completamente os dados em desenvolvimento, é necessário remover volumes com cuidado.

Exemplo:

```bash
docker compose down -v
```

Atenção:

> Nunca remover volumes de produção sem procedimento formal de backup e restauração.

---

## 7. Serviço `postgres-core`

O serviço `postgres-core` é o banco PostgreSQL usado pela Core API.

Imagem:

```yaml
image: postgres:15
```

Container:

```text
delpi-postgres-core
```

Variáveis principais:

```yaml
POSTGRES_DB: ${POSTGRES_CORE_DB}
POSTGRES_USER: ${POSTGRES_CORE_USER}
POSTGRES_PASSWORD: ${POSTGRES_CORE_PASSWORD}
TZ: ${TZ}
```

Em produção também é configurado:

```yaml
POSTGRES_HOST_AUTH_METHOD: scram-sha-256
```

Volumes:

```yaml
postgres_core_data:/var/lib/postgresql/data
./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
```

Em produção também existe montagem:

```yaml
./core-api/migrations:/app/migrations
```

Observação:

> A Core API se conecta a esse banco usando as variáveis `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` e `DB_PASSWORD`.

No ambiente de desenvolvimento, a porta é exposta:

```yaml
ports:
  - "5432:5432"
```

---

## 8. Serviço `keycloak-db`

O serviço `keycloak-db` é o banco PostgreSQL exclusivo do Keycloak.

Imagem:

```yaml
image: postgres:15
```

Container:

```text
delpi-keycloak-db
```

Variáveis principais:

```yaml
POSTGRES_DB: ${POSTGRES_KC_DB}
POSTGRES_USER: ${POSTGRES_KC_USER}
POSTGRES_PASSWORD: ${POSTGRES_KC_PASSWORD}
TZ: ${TZ}
```

Volume:

```yaml
keycloak_data:/var/lib/postgresql/data
```

Regra importante:

> A aplicação não deve acessar diretamente o banco `keycloak-db` para regras de negócio. Toda interação de autenticação deve passar pelos protocolos e endpoints do Keycloak.

---

## 9. Serviço `keycloak`

O serviço `keycloak` é o Identity Provider da Minha DELPI.

Imagem:

```yaml
image: quay.io/keycloak/keycloak:24.0
```

Em produção:

```yaml
command: ["start"]
```

Em desenvolvimento:

```yaml
command: ["start-dev"]
```

Variáveis principais:

```yaml
KC_DB: postgres
KC_DB_URL: jdbc:postgresql://keycloak-db:5432/${POSTGRES_KC_DB}
KC_DB_USERNAME: ${POSTGRES_KC_USER}
KC_DB_PASSWORD: ${POSTGRES_KC_PASSWORD}
KEYCLOAK_ADMIN: ${KEYCLOAK_ADMIN}
KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
KC_HTTP_ENABLED: ${KC_HTTP_ENABLED}
KC_HTTP_PORT: ${KC_HTTP_PORT}
KC_HTTP_RELATIVE_PATH: ${KC_HTTP_RELATIVE_PATH}
KC_HOSTNAME: ${KC_HOSTNAME}
KC_HOSTNAME_STRICT: ${KC_HOSTNAME_STRICT}
KC_HOSTNAME_STRICT_HTTPS: ${KC_HOSTNAME_STRICT_HTTPS}
KC_PROXY: ${KC_PROXY}
KC_PROXY_HEADERS: ${KC_PROXY_HEADERS}
```

Volume de temas:

```yaml
./keycloak/themes:/opt/keycloak/themes:ro
```

Dependência:

```yaml
depends_on:
  - keycloak-db
```

Observação:

> O Keycloak é responsável por autenticação. A autorização funcional da Minha DELPI é resolvida internamente pela Core API.

---

## 10. Serviço `core-api`

O serviço `core-api` é a API de governança central da Minha DELPI.

Container:

```text
delpi-core-api
```

### 10.1 Produção

Build:

```yaml
build:
  context: ..
  dockerfile: core-api/Dockerfile.prod
```

Ambiente:

```yaml
FLASK_APP: app.create_app:create_app
FLASK_ENV: production
```

### 10.2 Desenvolvimento

Build:

```yaml
build:
  context: ..
  dockerfile: core-api/Dockerfile.dev
```

Ambiente:

```yaml
FLASK_APP: app.create_app:create_app
FLASK_ENV: development
```

Volume em desenvolvimento:

```yaml
../core-api:/app
```

### 10.3 Variáveis principais

```yaml
DB_HOST: ${DB_HOST}
DB_PORT: ${DB_PORT}
DB_NAME: ${DB_NAME}
DB_USER: ${DB_USER}
DB_PASSWORD: ${DB_PASSWORD}
SECRET_KEY: ${SECRET_KEY}
KEYCLOAK_JWKS_URL: ${KEYCLOAK_JWKS_URL}
KEYCLOAK_ISSUER: ${KEYCLOAK_ISSUER}
KEYCLOAK_AUDIENCE: ${KEYCLOAK_AUDIENCE}
INITIAL_SUPERADMIN_EMAIL: ${INITIAL_SUPERADMIN_EMAIL}
INITIAL_SUPERADMIN_NAME: ${INITIAL_SUPERADMIN_NAME}
KEYCLOAK_ADMIN_CLIENT_ID: ${KEYCLOAK_ADMIN_CLIENT_ID}
KEYCLOAK_ADMIN_CLIENT_SECRET: ${KEYCLOAK_ADMIN_CLIENT_SECRET}
KEYCLOAK_ADMIN_REALM: ${KEYCLOAK_ADMIN_REALM}
KEYCLOAK_ADMIN_URL: ${KEYCLOAK_ADMIN_URL}
```

Dependências:

```yaml
depends_on:
  - postgres-core
  - keycloak
```

Responsabilidades:

- usuários;
- RBAC;
- apps;
- rotas;
- plugins;
- manifestos;
- favoritos;
- notificações;
- eventos administrativos;
- auditoria.

---

## 11. Serviço `portal`

O serviço `portal` é o frontend principal da Minha DELPI.

Container:

```text
delpi-portal
```

### 11.1 Produção

Build:

```yaml
build:
  context: ../portal
  dockerfile: Dockerfile.prod
```

Args de build:

```yaml
VITE_KC_URL: ${VITE_KC_URL}
VITE_KC_REALM: ${VITE_KC_REALM}
VITE_KC_CLIENT_ID: ${VITE_KC_CLIENT_ID}
VITE_KC_REDIRECT_URI: ${VITE_KC_REDIRECT_URI}
```

### 11.2 Desenvolvimento

Build:

```yaml
build:
  context: ../portal
  dockerfile: Dockerfile.dev
```

Variáveis:

```yaml
VITE_KC_URL: ${VITE_KC_URL}
VITE_KC_REALM: ${VITE_KC_REALM}
VITE_KC_CLIENT_ID: ${VITE_KC_CLIENT_ID}
VITE_KC_REDIRECT_URI: ${VITE_KC_REDIRECT_URI}
```

Volumes em desenvolvimento:

```yaml
../portal:/app
/app/node_modules
```

Dependência:

```yaml
depends_on:
  - core-api
```

---

## 12. Serviços de plugins frontend

A stack inclui plugins/microfrontends.

### 12.1 `dashboard-delpi`

Build:

```yaml
build:
  context: ../plugins/dashboard-delpi
  dockerfile: Dockerfile
```

Container:

```text
delpi-dashboard-delpi
```

Em desenvolvimento, monta:

```yaml
../plugins/dashboard-delpi:/app
/app/node_modules
```

---

### 12.2 `strategic-indicators`

Build:

```yaml
build:
  context: ../plugins/strategic-indicators
  dockerfile: Dockerfile
```

Container:

```text
delpi-strategic-indicators
```

Em desenvolvimento, monta:

```yaml
../plugins/strategic-indicators:/app
/app/node_modules
```

---

### 12.3 `dashboard-lmps`

Build:

```yaml
build:
  context: ../plugins/dashboard-lmps
  dockerfile: Dockerfile
```

Container:

```text
delpi-dashboard-lmps
```

Em desenvolvimento, monta:

```yaml
../plugins/dashboard-lmps:/app
/app/node_modules
```

---

## 13. Serviço `postgres-plugins`

O serviço `postgres-plugins` é o banco PostgreSQL para plugins e módulos de domínio.

Imagem:

```yaml
image: postgres:15
```

Container:

```text
delpi-postgres-plugins
```

Variáveis:

```yaml
POSTGRES_DB: ${PLUGINS_DB_NAME}
POSTGRES_USER: ${PLUGINS_DB_USER}
POSTGRES_PASSWORD: ${PLUGINS_DB_PASSWORD}
TZ: ${TZ}
```

Volumes:

```yaml
postgres_plugins_data:/var/lib/postgresql/data
./docker/postgres/plugins-init.sql:/docker-entrypoint-initdb.d/plugins-init.sql
```

Em desenvolvimento, expõe:

```yaml
ports:
  - "5433:5432"
```

Consumidor principal:

```text
api-delpi
```

Variáveis usadas pela API DELPI:

```yaml
PLUGINS_DB_HOST
PLUGINS_DB_PORT
PLUGINS_DB_NAME
PLUGINS_DB_USER
PLUGINS_DB_PASSWORD
PLUGINS_DB_CONNECT_TIMEOUT
PLUGINS_DB_SSLMODE
```

---

## 14. Serviço `api-delpi`

O serviço `api-delpi` é a API operacional da plataforma.

Container:

```text
delpi-api-delpi
```

Build:

```yaml
build:
  context: ..
  dockerfile: api-delpi/Dockerfile
```

Usa:

```yaml
env_file:
  - .env
```

Variáveis principais:

```yaml
DB_HOST: ${TOTVS_DB_HOST}
DB_PORT: ${TOTVS_DB_PORT}
DB_USER: ${TOTVS_DB_USER}
DB_PASSWORD: ${TOTVS_DB_PASSWORD}
DB_DATABASE: ${TOTVS_DB_DATABASE}
PORT: ${API_DELPI_PORT}
ENV: ${API_DELPI_ENV}
JWT_SECRET: ${API_DELPI_JWT_SECRET}
KEYCLOAK_REALM: ${KEYCLOAK_REALM}
KEYCLOAK_AUDIENCE: ${KEYCLOAK_AUDIENCE}
KEYCLOAK_JWKS_URL: ${KEYCLOAK_JWKS_URL}
KEYCLOAK_ISSUER: ${KEYCLOAK_ISSUER}
JWT_ALGORITHMS: ${JWT_ALGORITHMS}
LOG_LEVEL: ${LOG_LEVEL}
TZ: ${TZ}
PLUGINS_DB_HOST: ${PLUGINS_DB_HOST}
PLUGINS_DB_PORT: ${PLUGINS_DB_PORT}
PLUGINS_DB_NAME: ${PLUGINS_DB_NAME}
PLUGINS_DB_USER: ${PLUGINS_DB_USER}
PLUGINS_DB_PASSWORD: ${PLUGINS_DB_PASSWORD}
PLUGINS_DB_CONNECT_TIMEOUT: ${PLUGINS_DB_CONNECT_TIMEOUT}
PLUGINS_DB_SSLMODE: ${PLUGINS_DB_SSLMODE}
PORTAL_RH_DB_HOST: ${PORTAL_RH_DB_HOST}
PORTAL_RH_DB_PORT: ${PORTAL_RH_DB_PORT}
PORTAL_RH_DB_NAME: ${PORTAL_RH_DB_NAME}
PORTAL_RH_DB_USER: ${PORTAL_RH_DB_USER}
PORTAL_RH_DB_PASSWORD: ${PORTAL_RH_DB_PASSWORD}
PORTAL_RH_DB_CONNECT_TIMEOUT: ${PORTAL_RH_DB_CONNECT_TIMEOUT}
PORTAL_RH_DB_SSLMODE: ${PORTAL_RH_DB_SSLMODE}
```

Dependências:

```yaml
depends_on:
  - keycloak
  - postgres-plugins
```

Em desenvolvimento, monta:

```yaml
../api-delpi:/app
```

Responsabilidades:

- integração TOTVS;
- rotas operacionais;
- backend de módulos de negócio;
- acesso ao `postgres-plugins`;
- acesso a outros bancos corporativos quando configurado.

---

## 15. Serviço `gateway`

O serviço `gateway` é o reverse proxy da plataforma.

Container:

```text
delpi-gateway
```

### 15.1 Produção

Build:

```yaml
build:
  context: ../gateway
  dockerfile: Dockerfile.prod
```

Porta pública:

```yaml
ports:
  - "80:80"
```

Dependências:

```yaml
depends_on:
  - portal
  - core-api
  - keycloak
  - api-delpi
  - strategic-indicators
  - dashboard-lmps
```

### 15.2 Desenvolvimento

Build:

```yaml
build:
  context: ../gateway
  dockerfile: Dockerfile.dev
```

Volume de configuração:

```yaml
../gateway/nginx.dev.conf:/etc/nginx/nginx.conf
```

Porta pública:

```yaml
ports:
  - "80:80"
```

---

## 16. Diferenças entre produção e desenvolvimento

| Aspecto | Produção | Desenvolvimento |
|---|---|---|
| Keycloak | `start` | `start-dev` |
| Core API | `Dockerfile.prod` | `Dockerfile.dev` |
| Portal | `Dockerfile.prod` | `Dockerfile.dev` |
| Gateway | `Dockerfile.prod` | `Dockerfile.dev` |
| Código montado como volume | Não | Sim |
| `postgres-core` exposto localmente | Não | `5432:5432` |
| `postgres-plugins` exposto localmente | Não | `5433:5432` |
| Gateway exposto | `80:80` | `80:80` |
| Hot reload/desenvolvimento | Não priorizado | Sim |
| Logs com rotação | Sim em serviços críticos | Parcial/menor ênfase |

---

## 17. Ordem de dependências

Ordem lógica de inicialização:

```text
postgres-core
keycloak-db
postgres-plugins
  ↓
keycloak
  ↓
core-api
api-delpi
  ↓
portal
plugins
  ↓
gateway
```

No Compose, isso é parcialmente controlado por `depends_on`.

Atenção:

> `depends_on` garante ordem de inicialização de containers, mas não garante que o serviço interno esteja pronto para uso. Serviços como bancos e Keycloak podem precisar de alguns segundos adicionais antes de aceitar conexões.

---

## 18. Variáveis de ambiente por grupo

### 18.1 PostgreSQL Core

```env
POSTGRES_CORE_DB=
POSTGRES_CORE_USER=
POSTGRES_CORE_PASSWORD=
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
```

### 18.2 Keycloak

```env
POSTGRES_KC_DB=
POSTGRES_KC_USER=
POSTGRES_KC_PASSWORD=
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

### 18.3 JWT / OIDC

```env
KEYCLOAK_JWKS_URL=
KEYCLOAK_ISSUER=
KEYCLOAK_AUDIENCE=
KEYCLOAK_REALM=
JWT_ALGORITHMS=
```

### 18.4 Portal

```env
VITE_KC_URL=
VITE_KC_REALM=
VITE_KC_CLIENT_ID=
VITE_KC_REDIRECT_URI=
```

### 18.5 API DELPI / TOTVS

```env
TOTVS_DB_HOST=
TOTVS_DB_PORT=
TOTVS_DB_USER=
TOTVS_DB_PASSWORD=
TOTVS_DB_DATABASE=
API_DELPI_PORT=
API_DELPI_ENV=
API_DELPI_JWT_SECRET=
LOG_LEVEL=
```

### 18.6 Plugins DB

```env
PLUGINS_DB_HOST=
PLUGINS_DB_PORT=
PLUGINS_DB_NAME=
PLUGINS_DB_USER=
PLUGINS_DB_PASSWORD=
PLUGINS_DB_CONNECT_TIMEOUT=
PLUGINS_DB_SSLMODE=
```

### 18.7 Portal RH DB

```env
PORTAL_RH_DB_HOST=
PORTAL_RH_DB_PORT=
PORTAL_RH_DB_NAME=
PORTAL_RH_DB_USER=
PORTAL_RH_DB_PASSWORD=
PORTAL_RH_DB_CONNECT_TIMEOUT=
PORTAL_RH_DB_SSLMODE=
```

### 18.8 Gerais

```env
TZ=America/Sao_Paulo
SECRET_KEY=
INITIAL_SUPERADMIN_EMAIL=
INITIAL_SUPERADMIN_NAME=
KEYCLOAK_ADMIN_CLIENT_ID=
KEYCLOAK_ADMIN_CLIENT_SECRET=
KEYCLOAK_ADMIN_REALM=
KEYCLOAK_ADMIN_URL=
```

---

## 19. Subindo ambiente de desenvolvimento

A partir da pasta `infra`:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Ou em segundo plano:

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

Serviços esperados:

```bash
docker ps
```

Principais containers esperados:

```text
delpi-postgres-core
delpi-keycloak-db
delpi-keycloak
delpi-core-api
delpi-portal
delpi-api-delpi
delpi-postgres-plugins
delpi-gateway
```

---

## 20. Parando ambiente de desenvolvimento

Parar containers preservando volumes:

```bash
docker compose -f docker-compose.dev.yml down
```

Parar containers removendo volumes:

```bash
docker compose -f docker-compose.dev.yml down -v
```

Atenção:

> `down -v` apaga os dados persistidos dos bancos definidos como volumes. Usar apenas quando quiser resetar completamente o ambiente local.

---

## 21. Subindo ambiente de produção

A partir da pasta `infra`:

```bash
docker compose -f docker-compose.yml up -d --build
```

Verificar logs:

```bash
docker compose -f docker-compose.yml logs -f
```

Verificar um serviço específico:

```bash
docker compose -f docker-compose.yml logs -f core-api
```

---

## 22. Healthchecks e validações manuais

Exemplos de validação após subir a stack:

### 22.1 Portal

```text
http://localhost/
```

### 22.2 Core API

```text
http://localhost/core-api/health
```

### 22.3 Keycloak

```text
http://localhost/auth
```

### 22.4 API DELPI

O path depende da configuração do gateway, mas a base esperada é:

```text
/apps/api-delpi
```

---

## 23. Relação entre Compose e documentação da aplicação

Este documento descreve a infraestrutura de execução.

Detalhes específicos devem ser mantidos em documentos separados:

```text
docs/02-infraestrutura/gateway-nginx.md
docs/02-infraestrutura/variaveis-de-ambiente.md
docs/02-infraestrutura/bancos-de-dados.md
docs/03-autenticacao-autorizacao/keycloak-sso.md
docs/04-core-api/visao-geral-core-api.md
docs/07-api-delpi/visao-geral-api-delpi.md
```

---

## 24. Pontos de atenção

1. A pasta `infra` é o ponto de execução dos Compose.
2. Os caminhos de build usam `context: ..`, assumindo que `infra` está um nível abaixo da raiz do projeto.
3. A Core API e a API DELPI são serviços diferentes e usam variáveis diferentes.
4. `postgres-core` e `postgres-plugins` não devem ser confundidos.
5. O banco do Keycloak não deve ser usado diretamente pela aplicação.
6. Em desenvolvimento, os bancos são expostos localmente; em produção, não.
7. `depends_on` não garante readiness total dos serviços.
8. O gateway é o único serviço exposto na porta `80`.
9. O alias `keycloak` na rede é importante para resolução interna.
10. Remover volumes apaga dados persistidos.

