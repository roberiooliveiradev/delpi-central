# 📊 ROADMAP TÉCNICO FASEADO — DELPI CENTRAL

---

# 🟢 FASE 0 — Fundação Infra (Semana 1)

## 🎯 Objetivo
Estrutura mínima rodando com autenticação real.

## ✅ Entregáveis
- VM preparada
- Docker + Docker Compose
- Nginx (Gateway)
- Keycloak configurado
- PostgreSQL (core)
- Estrutura inicial de repositório

## 🔧 Tarefas Técnicas

### Infraestrutura
- Configurar domínio central.delpi.com.br
- Configurar SSL (Let's Encrypt)
- Estrutura base:
```
/delpi-central
  /gateway
  /portal
  /core-api
  /infra
```

### Keycloak
- Criar Realm: delpi
- Criar Client: delpi-central
- Configurar Authorization Code + PKCE
- Configurar RS256
- Audience: delpi-central
- Criar roles iniciais (admin, user)

### Gateway
Rotas públicas:
- / → Portal
- /core-api → Core API
- /auth → Keycloak
- /apps/* → Aplicações futuras

---

# 🟢 FASE 1 — Core API + RBAC (Semanas 2–3)

## 🎯 Objetivo
Governança central funcionando.

## ✅ Entregáveis
- Core API (FastAPI)
- Banco estruturado
- RBAC funcional
- Endpoint /me
- Auditoria básica

## 🔧 Tarefas Técnicas

### Banco de Dados
Implementar:
- users
- roles
- permissions
- user_roles
- role_permissions
- groups
- group_roles
- user_permissions (override)
- apps
- app_routes
- app_manifests
- audit_logs

### Integração JWT
Core deve:
- Validar assinatura
- Validar issuer
- Validar audience
- Validar expiração
- Extrair sub (user_id)
- Sincronizar usuário automaticamente

### Endpoints
- GET /core-api/me
- GET /core-api/me/apps
- GET /core-api/me/routes

Fluxo:
1. Login
2. Portal recebe token
3. Portal chama /me
4. Menu é montado dinamicamente

---

# 🟢 FASE 2 — Portal Shell + Menu Dinâmico (Semana 4)

## 🎯 Objetivo
Interface central funcionando.

## ✅ Entregáveis
- Portal React + Vite
- Integração SSO
- Menu dinâmico por permissão
- App Launcher inicial

## 🔧 Tarefas Técnicas

### Login
- Redirecionamento para Keycloak
- Armazenamento seguro do token
- Refresh token controlado

### Consumo da Core
- Chamar /me
- Chamar /me/apps
- Chamar /me/routes

### Layout
- Sidebar dinâmica
- Topbar com usuário
- Área de conteúdo principal

---

# 🟡 FASE 3 — Sistema Oficial de Plugins (Semanas 5–6)

## 🎯 Objetivo
Arquitetura plugável operacional.

## ✅ Entregáveis
- Endpoint de registro de plugin
- Validador de manifesto
- Auto-criação de permissões
- Auto-criação de rotas
- Armazenamento do manifest
- Auditoria do registro

## 🔧 Tarefas Técnicas

### Endpoint
POST /core-api/plugins/register

### Fluxo
1. Validar schemaVersion
2. Validar ID único
3. Validar permissões
4. Criar registros:
   - apps
   - permissions
   - app_routes
   - app_manifests
5. Registrar auditoria

### Regras
- Sem sobrescrever rotas existentes
- Sem colisão de permission code
- Versionamento SemVer obrigatório

---

# 🟡 FASE 4 — Integração CRM (Semana 7)

## 🎯 Objetivo
Primeiro módulo real integrado.

## ✅ Entregáveis
- CRM publicado em /apps/crm
- JWT validado
- Permissões aplicadas
- Manifest registrado
- Menu dinâmico funcionando

## 🔧 Tarefas Técnicas
- Implementar validação JWT no backend
- Criar delpi.manifest.json
- Registrar plugin na Core
- Testar permissões por rota

---

# 🟡 FASE 5 — Integração GPT API (Semana 8)

## 🎯 Objetivo
API TOTVS integrada à governança.

## ✅ Entregáveis
- GPT API sob /apps/gpt
- Protegida por JWT
- Permissão gpt.access
- Auditoria de chamadas

---

# 🟠 FASE 6 — Microfrontends (Semanas 9–10)

## 🎯 Objetivo
Evolução arquitetural para escala.

## Migração
De:
- iFrame simples

Para:
- Module Federation

## Benefícios
- Carregamento sob demanda
- Versionamento independente
- Isolamento real entre módulos

---

# 🟠 FASE 7 — Observabilidade + Segurança Avançada (Semanas 11–12)

## 🎯 Entregáveis
- Logs estruturados JSON
- Prometheus
- Grafana
- Métricas por plugin
- Rate limit no gateway
- CSP configurado
- HSTS
- Auditoria expandida

---

# 🔴 FASE 8 — Evolução Estratégica

## Próximos Passos
- Feature flags por plugin
- Multi-tenant
- Marketplace interno
- Assinatura digital de manifest
- Evolução para ABAC

---

# 📈 Linha do Tempo Resumida

| Fase | Tema | Complexidade | Impacto |
|------|------|-------------|----------|
| 0 | Infra + SSO | Média | Alta |
| 1 | Core + RBAC | Alta | Crítica |
| 2 | Portal Base | Média | Alta |
| 3 | Plugin System | Alta | Estratégica |
| 4 | CRM | Média | Operacional |
| 5 | GPT | Média | Integração |
| 6 | Microfrontends | Alta | Escala |
| 7 | Observabilidade | Média | Governança |
| 8 | Evolução | Alta | Plataforma |

---

# 🏗 Resultado Esperado ao Final da Fase 4

- SSO corporativo implementado
- Controle de permissões por rota
- CRM governado pela central
- GPT API governada
- Portal unificado operacional
- Arquitetura plugável real

---

Documento estruturado para execução técnica imediata da DELPI Central.

