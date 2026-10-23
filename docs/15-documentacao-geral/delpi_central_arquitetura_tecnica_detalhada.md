# DELPI Central
## Arquitetura Técnica Detalhada

---

# 1. Visão Geral

A DELPI Central será um portal web responsável por:

- Autenticação única (SSO)
- Controle de permissões por usuário, grupo e papel
- Centralização de aplicações (CRM, GPT API, Dashboards, futuras apps)
- Ecossistema plugável de módulos

A arquitetura será baseada em:

- Gateway (entrada única)
- Provedor de identidade (SSO)
- Core API (controle central)
- Portal Frontend (shell da aplicação)
- Aplicações plugáveis (microfrontends ou serviços independentes)

---

# 2. Arquitetura em Camadas

## 2.1 Edge Layer (Publicação)

### Reverse Proxy / API Gateway (Nginx ou Traefik)

Responsável por:

- Terminação HTTPS
- Roteamento por path
- Segurança (headers, CORS, rate limit)
- Log centralizado

### Estrutura de Rotas

- `/` → Portal React
- `/core-api/*` → Core API (FastAPI)
- `/auth/*` → Keycloak
- `/apps/crm/*` → CRM
- `/apps/gpt/*` → GPT API
- `/apps/<plugin>/*` → Plugins futuros

---

# 3. Autenticação e Autorização

## 3.1 Provedor de Identidade (Recomendado: Keycloak)

- OAuth2 + OpenID Connect
- Fluxo Authorization Code + PKCE
- Emissão de JWT (access + refresh token)
- Single Sign-On entre todos os módulos

## 3.2 Modelo de Permissões

Modelo RBAC com possibilidade futura de ABAC.

Entidades principais:

- users
- groups
- roles
- permissions
- role_permissions
- user_roles
- user_groups
- apps
- app_routes
- route_permissions

Exemplo de permissão:

- `crm.leads.read`
- `crm.pipeline.view`
- `dash.sales.view`

---

# 4. Core API (Serviço Central)

Tecnologia recomendada: FastAPI + PostgreSQL

Responsável por:

- Cadastro de usuários (ou integração com IdP)
- Gestão de grupos e papéis
- Registro de plugins
- Controle de permissões por rota
- Endpoint `/me` com dados consolidados
- Endpoint `/me/apps`
- Endpoint `/me/routes`
- Auditoria de ações

Banco principal: PostgreSQL (core)

---

# 5. Portal Frontend (React + Vite)

Função: Shell da aplicação

Responsável por:

- Layout principal
- Menu dinâmico baseado em permissões
- Integração com SSO
- Carregamento de módulos plugáveis

Estratégias de integração:

1. Microfrontend (Module Federation) – recomendado
2. iFrame – opção mais simples inicialmente

---

# 6. Arquitetura Plugável (Plugin System)

Cada aplicação terá um manifesto padrão.

## Exemplo de manifest.json

```json
{
  "id": "crm",
  "name": "CRM",
  "version": "1.3.0",
  "type": "microfrontend",
  "entry": "/apps/crm/remoteEntry.js",
  "routes": [
    {
      "path": "/crm/leads",
      "label": "Leads",
      "permission": "crm.leads.read"
    },
    {
      "path": "/crm/pipeline",
      "label": "Pipeline",
      "permission": "crm.pipeline.view"
    }
  ]
}
```

Fluxo de registro:

1. Plugin é deployado
2. Admin registra no Core API
3. Permissões são associadas
4. Portal passa a exibir no menu conforme regras

---

# 7. Aplicações Integradas

## 7.1 CRM

- Backend: Python (Flask ou FastAPI)
- Frontend: React
- Banco: PostgreSQL
- Publicado em `/apps/crm/*`
- Valida JWT do Keycloak

## 7.2 GPT API (TOTVS)

- Backend Python
- Publicado em `/apps/gpt/*`
- Protegido por validação de token

## 7.3 Dashboards

- Podem ser microfrontends independentes
- Controle por permissão específica

---

# 8. Deploy Inicial (VM com Docker Compose)

Serviços:

- gateway
- portal
- core-api
- postgres-core
- keycloak
- keycloak-db
- crm-backend
- crm-frontend
- gpt-api

Evolução futura:

- Separação por ambientes (dev, staging, prod)
- Kubernetes
- Monitoramento (Prometheus + Grafana)

---

# 9. Fluxos Principais

## Login

1. Usuário acessa portal
2. Redireciona para Keycloak
3. Retorna com access_token
4. Portal chama `/core-api/me`
5. Menu é montado dinamicamente

## Acesso a módulo

1. Usuário clica em módulo
2. Portal verifica permissão
3. Backend do módulo valida token
4. Acesso concedido ou negado

---

# 10. Segurança

- HTTPS obrigatório
- JWT com expiração curta
- Refresh token controlado
- Validação de issuer e audience
- Auditoria de login e permissões
- Rate limit no gateway
- Security headers (HSTS, CSP, X-Frame-Options)

---

# 11. Evolução Estratégica

Fase 1 – Fundação
- Gateway
- Keycloak
- Core API
- Portal base

Fase 2 – Integração
- CRM integrado
- GPT API integrada
- Controle fino de permissões

Fase 3 – Ecossistema
- Microfrontends padronizados
- Plugin registry automático
- Observabilidade completa

---

Arquitetura preparada para escalar, adicionar novos módulos rapidamente e manter governança centralizada de acesso.

---

# 12. Blueprint Técnico (Nomes, Portas, Contratos)

## 12.1 Serviços e Portas (Docker Compose - Produção VM)

| Serviço | Container | Porta Interna | Porta Externa | Observação |
|----------|------------|---------------|---------------|------------|
| gateway | delpi-gateway | 80 | 80 / 443 | Nginx ou Traefik |
| portal | delpi-portal | 5173 (build servido 80) | - | Apenas via gateway |
| core-api | delpi-core-api | 8000 | - | FastAPI |
| postgres-core | delpi-postgres-core | 5432 | - | Banco do Core |
| keycloak | delpi-keycloak | 8080 | - | IdP |
| keycloak-db | delpi-keycloak-db | 5432 | - | Banco do IdP |
| crm-backend | delpi-crm-api | 5000 | - | API CRM |
| crm-frontend | delpi-crm-web | 5174 | - | Microfrontend |
| gpt-api | delpi-gpt-api | 7000 | - | API TOTVS |

Todos os serviços são acessados externamente apenas pelo gateway.

---

## 12.2 Estrutura Oficial de Rotas Públicas

- https://central.delpi.com.br/ → Portal
- https://central.delpi.com.br/core-api/* → Core API
- https://central.delpi.com.br/auth/* → Keycloak
- https://central.delpi.com.br/apps/crm/* → CRM
- https://central.delpi.com.br/apps/gpt/* → GPT API
- https://central.delpi.com.br/apps/<plugin>/* → Plugins futuros

---

## 12.3 Contrato Principal da Core API

### GET /core-api/me
Retorna perfil consolidado:

```json
{
  "id": "uuid",
  "name": "Usuário",
  "email": "user@delpi.com.br",
  "roles": ["admin"],
  "groups": ["comercial"],
  "permissions": ["crm.leads.read"]
}
```

### GET /core-api/me/apps

```json
[
  {
    "id": "crm",
    "name": "CRM",
    "basePath": "/crm",
    "icon": "chart-line"
  }
]
```

### GET /core-api/me/routes

```json
[
  {
    "app": "crm",
    "path": "/crm/leads",
    "permission": "crm.leads.read"
  }
]
```

---

## 12.4 Estrutura Base de Tabelas (DDL Simplificado)

users (id, name, email, active)
roles (id, name)
permissions (id, code)
role_permissions (role_id, permission_id)
user_roles (user_id, role_id)
groups (id, name)
user_groups (user_id, group_id)
apps (id, name, version, base_path, active)
app_routes (id, app_id, path, label, permission_code)

---

## 12.5 Validação de Token nos Serviços

Todos os serviços devem:

1. Validar assinatura JWT
2. Validar issuer (Keycloak)
3. Validar audience (delpi-central)
4. Validar expiração
5. Aplicar verificação de permissão quando necessário

---

## 12.6 Estrutura de Pastas Recomendada (Monorepo Opcional)

```
/delpi-central
  /gateway
  /portal
  /core-api
  /plugins
      /crm
      /dashboards
      /gpt-module
  /infra
      docker-compose.yml
      nginx.conf
```

---

## 12.7 Padrão para Novos Plugins

Checklist obrigatório:

- Manifesto compatível
- Validação JWT implementada
- Permissões declaradas
- Rota sob /apps/<id>
- Logs estruturados (JSON)
- Healthcheck endpoint: /health

---

Blueprint pronto para iniciar implementação técnica imediata.

