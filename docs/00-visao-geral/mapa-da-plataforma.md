# Minha DELPI — Mapa da Plataforma

> **Arquivo:** `docs/00-visao-geral/mapa-da-plataforma.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** visão navegável dos componentes, fluxos, repositório e documentação

---

## 1. Objetivo

Este documento apresenta o mapa geral da **Minha DELPI**.

Ele deve ajudar qualquer pessoa a entender rapidamente:

- quais componentes formam a plataforma;
- como as requisições fluem;
- quais bancos existem;
- como autenticação e autorização se conectam;
- como plugins entram no ecossistema;
- onde encontrar cada assunto na documentação.

Este documento não substitui os documentos técnicos detalhados. Ele funciona como uma visão de orientação.

---

## 2. Visão de alto nível

A Minha DELPI é uma plataforma corporativa modular.

Ela centraliza:

- autenticação via Keycloak;
- autorização via RBAC interno na Core API;
- acesso a apps e plugins;
- menu dinâmico por permissão;
- governança de manifestos;
- integração com APIs operacionais;
- execução local via Docker Compose.

Visão conceitual:

```text
Usuário
  ↓
Gateway / Nginx
  ↓
Portal React
  ↓
Core API
  ↓
PostgreSQL Core
```

Em paralelo:

```text
Portal / Plugins
  ↓
API DELPI
  ↓
TOTVS / postgres-plugins / Portal RH
```

E autenticação:

```text
Portal
  ↓
Keycloak
  ↓
JWT
  ↓
Core API / API DELPI
```

---

## 3. Componentes principais

| Componente | Serviço/Pasta | Responsabilidade |
|---|---|---|
| Gateway | `gateway` | Entrada HTTP única e roteamento por path |
| Portal | `portal` | Shell frontend, login, menu e carregamento de plugins |
| Core API | `core-api` | Governança, RBAC, apps, plugins, favoritos e notificações |
| Keycloak | `keycloak` | SSO, login e emissão de JWT |
| PostgreSQL Core | `postgres-core` | Banco de governança da Core API |
| Keycloak DB | `keycloak-db` | Banco interno do Keycloak |
| API DELPI | `api-delpi` | Backend operacional e integrações de domínio |
| PostgreSQL Plugins | `postgres-plugins` | Banco de plugins/domínios operacionais |
| Plugins | `plugins/*` | Microfrontends, iframes ou módulos plugáveis |

---

## 4. Mapa de execução Docker

Serviços atuais da stack:

```text
postgres-core
keycloak-db
keycloak
core-api
portal
dashboard-delpi
strategic-indicators
dashboard-lmps
postgres-plugins
api-delpi
gateway
```

Rede principal:

```text
delpi-network
```

Volumes principais:

```text
postgres_core_data
keycloak_data
postgres_plugins_data
```

Entrada pública:

```text
Gateway → porta 80
```

---

## 5. Mapa de rotas públicas

Rotas conceituais da plataforma:

| Path | Destino | Finalidade |
|---|---|---|
| `/` | Portal | Interface principal |
| `/core-api/*` | Core API | Governança e APIs centrais |
| `/auth/*` | Keycloak | Login, realm e OIDC |
| `/apps/*` | Plugins / API DELPI | Apps plugáveis e backends operacionais |

Exemplos de uso:

```text
/                         → Portal
/core-api/health          → Healthcheck da Core API
/core-api/me              → Usuário atual
/core-api/me/apps         → Apps autorizados
/auth                     → Keycloak
/apps/dashboard-lmps      → Plugin ou rota de app
/apps/api-delpi           → API operacional exposta pelo Gateway
```

A configuração exata deve ser validada no Nginx/Gateway.

---

## 6. Mapa de autenticação

Fluxo de login:

```text
1. Usuário acessa o Portal.
2. Portal redireciona para Keycloak.
3. Usuário autentica.
4. Keycloak emite access token JWT.
5. Portal envia Authorization: Bearer <token> para a Core API.
6. Core API valida assinatura, issuer, audience e expiração.
7. Core API sincroniza o usuário local.
8. Core API resolve permissões efetivas.
```

Ponto central:

> Keycloak autentica. Core API autoriza.

---

## 7. Mapa de autorização

Fluxo de autorização para o Portal:

```text
Portal chama /core-api/me
  ↓
Core API retorna usuário e permissões efetivas
  ↓
Portal chama /core-api/me/apps
  ↓
Core API filtra apps e rotas por permissão
  ↓
Portal monta menu dinâmico
```

Fontes de autorização:

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
```

A lista final de apps não deve ser hardcoded no Portal.

---

## 8. Mapa do RBAC

Modelo conceitual:

```text
users
  ├── user_roles ───── roles ───── role_permissions ───── permissions
  │
  ├── user_groups ──── groups ──── group_roles ────────── roles
  │
  └── user_permissions ────────────────────────────────── permissions
```

Regras principais:

- roles concedem permissões;
- grupos concedem roles aos usuários;
- usuários podem ter roles diretas;
- usuários podem ter overrides individuais;
- superadmin possui bypass administrativo;
- permissões efetivas são calculadas pela Core API.

---

## 9. Mapa do Plugin System

Fluxo de registro de plugin:

```text
Manifesto JSON
  ↓
Core API valida schema e regras
  ↓
Core API cria/atualiza app
  ↓
Core API cria permissões
  ↓
Core API cria rotas
  ↓
Core API salva manifesto vigente
  ↓
Core API salva versão histórica
  ↓
Portal recebe app em /me/apps quando usuário tem permissão
```

Entidades principais:

```text
apps
app_routes
app_manifests
app_versions
permissions
```

Tipos de plugin:

```text
microfrontend
iframe
backend-only
```

---

## 10. Mapa do Portal

O Portal é o shell da aplicação.

Responsabilidades:

```text
Login Keycloak
  ↓
Carregar /me
  ↓
Carregar /me/apps
  ↓
Carregar favoritos
  ↓
Carregar notificações
  ↓
Conectar Socket.IO
  ↓
Montar menu e rotas
  ↓
Renderizar plugin autorizado
```

O Portal deve usar a Core API como fonte oficial de apps autorizados.

---

## 11. Mapa da Core API

A Core API é organizada em camadas.

```text
interfaces
  ↓
application
  ↓
domain
  ↓
infrastructure
```

Na prática:

| Camada | Conteúdo |
|---|---|
| `interfaces` | Controllers HTTP, middleware, socket handlers |
| `application` | Use cases, services e Unit of Work |
| `domain` | Ports, eventos e regras de domínio |
| `infrastructure` | SQLAlchemy, banco, configurações, JWT, repositories |

Blueprints registrados na aplicação:

```text
health_bp
rbac_bp
admin_apps_bp
me_bp
```

---

## 12. Mapa da API DELPI

A API DELPI é o backend operacional.

Ela deve ser usada para:

- integrações com TOTVS;
- dados operacionais;
- módulos de domínio;
- endpoints consumidos por plugins;
- acesso ao `postgres-plugins`;
- integração com Portal RH, quando configurada.

Ela não deve substituir a Core API na governança da plataforma.

Separação:

```text
Core API  → governança da plataforma
API DELPI → regras e dados operacionais
```

---

## 13. Mapa dos bancos de dados

| Banco | Serviço | Dono funcional | Conteúdo |
|---|---|---|---|
| PostgreSQL Core | `postgres-core` | Core API | usuários, RBAC, apps, rotas, manifestos, favoritos, notificações, auditoria |
| Keycloak DB | `keycloak-db` | Keycloak | dados internos do IdP |
| PostgreSQL Plugins | `postgres-plugins` | API DELPI / plugins | dados operacionais e módulos de domínio |
| TOTVS | externo | API DELPI | datasource corporativo operacional |
| Portal RH DB | externo | API DELPI | datasource corporativo de RH |

Regra:

> Banco do Keycloak não deve ser usado diretamente pela aplicação para regras de negócio.

---

## 14. Mapa de eventos e tempo real

A Core API usa eventos para notificar mudanças relevantes.

Fluxo:

```text
Use case executa alteração
  ↓
Unit of Work coleta evento
  ↓
Commit da transação
  ↓
EventBus publica evento
  ↓
Handlers internos reagem
  ↓
Socket.IO emite admin.changed
  ↓
Portal recarrega estado necessário
```

Eventos podem afetar:

- RBAC;
- menu;
- plugins;
- rotas;
- favoritos;
- notificações.

---

## 15. Mapa de documentação

### Visão geral

```text
docs/00-visao-geral/minha-delpi-visao-geral.md
docs/00-visao-geral/glossario.md
docs/00-visao-geral/mapa-da-plataforma.md
```

### Arquitetura

```text
docs/01-arquitetura/arquitetura-geral.md
docs/01-arquitetura/estrutura-de-repositorio.md
docs/01-arquitetura/fluxo-de-requisicao.md
docs/01-arquitetura/clean-architecture.md
docs/01-arquitetura/event-driven-e-socket.md
```

### Infraestrutura

```text
docs/02-infraestrutura/docker-compose.md
docs/02-infraestrutura/ambientes-dev-prod.md
docs/02-infraestrutura/gateway-nginx.md
docs/02-infraestrutura/bancos-de-dados.md
docs/02-infraestrutura/variaveis-de-ambiente.md
```

### Autenticação e autorização

```text
docs/03-autenticacao-autorizacao/keycloak-sso.md
docs/03-autenticacao-autorizacao/jwt.md
docs/03-autenticacao-autorizacao/rbac.md
docs/03-autenticacao-autorizacao/permission-resolver.md
docs/03-autenticacao-autorizacao/superadmin.md
docs/03-autenticacao-autorizacao/policies-e-decorators.md
```

### Core API

```text
docs/04-core-api/visao-geral-core-api.md
docs/04-core-api/bootstrap-da-aplicacao.md
docs/04-core-api/controllers-e-rotas.md
docs/04-core-api/use-cases.md
docs/04-core-api/unit-of-work.md
docs/04-core-api/repositories.md
docs/04-core-api/modelos-de-banco.md
docs/04-core-api/migrations.md
docs/04-core-api/erros-api.md
docs/04-core-api/notificacoes.md
```

### Plugin System

```text
docs/05-plugin-system/visao-geral-plugin-system.md
docs/05-plugin-system/manifesto-plugin.md
docs/05-plugin-system/registro-de-plugin.md
docs/05-plugin-system/atualizacao-de-manifesto.md
docs/05-plugin-system/versionamento-e-rollback.md
docs/05-plugin-system/microfrontends.md
docs/05-plugin-system/backend-only.md
docs/05-plugin-system/iframe.md
```

### Portal frontend

```text
docs/06-portal-frontend/visao-geral-portal.md
docs/06-portal-frontend/autenticacao-frontend.md
docs/06-portal-frontend/menu-dinamico.md
docs/06-portal-frontend/app-authorization.md
docs/06-portal-frontend/favoritos.md
docs/06-portal-frontend/consumo-de-plugins.md
```

### API DELPI

```text
docs/07-api-delpi/visao-geral-api-delpi.md
docs/07-api-delpi/integracao-totvs.md
docs/07-api-delpi/banco-postgres-plugins.md
docs/07-api-delpi/rotas-operacionais.md
docs/07-api-delpi/modulos-de-dominio.md
```

### Plugins

```text
docs/08-plugins/dashboard-delpi.md
docs/08-plugins/strategic-indicators.md
docs/08-plugins/dashboard-lmps.md
docs/08-plugins/qualidade.md
```

### Banco de dados

```text
docs/09-banco-de-dados/core-db.md
docs/09-banco-de-dados/plugins-db.md
docs/09-banco-de-dados/keycloak-db.md
docs/09-banco-de-dados/modelo-rbac.md
docs/09-banco-de-dados/modelo-plugin-system.md
```

### Guias operacionais

```text
docs/10-guias-operacionais/subir-ambiente-dev.md
docs/10-guias-operacionais/reset-banco-dev.md
docs/10-guias-operacionais/configurar-keycloak.md
docs/10-guias-operacionais/registrar-plugin.md
docs/10-guias-operacionais/troubleshooting.md
```

### Padrões de desenvolvimento

```text
docs/11-padroes-de-desenvolvimento/padrao-de-rota.md
docs/11-padroes-de-desenvolvimento/padrao-de-use-case.md
docs/11-padroes-de-desenvolvimento/padrao-de-repository.md
docs/11-padroes-de-desenvolvimento/padrao-de-erro.md
docs/11-padroes-de-desenvolvimento/padrao-de-evento.md
docs/11-padroes-de-desenvolvimento/checklist-code-review.md
```

### Roadmap e evolução

```text
docs/12-roadmap-e-evolucao/status-atual.md
docs/12-roadmap-e-evolucao/decisoes-tecnicas.md
docs/12-roadmap-e-evolucao/pendencias-tecnicas.md
docs/12-roadmap-e-evolucao/roadmap.md
```

---

## 16. Caminho recomendado de leitura

### Para visão de produto

```text
1. minha-delpi-visao-geral.md
2. glossario.md
3. mapa-da-plataforma.md
4. arquitetura-geral.md
```

### Para backend/Core API

```text
1. arquitetura-geral.md
2. rbac.md
3. permission-resolver.md
4. visao-geral-core-api.md
5. controllers-e-rotas.md
6. use-cases.md
7. unit-of-work.md
8. repositories.md
```

### Para frontend/Portal

```text
1. visao-geral-portal.md
2. autenticacao-frontend.md
3. menu-dinamico.md
4. app-authorization.md
5. consumo-de-plugins.md
```

### Para plugins

```text
1. visao-geral-plugin-system.md
2. manifesto-plugin.md
3. registro-de-plugin.md
4. microfrontends.md
5. backend-only.md
6. iframe.md
```

### Para operação/infra

```text
1. docker-compose.md
2. ambientes-dev-prod.md
3. gateway-nginx.md
4. bancos-de-dados.md
5. variaveis-de-ambiente.md
```

---

## 17. Limites deste mapa

Este documento não detalha:

- todas as rotas da API DELPI;
- todos os contratos dos plugins;
- configuração completa do Gateway;
- scripts de deploy;
- troubleshooting detalhado.

Esses assuntos devem ser mantidos nos documentos específicos de cada pasta.

---

## 18. Documentos relacionados

```text
docs/00-visao-geral/minha-delpi-visao-geral.md
docs/00-visao-geral/glossario.md
docs/01-arquitetura/arquitetura-geral.md
docs/02-infraestrutura/docker-compose.md
docs/03-autenticacao-autorizacao/rbac.md
docs/04-core-api/visao-geral-core-api.md
docs/05-plugin-system/manifesto-plugin.md
docs/06-portal-frontend/visao-geral-portal.md
```
