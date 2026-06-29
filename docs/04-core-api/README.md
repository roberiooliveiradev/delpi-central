# Core API — documentação

> **Código:** `core-api/` · **Base URL (gateway):** `/core-api`  
> **Status:** documentação oficial (maio/2026)

A Core API é o backend de **governança** da Minha DELPI: JWT/Keycloak, RBAC, plugins, favoritos, notificações e Socket.IO.

---

## Por onde começar

| Ordem | Documento | Uso |
|---:|---|---|
| 1 | [controllers-e-rotas.md](./controllers-e-rotas.md) | **Referência de rotas HTTP** (fonte enxuta) |
| 2 | [visao-geral-core-api.md](./visao-geral-core-api.md) | Visão enxuta: papel, camadas, fluxos |
| 3 | [../03-autenticacao-autorizacao/rbac.md](../03-autenticacao-autorizacao/rbac.md) | Autenticação vs autorização |
| 4 | [../10-guias-operacionais/registrar-plugin.md](../10-guias-operacionais/registrar-plugin.md) | Registrar manifestos |

---

## Documentos desta pasta

| Arquivo | Conteúdo |
|---|---|
| [controllers-e-rotas.md](./controllers-e-rotas.md) | Endpoints `/health`, `/me`, `/admin/apps`, `/admin/rbac`, integrações S2S |
| [diretorio-usuarios-integracoes.md](./diretorio-usuarios-integracoes.md) | `GET /integrations/directory/users` — PAC assignable users |
| [rastreamento-uso-apps.md](./rastreamento-uso-apps.md) | Uso de apps, integração api-delpi, LGPD, caller app |
| [visao-geral-core-api.md](./visao-geral-core-api.md) | Visão geral (enxuta) |
| [modelos-de-banco.md](./modelos-de-banco.md) | Models SQLAlchemy (`postgres-core`) |
| [migrations.md](./migrations.md) | Flask-Migrate / Alembic |
| [use-cases.md](./use-cases.md) | Casos de uso por domínio |
| [unit-of-work.md](./unit-of-work.md) | Transações, commit, eventos pós-commit |
| [repositories.md](./repositories.md) | Ports e implementações SQLAlchemy |
| [erros-api.md](./erros-api.md) | Formato `{ errors: [...] }` e helpers HTTP |
| [notificacoes.md](./notificacoes.md) | API `/me/notifications`, preferências, dispatch, cron |

---

## Stack e bootstrap

```text
Python 3 · Flask · SQLAlchemy · Flask-Migrate · Socket.IO (eventlet)
```

- Factory: `app/create_app.py`
- Migrations no boot: `docker-entrypoint.sh` → `flask db upgrade`
- Health: `GET /core-api/health` → `{"status":"Api rodando!"}`

---

## Blueprints registrados

| Blueprint | Prefixo | Arquivo |
|---|---|---|
| `health_bp` | `/` | `health_controller.py` |
| `me_bp` | `/` | `me_controller.py` |
| `admin_apps_bp` | `/admin/apps` | `apps_controller.py` |
| `rbac_bp` | `/admin/rbac/...` | `rbac_controller.py` |
| `integrations_directory_bp` | `/integrations/directory` | `integrations_directory_controller.py` |

---

## Documentos externos

- [../09-banco-de-dados/README.md](../09-banco-de-dados/README.md) · [core-db.md](../09-banco-de-dados/core-db.md)
- [../05-plugin-system/manifesto-plugin.md](../05-plugin-system/manifesto-plugin.md)
- [../02-infraestrutura/docker-compose.md](../02-infraestrutura/docker-compose.md)
