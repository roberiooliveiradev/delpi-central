# Minha DELPI — Visão geral da Core API

> **Arquivo:** `docs/04-core-api/visao-geral-core-api.md`  
> **Status:** documentação oficial (maio/2026)  
> **Código:** `core-api/` · **Base URL:** `/core-api`

Visão **enxuta** da Core API. Detalhes de rotas, models, use cases e erros estão nos documentos linkados abaixo — não duplicar listagens longas neste arquivo.

---

## Documentação por tema

| Tema | Documento |
|---|---|
| **Rotas HTTP (referência)** | [controllers-e-rotas.md](./controllers-e-rotas.md) |
| Índice da pasta | [README.md](./README.md) |
| JWT / Keycloak | [../03-autenticacao-autorizacao/jwt.md](../03-autenticacao-autorizacao/jwt.md) |
| RBAC e permissões | [../03-autenticacao-autorizacao/rbac.md](../03-autenticacao-autorizacao/rbac.md) |
| Permission resolver | [../03-autenticacao-autorizacao/permission-resolver.md](../03-autenticacao-autorizacao/permission-resolver.md) |
| Schema `postgres-core` | [../09-banco-de-dados/core-db.md](../09-banco-de-dados/core-db.md) |
| Models SQLAlchemy | [modelos-de-banco.md](./modelos-de-banco.md) |
| Migrations | [migrations.md](./migrations.md) |
| Use cases | [use-cases.md](./use-cases.md) |
| Unit of Work | [unit-of-work.md](./unit-of-work.md) |
| Repositories | [repositories.md](./repositories.md) |
| Erros API | [erros-api.md](./erros-api.md) |
| Notificações | [notificacoes.md](./notificacoes.md) |
| Manifesto / plugins | [../05-plugin-system/manifesto-plugin.md](../05-plugin-system/manifesto-plugin.md) |
| Registrar plugin (runbook) | [../10-guias-operacionais/registrar-plugin.md](../10-guias-operacionais/registrar-plugin.md) |

---

## 1. Papel

A Core API é o backend de **governança** da Minha DELPI. Ela **não** implementa regras operacionais de negócio (TOTVS, KPIs, etc.) — isso é a [API DELPI](../07-api-delpi/visao-geral-api-delpi.md).

| Faz | Não faz |
|---|---|
| Validar JWT (Keycloak) e sincronizar usuário local | Consultar Protheus / SQL Server operacional |
| RBAC: roles, groups, permissions, superadmin | Substituir autorização do Keycloak (só autentica) |
| Apps, manifestos, versões, rotas de plugins | Lógica de domínio dos plugins (fica no MFE / API DELPI) |
| `/me`, `/me/apps`, favoritos, notificações | Menu hardcoded no Portal |
| Eventos `admin.changed` via Socket.IO | Chat / LLM (AI API) |

```text
Keycloak autentica → Core API autoriza → Portal consome /me e /me/apps
```

---

## 2. Stack e deploy

| Item | Valor |
|---|---|
| Linguagem | Python 3 |
| Framework | Flask, Flask-SQLAlchemy, Flask-Migrate (Alembic) |
| Tempo real | Flask-SocketIO (eventlet) |
| Banco | PostgreSQL (`postgres-core`) |
| Auth | JWT RS256 via JWKS (`delpi_auth` / validação Keycloak) |
| Container | `delpi-core-api` |
| Porta interna | `8000` |
| Health | `GET /core-api/health` → `{"status":"Api rodando!"}` |

Boot do container: `docker-entrypoint.sh` aguarda DB → `flask db upgrade` → `python -m app.main` (Socket.IO).

Variáveis: [../02-infraestrutura/variaveis-de-ambiente.md](../02-infraestrutura/variaveis-de-ambiente.md).

---

## 3. Estrutura do código

```text
core-api/app/
  create_app.py          # factory Flask
  main.py                # socketio.run
  application/           # use cases, validators, event_bus
  domain/                # ports, events, services (PermissionResolver, …)
  infrastructure/        # SQLAlchemy repos, cache, seeds, jwt
  interfaces/http/       # controllers + auth_middleware + security/*
  interfaces/socket/     # handlers Socket.IO
  extensions/            # db, migrate, socketio
```

| Camada | Responsabilidade |
|---|---|
| `interfaces` | HTTP fino, decorators, Socket.IO |
| `application` | Orquestração, validação de manifesto, UoW |
| `domain` | Regras e ports (sem Flask/SQLAlchemy) |
| `infrastructure` | Persistência, cache RBAC, dispatch de eventos |

---

## 4. Bootstrap (`create_app`)

```text
create_app()
  → Config / TestingConfig
  → db, migrate, socketio
  → before_request: authenticate()  (ignora se TESTING)
  → blueprints: health, rbac, admin_apps, me
  → seed_base_permissions() (fora de TESTING)
```

Models importados com `from app.infrastructure.db.models import *` para Alembic enxergar metadata — cuidado em refatorações.

Policies registradas via import de `app.interfaces.http.security.policies`.

---

## 5. Blueprints

| Blueprint | Prefixo | Controller |
|---|---|---|
| `health_bp` | `/health` | `health_controller.py` |
| `me_bp` | `/me`, `/me/apps`, … | `me_controller.py` |
| `admin_apps_bp` | `/admin/apps` | `apps_controller.py` |
| `rbac_bp` | `/admin/rbac/...` | `rbac_controller.py` |

Tabela completa de métodos e permissões: [controllers-e-rotas.md](./controllers-e-rotas.md).

---

## 6. Autenticação (middleware)

Arquivo: `app/interfaces/http/auth_middleware.py`.

```text
Authorization: Bearer <JWT>
  → valida issuer, audience, assinatura (JWKS)
  → sub (UUID), email, name
  → upsert users por email
  → PermissionResolver → g.current_user (roles, groups, permissions, is_superadmin)
```

**Importante:** sem token o middleware **não** retorna 401 sozinho. Endpoints protegidos usam `@require_auth()`, `@require_permission()`, `@require_superadmin()`.

Superadmin: bypass em decorators; bootstrap via `INITIAL_SUPERADMIN_EMAIL` no `.env`.

---

## 7. Domínios funcionais (resumo)

### 7.1 Usuário atual (`me_bp`)

- `GET /me` — perfil + permissions efetivas  
- `GET /me/apps` — apps ativos com rotas filtradas (`ListUserAppsUseCase` + `AppAuthorizationService`)  
- Favoritos e notificações — ver [notificacoes.md](./notificacoes.md)

### 7.2 RBAC (`rbac_bp`)

CRUD de roles, groups, users; vínculos; `GET /admin/rbac/permissions`. Portal admin: `portal/src/data/adminApi.ts`.

### 7.3 Plugin System (`admin_apps_bp`)

- `POST /admin/apps/register` — manifesto JSON → app, permissions, routes, versão  
- `PUT /admin/apps/<id>/manifest` — alterações **não estruturais**  
- Rollback, unregister, active, rotas admin  

Contrato: [manifesto-plugin.md](../05-plugin-system/manifesto-plugin.md). Fluxo técnico: [registro-de-plugin.md](../05-plugin-system/registro-de-plugin.md).

### 7.4 Eventos e Socket.IO

```text
Use case → UoW.commit() → EventBus → RbacEventHandler (invalida cache)
                      → SocketIOEventDispatcher → admin.changed / notification
```

Sala Socket = `sub` do JWT. Path público: `/socket.io/` (gateway → core-api). Detalhe: [../01-arquitetura/event-driven-e-socket.md](../01-arquitetura/event-driven-e-socket.md).

---

## 8. Transação e persistência

Padrão nos controllers:

```python
with SqlAlchemyUnitOfWork() as uow:
    result = SomeUseCase(uow).execute(...)
# commit + publicação de eventos no __exit__
```

`SqlAlchemyUnitOfWork` expõe repositories (`users`, `plugins`, `plugin_manifests`, `cache`, `events`, …). Ver [unit-of-work.md](./unit-of-work.md) e [repositories.md](./repositories.md).

Migration inicial: `7aa51b680332_initial_clean_schema_from_current_models.py`.

---

## 9. Erros

Formato único `{ "errors": [{ "code", "message", "path" }] }` — helpers em `app/interfaces/http/utils/errors.py`. Ver [erros-api.md](./erros-api.md).

---

## 10. Integração com o Portal

```text
Login Keycloak (portal)
  → GET /core-api/me
  → GET /core-api/me/apps  → menu + rotas React
  → AppHost (federated | iframe | external)
  → Socket.IO (reload após admin.changed)
```

Código: `portal/src/state/AuthContext.tsx`, `portal/src/ui/AppHost.tsx`, `portal/src/data/coreApi.ts`.

---

## 11. Pontos de atenção

1. Decorators obrigatórios em rotas protegidas — middleware não bloqueia sem token.  
2. Cache RBAC **em memória** por processo (réplicas múltiplas exigem estratégia distribuída ou invalidação via eventos).  
3. Permissões de plugin vêm do **manifesto** (`module` = `id` do plugin); seed só cria permissions de sistema.  
4. `sub` do JWT deve ser **UUID** válido.  
5. Não mover lógica operacional para a Core API.  
6. `import *` de models no bootstrap — necessário para migrations.  
7. Alguns use cases ainda podem fazer commit interno; preferir UoW externo.

---

## 12. Documentos relacionados

- [README.md](./README.md)
- [controllers-e-rotas.md](./controllers-e-rotas.md)
- [use-cases.md](./use-cases.md)
- [modelos-de-banco.md](./modelos-de-banco.md)
- [migrations.md](./migrations.md)
- [erros-api.md](./erros-api.md)
- [notificacoes.md](./notificacoes.md)
- [../03-autenticacao-autorizacao/rbac.md](../03-autenticacao-autorizacao/rbac.md)
- [../05-plugin-system/manifesto-plugin.md](../05-plugin-system/manifesto-plugin.md)
- [../06-portal-frontend/visao-geral-portal.md](../06-portal-frontend/visao-geral-portal.md)
