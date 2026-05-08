# Minha DELPI — Bancos de Dados

> **Arquivo:** `docs/02-infraestrutura/bancos-de-dados.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** bancos de dados usados pela plataforma, responsabilidades e limites entre dados de governança e dados operacionais

---

## 1. Objetivo

Este documento descreve os bancos de dados usados pela Minha DELPI.

A plataforma separa bancos por responsabilidade para evitar acoplamento entre autenticação, governança e dados operacionais.

---

## 2. Bancos atuais

A infraestrutura atual possui três bancos PostgreSQL em containers Docker e conexões para bancos externos.

Bancos em containers:

```text
postgres-core
keycloak-db
postgres-plugins
```

Bancos externos ou datasources configuráveis:

```text
TOTVS
Portal RH
```

---

## 3. Visão geral

| Banco/Datasource | Serviço | Responsabilidade |
|---|---|---|
| `postgres-core` | PostgreSQL Docker | Governança da Core API |
| `keycloak-db` | PostgreSQL Docker | Persistência interna do Keycloak |
| `postgres-plugins` | PostgreSQL Docker | Dados de plugins/domínios operacionais |
| TOTVS | Externo | Dados operacionais corporativos consumidos pela API DELPI |
| Portal RH | Externo | Dados de RH consumidos pela API DELPI quando configurado |

---

## 4. `postgres-core`

Serviço:

```text
postgres-core
```

Container:

```text
delpi-postgres-core
```

Imagem:

```text
postgres:15
```

Responsabilidade:

```text
Banco de governança da Core API.
```

Armazena:

- usuários locais;
- roles;
- grupos;
- permissões;
- vínculos RBAC;
- apps/plugins registrados;
- rotas de apps;
- manifestos vigentes;
- versões de plugins;
- favoritos;
- notificações;
- auditoria.

---

## 5. Variáveis do `postgres-core`

Variáveis de criação do container:

```env
POSTGRES_CORE_DB=
POSTGRES_CORE_USER=
POSTGRES_CORE_PASSWORD=
TZ=
```

Variáveis usadas pela Core API para conexão:

```env
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
```

No código da Core API, a URI SQLAlchemy é montada com:

```text
postgresql://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:<DB_PORT>/<DB_NAME>
```

---

## 6. Volume do `postgres-core`

Volume persistente:

```text
postgres_core_data
```

Mount principal:

```yaml
postgres_core_data:/var/lib/postgresql/data
```

Script inicial:

```yaml
./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
```

O script em `docker-entrypoint-initdb.d` roda apenas na inicialização de um volume novo.

---

## 7. Schema da Core API

O schema do `postgres-core` é controlado por migrations da Core API.

Ferramentas:

```text
Flask-Migrate
Alembic
SQLAlchemy
```

Tabelas principais:

```text
users
roles
groups
permissions
user_roles
user_groups
group_roles
role_permissions
user_permissions
apps
app_routes
app_manifests
app_versions
user_favorite_apps
notifications
audit_logs
```

---

## 8. `keycloak-db`

Serviço:

```text
keycloak-db
```

Container:

```text
delpi-keycloak-db
```

Imagem:

```text
postgres:15
```

Responsabilidade:

```text
Banco interno do Keycloak.
```

Armazena dados próprios do Keycloak, como:

- realms;
- clients;
- usuários do Keycloak;
- sessões;
- credenciais;
- configurações OIDC;
- mappers;
- temas/configurações internas.

---

## 9. Variáveis do `keycloak-db`

Variáveis:

```env
POSTGRES_KC_DB=
POSTGRES_KC_USER=
POSTGRES_KC_PASSWORD=
TZ=
```

O serviço `keycloak` acessa esse banco por:

```env
KC_DB=postgres
KC_DB_URL=jdbc:postgresql://keycloak-db:5432/${POSTGRES_KC_DB}
KC_DB_USERNAME=${POSTGRES_KC_USER}
KC_DB_PASSWORD=${POSTGRES_KC_PASSWORD}
```

---

## 10. Regra crítica sobre `keycloak-db`

A aplicação Minha DELPI não deve consultar ou alterar diretamente o banco `keycloak-db`.

Integrações com identidade devem passar por:

- protocolo OIDC;
- JWT emitido pelo Keycloak;
- endpoint JWKS;
- Admin API do Keycloak, quando necessário e de forma controlada.

Regra:

```text
Nunca implementar regra de negócio lendo tabelas internas do Keycloak.
```

---

## 11. `postgres-plugins`

Serviço:

```text
postgres-plugins
```

Container:

```text
delpi-postgres-plugins
```

Imagem:

```text
postgres:15
```

Responsabilidade:

```text
Banco para dados de plugins, módulos de domínio e persistências operacionais que não pertencem à Core API.
```

Consumidor principal atual:

```text
api-delpi
```

---

## 12. Variáveis do `postgres-plugins`

Variáveis de criação do container:

```env
PLUGINS_DB_NAME=
PLUGINS_DB_USER=
PLUGINS_DB_PASSWORD=
TZ=
```

Variáveis usadas pela API DELPI:

```env
PLUGINS_DB_HOST=
PLUGINS_DB_PORT=
PLUGINS_DB_NAME=
PLUGINS_DB_USER=
PLUGINS_DB_PASSWORD=
PLUGINS_DB_CONNECT_TIMEOUT=
PLUGINS_DB_SSLMODE=
```

---

## 13. Volume do `postgres-plugins`

Volume persistente:

```text
postgres_plugins_data
```

Mount principal:

```yaml
postgres_plugins_data:/var/lib/postgresql/data
```

Script inicial:

```yaml
./docker/postgres/plugins-init.sql:/docker-entrypoint-initdb.d/plugins-init.sql
```

---

## 14. Diferença entre `postgres-core` e `postgres-plugins`

| Tema | `postgres-core` | `postgres-plugins` |
|---|---|---|
| Dono funcional | Core API | API DELPI/plugins |
| Tipo de dado | Governança da plataforma | Dados operacionais/domínio |
| RBAC | Sim | Não como fonte principal |
| Apps/manifestos | Sim | Não |
| Favoritos/notificações | Sim | Não |
| Dados de dashboard/domínio | Não | Sim |
| Migrations | Core API | API DELPI ou módulo correspondente |

Regra:

> Dados de governança ficam no `postgres-core`. Dados de domínio/plugin ficam no `postgres-plugins` ou datasource próprio.

---

## 15. Datasource TOTVS

A API DELPI consome dados do TOTVS por variáveis externas.

No Compose, o código da API espera nomes `DB_*`, e o Compose mapeia a partir de `TOTVS_DB_*`:

```env
DB_HOST=${TOTVS_DB_HOST}
DB_PORT=${TOTVS_DB_PORT}
DB_USER=${TOTVS_DB_USER}
DB_PASSWORD=${TOTVS_DB_PASSWORD}
DB_DATABASE=${TOTVS_DB_DATABASE}
```

Isso significa:

```text
Dentro do container api-delpi, DB_* = datasource TOTVS.
```

Ponto de atenção:

> Não confundir `DB_*` da API DELPI com `DB_*` da Core API. Na Core API, `DB_*` aponta para `postgres-core`; na API DELPI, `DB_*` aponta para TOTVS.

---

## 16. Datasource Portal RH

A API DELPI também recebe variáveis para Portal RH:

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

- consultas operacionais de RH;
- integrações de domínio;
- suporte a módulos ou rotas da API DELPI.

O código real da API DELPI deve ser consultado para documentar tabelas, queries e rotas específicas.

---

## 17. Portas em desenvolvimento

No ambiente dev:

```text
postgres-core    → localhost:5432
postgres-plugins → localhost:5433
```

Isso facilita:

- inspeção com DBeaver/psql;
- debug local;
- execução de scripts;
- validação de migrations.

Em produção, essas portas não devem ser expostas sem necessidade.

---

## 18. Backup e restore

Recomendação por banco:

| Banco | Backup obrigatório? | Observação |
|---|---:|---|
| `postgres-core` | Sim | Contém governança, RBAC, apps e auditoria |
| `keycloak-db` | Sim | Contém realm, clients, usuários e sessões/configurações |
| `postgres-plugins` | Sim | Contém dados operacionais de módulos/plugins |
| TOTVS | Fora da stack | Política corporativa própria |
| Portal RH | Fora da stack | Política corporativa própria |

Nunca remover volumes de produção sem backup validado.

---

## 19. Reset em desenvolvimento

Para resetar volumes locais:

```bash
cd infra
docker compose -f docker-compose.dev.yml down -v
```

Depois subir novamente:

```bash
cd infra
docker compose -f docker-compose.dev.yml up --build
```

Atenção:

> Isso apaga usuários, roles, grupos, apps registrados, configurações do Keycloak e dados de plugins no ambiente local.

---

## 20. Segurança

Regras:

1. Não versionar senhas reais.
2. Não expor bancos em produção sem necessidade.
3. Não usar `keycloak-db` diretamente pela aplicação.
4. Não misturar dados de governança com dados operacionais.
5. Não registrar secrets em logs.
6. Usar usuários e senhas específicos por banco.
7. Fazer backup de volumes produtivos.
8. Proteger acessos administrativos aos bancos.

---

## 21. Checklist de validação

- [ ] `postgres-core` sobe e aceita conexão da Core API.
- [ ] Core API monta `SQLALCHEMY_DATABASE_URI` corretamente.
- [ ] Migrations da Core API foram aplicadas.
- [ ] `keycloak-db` sobe e Keycloak inicializa.
- [ ] `postgres-plugins` sobe e API DELPI conecta.
- [ ] TOTVS está acessível pela API DELPI quando necessário.
- [ ] Portal RH está acessível quando rotas dependem dele.
- [ ] Volumes persistentes existem.
- [ ] Em dev, portas locais estão corretas.
- [ ] Em produção, bancos não estão expostos indevidamente.

---

## 22. Documentos relacionados

```text
docs/02-infraestrutura/docker-compose.md
docs/02-infraestrutura/variaveis-de-ambiente.md
docs/09-banco-de-dados/core-db.md
docs/09-banco-de-dados/plugins-db.md
docs/09-banco-de-dados/keycloak-db.md
docs/07-api-delpi/banco-postgres-plugins.md
```
