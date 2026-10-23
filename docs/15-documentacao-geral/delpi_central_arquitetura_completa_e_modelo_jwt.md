# 🔷 DELPI Central — Documento Consolidado de Arquitetura, Segurança e Plugin System

---

# 1️⃣ Visão Estratégica

A DELPI Central será o portal unificado responsável por:

- Autenticação única (SSO)
- Governança de permissões
- Centralização de aplicações (CRM, GPT, Dashboards, futuras apps)
- Ecossistema plugável
- Auditoria e observabilidade

Base arquitetural:

- Gateway (camada de borda)
- Keycloak (Identity Provider)
- Core API (governança central)
- Portal React (shell da aplicação)
- Aplicações plugáveis (microfrontends ou serviços independentes)

---

# 2️⃣ Arquitetura em Camadas

## Edge Layer (Gateway)

Reverse Proxy: Nginx ou Traefik

Responsável por:

- HTTPS
- Roteamento por path
- Rate limit
- CORS
- Headers de segurança
- Logs centralizados

### Rotas Públicas

- `/` → Portal
- `/core-api/*` → Core API
- `/auth/*` → Keycloak
- `/apps/crm/*` → CRM
- `/apps/gpt/*` → GPT
- `/apps/<plugin>/*` → Plugins

Todos os serviços são acessados externamente apenas pelo gateway.

---

# 3️⃣ Autenticação e Modelo JWT Oficial

## Provedor de Identidade

Keycloak com:

- OAuth2
- OpenID Connect
- Authorization Code + PKCE
- Access Token (JWT)
- Refresh Token

---

# 🔐 Modelo Ideal de JWT

O JWT deve conter apenas informações de identidade e contexto.

## Exemplo de Payload

```json
{
  "iss": "https://central.delpi.com.br/auth/realms/delpi",
  "sub": "uuid-do-usuario",
  "aud": "delpi-central",
  "exp": 1712345678,
  "iat": 1712342000,
  "email": "usuario@delpi.com.br",
  "name": "Usuário DELPI",
  "realm_access": {
    "roles": ["admin"]
  },
  "groups": ["comercial"],
  "tenant_id": "delpi",
  "token_version": 1
}
```

## O que vai no JWT

- user_id (sub)
- email
- roles
- groups
- tenant_id
- token_version

## O que NÃO vai no JWT

- Lista completa de permissões
- Rotas liberadas
- Estrutura de menus

---

# 🔄 Fluxo de Autorização Real

1. Usuário loga
2. Portal recebe access_token
3. Portal chama `/core-api/me`
4. Core resolve permissões efetivas no banco
5. Portal monta menu dinamicamente

---

# 4️⃣ Core API (FastAPI + PostgreSQL)

Responsável por:

- Gestão de usuários
- Gestão de roles e groups
- Registro de plugins
- Controle de permissões
- Endpoints consolidados
- Auditoria

## Endpoints principais

### GET /core-api/me

Retorna perfil consolidado.

### GET /core-api/me/apps

Lista aplicações permitidas.

### GET /core-api/me/routes

Lista rotas autorizadas.

---

# 5️⃣ Modelagem Completa do Banco (PostgreSQL)

## Entidades Principais

- users
- roles
- permissions
- groups
- apps
- app_routes
- audit_logs

---

## Estrutura RBAC

users
 ├── user_roles → roles
 ├── user_groups → groups → group_roles → roles
 └── user_permissions (override)

roles → role_permissions → permissions

apps → app_routes → permissions

---

## Capacidades

- RBAC completo
- Override por usuário
- Controle por rota
- Controle por módulo
- Plugin registry
- Auditoria estruturada
- Preparado para ABAC futuro

---

# 6️⃣ Portal Frontend (React + Vite)

Função: Shell da aplicação.

Responsável por:

- Layout principal
- Menu dinâmico
- Integração SSO
- Carregamento de plugins

Estratégias:

1. Microfrontend (Module Federation)
2. iFrame (inicial)

---

# 7️⃣ Sistema Oficial de Plugins (Manifest v2)

Arquivo obrigatório:

```
delpi.manifest.json
```

---

## Estrutura Essencial

Campos obrigatórios:

- schemaVersion
- id
- name
- version
- type
- basePath
- permissions
- routes

---

## Tipos de Plugin

- microfrontend
- iframe
- backend-only

---

## Fluxo de Registro

1. Plugin é deployado
2. Admin envia manifesto
3. Core valida schema
4. Core cria:
   - Registro em apps
   - Permissões
   - Rotas
   - Manifest armazenado
   - Log de auditoria
5. Portal atualiza menu automaticamente

---

# 8️⃣ Validação de Token nos Serviços

Todos os serviços devem:

1. Validar assinatura (RS256)
2. Validar issuer
3. Validar audience
4. Validar expiração
5. Aplicar verificação de permissão

---

# 9️⃣ Deploy Inicial (VM + Docker Compose)

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

- Ambientes separados
- Kubernetes
- Prometheus + Grafana

---

# 🔟 Segurança

- HTTPS obrigatório
- JWT curto (5–15 min)
- Refresh token controlado
- Rate limit
- CSP
- HSTS
- Auditoria completa

---

# 1️⃣1️⃣ Estratégia de Escala

Fase 1 – Fundação
- Gateway
- Keycloak
- Core API
- Portal

Fase 2 – Integração
- CRM
- GPT
- Controle fino de permissões

Fase 3 – Ecossistema
- Microfrontends padronizados
- Plugin registry automático
- Observabilidade
- Feature flags

---

# 1️⃣2️⃣ Resultado Final

A DELPI Central fica estruturada como:

✔ Plataforma de identidade
✔ Plataforma de autorização
✔ Plataforma de plugins
✔ Portal unificado
✔ Arquitetura escalável
✔ Segurança padronizada
✔ Governança centralizada
✔ Preparada para multi-tenant futuro

---

Documento consolidado oficial da arquitetura da DELPI Central.

