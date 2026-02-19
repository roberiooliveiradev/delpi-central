# 📄 DELPI Central — Documento Técnico Oficial
## Fase 2 — RBAC, Apps & Admin Console

---

# 🎯 Objetivo da Fase 2

A Fase 2 consolida o núcleo de autorização e administração da DELPI Central, transformando o sistema em uma plataforma multi‑aplicações com controle granular de acesso.

Esta fase implementa:

- ✅ RBAC completo (Users, Roles, Groups, Permissions)
- ✅ Cache de permissões
- ✅ Admin Backend (RBAC + Apps + Routes)
- ✅ Seed oficial de permissões base
- ✅ Seed de aplicação CRM
- ✅ Superadmin independente de permissão
- ✅ Proteção real de rotas
- ✅ Notificações em tempo real
- ✅ Console administrativo frontend

---

# 🧠 Arquitetura Conceitual

## 🔐 Autenticação

- Keycloak (OIDC)
- JWT validado via JWKS
- Audience validado
- Issuer validado

## 🔑 Autorização

Modelo híbrido:

- Roles
- Groups
- Permission Overrides
- Superadmin bypass

Fluxo:

JWT → authenticate() → resolve_user_permissions() → cache → rotas protegidas

---

# 🏗 Estrutura de Domínio

## 👤 User
- id (UUID do Keycloak)
- email
- name
- is_superadmin
- last_login_at

## 🧩 Role
- id (UUID)
- name
- description
- system_role

## 👥 Group
- id
- name
- description

## 🔐 Permission
- id (UUID)
- code (único)
- name
- description
- module

## 📦 App
- id
- name
- base_path
- icon
- type
- version
- active

## 🛣 AppRoute
- id
- app_id
- path
- label
- icon
- order
- show_in_menu
- permission_id (UUID FK)
- active

---

# ⚙️ RBAC Engine

## Resolução de Permissões

1. Se `is_superadmin = True` → retorna todas permissões
2. Roles diretas
3. Roles via grupos
4. Overrides do usuário
5. Cache em memória

Cache invalidado automaticamente quando:

- Role alterada
- Permissões da role alteradas
- Usuário recebe/remove role
- Grupo recebe/remove role
- Overrides alterados

---

# 🧱 Seed Oficial de Permissões Base

Criadas automaticamente no bootstrap:

### RBAC
- rbac.manage

### Users
- users.view
- users.manage

### Groups
- groups.manage

### Permissions
- permissions.manage

### Apps & Routes
- apps.manage
- routes.manage

### Dashboard
- dashboard.view

### Notifications
- notifications.view
- notifications.manage

Seed idempotente.

---

# 👑 Superadmin

## Regras

- Criado apenas se variáveis de ambiente existirem:
  - INITIAL_SUPERADMIN_EMAIL
  - INITIAL_SUPERADMIN_NAME
- Não depende de rbac.manage
- Bypass completo do RBAC

---

# 📦 Apps & Routes Admin

## Funcionalidades

- CRUD de Apps
- Ativação/Desativação
- CRUD de Rotas por App
- Associação automática de permission_code
- Validação de duplicidade de rota por app
- Seed automático do CRM

## CRM Seed

App: crm

Rotas:
- /crm/dashboard
- /crm/leads

---

# 🧭 Endpoint /core-api/me/routes

Retorna apenas:

- Rotas ativas
- Apps ativos
- Rotas permitidas pelo usuário
- Ordenadas por app e order

Utiliza eager loading para performance.

---

# 🔔 Notificações em Tempo Real

Arquitetura:

- Socket.IO
- Room por user_id (sub)
- JWT validado na conexão
- notify_user() emite para room

Fluxo:

Evento → Persistência → Emit → Atualização React

---

# 🖥 Admin UI

## AdminPage
Tabs:
- RBAC
- Apps
- Routes

## RbacTab
- Users
- Roles
- Groups
- Permissions

## AppsTab
- Lista Apps
- Criar/Editar

## RoutesTab
- Rotas por App
- Associação de permissões

Proteção da rota:

- /admin
- Exige permission: rbac.manage
- Superadmin acessa independentemente

---

# 🚀 Estado Final da Fase 2

✔ Autenticação consolidada
✔ Autorização robusta
✔ Cache implementado
✔ Admin Backend completo
✔ Console Admin funcional
✔ Multi-app foundation
✔ Seeds idempotentes
✔ Estrutura pronta para plugins

---

# 🔮 Preparação para Fase 3

A base agora permite:

- Plugin system
- Manifest dinâmico
- App Federation
- Marketplace interno
- Multi-tenant
- Audit Log avançado

---

# 📌 Conclusão

A Fase 2 transforma a DELPI Central em uma plataforma estruturada, segura e escalável.

O sistema agora possui:

- Governança
- Controle granular
- Administração centralizada
- Infraestrutura preparada para expansão modular

---

**Documento oficial — DELPI Central Fase 2**
Versão: 1.0
Status: Concluída

