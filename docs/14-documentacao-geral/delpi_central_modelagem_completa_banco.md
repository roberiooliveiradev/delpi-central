# DELPI Central
## Modelagem Completa de Banco de Dados (PostgreSQL)

---

# 1. Conceitos Gerais

A modelagem contempla:

- RBAC completo (Role-Based Access Control)
- Controle por aplicação e rota
- Sistema plugável de módulos
- Permissões granulares
- Overrides por usuário
- Auditoria completa
- Estrutura preparada para escalar

Banco alvo: **PostgreSQL**

---

# 2. Estrutura de Identidade

## 2.1 users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    is_superadmin BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

---

## 2.2 groups

```sql
CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 2.3 roles

```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 2.4 permissions

```sql
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(150) UNIQUE NOT NULL,
    code VARCHAR(150) NOT NULL,
    description TEXT,
    module VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_permissions_module ON permissions(module);
```

---

# 3. Relacionamentos RBAC

## 3.1 user_roles

```sql
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);
```

---

## 3.2 role_permissions

```sql
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);
```

---

## 3.3 user_groups

```sql
CREATE TABLE user_groups (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, group_id)
);
```

---

## 3.4 group_roles

```sql
CREATE TABLE group_roles (
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (group_id, role_id)
);
```

---

## 3.5 user_permissions (Override)

```sql
CREATE TABLE user_permissions (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    granted BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (user_id, permission_id)
);
```

---

# 4. Sistema de Aplicações (Plugin System)

## 4.1 apps

```sql
CREATE TABLE apps (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    base_path VARCHAR(150) NOT NULL,
    icon VARCHAR(100),
    type VARCHAR(50) NOT NULL,
    version VARCHAR(20),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 4.2 app_routes

```sql
CREATE TABLE app_routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    app_id VARCHAR(50) REFERENCES apps(id) ON DELETE CASCADE,
    path VARCHAR(200) NOT NULL,
    label VARCHAR(150),
    icon VARCHAR(100),
    permission_id UUID REFERENCES permissions(id),
    show_in_menu BOOLEAN DEFAULT TRUE,
    order INT DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_app_routes_app ON app_routes(app_id);
```

---

## 4.3 app_manifests

```sql
CREATE TABLE app_manifests (
    app_id VARCHAR(50) PRIMARY KEY REFERENCES apps(id) ON DELETE CASCADE,
    manifest JSONB NOT NULL,
    checksum VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

# 5. Auditoria

## 5.1 audit_logs

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID,
    action VARCHAR(100),
    resource_type VARCHAR(100),
    resource_id VARCHAR(100),
    metadata JSONB,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_created_at ON audit_logs(created_at);
```

---

# 6. View de Permissões Efetivas

```sql
CREATE MATERIALIZED VIEW user_effective_permissions AS
SELECT DISTINCT
    u.id AS user_id,
    p.code AS permission_code
FROM users u
LEFT JOIN user_roles ur ON ur.user_id = u.id
LEFT JOIN role_permissions rp ON rp.role_id = ur.role_id
LEFT JOIN permissions p ON p.id = rp.permission_id
WHERE u.active = TRUE;
```

---

# 7. Diagrama Lógico Resumido

```
users
 ├── user_roles ── roles ── role_permissions ── permissions
 ├── user_groups ── groups ── group_roles ── roles
 └── user_permissions

apps
 └── app_routes ── permissions

app_manifests

audit_logs
```

---

# 8. Capacidades da Modelagem

- SSO via Keycloak
- Controle por módulo
- Controle por rota
- Permissão granular
- Plugins plugáveis
- Auditoria estruturada
- Preparado para futura evolução para ABAC
- Estrutura escalável para Kubernetes

---

Modelagem pronta para iniciar implementação da Core API com FastAPI + Alembic.

