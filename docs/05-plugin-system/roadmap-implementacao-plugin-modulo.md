# Roadmap de implementação — plugin e módulo

> **Status:** planejamento (jun/2026)  
> **Especificação:** [plugin-vs-module.md](./plugin-vs-module.md) · [manifest-schema-1.1.0.md](./manifest-schema-1.1.0.md)

Implementar **nesta ordem**. Cada fase deve ter testes antes da seguinte.

---

## Visão geral das fases

```text
Fase 0 ─ Schema + validação Core API (sem runtime)
Fase 1 ─ /me/apps enriquecido + RouteDelegate no portal (POC SI → commercial)
Fase 2 ─ @delpi/module-runtime + branch module no AppHost
Fase 3 ─ menuGroup + política de launcher
Fase 4 ─ Migração maintenance
Fase 5 ─ Admin CRUD + colunas DB (opcional)
Fase 6 ─ CI gates + manifests produção 1.1.0
```

---

## Fase 0 — Schema e validação (Core API)

**Entrega:** manifests `1.1.0` passam no register; `1.0.0` inalterado; **sem** mudança no portal.

### Tarefas

- [ ] `ManifestVersionResolver` — aceitar `1.1.0`
- [ ] JSON Schema `1.1.0` (`target`, `ui.module`, `type` plugin/module)
- [ ] `manifest_normalizer` — trim/normalize `target`, defaults
- [ ] `manifest_rules.py` — regras §9 de `manifest-schema-1.1.0.md`
- [ ] Strategies: `plugin_strategy.py`, `module_strategy.py`; aliases `microfrontend`/`iframe`
- [ ] `RegisterPluginUseCase` — validar `composedPlugins` existem
- [ ] `UnregisterPluginUseCase` — bloquear se módulo depende do plugin
- [ ] Testes: `test_manifest_validator.py`, `test_manifest_rules.py`, fixtures SI/maintenance 1.1.0

### Arquivos principais

```
core-api/app/application/validators/manifest_version_resolver.py
core-api/app/application/validators/manifest_normalizer.py
core-api/app/application/validators/manifest_validator.py
core-api/app/domain/plugins/manifest_rules.py
core-api/app/application/validators/strategies/plugin_strategy.py      (novo)
core-api/app/application/validators/strategies/module_strategy.py      (novo)
core-api/app/infrastructure/plugins/schemas/delpi.manifest.schema.json
core-api/tests/... (fixtures manifest-1.1.0/)
```

### Critério de aceite

```bash
cd core-api && pytest app/tests/application/test_manifest_validator.py app/tests/domain/test_manifest_rules.py -q
# register dry-run com manifest SI 1.1.0 de fixture
```

---

## Fase 1 — API de leitura + delegate no portal (POC)

**Entrega:** `GET /me/apps` retorna `target` e `menuGroup`; portal redireciona SI `/departments/commercial` → `dashboard-commercial`.

### Core API

- [ ] `RouteDTO`: `target`, `menuGroup`
- [ ] `AppDTO`: `moduleConfig` (de `ui.module`)
- [ ] `app_query_repository.py` — merge manifest → DTO
- [ ] `ListUserAppsUseCase` — repassar campos
- [ ] Testes `test_list_user_apps_use_case.py`

### Portal

- [ ] `coreApi.ts` — tipos `RouteTarget`, `ModuleConfig`
- [ ] `appHostEntry.ts` — `resolveRouteTarget`, `resolveDelegatedApp`
- [ ] `RouteDelegate.tsx` (novo) ou lógica em `App.tsx` — `Navigate` quando `target.kind === plugin`
- [ ] Gate `requiredPermissions` + `onDenied`
- [ ] Testes unitários `appHostEntry`

### Manifest POC

- [ ] Fixture ou branch de `strategic-indicators.manifest.json` com uma rota `target` commercial (ambiente dev)

### Critério de aceite

- Usuário com SI + commercial abre `/apps/strategic-indicators/departments/commercial` e vê dashboard comercial
- Usuário só com SI vê fallback ou erro conforme `onDenied`

---

## Fase 2 — Module runtime

**Entrega:** módulos usam pacote compartilhado; `AppHost` passa `routeTarget` e catálogo de rotas.

### Pacote

- [ ] Criar `shared/delpi-module-runtime/` (ver [module-runtime.md](./module-runtime.md))
- [ ] `ModuleRouter`, `LocalViewRegistry`, `IframeEmbed`, `TileMenu`
- [ ] Testes Vitest no pacote

### MFE strategic-indicators

- [ ] `App.tsx` → `ModuleRuntime` + registry de views locais
- [ ] Remover redirect manual quando portal assumir delegate (ou manter fallback)

### Portal

- [ ] `AppHost` — props `routeTarget`, `manifestRoutes` para módulos
- [ ] Branch `app.type === module` (ou normalizado)

### Critério de aceite

- SI: rotas locais (executive, departments) via `viewId`
- SI: rota iframe de teste (se houver) via `target.kind: iframe`

---

## Fase 3 — Menu e launcher

**Entrega:** `menuGroup` no sidebar; plugins filhos opcionalmente ocultos do launcher.

### Portal

- [ ] `Sidebar.tsx` — agrupar por `menuGroup` dentro do app
- [ ] `useRoutesByApp.ts` — sort `menuGroup` + `order`
- [ ] `launchableApps.ts` — política `ui.displayInLauncher` (campo novo opcional no plugin)

### Core API (opcional)

- [ ] `ui.displayInLauncher` no schema plugin

### Critério de aceite

- Menu SI agrupa “Análise” vs “Departamentos” conforme manifest
- Dashboard-commercial pode ficar só acessível via SI (config)

---

## Fase 4 — Migração Manutenção

**Entrega:** `maintenance.manifest.json` `1.1.0` + `type: module`; reduzir `routeParser.ts`.

### Tarefas

- [ ] Converter rotas para `target` (local / iframe)
- [ ] `App.tsx` usa `ModuleRuntime`
- [ ] Manter paths legados (`/manutencao-geral` sem filial) como rotas com redirect ou parser fino
- [ ] Testes E2E smoke maintenance

### Arquivos

```
plugins/maintenance/maintenance.manifest.json
plugins/maintenance/src/App.tsx
plugins/maintenance/src/utils/routeParser.ts  → reduzir / deprecar
plugins/maintenance/src/constants/manutencaoGeralForm.ts → URL no manifest target
```

---

## Fase 5 — Admin e persistência (opcional)

**Entrega:** UI admin edita `menuGroup`; opcionalmente `target` via CRUD ou só via register.

### Core API

- [ ] Migration `menu_group`, `target_json` em `app_routes`
- [ ] `CreateAppRouteUseCase` / `UpdateRouteUseCase`
- [ ] Sync register/rollback com novas colunas

### Portal admin

- [ ] `ManifestRegisterModal` — tipo plugin/module, `RouteTargetFields`, `ModuleBaseFields`
- [ ] Consolidar `ManifestRegisterModal_2.tsx` (remover duplicata)
- [ ] `AppsTab` — labels plugin vs module

### Critério de aceite

- Admin registra módulo 1.1.0 pela UI sem JSON manual

---

## Fase 6 — Produção e CI

**Entrega:** gates e manifests reais em 1.1.0.

### CI

- [ ] Script `validate-manifest-1.1.0.py` ou estender register dry-run
- [ ] Gate: todo `composedPlugins` resolvível no registry
- [ ] Gate: módulos não referenciam apps inativos

### Manifests produção

- [ ] `strategic-indicators` → `1.2.0` type module
- [ ] `maintenance` → `0.3.0` type module
- [ ] Dashboards permanecem `type: plugin` (ou alias microfrontend)

### Documentação

- [ ] Atualizar [../08-plugins/README.md](../08-plugins/README.md) inventário
- [ ] Runbook [../10-guias-operacionais/registrar-plugin.md](../10-guias-operacionais/registrar-plugin.md)

### Dívida técnica

- [ ] Remover/corrigir `test_plugins_controller.py`, `test_routes_controller.py`, `test_me_controller.py` (órfãos)

---

## Inventário de plugins — classificação alvo

### Módulos (após migração)

| `id` | Versão alvo | Notas |
|------|-------------|-------|
| `strategic-indicators` | 1.2.0 | Delegate departamentos → dashboard-* |
| `maintenance` | 0.3.0 | Parser → target declarativo |

### Plugins (permanecem autônomos)

`dashboard-commercial`, `dashboard-production`, `dashboard-financial`, `dashboard-hr`, `dashboard-quality`, `dashboard-supplies`, `dashboard-engineering`, `dashboard-delpi`, `dash-lmps`, `minha-delpi-chat`, `eficiencia-fabril`, `auditoria-5s`, `central-agendamento`, `cadastro-kaizen`, `inspecoes-entrada`, `pedidos-venda-abertos`, `propostas-comerciais`, `api-delpi-console`, `cultura-delpi`, `transformometro`, `helpdesk`, `idd_production`, etc.

---

## Estimativa de esforço

| Fase | Esforço relativo |
|------|------------------|
| 0 | Médio |
| 1 | Alto |
| 2 | Alto |
| 3 | Médio |
| 4 | Alto |
| 5 | Médio |
| 6 | Baixo–médio |

---

## O que não entra neste roadmap

- Mudanças em **api-delpi**, **minha-delpi-ai-api**, **gateway nginx** (permanecem genéricos)
- Novo tipo **backend-only** (inalterado)
- Substituição de Keycloak / RBAC global
