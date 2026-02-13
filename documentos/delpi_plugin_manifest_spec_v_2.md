# 🧩 DELPI Central — Especificação Oficial de Manifesto de Plugin

Versão do Documento: 2.0.0  
Status: Produção  
Compatível com Core API + RBAC + Plugin Registry

---

# 1️⃣ Objetivo

O manifesto de plugin define o contrato oficial entre um módulo (aplicação plugável) e a DELPI Central.

Ele permite:

- Registro automático de aplicações
- Criação automática de permissões
- Criação automática de rotas
- Integração com menu dinâmico
- Validação de segurança
- Governança centralizada
- Versionamento controlado
- Auditoria

---

# 2️⃣ Nome do Arquivo

```bash
delpi.manifest.json
```

---

# 3️⃣ Estrutura Completa do Manifesto (v2)

```json
{
  "schemaVersion": "2.0.0",
  "id": "crm",
  "name": "CRM DELPI",
  "description": "Sistema de gestão comercial e funil de vendas",
  "version": "2.1.0",
  "category": "comercial",
  "icon": "chart-line",
  "type": "microfrontend",
  "basePath": "/crm",
  "entry": "/apps/crm/remoteEntry.js",
  "healthcheck": "/apps/crm/health",
  "dependencies": [],
  "permissions": [
    {
      "code": "crm.access",
      "description": "Permite acessar o módulo CRM",
      "module": "crm"
    },
    {
      "code": "crm.leads.read",
      "description": "Visualizar leads",
      "module": "crm"
    },
    {
      "code": "crm.leads.write",
      "description": "Criar e editar leads",
      "module": "crm"
    }
  ],
  "routes": [
    {
      "path": "/crm",
      "label": "Dashboard",
      "icon": "layout-dashboard",
      "permission": "crm.access",
      "showInMenu": true,
      "order": 1,
      "menuGroup": "Comercial"
    },
    {
      "path": "/crm/leads",
      "label": "Leads",
      "icon": "users",
      "permission": "crm.leads.read",
      "showInMenu": true,
      "order": 2,
      "menuGroup": "Comercial"
    }
  ],
  "backend": {
    "required": true,
    "serviceName": "crm-api",
    "baseUrl": "/apps/crm/api",
    "validateJwt": true,
    "audience": "delpi-central",
    "issuer": "https://central.delpi.com.br/auth",
    "requiredPermissionsHeader": "x-user-permissions"
  },
  "features": {
    "enableFeatureFlags": true,
    "exposeMetrics": true,
    "supportsMultiTenant": false
  },
  "lifecycle": {
    "autoRegisterPermissions": true,
    "autoCreateRoutes": true,
    "allowVersionUpgrade": true,
    "allowHotReload": false
  },
  "security": {
    "contentSecurityPolicy": true,
    "allowIframeEmbedding": false,
    "requireHttps": true
  },
  "observability": {
    "healthEndpoint": "/health",
    "metricsEndpoint": "/metrics",
    "logFormat": "json"
  },
  "ui": {
    "displayInAppLauncher": true,
    "launcherOrder": 3,
    "badge": null
  },
  "metadata": {
    "author": "Equipe DELPI",
    "repository": "git@delpi.com:crm.git",
    "documentationUrl": "https://docs.delpi.com/crm",
    "supportEmail": "ti@delpi.com.br"
  }
}
```

---

# 4️⃣ Campos Obrigatórios

| Campo | Obrigatório | Descrição |
|--------|------------|-----------|
| schemaVersion | ✔ | Versão do contrato |
| id | ✔ | Identificador único do plugin |
| name | ✔ | Nome amigável |
| version | ✔ | Versionamento semântico |
| type | ✔ | microfrontend \| iframe \| backend-only |
| basePath | ✔ | Prefixo oficial da aplicação |
| permissions | ✔ | Lista de permissões declaradas |
| routes | ✔ | Rotas registráveis |

---

# 5️⃣ Tipos de Plugin Suportados

## microfrontend
Carregado via Module Federation

## iframe
Aplicação externa embutida

## backend-only
Sem interface, apenas API integrada

---

# 6️⃣ Regras de Validação

### ID
- Deve ser único
- Sem espaços
- Lowercase

### Version
- Deve seguir SemVer (MAJOR.MINOR.PATCH)

### Permissões
- Devem seguir padrão: module.resource.action
- Não podem colidir com outro módulo

### Rotas
- Devem iniciar com basePath
- Não podem sobrescrever rotas existentes

---

# 7️⃣ Fluxo Oficial de Registro

1. Plugin é deployado
2. Admin envia manifesto para Core API
3. Core valida schema
4. Core cria:
   - Registro em apps
   - Permissões
   - Rotas
   - Manifest armazenado
   - Log de auditoria
5. Portal atualiza menu dinamicamente

---

# 8️⃣ Versionamento e Upgrade

Quando versão muda:

- Se MAJOR → exige aprovação manual
- Se MINOR → cria novas permissões se existirem
- Se PATCH → apenas atualização técnica

Checksum pode ser armazenado para controle de integridade.

---

# 9️⃣ Suporte a Dependências Entre Plugins

Campo:

```json
"dependencies": ["core-dashboard", "shared-components"]
```

Core valida se dependências estão ativas antes de habilitar plugin.

---

# 🔟 Suporte Futuro Planejado

- Migrações automáticas
- Hooks de instalação
- Configuração dinâmica por tenant
- Marketplace interno de plugins
- Assinatura digital de manifesto

---

# 1️⃣1️⃣ Benefícios Arquiteturais

✔ Governança centralizada  
✔ Controle fino de permissões  
✔ Plugins realmente independentes  
✔ Segurança padronizada  
✔ Preparado para Kubernetes  
✔ Escalável para múltiplas equipes  
✔ Auditoria completa  
✔ Estrutura preparada para ABAC futuro

---

Documento oficial da especificação de plugins da DELPI Central.

