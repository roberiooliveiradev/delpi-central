# Banco de dados — documentação

> **Escopo:** schemas persistidos pela Minha DELPI (governança e plugins)  
> **Status:** documentação oficial (maio/2026)

---

## Bancos na plataforma

| Banco / serviço | Container (dev) | Consumidor principal |
|---|---|---|
| **postgres-core** | `delpi-postgres-core` | Core API |
| **keycloak-db** | `delpi-keycloak-db` | Keycloak (não acessar pela app) |
| **postgres-plugins** | `delpi-postgres-plugins` | API DELPI, Minha DELPI AI API (pgvector) |
| TOTVS / SQL Server | externo | API DELPI |
| Portal RH | externo (opcional) | API DELPI |

Visão de infra: [../02-infraestrutura/bancos-de-dados.md](../02-infraestrutura/bancos-de-dados.md).

---

## Documentos desta pasta

| Arquivo | Conteúdo |
|---|---|
| [core-db.md](./core-db.md) | Schema completo do `postgres-core` (16 tabelas) |
| [modelo-rbac.md](./modelo-rbac.md) | Usuários, roles, groups, permissions, overrides |
| [modelo-plugin-system.md](./modelo-plugin-system.md) | Apps, rotas, manifestos, versões |

---

## Fonte de verdade do schema Core

| Artefato | Caminho |
|---|---|
| Migration inicial | `core-api/migrations/versions/7aa51b680332_initial_clean_schema_from_current_models.py` |
| Models SQLAlchemy | `core-api/app/infrastructure/db/models/` |
| Seed permissões base | `core-api/app/infrastructure/seeds/permissions_seed.py` |

Comandos: [../04-core-api/migrations.md](../04-core-api/migrations.md) · Reset local: [../10-guias-operacionais/reset-banco-dev.md](../10-guias-operacionais/reset-banco-dev.md).

---

## Diagrama resumido (`postgres-core`)

```text
users ──┬── user_roles ── roles ── role_permissions ── permissions
        ├── user_groups ── groups ── group_roles ──┘
        ├── user_permissions (granted) ──────────────┘
        ├── user_favorite_apps ── apps
        ├── notifications
        └── audit_logs

apps ──┬── app_routes ── permissions
       ├── app_manifests (JSON vigente)
       └── app_versions (histórico)
```

---

## Documentos relacionados

- [../04-core-api/README.md](../04-core-api/README.md)
- [../04-core-api/modelos-de-banco.md](../04-core-api/modelos-de-banco.md)
- [../03-autenticacao-autorizacao/permission-resolver.md](../03-autenticacao-autorizacao/permission-resolver.md)
