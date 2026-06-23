# Core API — alterações para plugin e módulo

> **Status:** especificação (implementação pendente)  
> **Roadmap:** [roadmap-implementacao-plugin-modulo.md](./roadmap-implementacao-plugin-modulo.md)

---

## 1. Escopo

Alterações no pacote **`core-api`** para suportar manifests `schemaVersion: "1.1.0"`, tipos `plugin`/`module`, `routes[].target`, `ui.module` e exposição enriquecida em `/me/apps`.

**Fora de escopo:** runtime do portal, pacote `@delpi/module-runtime`, builds Docker dos MFEs.

---

## 2. Endpoints existentes — impacto

| Método | Path | Mudança |
|--------|------|---------|
| `POST` | `/admin/apps/register` | Validar 1.1.0; strategies plugin/module |
| `PUT` | `/admin/apps/{id}/manifest` | Rejeitar mudança estrutural de `target`/`type` |
| `GET` | `/me/apps` | DTO com `target`, `menuGroup`, `moduleConfig` |
| `GET` | `/admin/apps/{id}/manifest` | Retorna manifest 1.1.0 completo |
| `POST` | `/admin/apps/{id}/rollback` | Restaura `target` do manifest histórico |
| `DELETE` | `/admin/apps/{id}` | Verificar dependentes em `composedPlugins` |
| `GET/POST/PUT/DELETE` | `/admin/apps/.../routes` | Fase 5: campos `menu_group`, `target_json` |

**Não implementar** `GET /me/routes` separado — manter rotas embutidas em `/me/apps` (corrigir teste órfão).

---

## 3. Pipeline de validação

### 3.1 Fluxo atual (mantido)

```text
ManifestNormalizer → ManifestVersionResolver → JSON Schema
  → Strategy por type → validate_manifest_rules() → ValidationResult
```

### 3.2 Alterações

| Componente | Arquivo | Alteração |
|------------|---------|-----------|
| Version resolver | `application/validators/manifest_version_resolver.py` | Mapear `1.1.0` → schema v1.1 |
| Schema | `infrastructure/plugins/schemas/delpi.manifest.schema.json` | Estender ou arquivo `*-1.1.0.json` |
| Normalizer | `application/validators/manifest_normalizer.py` | `target`, `ui.module` |
| Validator dispatch | `application/validators/manifest_validator.py` | `plugin`, `module` + aliases |
| Rules | `domain/plugins/manifest_rules.py` | Regras §9 schema 1.1.0 |
| Plugin strategy | `strategies/plugin_strategy.py` | **Novo** (substitui lógica microfrontend/iframe) |
| Module strategy | `strategies/module_strategy.py` | **Novo** |
| Microfrontend/iframe | `strategies/microfrontend_strategy.py`, `iframe_strategy.py` | Delegar para plugin_strategy ou deprecar |

---

## 4. Use cases

| Use case | Arquivo | Alterações |
|----------|---------|------------|
| Register | `register_plugin_use_case.py` | Validar `composedPlugins`; persistir manifest 1.1.0 |
| Update manifest | `update_plugin_manifest_use_case.py` | Bloquear diff estrutural em `target`, `type`, `ui.module` |
| List user apps | `list_user_apps_use_case.py` | Montar DTO enriquecido |
| Unregister | `unregister_plugin_use_case.py` | Checar módulos com `dependencies` apontando para id |
| Bulk unregister | `bulk_unregister_plugins_use_case.py` | Idem |
| Rollback | `rollback_plugin_version_use_case.py` | Sem mudança se manifest é fonte de `target` |
| Create/update route | `create_app_route_use_case.py`, `update_route_use_case.py` | Fase 5: `menu_group`, `target_json` |

---

## 5. DTOs e ports

### 5.1 `RouteDTO` (`domain/ports/app_query_port.py`)

Campos novos:

```python
menu_group: str | None = None
target: dict | None = None  # ou dataclass RouteTargetDTO
```

### 5.2 `AppDTO`

```python
module_config: dict | None = None  # ui.module do manifest
# type permanece string; normalizar plugin/module na leitura se necessário
```

### 5.3 `AdminRouteDTO` (Fase 5)

```python
menu_group: str | None
target_json: dict | None
```

---

## 6. Persistência

### 6.1 Tabelas atuais

| Tabela | Papel |
|--------|-------|
| `apps` | `type` aceita `plugin`, `module`, legados |
| `app_routes` | path, label, permission, order, show_in_menu |
| `app_manifests` | JSON completo — **fonte de `target` na Fase 1** |
| `app_versions` | Histórico |
| `permissions` | RBAC |

### 6.2 Leitura (`app_query_repository.py`)

Hoje:

- `entryUrl`, `renderMode` ← manifest
- `routes[].entry` ← manifest (merge por path)

Adicionar:

- `routes[].target` ← manifest
- `routes[].menuGroup` ← manifest
- `moduleConfig` ← `manifest.ui.module`

### 6.3 Migration Fase 5 (opcional)

```sql
-- migrations/versions/xxxx_app_routes_target_menu_group.py
ALTER TABLE app_routes ADD COLUMN IF NOT EXISTS menu_group VARCHAR(100);
ALTER TABLE app_routes ADD COLUMN IF NOT EXISTS target_json JSONB;
```

`plugin_route_repository.bulk_create` — popular na register a partir do manifest.

---

## 7. Telemetria e estatísticas

| Arquivo | Consideração |
|---------|--------------|
| `record_app_usage_use_case.py` | Delegate: qual `app_id` gravar |
| `app_usage_repository.py` | `BACKEND_ONLY_APP_TYPE` inalterado |
| `get_app_usage_snapshot_use_case.py` | Módulos contam como UI? |
| `get_least_engaged_users_use_case.py` | Incluir/excluir módulos |

**Recomendação:** gravar uso no **app efetivamente renderizado**; metadata `callerRoute`, `delegatedFrom`.

---

## 8. Eventos e auditoria

`AdminChangedEvent` em register/update/unregister — sem mudança de contrato.

Auditoria deve registrar mudanças de `type` e `target` em nova versão (register).

---

## 9. Testes

### Novos / atualizar

| Arquivo | Casos |
|---------|-------|
| `app/tests/application/test_manifest_validator.py` | Manifest plugin 1.1.0, module 1.1.0, aliases 1.0.0 |
| `app/tests/domain/test_manifest_rules.py` | `target_app_not_found`, cycle, module_config_required |
| `app/tests/use_cases/test_register_plugin_use_case.py` | composedPlugins |
| `app/tests/use_cases/test_list_user_apps_use_case.py` | target no response |
| `app/tests/use_cases/test_unregister_plugin_use_case.py` | dependente de módulo |

### Fixtures

```
core-api/tests/fixtures/manifests/
  plugin-dashboard-commercial-1.1.0.json
  module-strategic-indicators-1.1.0.json
  module-maintenance-1.1.0.json
```

### Corrigir órfãos

| Arquivo | Ação |
|---------|------|
| `test_plugins_controller.py` | Remover ou apontar para `apps_controller` |
| `test_routes_controller.py` | Idem |
| `test_me_controller.py` | Remover expectativa de `/me/routes` |

---

## 10. Lista completa de arquivos tocados

### Validação

- `app/application/validators/manifest_validator.py`
- `app/application/validators/manifest_normalizer.py`
- `app/application/validators/manifest_version_resolver.py`
- `app/application/validators/validation_result.py`
- `app/application/validators/strategies/manifest_strategy.py`
- `app/application/validators/strategies/plugin_strategy.py` *(novo)*
- `app/application/validators/strategies/module_strategy.py` *(novo)*
- `app/application/validators/strategies/microfrontend_strategy.py`
- `app/application/validators/strategies/iframe_strategy.py`
- `app/application/validators/strategies/backend_only_strategy.py`
- `app/domain/plugins/manifest_rules.py`
- `app/infrastructure/plugins/schemas/delpi.manifest.schema.json`

### Application

- `app/application/use_cases/register_plugin_use_case.py`
- `app/application/use_cases/update_plugin_manifest_use_case.py`
- `app/application/use_cases/list_user_apps_use_case.py`
- `app/application/use_cases/unregister_plugin_use_case.py`
- `app/application/use_cases/bulk_unregister_plugins_use_case.py`
- `app/application/use_cases/rollback_plugin_version_use_case.py`
- `app/application/use_cases/create_app_route_use_case.py` *(Fase 5)*
- `app/application/use_cases/update_route_use_case.py` *(Fase 5)*
- `app/application/services/app_authorization_service.py` *(se gate em target.requiredPermissions)*

### Infrastructure

- `app/infrastructure/persistence/sqlalchemy/app_query_repository.py`
- `app/infrastructure/persistence/sqlalchemy/plugin_route_repository.py` *(Fase 5)*
- `app/infrastructure/persistence/sqlalchemy/plugin_repository.py`
- `app/infrastructure/db/models/app_route.py` *(Fase 5)*

### HTTP

- `app/interfaces/http/apps_controller.py`
- `app/interfaces/http/me_controller.py`

### Migrations

- `migrations/versions/*_app_routes_target_menu_group.py` *(Fase 5)*

---

## 11. Compatibilidade

- Manifests `1.0.0` registrados **não** exigem re-register
- Coluna `apps.type` já é `String(50)` — sem migration obrigatória
- Portal antigo ignora campos novos em `/me/apps` até Fase 1
